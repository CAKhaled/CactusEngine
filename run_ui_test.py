import subprocess

print("Starting ui2.py...")
try:
    proc = subprocess.run(["python", "ui2.py"], capture_output=True, text=True, timeout=3)
    print("STDOUT:")
    print(proc.stdout)
    print("STDERR:")
    print(proc.stderr)
except subprocess.TimeoutExpired as e:
    print("Timeout, as expected.")
    print("STDOUT:")
    print(e.stdout)
    print("STDERR:")
    print(e.stderr)
except Exception as e:
    print(f"Error: {e}")
