import requests
import subprocess
import os
import time
import sys

API_KEY = "YOUR_API_KEY"
URL = "YOUR_BASE_URL"
MODEL = "vertex_ai/qwen/qwen3-coder-480b-a35b-instruct-maas"
SELF_FILE = os.path.basename(__file__)

class UI:
    R = "\033[91m"
    G = "\033[92m"
    Y = "\033[93m"
    B = "\033[94m"
    P = "\033[95m"
    C = "\033[96m"
    W = "\033[0m"
    BOLD = "\033[1m"

class XZVAgentFinal:
    def __init__(self):
        self.workdir = os.getcwd()
        self.history = []
        self.system_prompt = f"""
        ROLE: Senior Autonomous Terminal Agent.
        STRICT RULES:
        1. JANGAN HALUSINASI: Kamu belum selesai jika belum ada ACTION yang sukses.
        2. FILE FIRST: Gunakan ACTION (echo/printf) untuk buat file sebelum menjalankannya.
        3. VERIFIKASI: Wajib jalankan file yang dibuat untuk cek outputnya.
        4. NO SELF-ACCESS: Dilarang akses/baca {SELF_FILE}.
        5. NO OVERTHINKING: Fokus ke GOAL. Jangan urus sistem/library.
        FORMAT:
        THOUGHT: <alasan>
        ACTION: <perintah terminal>
        FINAL_ANSWER: <hanya jika verifikasi sukses>
        """
        self.reset()

    def reset(self):
        self.history = [{"role": "system", "content": self.system_prompt}]

    def execute(self, cmd):
        if SELF_FILE in cmd and ("cat" in cmd or "rm" in cmd or "nano" in cmd):
            return f"Error: Access to {SELF_FILE} restricted."
        try:
            p = subprocess.run(cmd, shell=True, cwd=self.workdir, capture_output=True, text=True, timeout=45)
            return (p.stdout + "\n" + p.stderr).strip() or "Success (No Output)"
        except Exception as e:
            return f"Error: {str(e)}"

    def call_brain(self):
        try:
            r = requests.post(URL, json={
                "model": MODEL,
                "messages": self.history,
                "temperature": 0.0
            }, headers={"Authorization": f"Bearer {API_KEY}"}, timeout=60)
            return r.json()["choices"][0]["message"]["content"]
        except:
            return "THOUGHT: API Error.\nACTION: echo error"

    def solve(self, goal):
        self.reset()
        self.history.append({"role": "user", "content": f"GOAL: {goal}"})
        print(f"\n{UI.P}🚀 GOAL: {goal}{UI.W}")
        
        last_obs = ""
        for step in range(1, 21):
            print(f"{UI.B}[Step {step}]{UI.W} Thinking...", end="\r")
            res = self.call_brain()
            
            thought = action = final = ""
            for line in res.split('\n'):
                if line.startswith("THOUGHT:"): thought = line.replace("THOUGHT:", "").strip()
                if line.startswith("ACTION:"): action = line.replace("ACTION:", "").strip()
                if line.startswith("FINAL_ANSWER:"): final = line.replace("FINAL_ANSWER:", "").strip()

            if thought: print(f"\n{UI.Y}💭 {thought}{UI.W}")
            
            if final and not action and step == 1:
                self.history.append({"role": "user", "content": "Error: Kamu belum melakukan ACTION apa pun. Buat filenya dulu!"})
                continue

            if action:
                print(f"{UI.G}⚡ EXEC: {UI.C}{action}{UI.W}")
                last_obs = self.execute(action)
                print(f"{UI.W}📄 OBS: {last_obs[:150]}...")
                self.history.append({"role": "assistant", "content": res})
                self.history.append({"role": "user", "content": f"OBSERVATION: {last_obs}"})
                
                if "Error" in last_obs or "not found" in last_obs:
                    continue

            if final and not ("Error" in last_obs or "not found" in last_obs):
                print(f"\n{UI.G}✅ DONE: {final}{UI.W}")
                break

if __name__ == "__main__":
    agent = XZVAgentFinal()
    os.system("clear")
    print(f"{UI.C}--- XZV AGENT SUPREME v10 ---{UI.W}\n")
    while True:
        try:
            target = input(f"{UI.B}Target > {UI.W}").strip()
            if target.lower() in ['exit', 'quit']: break
            if target: agent.solve(target)
            print(f"\n{UI.P}{'-'*40}{UI.W}")
        except KeyboardInterrupt:
            break