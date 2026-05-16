#!/usr/bin/env python3
import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext
import re
import signal
import subprocess
import threading
import os
import sys

BINARY = os.path.join(os.path.dirname(os.path.abspath(__file__)), "steam-haptics-singer")

SELECT_RE = re.compile(r'Select device \(1-(\d+)\): $')
DEVICE_LINE_RE = re.compile(r'^\s+\d+\.')


class DeviceDialog(tk.Toplevel):
    def __init__(self, parent, devices):
        super().__init__(parent)
        self.title("Select Device")
        self.resizable(False, False)
        self.grab_set()
        self.choice = None

        ttk.Label(self, text="Multiple controllers found. Pick one:").pack(padx=12, pady=(10, 4))

        self.var = tk.IntVar(value=1)
        for i, name in enumerate(devices, start=1):
            ttk.Radiobutton(self, text=name, variable=self.var, value=i).pack(anchor="w", padx=20, pady=2)

        ttk.Button(self, text="OK", command=self._ok).pack(pady=(6, 12))
        self.protocol("WM_DELETE_WINDOW", self._ok)
        self.transient(parent)
        self.wait_visibility()
        self.lift()

    def _ok(self):
        self.choice = self.var.get()
        self.destroy()


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Steam Haptics Singer")
        self.resizable(False, False)
        self.process = None
        self._build_ui()

    def _build_ui(self):
        pad = {"padx": 8, "pady": 4}

        file_frame = ttk.LabelFrame(self, text="MIDI File")
        file_frame.pack(fill="x", **pad)

        self.file_var = tk.StringVar()
        ttk.Entry(file_frame, textvariable=self.file_var, width=48).pack(side="left", padx=4, pady=4)
        ttk.Button(file_frame, text="Browse…", command=self._browse).pack(side="left", padx=(0, 4), pady=4)

        opt_frame = ttk.LabelFrame(self, text="Options")
        opt_frame.pack(fill="x", **pad)

        self.repeat_var    = tk.BooleanVar()
        self.directvel_var = tk.BooleanVar()
        self.trackpad_var  = tk.BooleanVar()
        self.rumble_var    = tk.BooleanVar()

        ttk.Checkbutton(opt_frame, text="-p  Repeat song",              variable=self.repeat_var   ).grid(row=0, column=0, sticky="w", padx=8, pady=2)
        ttk.Checkbutton(opt_frame, text="-e  Direct velocity → gain",   variable=self.directvel_var).grid(row=1, column=0, sticky="w", padx=8, pady=2)
        ttk.Checkbutton(opt_frame, text="-t  Trackpads only (SC 2026)", variable=self.trackpad_var ).grid(row=0, column=1, sticky="w", padx=8, pady=2)
        ttk.Checkbutton(opt_frame, text="-s  Swap rumble/trackpad (SC 2026)",variable=self.rumble_var   ).grid(row=1, column=1, sticky="w", padx=8, pady=2)

        interval_frame = ttk.Frame(opt_frame)
        interval_frame.grid(row=2, column=0, columnspan=2, sticky="w", padx=8, pady=4)
        ttk.Label(interval_frame, text="-i  Interval (µs):").pack(side="left")
        self.interval_var = tk.StringVar(value="10000")
        ttk.Entry(interval_frame, textvariable=self.interval_var, width=10).pack(side="left", padx=4)
        ttk.Label(interval_frame, text="(lower = better fidelity, higher CPU)").pack(side="left")

        debug_frame = ttk.Frame(opt_frame)
        debug_frame.grid(row=3, column=0, columnspan=2, sticky="w", padx=8, pady=4)
        ttk.Label(debug_frame, text="-d  Libusb debug level:").pack(side="left")
        self.debug_var = tk.StringVar(value="0")
        ttk.Combobox(debug_frame, textvariable=self.debug_var, values=["0","1","2","3","4"], width=4, state="readonly").pack(side="left", padx=4)

        btn_frame = ttk.Frame(self)
        btn_frame.pack(**pad)
        self.play_btn = ttk.Button(btn_frame, text="Play", command=self._play)
        self.play_btn.pack(side="left", padx=4)
        self.stop_btn = ttk.Button(btn_frame, text="Stop", command=self._stop, state="disabled")
        self.stop_btn.pack(side="left", padx=4)

        log_frame = ttk.LabelFrame(self, text="Output")
        log_frame.pack(fill="both", expand=True, **pad)
        self.log = scrolledtext.ScrolledText(log_frame, height=10, state="disabled", font=("Monospace", 9))
        self.log.pack(fill="both", expand=True, padx=4, pady=4)

    def _browse(self):
        path = filedialog.askopenfilename(
            initialdir=os.path.dirname(os.path.abspath(__file__)),
            filetypes=[("MIDI files", "*.mid *.midi"), ("All files", "*")])
        if path:
            self.file_var.set(path)

    def _build_cmd(self):
        cmd = [BINARY]
        if self.repeat_var.get():    cmd.append("-p")
        if self.directvel_var.get(): cmd.append("-e")
        if self.trackpad_var.get():  cmd.append("-t")
        if self.rumble_var.get():    cmd.append("-s")
        interval = self.interval_var.get().strip()
        if interval and interval != "10000":
            cmd += ["-i", interval]
        debug = self.debug_var.get().strip()
        if debug and debug != "0":
            cmd += ["-d", debug]
        cmd.append(self.file_var.get())
        return cmd

    def _log(self, text):
        self.log.configure(state="normal")
        self.log.insert("end", text)
        self.log.see("end")
        self.log.configure(state="disabled")

    def _play(self):
        path = self.file_var.get().strip()
        if not path:
            self._log("No MIDI file selected.\n")
            return
        if not os.path.exists(BINARY):
            self._log(f"Binary not found: {BINARY}\nRun 'make' first.\n")
            return

        cmd = self._build_cmd()
        self._log(f"$ {' '.join(cmd)}\n")
        self.play_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")

        def run():
            try:
                self.process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                    stdin=subprocess.PIPE,
                    text=True, bufsize=0,
                )
                self._read_output()
                self.process.wait()
            except Exception as e:
                self.after(0, self._log, f"Error: {e}\n")
            finally:
                self.after(0, self._on_done)

        threading.Thread(target=run, daemon=True).start()

    def _read_output(self):
        """Read stdout char-by-char so we can catch prompts that have no newline."""
        buf = ""
        device_lines = []
        collecting = False

        while True:
            ch = self.process.stdout.read(1)
            if not ch:
                if buf:
                    self.after(0, self._log, buf)
                break
            buf += ch

            # flush complete lines
            if '\n' in buf:
                parts = buf.split('\n')
                buf = parts[-1]
                for line in parts[:-1]:
                    full = line + '\n'
                    self.after(0, self._log, full)
                    if "Multiple devices found:" in full:
                        collecting = True
                        device_lines = []
                    elif collecting and DEVICE_LINE_RE.match(full):
                        device_lines.append(full.strip())

            # detect "Select device (1-N): " prompt (no trailing newline)
            m = SELECT_RE.search(buf)
            if m:
                self.after(0, self._log, buf + "\n")
                buf = ""
                count = int(m.group(1))
                names = device_lines if device_lines else [f"Device {i}" for i in range(1, count + 1)]

                event = threading.Event()
                result = [1]

                def show_dialog(names=names, result=result, event=event):
                    dlg = DeviceDialog(self, names)
                    self.wait_window(dlg)
                    if dlg.choice is not None:
                        result[0] = dlg.choice
                    event.set()

                self.after(0, show_dialog)
                event.wait()
                self.process.stdin.write(f"{result[0]}\n")
                self.process.stdin.flush()
                self.after(0, self._log, f"{result[0]}\n")

    def _stop(self):
        if self.process and self.process.poll() is None:
            self.process.send_signal(signal.SIGINT)

    def _on_done(self):
        self.process = None
        self.play_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")
        self._log("--- done ---\n")


if __name__ == "__main__":
    App().mainloop()
