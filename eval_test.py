from interpreter import Interpreter
import json

interpreter = Interpreter()
interpreter.variables["س"] = [10,20,30]
interpreter.variables["ص"] = [20,40,60]
interpreter.variables["المرات"] = 0
interpreter.variables["نتيجة_التنبؤ"] = [10]

try:
    interpreter.evaluate("ص[المرات] - نتيجة_التنبؤ[المرات) اطبع نتيجة_الخطا")
    print("Success?")
except Exception as e:
    print(f"Exception: {e}")
