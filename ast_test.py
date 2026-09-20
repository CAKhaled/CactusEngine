from interpreter import Interpreter
import json

code = """
دالة تدريب():
    كرر:
        إذا التدريب < عدد_التدريب:
            التدريب += 1
            نتيجة_التنبؤ = []
            كرر:
                إذا نتيجة_التنبؤ.طول < س.طول:
                    المعادلة = الميل*س[نتيجة_التنبؤ.طول] + التحيز
                    نتيجة_التنبؤ.ضف(المعادلة)
            اطبع "هنا لا يكمل الكود"
"""

interpreter = Interpreter()
lines = code.splitlines()
enumerated_lines = [(i+1, line.replace("\t", "    ")) for i, line in enumerate(lines)]
preprocessed_lines = interpreter._preprocess_lines(enumerated_lines)
blocks = interpreter.parse_blocks(preprocessed_lines, 0)

import pprint
pprint.pprint(blocks)
