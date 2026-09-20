from interpreter import Interpreter
code = """دالة تدريب():
    كرر:
        إذا التدريب < عدد_التدريب:
            التدريب += 1
            نتيجة_التنبؤ = []
            كرر:
                إذا نتيجة_التنبؤ.طول < س.طول:
                    المعادلة = (الميل*س[نتيجة_التنبؤ.طول]) + التحيز
                    نتيجة_التنبؤ.ضف(المعادلة)        
            المرات = 0
            المشتقة_الميل = 0
            المشتقة_التحيز = 0
            خطأ = 0
            كرر:
                إذا المرات < س.طول:
                    نتيجة_الخطا = ص[المرات] - نتيجة_التنبؤ[المرات)
                    اطبع نتيجة_الخطا 
                    المشتقة_الميل += نتيجة_الخطا * س[المرات]
                    المشتقة_التحيز += نتيجة_الخطا
                    المرات += 1 
            المشتقة_الميل = (-2/س.طول) * المشتقة_الميل
            المشتقة_التحيز = (-2/س.طول)
            الميل = الميل - التعلم * المشتقة_الميل
            التحيز = التحيز - التعلم * المشتقة_التحيز
            اطبع الميل"""
interpreter = Interpreter()
lines = code.splitlines()
enumerated_lines = [(i+1, line.replace("\t", "    ")) for i, line in enumerate(lines)]
preprocessed_lines = interpreter._preprocess_lines(enumerated_lines)
blocks = interpreter.parse_blocks(preprocessed_lines, 0)
import pprint
pprint.pprint(blocks)
