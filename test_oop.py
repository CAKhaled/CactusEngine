import traceback
import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

from interpreter import Interpreter

code = """
كلاس لاعب:
    دالة بناء(اسم, طاقة):
        هذا.الاسم = اسم
        هذا.الطاقة = طاقة
        
    دالة هجوم(ضرر):
        هذا.الطاقة -= ضرر
        اطبع "اللاعب " + هذا.الاسم + " تعرض لضرر! الطاقة المتبقية: " + هذا.الطاقة

ابغا بطل = لاعب("خالد", 100)
اطبع "اسم البطل:"
اطبع بطل.الاسم
بطل.هجوم(20)
اطبع بطل.الطاقة
"""

try:
    interp = Interpreter()
    interp.execute(code)
except Exception as e:
    traceback.print_exc()
