import os
import json
import shutil
import zipfile
import ctypes
import subprocess
import threading
from pathlib import Path
import tkinter as tk
from tkinter import messagebox
import requests

# === Constants ===
SETTINGS_FILE = "settings.json"
APP_DIR = Path("C:/matcha/app/")
APP_EXE_UM = APP_DIR / "usermode/app.exe"
APP_EXE_KM = APP_DIR / "app.exe"
DESKTOP = Path.home() / "Desktop"
SHORTCUT_NAME = "Matcha Launcher.lnk"

VERSION_URL = "JSON FILE LOCATION IN THE WEB"
ZIP_URL = "ZIP FILE LOCATION IN THE WEB"

# === Settings Management ===
def load_settings() -> dict:
    """Load user settings from JSON file."""
    if Path(SETTINGS_FILE).exists():
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            messagebox.showwarning("Settings", "Settings file corrupted. Resetting.")
    return {"auto_launch": True, "auto_update": True, "version": "0.0"}

def save_settings(s: dict) -> None:
    """Save user settings to JSON file."""
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(s, f, indent=4)

settings = load_settings()

# === Update Handling ===
def update_app():
    """Download and install the latest app update."""
    try:
        on_update(True)
        resp = requests.get(ZIP_URL, stream=True, timeout=20)
        resp.raise_for_status()

        zip_path = Path("update.zip")
        with zip_path.open("wb") as f:
            for chunk in resp.iter_content(1024):
                f.write(chunk)

        if APP_DIR.exists():
            shutil.rmtree(APP_DIR)
        APP_DIR.mkdir(parents=True, exist_ok=True)

        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(APP_DIR)

        zip_path.unlink(missing_ok=True)
        messagebox.showinfo("Matcha", "Update installed successfully!")
    except Exception as e:
        messagebox.showerror("Error", f"Update failed: {e}")
    finally:
        on_update(False)

def check_update():
    """Check for updates and prompt user if available."""
    try:
        resp = requests.get(VERSION_URL, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        latest = data.get("version", settings["version"])
        changelog = data.get("Update", "No changelog provided.")

        if latest != settings["version"]:
            if messagebox.askyesno("Update available", f"New version {latest} found.\n\nChangelog:\n{changelog}\n\nInstall now?"):
                update_app()
                settings["version"] = latest
                save_settings(settings)
        else:
            messagebox.showinfo("Matcha", "Already up-to-date.")
    except Exception as e:
        messagebox.showerror("Error", f"Check failed: {e}")

# === Launch Functions ===
def launch_um():
    """Launch app in User Mode."""
    if APP_EXE_UM.exists():
        subprocess.Popen([str(APP_EXE_UM)], cwd=APP_DIR, shell=True)
    else:
        messagebox.showerror("Error", "App not installed!")

def launch_km():
    """Launch app in Kernel Mode (Admin required)."""
    if not ctypes.windll.shell32.IsUserAnAdmin():
        messagebox.showerror("Error", "Matcha Launcher must run as ADMIN for Kernel Mode!")
        return
    if APP_EXE_KM.exists():
        subprocess.Popen([str(APP_EXE_KM)], cwd=APP_DIR, shell=True)
    else:
        messagebox.showerror("Error", "App not installed!")

# === Settings Window ===
def open_settings():
    """Open the settings window."""
    win = tk.Toplevel(root)
    win.title("Settings")
    win.geometry("220x160")

    auto_launch_var = tk.BooleanVar(value=settings["auto_launch"])
    auto_update_var = tk.BooleanVar(value=settings["auto_update"])

    tk.Checkbutton(win, text="Auto Launch", variable=auto_launch_var).pack(pady=5)
    tk.Checkbutton(win, text="Auto Update", variable=auto_update_var).pack(pady=5)

    def save_and_close():
        settings["auto_launch"] = auto_launch_var.get()
        settings["auto_update"] = auto_update_var.get()
        save_settings(settings)
        win.destroy()

    def reinstall():
        Path(SETTINGS_FILE).unlink(missing_ok=True)
        threading.Thread(target=update_app, daemon=True).start()

    tk.Button(win, text="Re-install Matcha", command=reinstall).pack(pady=5)
    tk.Button(win, text="Save", command=save_and_close).pack(pady=5)

# === UI Setup ===
root = tk.Tk()
root.title("Matcha Launcher")
root.geometry("400x225")
root.configure(bg="black")
root.resizable(False, False)

messagebox.showwarning(
    "DISCLAIMER",
    f"All files will be downloaded from callmeagoodgirl.com\n"
    f"Installation path: {APP_DIR}\n\n"
    f"Katyusha/CMGG does NOT own Matcha, only redistributes the original files."
)

title = tk.Label(root, text="Matcha Launcher", fg="purple", bg="black", font=("Arial", 18))
title.pack(pady=5)

updating_label = tk.Label(root, text="Matcha Downloading~", fg="purple", bg="black", font=("Arial", 18))
updating_label.pack_forget()

btn_launch_um = tk.Button(root, text="Launch in UserMode", command=launch_um, width=20, bg="purple", fg="white")
btn_launch_um.pack(pady=5)

btn_launch_km = tk.Button(root, text="Launch in KernelMode", command=launch_km, width=20, bg="purple", fg="white")
btn_launch_km.pack(pady=5)

btn_update = tk.Button(
    root, text="Check for Updates",
    command=lambda: threading.Thread(target=check_update, daemon=True).start(),
    width=20, bg="purple", fg="white"
)
btn_update.pack(pady=5)

credit = tk.Label(root, text="Vault never did a launcher, so I did ~ KatyushaMeta",
                  fg="purple", bg="black", font=("Arial", 10))
credit.pack(pady=5)

btn_settings = tk.Button(root, text="⚙", command=open_settings, bg="black", fg="purple")
btn_settings.pack(pady=5)

ui_elements = [title, btn_launch_um, btn_launch_km, btn_update, credit, btn_settings]

# === UI Update State ===
def on_update(in_progress: bool):
    """Switch UI between normal and updating states."""
    if in_progress:
        for widget in ui_elements:
            widget.pack_forget()
        updating_label.pack()
    else:
        updating_label.pack_forget()
        for widget in ui_elements:
            widget.pack(pady=5)

# === Auto-update check ===
if settings.get("auto_update", True):
    threading.Thread(target=check_update, daemon=True).start()

root.mainloop()
