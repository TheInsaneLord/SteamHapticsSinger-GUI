# Steam Haptics Singer — GUI

A graphical front-end for [Steam Haptics Singer](https://github.com/CrazyCritic89/SteamHapticsSinger) by CrazyCritic89, itself a continuation of [SteamControllerSinger](https://gitlab.com/Pilatomic/SteamControllerSinger) originally by Pila (and [Roboron3042's fork](https://github.com/Roboron3042/SteamControllerSinger)).

This repo contains **only the GUI layer and an optional patch** — the core program is not included. All credit for the underlying haptic playback engine goes to the original authors above.

---

## Requirements

- Python 3.6 or newer
- `tkinter` — included in most Python installations. If it's missing, install it with your package manager:
  - Debian/Ubuntu: `sudo apt install python3-tk`
  - Arch: `sudo pacman -S tk`
  - Fedora: `sudo dnf install python3-tkinter`

No third-party Python packages are needed.

---

## Installation

1. Build Steam Haptics Singer from the [original repo](https://github.com/CrazyCritic89/SteamHapticsSinger) first (`make` on Linux).
2. Drop `gui.py` into the same folder as the compiled `steam-haptics-singer` binary.
3. Run it:
   ```
   python3 gui.py
   ```

### Optional: mono pitch-split patch

Single-channel MIDI files normally only play on the right haptic. `pitch_split.patch` adds automatic detection and splits notes by pitch so both haptics play.

To apply it, from inside the original repo folder:
```
git apply /path/to/pitch_split.patch
make
```

---

## Features

- Browse and pick MIDI files
- Toggle all command-line flags (`-p`, `-e`, `-t`, `-b`) via checkboxes
- Adjust interval and libusb debug level
- If multiple controllers are connected, a device picker dialog appears automatically
- Live output log in the window

---

## License

`gui.py` and `pitch_split.patch` are released under the MIT License. The underlying Steam Haptics Singer project retains its own license.
