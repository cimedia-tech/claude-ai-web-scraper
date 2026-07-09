"""
Secure API Key Manager — drop your key in and save.
Built-in Python only (tkinter). No installs needed.
"""
import tkinter as tk
from tkinter import messagebox
from pathlib import Path

ENV_PATH = Path(__file__).parent / ".env"

def save_key():
    key = entry.get().strip()
    if not key.startswith("sk-ant-"):
        messagebox.showerror("Invalid Key", "Key must start with  sk-ant-\n\nGet it at: console.anthropic.com/settings/keys")
        return
    if not ENV_PATH.exists():
        messagebox.showerror("Missing .env", f".env file not found at:\n{ENV_PATH}")
        return
    content = ENV_PATH.read_text(encoding="utf-8")
    import re
    content = re.sub(r"ANTHROPIC_API_KEY=.*", f"ANTHROPIC_API_KEY={key}", content)
    ENV_PATH.write_text(content, encoding="utf-8")
    entry.delete(0, tk.END)
    entry.insert(0, "")
    status_var.set("✓  Key saved to .env  —  never pushed to GitHub")
    status_label.config(fg="#2ecc71")
    messagebox.showinfo("Saved", "API key saved successfully.\n\nYou can now run:\npython main.py scrape <url> --schema lead")

def toggle_show():
    if entry.cget("show") == "*":
        entry.config(show="")
        toggle_btn.config(text="Hide")
    else:
        entry.config(show="*")
        toggle_btn.config(text="Show")

# ── Window ──────────────────────────────────────────────────
root = tk.Tk()
root.title("Claude Scraper — API Key Setup")
root.geometry("560x300")
root.resizable(False, False)
root.configure(bg="#0d1120")

# ── Title ───────────────────────────────────────────────────
tk.Label(root, text="Claude AI Scraper", font=("Helvetica", 18, "bold"),
         bg="#0d1120", fg="#c8a96e").pack(pady=(28, 4))
tk.Label(root, text="Secure API Key Setup", font=("Helvetica", 11),
         bg="#0d1120", fg="#8891a8").pack(pady=(0, 24))

# ── Input row ───────────────────────────────────────────────
frame = tk.Frame(root, bg="#0d1120")
frame.pack(padx=40, fill="x")

tk.Label(frame, text="Anthropic API Key", font=("Helvetica", 10),
         bg="#0d1120", fg="#8891a8").pack(anchor="w", pady=(0, 6))

row = tk.Frame(frame, bg="#0d1120")
row.pack(fill="x")

entry = tk.Entry(row, show="*", font=("Courier New", 12),
                 bg="#121827", fg="#dde3f0", insertbackground="#3ddbd9",
                 relief="flat", bd=0, highlightthickness=1,
                 highlightbackground="#2a3a55", highlightcolor="#3ddbd9")
entry.pack(side="left", fill="x", expand=True, ipady=10, ipadx=10)
entry.focus()

toggle_btn = tk.Button(row, text="Show", font=("Helvetica", 9),
                       bg="#1a2540", fg="#8891a8", relief="flat",
                       padx=12, cursor="hand2", command=toggle_show)
toggle_btn.pack(side="left", padx=(6, 0))

# ── Hint ────────────────────────────────────────────────────
tk.Label(frame, text="Get your key at: console.anthropic.com/settings/keys",
         font=("Helvetica", 9), bg="#0d1120", fg="#4a5268").pack(anchor="w", pady=(6, 0))

# ── Save button ─────────────────────────────────────────────
tk.Button(root, text="  Save Key  ", font=("Helvetica", 11, "bold"),
          bg="#3ddbd9", fg="#060810", relief="flat", padx=20, pady=8,
          cursor="hand2", command=save_key).pack(pady=20)

# ── Status ──────────────────────────────────────────────────
status_var = tk.StringVar()
status_label = tk.Label(root, textvariable=status_var, font=("Helvetica", 9),
                        bg="#0d1120", fg="#4a5268")
status_label.pack()

root.mainloop()
