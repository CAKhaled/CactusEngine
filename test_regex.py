import re

# محاكاة ملف khscene حقيقي
sample_code = """ماوس.معلق = مقفل

صنع_سماء(لون(0.15, 0.15, 0.15))

الكاميرا.الموقع = متجه3(-0.88, 0.59, 3.96)
الكاميرا.الدوران = متجه3(0.0, 0.0, 1.25)
الكاميرا.مجال_الرؤية = 60.0
الكاميرا.القطع_القريب = 0.1
الكاميرا.القطع_البعيد = 2000.0

ابغا مكعب1 = صنع_مكعب()
مكعب1.الموقع = متجه3(0.0, 0.0, 0.0)
مكعب1.الدوران = متجه3(0.0, 0.0, 0.0)
مكعب1.المقياس = متجه3(1.0, 1.0, 1.0)
مكعب1.اللون = لون(0.8, 0.2, 0.2)
مكعب1.الخامة.base = تحميل_خامة("C:/textures/wall.png")
"""

re_create   = re.compile(r'ابغا\s+([^\s=]+)\s*=\s*(صنع_[^\(]+)\((.*)\)')
re_prop_vec3= re.compile(r'([^\.]+)\.(الموقع|الدوران|المقياس)\s*=\s*متجه3\(([^,]+),\s*([^,]+),\s*([^\)]+)\)')
re_color    = re.compile(r'([^\.]+)\.اللون\s*=\s*لون\(([^,]+),\s*([^,]+),\s*([^\)]+)\)')
re_mat      = re.compile(r'([^\.]+)\.الخامة\.([a-zA-Z]+)\s*=\s*تحميل_خامة\("([^"]+)"\)')

obj_dict = {}
results = []

for line in sample_code.splitlines():
    line = line.strip()
    if not line: continue
    
    m = re_create.match(line)
    if m:
        name = m.group(1).strip()
        obj_dict[name] = {'name': name, 'color': None, 'material': {}}
        print(f'Created: {repr(name)}')
        continue
    
    m = re_color.search(line)
    if m:
        name = m.group(1).strip()
        r, g, b = float(m.group(2)), float(m.group(3)), float(m.group(4))
        print(f'Color line - name: {repr(name)}, in dict: {name in obj_dict}')
        if name in obj_dict:
            obj_dict[name]['color'] = [r, g, b]
        continue
    
    m = re_mat.search(line)
    if m:
        name = m.group(1).strip()
        key = m.group(2)
        path = m.group(3)
        print(f'Material line - name: {repr(name)}, in dict: {name in obj_dict}, key={key}')
        if name in obj_dict:
            obj_dict[name]['material'][key] = path
        continue

print('\nFinal obj_dict:')
for k, v in obj_dict.items():
    print(f'  {repr(k)}: color={v["color"]}, material={v["material"]}')
