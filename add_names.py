import re

with open('graphics.py', 'r', encoding='utf-8') as f:
    code = f.read()

classes = ['Cube', 'CustomModel', 'Square2D', 'Circle2D', 'Triangle2D', 'Custom2D', 'Sphere', 'Plane', 'Pyramid', 'Cylinder', 'Capsule']

for cls in classes:
    pattern = r'(class ' + cls + r'[\s\S]*?def __init__\(.*?\):\n)'
    replacement = r'\g<1>        self.الاسم = ""\n'
    code = re.sub(pattern, replacement, code, count=1)

with open('graphics.py', 'w', encoding='utf-8') as f:
    f.write(code)

print("Added Name to classes")
