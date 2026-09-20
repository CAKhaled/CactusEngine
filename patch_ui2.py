import re

with open('ui2.py', 'r', encoding='utf-8') as f:
    code = f.read()

# 1. Replace overlay QWidget initialization with overlay_rect dict
code = re.sub(
    r'self\.overlay = QWidget\(self\.browser\)\n\s*self\.overlay\.setStyleSheet\("background: transparent;"\)\n\s*self\.overlay\.hide\(\) # Hidden until running',
    r'self.overlay_rect = {"x": 0, "y": 0, "w": 800, "h": 600}',
    code
)

# 2. Fix environment variable width/height passing
code = re.sub(
    r'env\.insert\("KH_WIDTH", str\(self\.mw\.overlay\.width\(\)\)\)\n\s*env\.insert\("KH_HEIGHT", str\(self\.mw\.overlay\.height\(\)\)\)',
    r'env.insert("KH_WIDTH", str(self.mw.overlay_rect["w"]))\n        env.insert("KH_HEIGHT", str(self.mw.overlay_rect["h"]))',
    code
)

# 3. Remove overlay.show() and hide()
code = re.sub(r'self\.mw\.overlay\.show\(\)', r'# Overlay show removed', code)
code = re.sub(r'self\.mw\.overlay\.hide\(\)', r'# Overlay hide removed', code)

# 4. Fix _on_stdout embedding
replacement_stdout = """                        qt_hwnd = int(self.mw.winId())
                        ctypes.windll.user32.SetParent(hwnd, qt_hwnd)
                        
                        w = self.mw.overlay_rect['w']
                        h = self.mw.overlay_rect['h']
                        x = self.mw.overlay_rect['x']
                        y = self.mw.overlay_rect['y']
                        ctypes.windll.user32.SetWindowPos(hwnd, 0, x, y, w, h, 0x0044)"""
                        
code = re.sub(
    r'qt_hwnd = int\(self\.mw\.overlay\.winId\(\)\)\n\s*ctypes\.windll\.user32\.SetParent\(hwnd, qt_hwnd\)\n\s*w = self\.mw\.overlay\.width\(\)\n\s*h = self\.mw\.overlay\.height\(\)\n\s*ctypes\.windll\.user32\.SetWindowPos\(hwnd, 0, 0, 0, w, h, 0x0044\)',
    replacement_stdout,
    code
)

# 5. Fix update_overlay_geometry
replacement_geom = """    def update_overlay_geometry(self, x, y, w, h):
        self.overlay_rect = {'x': x, 'y': y, 'w': w, 'h': h}
        if self.pygame_hwnd:
            import ctypes
            ctypes.windll.user32.SetWindowPos(self.pygame_hwnd, 0, x, y, w, h, 0x0044)"""

code = re.sub(
    r'    def update_overlay_geometry\(self, x, y, w, h\):\n.*?(?=\n    def resizeEvent)',
    replacement_geom + "\n",
    code,
    flags=re.DOTALL
)

with open('ui2.py', 'w', encoding='utf-8') as f:
    f.write(code)

print('Patched successfully!')
