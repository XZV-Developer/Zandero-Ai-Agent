# 🤖 Zandero Agent — Smart Terminal AI Agent

<div align="center">

![Python](https://img.shields.io/badge/Python-3.10+-blue?style=for-the-badge&logo=python)
![Platform](https://img.shields.io/badge/Platform-Linux%20%7C%20Termux-green?style=for-the-badge&logo=linux)
![LLM](https://img.shields.io/badge/LLM-LiteLLM%20Proxy-orange?style=for-the-badge)
![License](https://img.shields.io/badge/License-MIT-red?style=for-the-badge)

**AI agent terminal yang bisa berpikir, menjalankan command, dan mengingat — tanpa bingung.**

</div>

---

## ✨ Fitur Utama

| Fitur | Deskripsi |
|-------|-----------|
| 🧠 **Persistent Memory** | Ingatan tersimpan antar sesi di `~/.xzv_agent_memory.json` |
| ⚡ **Shell Operator Support** | Mendukung `>`, `>>`, `\|`, `&&`, `2>` dan operator shell lainnya |
| 🔁 **Auto Retry** | Jika LLM ngaco format, otomatis re-prompt sampai 3x |
| ✂️ **History Trimmer** | Context window otomatis dipangkas agar tidak overflow |
| 🔍 **Regex Parser** | Parser berbasis regex — lebih presisi dari string split biasa |
| 🛡️ **Safety Block** | Blokir command berbahaya secara otomatis |
| 🏷️ **MEMORY Tag** | Agent bisa menyimpan fakta penting sendiri ke memori |

---

## 🚀 Demo

```
╔══════════════════════════════════╗
║    Zandero AGENT V3 — SMART MODE     ║
╚══════════════════════════════════╝
📚 Memory: 3 facts

Target > buatkan script python print 1-20

🚀 TARGET: buatkan script python print 1-20

[Step 1/12] 💭 Membuat file Python untuk print angka 1-20.
⚡ CMD: printf "for i in range(1, 21):\n    print(i)\n" > print_numbers.py
📄 OBS: [OK - no output]

[Step 2/12] 💭 File berhasil dibuat. Jalankan untuk verifikasi.
⚡ CMD: python3 print_numbers.py
📄 OBS: 1
2
3
...
20

✅ FINAL: Script print_numbers.py berhasil dibuat dan berjalan dengan baik.
```

---

## 📦 Instalasi

### Termux / Linux

```bash
# Clone repo
git clone https://github.com/XZV-Developer/Zandero-Ai-Agent.git
cd Zandero-Ai-Agent

# Install dependency
pip install requests

# Jalankan
python AI-Zandero-Agent.py
```

### Requirements

- Python 3.10+
- `requests` library
- Akses ke LiteLLM proxy endpoint (atau API kompatibel OpenAI)

---

## ⚙️ Konfigurasi

Edit bagian ini di `AI-Zandero-Agent.py`:

```python
API_KEY = "YOUR_API_KEY"       # API key LiteLLM / OpenAI kamu
URL     = "https://..."        # URL endpoint LiteLLM proxy
MODEL   = "..."                # Model yang digunakan
```

Kamu juga bisa sesuaikan:

```python
MAX_STEPS        = 12    # Maksimum langkah per goal
MAX_HISTORY_CHARS = 8000 # Batas karakter history sebelum di-trim
MAX_RETRIES      = 3     # Maksimum retry jika LLM format salah
```

---

## 🧠 Sistem Memori

Agent menyimpan fakta penting secara otomatis ke file JSON:

```
~/.xzv_agent_memory.json
```

### Built-in Commands

| Command | Fungsi |
|---------|--------|
| `memory` | Tampilkan semua ingatan tersimpan |
| `clear memory` | Hapus seluruh ingatan |
| `exit` / `quit` | Keluar dari agent |

### MEMORY Tag

Agent bisa menyimpan fakta sendiri saat menemukan informasi penting:

```
THOUGHT: IP server ini adalah 192.168.1.1
ACTION: ping 192.168.1.1 -c 1
MEMORY: IP server lokal = 192.168.1.1
```

---

## 🔄 Format Agent

Agent menggunakan format ketat agar mudah di-parse:

```
# Format A — saat perlu action
THOUGHT: <analisis singkat>
ACTION: <satu command Linux>

# Format B — saat selesai
THOUGHT: <analisis>
FINAL: <jawaban akhir>

# Opsional
MEMORY: <fakta untuk disimpan>
```

---

## 🛡️ Safety

Command berikut diblokir secara otomatis:

```
rm -rf /
:(){ :|:& };:     (fork bomb)
dd if=/dev/zero
mkfs
```

---

## 📁 Struktur File

```
Zandero-Ai-Agent/
├── AI-Zandero-Agent.py.py       # Script utama
└── README.md             # Dokumentasi ini
```

Memory file dibuat otomatis saat pertama kali dijalankan:
```
~/.xzv_agent_memory.json
```

---

## 🗺️ Roadmap

- [ ] `PLAN:` tag — agent bikin rencana sebelum eksekusi
- [ ] Multi-directory support (cd antar folder)
- [ ] Web search tool integration
- [ ] Whitelist mode untuk keamanan ekstra
- [ ] Web UI via Flask

---

## 👨‍💻 Creator

<div align="center">

**XZV Developer**

[![GitHub](https://img.shields.io/badge/GitHub-XZV--Developer-black?style=for-the-badge&logo=github)](https://github.com/XZV-Developer)

*"Build tools that think."*

</div>

---

<div align="center">
<sub>Made with ☕ and too many terminal sessions</sub>
</div>

