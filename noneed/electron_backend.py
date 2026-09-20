import sys
import subprocess
import threading
import ctypes
import os

electron_hwnd_hex = sys.argv[1]
target_file = sys.argv[2]

electron_hwnd = int(electron_hwnd_hex, 16)

bounds = {'x': 0, 'y': 0, 'w': 100, 'h': 100}
pygame_hwnd = None

def stdin_thread():
    while True:
        line = sys.stdin.readline()
        if not line:
            break
        line = line.strip()
        if line.startswith("BOUNDS:"):
            parts = line[7:].split(',')
            if len(parts) == 4:
                try:
                    bounds['x'] = int(float(parts[0]))
                    bounds['y'] = int(float(parts[1]))
                    bounds['w'] = int(float(parts[2]))
                    bounds['h'] = int(float(parts[3]))
                    if pygame_hwnd:
                        ctypes.windll.user32.SetWindowPos(pygame_hwnd, 0, bounds['x'], bounds['y'], bounds['w'], bounds['h'], 0x0044)
                except Exception as e:
                    print(f"Error parsing bounds: {e}", file=sys.stderr)

t = threading.Thread(target=stdin_thread, daemon=True)
t.start()

proc = subprocess.Popen([sys.executable, "interpreter.py", target_file], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1)

def stderr_thread():
    for line in proc.stderr:
        print(line, end='', file=sys.stderr)
        sys.stderr.flush()

t2 = threading.Thread(target=stderr_thread, daemon=True)
t2.start()

for line in proc.stdout:
    if "__KH_HWND__:" in line:
        try:
            hw_str = line.strip().split("__KH_HWND__:")[1]
            pygame_hwnd = int(hw_str)
            
            # Embed the Pygame window inside the Electron window
            ctypes.windll.user32.SetParent(pygame_hwnd, electron_hwnd)
            
            # Remove window borders from Pygame window (WS_CAPTION | WS_THICKFRAME)
            WS_CAPTION = 0x00C00000
            WS_THICKFRAME = 0x00040000
            GWL_STYLE = -16
            style = ctypes.windll.user32.GetWindowLongW(pygame_hwnd, GWL_STYLE)
            style &= ~(WS_CAPTION | WS_THICKFRAME)
            ctypes.windll.user32.SetWindowLongW(pygame_hwnd, GWL_STYLE, style)
            
            # Apply bounds
            ctypes.windll.user32.SetWindowPos(pygame_hwnd, 0, bounds['x'], bounds['y'], bounds['w'], bounds['h'], 0x0020)
        except Exception as e:
            print(f"Error embedding: {e}", file=sys.stderr)
    else:
        print(line, end='')
        sys.stdout.flush()

proc.wait()
sys.exit(proc.returncode)
