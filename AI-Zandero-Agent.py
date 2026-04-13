import requests
import subprocess
import shlex
import os
import sys
import re
import json
from datetime import datetime

API_KEY = "YOUR_API_KEY"
URL = "https://litellm.koboi2026.biz.id/v1/chat/completions"
MODEL = "vertex_ai/qwen/qwen3-coder-480b-a35b-instruct-maas"

MAX_STEPS = 12
MAX_HISTORY_CHARS = 8000
MAX_RETRIES = 3

MEMORY_FILE = os.path.expanduser("~/.xzv_agent_memory.json")

def load_memory() -> dict:
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE) as f:
                return json.load(f)
        except Exception:
            pass
    return {"facts": []}

def save_memory(mem: dict):
    try:
        with open(MEMORY_FILE, "w") as f:
            json.dump(mem, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"\033[91m[MEMORY ERROR] {e}\033[0m")

def add_fact(mem: dict, fact: str):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    mem["facts"].append(f"[{ts}] {fact}")
    if len(mem["facts"]) > 40:
        mem["facts"] = mem["facts"][-40:]
    save_memory(mem)

memory = load_memory()


BLOCKED_PATTERNS = ["rm -rf /", ":(){ :|:& };:", "dd if=/dev/zero", "mkfs"]

def execute(cmd: str) -> str:
    try:
        cmd = cmd.strip()
        if not cmd:
            return "[EMPTY COMMAND]"

        if len(cmd) >= 2 and cmd[0] == cmd[-1] and cmd[0] in ('"', "'"):
            cmd = cmd[1:-1]

        for bad in BLOCKED_PATTERNS:
            if bad in cmd:
                return f"[BLOCKED] Perintah berbahaya ditolak: '{bad}'"

        args = shlex.split(cmd)
        p = subprocess.run(
            args,
            capture_output=True,
            text=True,
            timeout=30,
            cwd=os.path.expanduser("~")
        )

        out = (p.stdout or "").strip()
        err = (p.stderr or "").strip()

        if p.returncode != 0:
            return f"[ERROR rc={p.returncode}]\n{err or out}"

        return out[:2000] if out else "[OK - no output]"

    except subprocess.TimeoutExpired:
        return "[TIMEOUT] Command terlalu lama (>30s)"
    except FileNotFoundError as e:
        return f"[NOT FOUND] {e} — coba cek apakah program terinstall"
    except Exception as e:
        return f"[EXCEPTION] {type(e).__name__}: {e}"

def call_llm(messages: list) -> str | None:
    try:
        r = requests.post(
            URL,
            json={
                "model": MODEL,
                "messages": messages,
                "temperature": 0.0
            },
            headers={"Authorization": f"Bearer {API_KEY}"},
            timeout=90
        )
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]

    except requests.exceptions.Timeout:
        print("\033[91m[LLM TIMEOUT] Server tidak merespons dalam 90s\033[0m")
        return None
    except requests.exceptions.ConnectionError:
        print("\033[91m[LLM ERROR] Tidak bisa konek ke server\033[0m")
        return None
    except Exception as e:
        print(f"\033[91m[LLM ERROR] {type(e).__name__}: {e}\033[0m")
        return None

def parse_response(res: str) -> tuple[str, str, str, str]:
    """
    Returns: (thought, action, final, memory_note)
    Semua field bisa berupa string kosong.
    """
    FLAGS = re.DOTALL | re.IGNORECASE

    m = re.search(r"THOUGHT:\s*(.*?)(?=ACTION:|FINAL:|MEMORY:|$)", res, FLAGS)
    thought = m.group(1).strip() if m else ""

    action = ""
    m = re.search(r"ACTION:\s*(.+?)(?=\nTHOUGHT:|\nFINAL:|\nMEMORY:|\nACTION:|$)", res, FLAGS)
    if m:
        raw = m.group(1).strip().split("\n")[0].strip()
        for label in ["OBSERVATION", "THOUGHT", "FINAL", "ACTION", "MEMORY"]:
            idx = raw.upper().find(label)
            if idx > 0:
                raw = raw[:idx].strip()
        action = raw

    m = re.search(r"FINAL:\s*(.*?)(?=ACTION:|THOUGHT:|MEMORY:|$)", res, FLAGS)
    final = m.group(1).strip() if m else ""

    m = re.search(r"MEMORY:\s*(.+?)(?=\n|ACTION:|THOUGHT:|FINAL:|$)", res, FLAGS)
    memory_note = m.group(1).strip() if m else ""

    return thought, action, final, memory_note


def is_valid(thought: str, action: str, final: str) -> bool:
    return bool(thought or action or final)

def trim_history(history: list) -> list:
    """Pertahankan system prompt + trim pesan lama jika context terlalu besar."""
    system_msgs = [m for m in history if m["role"] == "system"]
    other_msgs  = [m for m in history if m["role"] != "system"]

    total_chars = sum(len(m["content"]) for m in other_msgs)
    while total_chars > MAX_HISTORY_CHARS and len(other_msgs) > 2:
        removed = other_msgs.pop(0)
        total_chars -= len(removed["content"])

    return system_msgs + other_msgs

def build_system_prompt(mem: dict) -> str:
    facts_str = (
        "\n".join(f"  • {f}" for f in mem["facts"][-10:])
        if mem["facts"] else "  (belum ada)"
    )
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    return f"""Kamu adalah Zandero Terminal Agent — AI agent terminal yang cerdas, tepat, dan persisten.

## FORMAT OUTPUT (WAJIB):
Gunakan salah satu dari dua format ini saja:

Format A — saat perlu menjalankan command:
THOUGHT: <analisis singkat 1-2 kalimat>
ACTION: <satu command Linux>

Format B — saat sudah selesai:
THOUGHT: <analisis singkat>
FINAL: <jawaban akhir yang jelas untuk user>

Opsional — tambahkan jika menemukan fakta penting:
MEMORY: <fakta singkat untuk disimpan>

## ATURAN KERAS:
1. ACTION hanya SATU baris command terminal — tidak boleh multi-line.
2. Jangan pernah tulis kata OBSERVATION di output — itu tugasku.
3. Jangan tambah teks di luar format di atas.
4. Jika command gagal, analisis error dan coba command berbeda.
5. Jangan ulangi command yang sudah gagal persis sama.
6. Gunakan data dari OBSERVATION untuk reasoning selanjutnya.

## MEMORI DARI SESI SEBELUMNYA:
{facts_str}

## WAKTU SEKARANG: {now}
"""

def solve(goal: str, mem: dict):
    history = [
        {"role": "system", "content": build_system_prompt(mem)},
        {"role": "user",   "content": f"GOAL: {goal}"}
    ]

    print(f"\n\033[95m🚀 TARGET: {goal}\033[0m")

    bad_count = 0

    for step in range(1, MAX_STEPS + 1):
        print(f"\n\033[94m[Step {step}/{MAX_STEPS}]\033[0m", end=" ", flush=True)

        history = trim_history(history)
        res = call_llm(history)

        if res is None:
            bad_count += 1
            print(f"\033[91mLLM gagal (#{bad_count})\033[0m")
            if bad_count >= MAX_RETRIES:
                print("\033[91m❌ Terlalu banyak kegagalan. Berhenti.\033[0m")
                break
            continue

        thought, action, final, memory_note = parse_response(res)

        if not is_valid(thought, action, final):
            bad_count += 1
            print(f"\033[91m[FORMAT SALAH #{bad_count}]\033[0m")
            print(f"\033[90mRaw: {res[:250]}\033[0m")

            if bad_count >= MAX_RETRIES:
                print("\033[91m❌ Format tetap salah. Hentikan goal ini.\033[0m")
                break

            history.append({"role": "assistant", "content": res})
            history.append({
                "role": "user",
                "content": (
                    "⚠️ FORMAT SALAH. Gunakan HANYA:\n"
                    "THOUGHT: ...\nACTION: <command>\n\n"
                    "ATAU:\n"
                    "THOUGHT: ...\nFINAL: <jawaban>"
                )
            })
            continue

        bad_count = 0

        if thought:
            print(f"\033[93m💭 {thought}\033[0m")


        if memory_note:
            add_fact(mem, memory_note)
            print(f"\033[35m🧠 SAVED: {memory_note}\033[0m")


        if action:
            print(f"\033[92m⚡ CMD: {action}\033[0m")
            obs = execute(action)
            print(f"\033[90m📄 OBS: {obs[:500]}\033[0m")

            history.append({"role": "assistant", "content": res})
            history.append({
                "role": "user",
                "content": (
                    f"OBSERVATION:\n{obs}\n\n"
                    "Analisis hasil di atas lalu lanjut. "
                    "Jika gagal, coba pendekatan berbeda."
                )
            })
            continue

        if final:
            print(f"\n\033[1;32m✅ FINAL: {final}\033[0m")
            add_fact(mem, f"Selesai: '{goal[:60]}'")
            break

    else:
        print(f"\n\033[91m⚠️ Maks step ({MAX_STEPS}) tercapai tanpa jawaban final.\033[0m")

if __name__ == "__main__":
    os.system("clear")
    print("\033[1;36m╔══════════════════════════════════╗\033[0m")
    print("\033[1;36m║    Zandero AGENT V3 — SMART MODE     ║\033[0m")
    print("\033[1;36m╚══════════════════════════════════╝\033[0m")

    fact_count = len(memory.get("facts", []))
    print(f"\033[90m📚 Memory: {fact_count} facts | File: {MEMORY_FILE}\033[0m")
    print("\033[90mKetik 'memory' untuk lihat ingatan, 'clear memory' untuk hapus.\033[0m\n")

    while True:
        try:
            goal = input("\033[1;92mTarget > \033[0m").strip()

            if not goal:
                continue

            if goal.lower() in ("exit", "quit", "bye"):
                print("Bye 👋")
                sys.exit(0)

            elif goal.lower() == "memory":
                facts = memory.get("facts", [])
                if facts:
                    print("\n\033[35m🧠 MEMORY:\033[0m")
                    for f in facts[-20:]:
                        print(f"  {f}")
                else:
                    print("\033[90m(Memory kosong)\033[0m")

            elif goal.lower() == "clear memory":
                confirm = input("Yakin hapus semua memory? [y/N] ").strip().lower()
                if confirm == "y":
                    memory["facts"] = []
                    save_memory(memory)
                    print("\033[91m🗑️ Memory dihapus.\033[0m")

            else:
                solve(goal, memory)

        except KeyboardInterrupt:
            print("\nBye 👋")
            sys.exit(0)
