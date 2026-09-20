content = open('ui2.py', encoding='utf-8').read()

object2d_str = '    "Object2D": ["الاسم", "الموقع", "الدوران", "المقياس", "اللون", "الصورة", "تصادم", "جاذبية", "صدام"],\n    "Object3D":'
content = content.replace('    "Object3D":', object2d_str, 1)

content = content.replace('"صنع_مربع2D": "Object3D"', '"صنع_مربع2D": "Object2D"')
content = content.replace('"صنع_دائرة2D": "Object3D"', '"صنع_دائرة2D": "Object2D"')
content = content.replace('"صنع_مثلث2D": "Object3D"', '"صنع_مثلث2D": "Object2D"')

open('ui2.py', 'w', encoding='utf-8').write(content)

content2 = open('graphics.py', encoding='utf-8').read()
content2 = content2.replace('self.اللون = Color(1, 1, 1)', 'self.اللون = Color(1, 1, 1)\n        self.الصورة = ""')
open('graphics.py', 'w', encoding='utf-8').write(content2)

print('Done')
