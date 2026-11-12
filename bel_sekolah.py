"""
Bel Sekolah Otomatis - aplikasi desktop (Python + Tkinter)
By HDZMXX

Tidak perlu memasang paket tambahan di Windows.
Data (data/) dan nada (nada/) disimpan di sebelah aplikasi, jadi bisa dibawa sepaket.
Jalankan: python bel_sekolah.py
Jadikan .exe: pip install pyinstaller
              pyinstaller --noconsole --onefile bel_sekolah.py
"""
import datetime as dt
import json
import math
import os
import re
import shutil
import struct
import subprocess
import sys
import time
import wave
import zipfile
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, simpledialog, ttk

import ctypes

AUDIO_OK = True
if os.name == "nt":
    # Windows: pakai pemutar bawaan (MCI); jika gagal, cadangannya Windows Media Player lewat PowerShell.
    _winmm = ctypes.windll.winmm
    _ps = None
    _PS = ("param([string]$f,[double]$v)\n"
           "try {\n"
           "Add-Type -AssemblyName PresentationCore\n"
           "$p = New-Object System.Windows.Media.MediaPlayer\n"
           "$p.Volume = $v\n$p.Open((New-Object System.Uri($f)))\n$p.Play()\n"
           "$n = 0\n"
           "while (-not $p.NaturalDuration.HasTimeSpan -and $n -lt 50) { Start-Sleep -Milliseconds 100; $n++ }\n"
           "if (-not $p.NaturalDuration.HasTimeSpan) { exit 4 }\n"
           "Start-Sleep -Seconds ([math]::Ceiling($p.NaturalDuration.TimeSpan.TotalSeconds) + 2)\n"
           "} catch { exit 3 }\n")

    def _mci(cmd):
        return _winmm.mciSendStringW(cmd, ctypes.create_unicode_buffer(256), 255, 0)

    def _mci_msg(err):
        b = ctypes.create_unicode_buffer(256); _winmm.mciGetErrorStringW(err, b, 255)
        return f"{b.value} (kode {err})"

    def _short(p):
        try:
            b = ctypes.create_unicode_buffer(520)
            return b.value if ctypes.windll.kernel32.GetShortPathNameW(p, b, 520) else p
        except Exception:
            return p

    def audio_stop():
        global _ps
        _mci("stop bel"); _mci("close bel")
        if _ps is not None and _ps.poll() is None:
            _ps.kill()
        _ps = None

    def audio_play(path, vol):
        global _ps
        audio_stop()
        tries = [(path, "")] if path.lower().endswith(".wav") else [(path, "mpegvideo"), (_short(path), "mpegvideo"), (path, "")]
        err = 0
        for p, typ in tries:
            err = _mci(f'open "{p}"' + (f" type {typ}" if typ else "") + " alias bel")
            if not err:
                _mci(f"setaudio bel volume to {int(vol * 1000)}")
                err = _mci("play bel")
                if not err:
                    return None
                _mci("close bel")
        try:  # cadangan: Windows Media Player lewat PowerShell (jalur lengkap)
            root = os.environ.get("SystemRoot", r"C:\Windows")
            exes = [os.path.join(root, d, "WindowsPowerShell", "v1.0", "powershell.exe") for d in ("System32", "Sysnative")]
            exe = next((e for e in exes if os.path.isfile(e)), shutil.which("powershell") or shutil.which("pwsh"))
            if not exe:
                return f"{_mci_msg(err)}; powershell.exe tidak ditemukan di komputer ini"
            ps1 = APP_DIR / "putar.ps1"
            ps1.write_text(_PS, encoding="utf-8")
            _ps = subprocess.Popen([exe, "-NoProfile", "-ExecutionPolicy", "Bypass", "-WindowStyle", "Hidden",
                                    "-File", str(ps1), "-f", path, "-v", str(vol)], creationflags=0x08000000)
            return None
        except Exception as e:
            return f"{_mci_msg(err)}; cadangan PowerShell gagal: {e}"

    def audio_failed():
        """Dipanggil beberapa detik setelah memutar; kembalikan pesan jika pemutar cadangan berhenti lebih awal."""
        if _ps is None or _ps.poll() is None:
            return None
        return ("Windows tidak bisa membuka mp3 ini (format atau codec tidak didukung). "
                f"Coba ubah ke mp3 biasa atau wav. (kode {_ps.poll()})")
else:
    try:  # Linux/Mac: butuh pygame
        os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
        import pygame
        pygame.mixer.init()

        def audio_failed():
            return None

        def audio_stop():
            pygame.mixer.music.stop()

        def audio_play(path, vol):
            pygame.mixer.music.load(path); pygame.mixer.music.set_volume(vol); pygame.mixer.music.play()
    except Exception:
        AUDIO_OK = False

BASE = Path(sys.executable).parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parent


def _writable(d):
    try:
        d.mkdir(parents=True, exist_ok=True)
        t = d / ".tulis"; t.write_text("x"); t.unlink()
        return True
    except OSError:
        return False


# Mode portabel: folder "data" dan "nada" ada di sebelah aplikasi (sepaket).
# Jika folder itu tidak bisa ditulis (mis. Program Files), pindah ke APPDATA.
_HOME = Path(os.environ.get("APPDATA", Path.home())) / "BelSekolahOtomatis"
PORTABLE = _writable(BASE / "data")
APP_DIR = BASE / "data" if PORTABLE else _HOME
NADA = BASE / "nada" if PORTABLE and _writable(BASE / "nada") else APP_DIR / "nada"
NADA.mkdir(parents=True, exist_ok=True)
CFG = APP_DIR / "config.json"
if not CFG.exists() and (_HOME / "config.json").exists():  # pindahkan data versi lama
    try:
        shutil.copy2(_HOME / "config.json", CFG)
    except OSError:
        pass
_PKG = Path(getattr(sys, "_MEIPASS", "")) / "nada"
if getattr(sys, "frozen", False) and _PKG.is_dir():  # nada yang ikut dibungkus ke dalam .exe
    for _f in _PKG.rglob("*"):
        _d = NADA / _f.relative_to(_PKG)
        try:
            if _f.is_file() and not _d.exists():
                _d.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(_f, _d)
        except OSError:
            pass
APP_NAME, APP_BY = "Bel Sekolah Otomatis", "HDZMXX"
KEYS = ("id", "cat", "desc", "day", "time", "sound")
HARI = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]  # weekday(): Senin=0
OPT = [("0", "Senin"), ("1", "Selasa"), ("2", "Rabu"), ("3", "Kamis"), ("4", "Jumat"),
       ("5", "Sabtu"), ("6", "Minggu"), ("mt", "Senin–Kamis"), ("wd", "Senin–Jumat"), ("ws", "Senin–Sabtu")]
BUILTIN = {"builtin:chime": "Ding-dong (bawaan)", "builtin:long": "Bel panjang (bawaan)"}
BG, PN, TX, MU, AC, OK, BAD = "#0d1420", "#151f30", "#e8edf5", "#93a0b5", "#e0a43a", "#4cc38a", "#ff8a80"
LN, SB, BTN, HOV = "#25324a", "#0a111d", "#1f2d47", "#2a3b5c"


def default_cfg():
    def it(i, d, day, t, s):
        return {"id": i, "cat": "Reguler", "desc": d, "day": day, "time": t, "sound": s}
    return {"school": "SMPN 3 Kebumen", "addr": "Jl. S. Parman No. 3", "vol": 1.0, "armed": True,
            "cats": ["Reguler", "Ujian"], "active": "Reguler", "items": [
                it(1, "Bel masuk", "ws", "07:00:00", "builtin:chime"),
                it(2, "Istirahat pertama", "wd", "09:20:00", "builtin:long"),
                it(3, "Masuk setelah istirahat", "wd", "09:40:00", "builtin:chime"),
                it(4, "Bel pulang", "wd", "13:30:00", "builtin:long")]}


def synth(path, notes, total, rate=22050):
    """Buat file WAV sederhana bernada lonceng dari daftar (frekuensi, mulai, durasi)."""
    buf = [0.0] * int(total * rate)
    for f, start, dur in notes:
        s0 = int(start * rate)
        for i in range(int(dur * rate)):
            if s0 + i >= len(buf):
                break
            t = i / rate
            env = min(1.0, t / 0.02) * math.exp(-5 * t / dur)
            buf[s0 + i] += env * (math.sin(2 * math.pi * f * t) + 0.25 * math.sin(2 * math.pi * f * 2.76 * t))
    peak = max(1e-9, max(abs(x) for x in buf))
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(rate)
        w.writeframes(b"".join(struct.pack("<h", int(x / peak * 26000)) for x in buf))


def ensure_builtin():
    APP_DIR.mkdir(parents=True, exist_ok=True)
    if not (APP_DIR / "chime.wav").exists():
        synth(APP_DIR / "chime.wav", [(784, 0, 1.2), (622, .8, 1.6), (784, 2.8, 1.2), (622, 3.6, 1.6)], 5.4)
    if not (APP_DIR / "long.wav").exists():
        synth(APP_DIR / "long.wav", [(880, i * .28, .25) for i in range(12)], 3.5)


def resolve(ref):
    if ref.startswith("builtin:"):
        return str(APP_DIR / (ref.split(":")[1] + ".wav"))
    p = Path(ref)
    return str(p if p.is_absolute() else BASE / p)


def ref_nada(name):
    return f"nada/{name}" if NADA == BASE / "nada" else str(NADA / name)


def keep_awake(on):
    try:
        import ctypes
        ctypes.windll.kernel32.SetThreadExecutionState(0x80000000 | (0x1 if on else 0))
    except Exception:
        pass


def set_autostart(on):
    import winreg
    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run",
                         0, winreg.KEY_SET_VALUE | winreg.KEY_QUERY_VALUE)
    if on:
        exe = sys.executable
        if getattr(sys, "frozen", False):
            cmd = f'"{exe}"'
        else:
            pw = exe.replace("python.exe", "pythonw.exe")
            cmd = f'"{pw if os.path.exists(pw) else exe}" "{os.path.abspath(__file__)}"'
        winreg.SetValueEx(key, "BelSekolahOtomatis", 0, winreg.REG_SZ, cmd)
    else:
        try:
            winreg.DeleteValue(key, "BelSekolahOtomatis")
        except FileNotFoundError:
            pass


def autostart_on():
    try:
        import winreg
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run")
        winreg.QueryValueEx(key, "BelSekolahOtomatis")
        return True
    except Exception:
        return False


class ItemDialog(tk.Toplevel):
    def __init__(self, app, item=None):
        super().__init__(app)
        self.app, self.item = app, item
        self.title("Ubah jadwal" if item else "Jadwal baru")
        self.configure(bg=BG, padx=16, pady=16)
        self.transient(app); self.grab_set(); self.resizable(True, False)
        for c in (1, 2, 3):
            self.columnconfigure(c, weight=1)
        ttk.Label(self, text="Keterangan").grid(row=0, column=0, sticky="w", pady=4)
        self.desc = tk.StringVar(value=item["desc"] if item else "")
        self.desc_entry = ttk.Entry(self, textvariable=self.desc, width=44)
        self.desc_entry.grid(row=0, column=1, columnspan=3, sticky="we")
        ttk.Label(self, text="Hari").grid(row=1, column=0, sticky="w", pady=4)
        self.day = ttk.Combobox(self, values=[n for _, n in OPT], state="readonly", width=16)
        self.day.set(dict(OPT)[item["day"]] if item else "Senin–Jumat")
        self.day.grid(row=1, column=1, sticky="w")
        ttk.Label(self, text="Jam (jam:menit:detik)").grid(row=2, column=0, sticky="w", pady=4)
        h, m, s = (item["time"] if item else "07:00:00").split(":")
        fr = ttk.Frame(self); fr.grid(row=2, column=1, sticky="w")
        self.sp = []
        for val, mx in ((h, 23), (m, 59), (s, 59)):
            sb = ttk.Spinbox(fr, from_=0, to=mx, width=4, format="%02.0f", wrap=True)
            sb.set(val); sb.pack(side="left", padx=(0, 4)); self.sp.append(sb)
        ttk.Label(self, text="Nada bel").grid(row=3, column=0, sticky="w", pady=4)
        self.snd = tk.StringVar(value=app.sound_label(item["sound"]) if item else BUILTIN["builtin:chime"])
        ttk.Combobox(self, textvariable=self.snd, values=list(BUILTIN.values()), width=42).grid(row=3, column=1, columnspan=3, sticky="we")
        row = ttk.Frame(self); row.grid(row=4, column=1, columnspan=3, sticky="w", pady=4)
        ttk.Button(row, text="Pilih mp3 dari komputer…", command=self.browse).pack(side="left", padx=(0, 6))
        ttk.Button(row, text="Putar", command=lambda: app.play(self.ref())).pack(side="left", padx=(0, 6))
        ttk.Button(row, text="Berhenti", command=app.stop).pack(side="left")
        bt = ttk.Frame(self); bt.grid(row=5, column=0, columnspan=4, sticky="we", pady=(12, 0))
        self.again, self.keep = tk.BooleanVar(value=False), tk.BooleanVar(value=False)
        if not item:  # hanya untuk jadwal baru
            opt = ttk.Frame(bt); opt.pack(side="left")
            ttk.Checkbutton(opt, text="Buat lagi setelah simpan", variable=self.again,
                            command=self._sync_opts).pack(side="left", padx=(0, 14))
            self.keep_cb = ttk.Checkbutton(opt, text="Pertahankan data yang diisi", variable=self.keep, state="disabled")
            self.keep_cb.pack(side="left")
        rt = ttk.Frame(bt); rt.pack(side="right")
        ttk.Button(rt, text="Simpan", style="Accent.TButton", command=self.save).pack(side="left", padx=6)
        ttk.Button(rt, text="Batal", command=self.destroy).pack(side="left")
        self.msg = ttk.Label(self, text="", foreground=OK)
        self.msg.grid(row=6, column=0, columnspan=4, sticky="w", pady=(6, 0))
        self.desc_entry.focus_set()

    def _sync_opts(self):
        self.keep_cb.config(state="normal" if self.again.get() else "disabled")
        if not self.again.get():
            self.keep.set(False)

    def reset_fields(self):
        self.desc.set(""); self.day.set("Senin–Jumat")
        for sb, v in zip(self.sp, ("07", "00", "00")):
            sb.set(v)
        self.snd.set(BUILTIN["builtin:chime"])

    def browse(self):
        p = filedialog.askopenfilename(parent=self, title="Pilih nada bel", initialdir=str(NADA),
                                       filetypes=[("Berkas audio", "*.mp3 *.wav *.ogg"), ("Semua berkas", "*.*")])
        if p:
            self.snd.set(self.app.import_sound(p))

    def ref(self):
        v = self.snd.get().strip()
        for k, n in BUILTIN.items():
            if v == n:
                return k
        return v

    def save(self):
        d = self.desc.get().strip()
        if not d:
            messagebox.showwarning("Keterangan kosong", "Isi keterangan jadwal.", parent=self); return
        try:
            hh, mm, ss = (int(float(x.get())) for x in self.sp)
            t = dt.time(hh, mm, ss).strftime("%H:%M:%S")
        except ValueError:
            messagebox.showwarning("Jam tidak valid", "Periksa jam, menit, dan detik.", parent=self); return
        ref = self.ref()
        if not ref.startswith("builtin:") and not os.path.isfile(resolve(ref)):
            messagebox.showwarning("Berkas tidak ditemukan", "Pilih berkas mp3 yang ada di komputer.", parent=self); return
        day = next(k for k, n in OPT if n == self.day.get())
        o = {"id": self.item["id"] if self.item else int(time.time() * 1000), "cat": self.app.cfg["active"],
             "desc": d, "day": day, "time": t, "sound": ref}
        its = self.app.cfg["items"]
        if self.item:
            its[its.index(self.item)] = o
        else:
            its.append(o)
        self.app.save(); self.app.refresh_list()
        if not self.item and self.again.get():
            self.msg.config(text=f"✔ “{d}” tersimpan. Silakan isi jadwal berikutnya.")
            if not self.keep.get():
                self.reset_fields()
            self.desc_entry.focus_set(); self.desc_entry.select_range(0, "end")
            return
        self.destroy()


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        ensure_builtin()
        self.cfg = default_cfg()
        try:
            self.cfg.update(json.loads(CFG.read_text(encoding="utf-8")))
        except Exception:
            pass
        self.armed = self.cfg.get("armed", True)
        self.last_key = ""
        self.last_ring = ""
        self.title(f"{APP_NAME} - by {APP_BY}")
        self.geometry("1040x700"); self.minsize(820, 660); self.configure(bg=BG)
        self.style_ui()
        self.build()
        self.build_menu()
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        keep_awake(self.armed)
        self.tick()

    # ---------- gaya ----------
    def style_ui(self):
        s = ttk.Style(self); s.theme_use("clam")
        s.configure(".", background=BG, foreground=TX, fieldbackground=PN, font=("Segoe UI", 10),
                    bordercolor=LN, lightcolor=PN, darkcolor=PN, troughcolor=PN)
        s.configure("TFrame", background=BG)
        s.configure("Card.TFrame", background=PN, bordercolor=LN, borderwidth=1, relief="solid")
        s.configure("TLabel", background=BG, foreground=TX)
        s.configure("Mu.TLabel", foreground=MU)
        s.configure("H1.TLabel", font=("Georgia", 20, "bold"))
        s.configure("Card.TLabel", background=PN)
        s.configure("CardMu.TLabel", background=PN, foreground=MU)
        s.configure("CardH.TLabel", background=PN, font=("Segoe UI", 12, "bold"))
        s.configure("TButton", background=BTN, foreground=TX, padding=(14, 8), borderwidth=0, relief="flat", focuscolor=BTN)
        s.map("TButton", background=[("active", HOV), ("pressed", HOV)])
        s.configure("Accent.TButton", background=AC, foreground="#1a1200", font=("Segoe UI", 10, "bold"), focuscolor=AC)
        s.map("Accent.TButton", background=[("active", "#f0b64d"), ("pressed", "#f0b64d")])
        s.configure("Nav.TButton", background=SB, foreground=MU, anchor="w", padding=(20, 12), font=("Segoe UI", 11), focuscolor=SB)
        s.map("Nav.TButton", background=[("active", "#16233a")], foreground=[("active", TX)])
        s.configure("NavOn.TButton", background="#16233a", foreground=AC, anchor="w", padding=(20, 12), font=("Segoe UI", 11, "bold"), focuscolor="#16233a")
        s.map("NavOn.TButton", background=[("active", "#16233a")])
        s.configure("Treeview", background=PN, fieldbackground=PN, foreground=TX, rowheight=34, borderwidth=0, font=("Segoe UI", 10))
        s.configure("Treeview.Heading", background=SB, foreground=MU, padding=8, relief="flat", font=("Segoe UI", 10, "bold"))
        s.map("Treeview", background=[("selected", "#34476c")], foreground=[("selected", "#ffffff")])
        s.map("Treeview.Heading", background=[("active", SB)])
        s.configure("Vertical.TScrollbar", background=BTN, troughcolor=PN, bordercolor=PN, arrowcolor=MU, relief="flat")
        s.configure("TEntry", fieldbackground=SB, insertcolor=TX, padding=6, bordercolor=LN)
        s.configure("TSpinbox", fieldbackground=SB, insertcolor=TX, padding=4, arrowcolor=TX, bordercolor=LN)
        s.configure("TCombobox", fieldbackground=SB, background=BTN, arrowcolor=TX, padding=5, bordercolor=LN)
        s.map("TCombobox", fieldbackground=[("readonly", SB)], foreground=[("readonly", TX)],
              selectbackground=[("readonly", SB)], selectforeground=[("readonly", TX)])
        for st, bg in (("TCheckbutton", BG), ("Card.TCheckbutton", PN)):
            s.configure(st, background=bg, foreground=TX, focuscolor=bg)
            s.map(st, background=[("active", bg), ("disabled", bg), ("pressed", bg)],
                  foreground=[("active", TX), ("disabled", "#5d6b82")],
                  indicatorbackground=[("disabled", "#1f2a40"), ("!disabled", "#ffffff")],
                  indicatorforeground=[("disabled", "#5d6b82"), ("!disabled", "#1a1200")])
        s.configure("Horizontal.TScale", background=PN, troughcolor=SB)
        self.option_add("*TCombobox*Listbox.background", PN)
        self.option_add("*TCombobox*Listbox.foreground", TX)
        self.option_add("*TCombobox*Listbox.selectBackground", AC)
        self.option_add("*TCombobox*Listbox.selectForeground", "#1a1200")

    # ---------- susunan (semua mengikuti ukuran jendela) ----------
    def build(self):
        root = ttk.Frame(self); root.pack(fill="both", expand=True)
        root.columnconfigure(1, weight=1); root.rowconfigure(0, weight=1)
        side = tk.Frame(root, bg=SB, width=230); side.grid(row=0, column=0, sticky="ns"); side.pack_propagate(False)
        tk.Label(side, text="Bel Sekolah", bg=SB, fg=AC, font=("Georgia", 16, "bold italic")).pack(anchor="w", padx=20, pady=(24, 0))
        tk.Label(side, text="Otomatis", bg=SB, fg=MU, font=("Georgia", 11, "italic")).pack(anchor="w", padx=20)
        tk.Label(side, text=f"by {APP_BY}", bg=SB, fg=AC, font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=20, pady=(2, 20))
        self.nav = {}
        for key, txt in (("home", "Beranda"), ("sched", "Jadwal"), ("set", "Pengaturan")):
            b = ttk.Button(side, text=txt, style="Nav.TButton", command=lambda k=key: self.show(k), cursor="hand2")
            b.pack(fill="x", padx=8, pady=2); self.nav[key] = b
        tk.Label(side, text="Biarkan aplikasi tetap\nterbuka (boleh diminimalkan)\nselama jam sekolah.", bg=SB, fg=MU,
                 justify="left", font=("Segoe UI", 9)).pack(side="bottom", anchor="w", padx=20, pady=18)
        main = ttk.Frame(root); main.grid(row=0, column=1, sticky="nsew")
        main.rowconfigure(0, weight=1); main.columnconfigure(0, weight=1)
        self.pages = {}
        for key in self.nav:
            p = ttk.Frame(main, padding=24); p.grid(row=0, column=0, sticky="nsew"); self.pages[key] = p
        bar = tk.Frame(root, bg=SB); bar.grid(row=1, column=0, columnspan=2, sticky="we")
        self.stat = tk.Label(bar, bg=SB, fg=MU); self.stat.pack(side="left", padx=16, pady=8)
        self.dtl = tk.Label(bar, bg=SB, fg=MU); self.dtl.pack(side="right", padx=16)
        ttk.Button(bar, text="Hentikan suara", command=self.stop).pack(side="right", pady=4)
        self.build_home(); self.build_sched(); self.build_settings()
        self.show("home")

    def show(self, key):
        self.pages[key].tkraise()
        for k, b in self.nav.items():
            b.configure(style="NavOn.TButton" if k == key else "Nav.TButton")

    def fit_clock(self, e):
        sz = int(max(28, min(110, e.width / 7.4, (e.height - 130) / 1.8)))
        if sz != self._clk:
            self._clk = sz; self.clock.config(font=("Georgia", sz, "bold"))
        self.h_next.config(wraplength=max(220, e.width - 50))

    def build_home(self):
        f = self.pages["home"]; self._clk = 0; self._sig = None
        f.columnconfigure(0, weight=3, uniform="h"); f.columnconfigure(1, weight=2, uniform="h")
        f.rowconfigure(1, weight=2, minsize=275); f.rowconfigure(2, weight=3, minsize=170)
        head = ttk.Frame(f); head.grid(row=0, column=0, columnspan=2, sticky="we", pady=(0, 14))
        self.h_name = tk.Label(head, bg=BG, fg=TX, font=("Georgia", 24, "bold")); self.h_name.pack(anchor="w")
        self.h_addr = ttk.Label(head, style="Mu.TLabel"); self.h_addr.pack(anchor="w")
        c = ttk.Frame(f, style="Card.TFrame", padding=20); c.grid(row=1, column=0, sticky="nsew", padx=(0, 8), pady=(0, 8))
        c.columnconfigure(0, weight=1); c.rowconfigure(0, weight=1)
        self.clock = tk.Label(c, bg=PN, fg=TX, font=("Georgia", 60, "bold")); self.clock.grid(row=0, column=0)
        self.h_date = ttk.Label(c, style="CardMu.TLabel"); self.h_date.grid(row=1, column=0)
        self.h_next = tk.Label(c, bg=PN, fg=TX, font=("Segoe UI", 11), justify="center"); self.h_next.grid(row=2, column=0, pady=(10, 0))
        c.bind("<Configure>", self.fit_clock)
        st = ttk.Frame(f, style="Card.TFrame", padding=(18, 14)); st.grid(row=1, column=1, sticky="nsew", pady=(0, 8)); st.columnconfigure(0, weight=1)
        ttk.Label(st, text="Status", style="CardH.TLabel").grid(row=0, column=0, sticky="w", pady=(0, 8))
        self.h_cat = tk.Label(st, bg=PN, fg=OK, font=("Segoe UI", 11), anchor="w"); self.h_cat.grid(row=1, column=0, sticky="we")
        self.h_arm = tk.Label(st, bg=PN, font=("Segoe UI", 11), anchor="w"); self.h_arm.grid(row=2, column=0, sticky="we")
        self.b_arm = ttk.Button(st, style="Accent.TButton", command=self.toggle_arm); self.b_arm.grid(row=3, column=0, sticky="we", pady=10)
        ttk.Label(st, text="Jadwal aktif", style="CardMu.TLabel").grid(row=4, column=0, sticky="w")
        self.h_combo = ttk.Combobox(st, state="readonly"); self.h_combo.grid(row=5, column=0, sticky="we", pady=(2, 0))
        self.h_combo.bind("<<ComboboxSelected>>", lambda e: self.set_active(self.h_combo.get()))
        self.h_warn = tk.Label(st, bg=PN, fg=BAD, wraplength=240, justify="left"); self.h_warn.grid(row=6, column=0, sticky="w", pady=8)
        if not AUDIO_OK:
            self.h_warn.config(text="Pemutar suara tidak ditemukan, bel tidak akan berbunyi.")
        t = ttk.Frame(f, style="Card.TFrame", padding=(16, 12)); t.grid(row=2, column=0, columnspan=2, sticky="nsew")
        t.columnconfigure(0, weight=1); t.rowconfigure(1, weight=1)
        ttk.Label(t, text="Jadwal hari ini", style="CardH.TLabel").grid(row=0, column=0, sticky="w", pady=(0, 8))
        self.today = ttk.Treeview(t, columns=("no", "time", "desc", "state"), show="headings", selectmode="none")
        for c_, h_, w_, a_ in (("no", "No", 50, "center"), ("time", "Jam", 100, "w"), ("desc", "Keterangan", 300, "w"), ("state", "Status", 110, "w")):
            self.today.heading(c_, text=h_); self.today.column(c_, width=w_, minwidth=40, anchor=a_, stretch=c_ == "desc")
        self.today.tag_configure("Sudah", foreground=MU)
        self.today.tag_configure("Berikutnya", foreground=AC, background="#2a3a58")
        sb = ttk.Scrollbar(t, command=self.today.yview); self.today.config(yscrollcommand=sb.set)
        self.today.grid(row=1, column=0, sticky="nsew"); sb.grid(row=1, column=1, sticky="ns")

    def update_today(self, todays, sec, nxt):
        rows = sorted(todays, key=lambda i: (i["time"], i["desc"]))
        stt = ["Sudah" if self.to_sec(i["time"]) <= sec else "Berikutnya" if nxt and i["id"] == nxt["id"] else "Menunggu" for i in rows]
        sig = tuple((i["id"], x, i["desc"], i["time"]) for i, x in zip(rows, stt))
        if sig == self._sig:
            return
        self._sig = sig; self.today.delete(*self.today.get_children())
        for n, (i, x) in enumerate(zip(rows, stt), 1):
            self.today.insert("", "end", values=(n, i["time"], i["desc"], x), tags=(x,))

    def build_sched(self):
        f = self.pages["sched"]; f.columnconfigure(0, weight=1); f.rowconfigure(2, weight=1)
        ttk.Label(f, text="Jadwal bel", style="H1.TLabel").grid(row=0, column=0, sticky="w", pady=(0, 12))
        top = ttk.Frame(f); top.grid(row=1, column=0, sticky="we", pady=(0, 10))
        ttk.Label(top, text="Kategori").pack(side="left", padx=(0, 6))
        self.s_combo = ttk.Combobox(top, state="readonly", width=16); self.s_combo.pack(side="left")
        self.s_combo.bind("<<ComboboxSelected>>", lambda e: self.set_active(self.s_combo.get()))
        ttk.Button(top, text="+", width=3, command=self.add_cat).pack(side="left", padx=4)
        ttk.Button(top, text="Hapus kategori", command=self.del_cat).pack(side="left")
        ttk.Label(top, text="Tampilkan hari").pack(side="left", padx=(24, 6))
        self.f_day = ttk.Combobox(top, state="readonly", width=14, values=["Semua hari"] + HARI)
        self.cur_wd = dt.datetime.now().weekday()
        self.f_day.set(HARI[self.cur_wd]); self.f_day.pack(side="left")
        self.f_day.bind("<<ComboboxSelected>>", lambda e: self.refresh_list())
        box = ttk.Frame(f, style="Card.TFrame", padding=2); box.grid(row=2, column=0, sticky="nsew")
        box.columnconfigure(0, weight=1); box.rowconfigure(0, weight=1)
        self.tree = ttk.Treeview(box, columns=("no", "desc", "day", "time", "sound"), show="headings", selectmode="browse")
        for c, t, w in (("no", "No", 50), ("desc", "Keterangan", 250), ("day", "Hari", 120), ("time", "Jam", 100), ("sound", "Nada bel", 250)):
            self.tree.heading(c, text=t)
            self.tree.column(c, width=w, minwidth=40, anchor="center" if c == "no" else "w", stretch=c in ("desc", "sound"))
        self.tree.tag_configure("odd", background=PN); self.tree.tag_configure("even", background="#19253b")
        sb = ttk.Scrollbar(box, command=self.tree.yview); self.tree.config(yscrollcommand=sb.set)
        self.tree.grid(row=0, column=0, sticky="nsew"); sb.grid(row=0, column=1, sticky="ns")
        self.tree.bind("<Double-1>", lambda e: self.edit_item())
        bt = ttk.Frame(f); bt.grid(row=3, column=0, sticky="we", pady=(12, 0))
        ttk.Button(bt, text="Tambah", style="Accent.TButton", command=lambda: ItemDialog(self)).pack(side="left", padx=(0, 6))
        ttk.Button(bt, text="Ubah", command=self.edit_item).pack(side="left", padx=(0, 6))
        ttk.Button(bt, text="Hapus", command=self.del_item).pack(side="left", padx=(0, 6))
        ttk.Button(bt, text="Coba bunyikan", command=self.try_item).pack(side="left")
        ttk.Button(bt, text="Impor…", command=self.import_db).pack(side="right")
        ttk.Button(bt, text="Ekspor…", command=self.export_db).pack(side="right", padx=(0, 6))

    def test_vol(self):
        self.cfg["vol"] = round(self.v_vol.get(), 2); self.play("builtin:chime")

    def build_settings(self):
        f = self.pages["set"]; f.columnconfigure(0, weight=1)
        ttk.Label(f, text="Pengaturan", style="H1.TLabel").grid(row=0, column=0, sticky="w", pady=(0, 12))
        c = ttk.Frame(f, style="Card.TFrame", padding=24); c.grid(row=1, column=0, sticky="we"); c.columnconfigure(1, weight=1)
        self.v_name, self.v_addr = tk.StringVar(value=self.cfg["school"]), tk.StringVar(value=self.cfg["addr"])
        for r, (lbl, var) in enumerate((("Nama sekolah", self.v_name), ("Alamat", self.v_addr))):
            ttk.Label(c, text=lbl, style="Card.TLabel").grid(row=r, column=0, sticky="w", pady=8, padx=(0, 20))
            ttk.Entry(c, textvariable=var).grid(row=r, column=1, sticky="we")
        ttk.Label(c, text="Volume bel", style="Card.TLabel").grid(row=2, column=0, sticky="w", pady=8)
        vf = ttk.Frame(c, style="Card.TFrame", borderwidth=0); vf.grid(row=2, column=1, sticky="we"); vf.columnconfigure(0, weight=1)
        self.v_vol = tk.DoubleVar(value=self.cfg["vol"])
        ttk.Scale(vf, from_=0, to=1, variable=self.v_vol, command=lambda v: hasattr(self, "vol_lbl") and self.vol_lbl.config(text=f"{float(v) * 100:.0f}%")).grid(row=0, column=0, sticky="we")
        self.vol_lbl = ttk.Label(vf, text=f"{self.cfg['vol'] * 100:.0f}%", style="Card.TLabel", width=5, anchor="e"); self.vol_lbl.grid(row=0, column=1, padx=8)
        ttk.Button(vf, text="Tes suara", command=self.test_vol).grid(row=0, column=2)
        self.v_auto = tk.BooleanVar(value=autostart_on())
        ck = ttk.Checkbutton(c, text="Jalankan otomatis saat Windows menyala", variable=self.v_auto, style="Card.TCheckbutton", command=self.toggle_auto)
        ck.grid(row=3, column=0, columnspan=2, sticky="w", pady=10)
        if os.name != "nt":
            ck.state(["disabled"])
        ttk.Button(c, text="Simpan pengaturan", style="Accent.TButton", command=self.save_settings).grid(row=4, column=0, columnspan=2, sticky="w", pady=(6, 0))
        ttk.Label(f, style="Mu.TLabel", justify="left", wraplength=700,
                  text=f"{APP_NAME} - by {APP_BY}\nDatabase: {CFG}\nFolder nada: {NADA}\nJika aplikasi ditutup, bel tidak berbunyi. Cukup diminimalkan.").grid(row=2, column=0, sticky="w", pady=16)

    # ---------- data ----------
    def save(self):
        self.cfg["armed"] = self.armed
        try:
            CFG.write_text(json.dumps(self.cfg, ensure_ascii=False, indent=1), encoding="utf-8")
        except OSError as e:
            messagebox.showerror("Gagal menyimpan", str(e))

    def sound_label(self, ref):
        if ref in BUILTIN:
            return BUILTIN[ref]
        return ref if os.path.isfile(resolve(ref)) else ref + "  (berkas hilang)"

    def day_name(self, d):
        return dict(OPT).get(d, "?")

    def refresh_list(self):
        self.tree.delete(*self.tree.get_children())
        pick = self.f_day.get()
        rows = [i for i in self.cfg["items"] if i["cat"] == self.cfg["active"]
                and (pick == "Semua hari" or self.applies(i, HARI.index(pick)))]
        rows.sort(key=lambda i: (i["time"], i["desc"]))
        for n, i in enumerate(rows, 1):
            snd = BUILTIN.get(i["sound"]) or os.path.basename(i["sound"]) + ("" if os.path.isfile(resolve(i["sound"])) else "  (hilang)")
            self.tree.insert("", "end", iid=str(i["id"]), tags=("odd" if n % 2 else "even",), values=(n, i["desc"], self.day_name(i["day"]), i["time"], snd))
        cats = self.cfg["cats"]
        for c in (self.h_combo, self.s_combo):
            c.config(values=cats); c.set(self.cfg["active"])

    def selected(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Pilih jadwal", "Klik satu baris jadwal dulu."); return None
        return next(i for i in self.cfg["items"] if str(i["id"]) == sel[0])

    def edit_item(self):
        it = self.selected()
        if it: ItemDialog(self, it)

    def del_item(self):
        it = self.selected()
        if it and messagebox.askyesno("Hapus jadwal", f"Hapus “{it['desc']}”?"):
            self.cfg["items"].remove(it); self.save(); self.refresh_list()

    def try_item(self):
        it = self.selected()
        if it: self.play(it["sound"])

    def set_active(self, c):
        self.cfg["active"] = c; self.save(); self.refresh_list()

    def add_cat(self):
        n = simpledialog.askstring("Kategori baru", "Nama kategori:", parent=self)
        if n and n.strip() and n.strip() not in self.cfg["cats"]:
            self.cfg["cats"].append(n.strip()); self.set_active(n.strip())

    def del_cat(self):
        a = self.cfg["active"]
        if len(self.cfg["cats"]) < 2:
            messagebox.showinfo("Tidak bisa dihapus", "Minimal harus ada satu kategori."); return
        if messagebox.askyesno("Hapus kategori", f"Hapus kategori “{a}” beserta semua jadwalnya?"):
            self.cfg["items"] = [i for i in self.cfg["items"] if i["cat"] != a]
            self.cfg["cats"].remove(a); self.set_active(self.cfg["cats"][0])

    def save_settings(self):
        self.cfg.update(school=self.v_name.get().strip() or "Sekolah", addr=self.v_addr.get().strip(), vol=round(self.v_vol.get(), 2))
        self.save(); messagebox.showinfo("Tersimpan", "Pengaturan disimpan.")

    def toggle_auto(self):
        try:
            set_autostart(self.v_auto.get())
        except Exception as e:
            self.v_auto.set(False); messagebox.showerror("Gagal", str(e))

    # ---------- suara ----------
    def play(self, ref, quiet=False):
        def fail(msg):
            self.last_ring = "GAGAL: " + msg
            if not quiet:
                messagebox.showerror("Suara tidak bisa diputar", msg)
        if not AUDIO_OK:
            fail("Pemutar suara tidak ditemukan di sistem ini."); return
        path = os.path.normpath(resolve(ref))
        if not os.path.isfile(path):
            fail(f"Berkas tidak ditemukan:\n{path}"); return
        try:
            err = audio_play(path, self.cfg["vol"])
            if err:
                fail(f"{err}\n\nBerkas: {path}")
            elif os.name == "nt":
                self.after(5500, lambda: self.check_audio(path, quiet))
        except Exception as e:
            fail(f"{e}\n\nBerkas: {path}")

    def check_audio(self, path, quiet):
        msg = audio_failed()
        if msg:
            self.last_ring = "GAGAL: " + msg
            if not quiet:
                messagebox.showerror("Suara tidak bisa diputar", f"{msg}\n\nBerkas: {path}")

    def stop(self):
        if AUDIO_OK:
            audio_stop()

    # ---------- menu, nada, ekspor/impor ----------
    def build_menu(self):
        m = tk.Menu(self); f = tk.Menu(m, tearoff=0)
        f.add_command(label="Ekspor database dan nada…", command=self.export_db)
        f.add_command(label="Impor database dan nada…", command=self.import_db)
        f.add_separator()
        f.add_command(label="Kumpulkan semua nada ke folder nada", command=self.collect_sounds)
        f.add_command(label="Buka folder nada", command=self.open_nada)
        f.add_separator()
        f.add_command(label="Keluar", command=self.on_close)
        m.add_cascade(label="Berkas", menu=f)
        h = tk.Menu(m, tearoff=0)
        h.add_command(label="Tentang aplikasi", command=self.about)
        m.add_cascade(label="Bantuan", menu=h); self.config(menu=m)

    def about(self):
        messagebox.showinfo("Tentang aplikasi", f"{APP_NAME}\n\nDibuat oleh {APP_BY}\nPenjadwal bel sekolah otomatis (Python + Tkinter).")

    def open_nada(self):
        try:
            os.startfile(NADA)
        except Exception:
            messagebox.showinfo("Folder nada", str(NADA))

    def import_sound(self, src):
        """Salin berkas nada ke folder nada; kembalikan referensi yang disimpan."""
        src = Path(src)
        try:
            return ref_nada(src.resolve().relative_to(NADA.resolve()).as_posix())
        except ValueError:
            pass
        dest, n = NADA / src.name, 2
        while dest.exists() and dest.stat().st_size != src.stat().st_size:
            dest = NADA / f"{src.stem}_{n}{src.suffix}"; n += 1
        try:
            if not dest.exists():
                shutil.copy2(src, dest)
        except OSError:
            return str(src)
        return ref_nada(dest.name)

    def collect_sounds(self):
        n = 0
        for i in self.cfg["items"]:
            if i["sound"].startswith("builtin:"):
                continue
            p = resolve(i["sound"])
            if os.path.isfile(p):
                new = self.import_sound(p)
                if new != i["sound"]:
                    i["sound"] = new; n += 1
        self.save(); self.refresh_list()
        messagebox.showinfo("Selesai", f"{n} jadwal dipindah ke folder nada:\n{NADA}")

    def export_db(self):
        dst = filedialog.asksaveasfilename(title="Ekspor database", defaultextension=".zip",
                                           initialfile=f"bel-sekolah-{dt.date.today():%Y%m%d}.zip",
                                           filetypes=[("Arsip ZIP", "*.zip")])
        if not dst:
            return
        cfg = json.loads(json.dumps(self.cfg)); files = {}; missing = []
        for i in cfg["items"]:
            if i["sound"].startswith("builtin:"):
                continue
            p = Path(resolve(i["sound"]))
            if not p.is_file():
                missing.append(i["desc"]); continue
            name, n = p.name, 2
            while name in files and files[name] != p:
                name = f"{p.stem}_{n}{p.suffix}"; n += 1
            files[name] = p; i["sound"] = "nada/" + name
        try:
            with zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as z:
                z.writestr("config.json", json.dumps(cfg, ensure_ascii=False, indent=1))
                for name, p in files.items():
                    z.write(p, "nada/" + name)
        except OSError as e:
            messagebox.showerror("Gagal ekspor", str(e)); return
        msg = f"Tersimpan: {dst}\nJadwal: {len(cfg['items'])}   Berkas nada: {len(files)}"
        if missing:
            msg += "\n\nBerkas nada hilang untuk: " + ", ".join(missing)
        messagebox.showinfo("Ekspor selesai", msg)

    def import_db(self):
        src = filedialog.askopenfilename(title="Impor database", filetypes=[("Arsip ZIP", "*.zip")])
        if not src:
            return
        try:
            with zipfile.ZipFile(src) as z:
                new = json.loads(z.read("config.json").decode("utf-8"))
                if not (isinstance(new.get("items"), list) and isinstance(new.get("cats"), list) and new["cats"]
                        and all(k in i for i in new["items"] for k in KEYS)):
                    raise ValueError("isi config.json tidak lengkap")
                mode = messagebox.askyesnocancel(
                    "Impor database",
                    f"Berkas ini berisi {len(new['items'])} jadwal.\n\n"
                    "Ya  = GANTI semua jadwal saat ini\n"
                    "Tidak  = GABUNG (tambahkan ke jadwal yang sudah ada)\n"
                    "Batal  = batalkan impor")
                if mode is None:
                    return
                for name in z.namelist():
                    if name.startswith("nada/") and not name.endswith("/"):
                        with z.open(name) as a, open(NADA / Path(name).name, "wb") as b:
                            shutil.copyfileobj(a, b)
        except Exception as e:
            messagebox.showerror("Gagal impor", f"Berkas tidak valid: {e}"); return
        for i in new["items"]:
            if not i["sound"].startswith("builtin:"):
                i["sound"] = ref_nada(Path(i["sound"]).name)
        if not mode:  # gabung: pengaturan sekolah & volume tidak diubah
            sig = lambda i: (i["cat"], i["desc"], i["day"], i["time"], i["sound"])
            have = {sig(i) for i in self.cfg["items"]}
            ids = {i["id"] for i in self.cfg["items"]}
            added = 0
            for c in new["cats"]:
                if c not in self.cfg["cats"]:
                    self.cfg["cats"].append(c)
            for i in new["items"]:
                if sig(i) in have:
                    continue
                while i["id"] in ids:
                    i["id"] += 1
                ids.add(i["id"]); have.add(sig(i))
                if i["cat"] not in self.cfg["cats"]:
                    self.cfg["cats"].append(i["cat"])
                self.cfg["items"].append(i); added += 1
            self.save(); self.refresh_list()
            messagebox.showinfo("Impor selesai", f"{added} jadwal baru ditambahkan ({len(new['items']) - added} sudah ada, dilewati).")
            return
        self.cfg = {**default_cfg(), **new}
        self.cfg["armed"] = self.armed
        if self.cfg["active"] not in self.cfg["cats"]:
            self.cfg["active"] = self.cfg["cats"][0]
        self.v_name.set(self.cfg["school"]); self.v_addr.set(self.cfg["addr"]); self.v_vol.set(self.cfg["vol"])
        self.save(); self.refresh_list()
        messagebox.showinfo("Impor selesai", f"{len(new['items'])} jadwal berhasil diimpor.")

    def toggle_arm(self):
        self.armed = not self.armed; keep_awake(self.armed); self.save()

    # ---------- penjadwal ----------
    @staticmethod
    def applies(it, d):
        """d = nomor hari (Senin=0 ... Minggu=6)."""
        return (it["day"] == str(d) or (it["day"] == "mt" and d <= 3)
                or (it["day"] == "wd" and d <= 4) or (it["day"] == "ws" and d <= 5))

    def match(self, it, now):
        return self.applies(it, now.weekday())

    def tick(self):
        now = dt.datetime.now(); hms = now.strftime("%H:%M:%S")
        self.clock.config(text=hms)
        if now.weekday() != self.cur_wd:  # ganti hari: daftar ikut hari baru jika masih menampilkan hari kemarin
            if self.f_day.get() == HARI[self.cur_wd]:
                self.f_day.set(HARI[now.weekday()]); self.refresh_list()
            self.cur_wd = now.weekday()
        tgl = f"{HARI[now.weekday()]}, {now.day} {['Januari','Februari','Maret','April','Mei','Juni','Juli','Agustus','September','Oktober','November','Desember'][now.month-1]} {now.year}"
        self.h_date.config(text=tgl); self.dtl.config(text=f"{tgl}   {hms}")
        self.h_name.config(text=self.cfg["school"]); self.h_addr.config(text=self.cfg["addr"])
        self.h_cat.config(text=f"✔ Jadwal aktif: {self.cfg['active']}")
        self.h_arm.config(text="✔ Bel otomatis aktif" if self.armed else "● Bel otomatis dimatikan", fg=OK if self.armed else BAD)
        self.b_arm.config(text="Matikan bel" if self.armed else "Aktifkan bel")
        self.stat.config(text=f"Jadwal: {self.cfg['active']}  ·  Bel {'aktif' if self.armed else 'mati'}")
        todays = [i for i in self.cfg["items"] if i["cat"] == self.cfg["active"] and self.match(i, now)]
        key = now.strftime("%Y%m%d") + hms
        if self.armed and key != self.last_key:
            for i in todays:
                if i["time"] == hms:
                    self.last_key = key; self.last_ring = f"{i['desc']} ({hms})"; self.play(i["sound"], quiet=True); break
        sec = now.hour * 3600 + now.minute * 60 + now.second
        nxt = sorted((self.to_sec(i["time"]), i) for i in todays if self.to_sec(i["time"]) > sec)
        if nxt:
            s, i = nxt[0][0] - sec, nxt[0][1]
            txt = f"Bel berikutnya: {i['desc']} pukul {i['time']}  (dalam {s // 3600} jam {s % 3600 // 60} menit {s % 60} detik)"
        else:
            txt = f"Tidak ada bel lagi hari ini di jadwal {self.cfg['active']}."
        if self.last_ring:
            txt += f"\nTerakhir berbunyi: {self.last_ring}"
        self.h_next.config(text=txt)
        self.update_today(todays, sec, nxt[0][1] if nxt else None)
        self.after(250, self.tick)

    @staticmethod
    def to_sec(t):
        h, m, s = (int(x) for x in t.split(":"))
        return h * 3600 + m * 60 + s

    def on_close(self):
        if messagebox.askyesno("Tutup aplikasi?", "Jika ditutup, bel tidak akan berbunyi.\n\nYa = tutup, Tidak = minimalkan saja."):
            keep_awake(False); self.destroy()
        else:
            self.iconify()


if __name__ == "__main__":
    app = App()
    app.refresh_list()
    app.mainloop()
