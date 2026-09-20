import sys
import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")
from interpreter import Interpreter

if len(sys.argv) != 2:
    print("الاستخدام:")
    print("python kh.py program.kh")
    exit()

filename = sys.argv[1]
script_dir = os.path.dirname(os.path.abspath(filename))
if script_dir:
    os.chdir(script_dir)
print(f"DEBUG: Working directory changed to: {os.getcwd()}")

if not filename.endswith(".kh"):
    print("الملف يجب أن يكون بامتداد .kh")
    exit()

with open(filename, "r", encoding="utf-8") as file:
    code = file.read()

# Execute all .khscene files in the project first
scene_codes = []
for fname in os.listdir(script_dir):
    if fname.endswith(".khscene"):
        fpath = os.path.join(script_dir, fname)
        if os.path.abspath(fpath) != os.path.abspath(filename):
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    scene_codes.append(f.read())
            except Exception as e:
                print(f"Warning: Could not read {fname}: {e}")

if scene_codes:
    # Prepend the scene code to the main code
    code = "\n\n".join(scene_codes) + "\n\n" + code

try:
    interpreter = Interpreter()
    interpreter.execute(code)
except Exception as e:
    import traceback
    traceback.print_exc()
    # الحصول على السطر والكود من الاستثناء
    kh_line = getattr(e, "kh_line", "غير معروف")
    kh_code = getattr(e, "kh_code", "")
    
    print("\n❌ [خطأ في تشغيل الكود]")
    if kh_line != "غير معروف":
        print(f"السطر: {kh_line}")
    if kh_code:
        print(f"الكود: {kh_code.strip()}")
        
    print(f"السبب: {e}\n")
    sys.exit(1)