import re

with open('ui2.py', 'r', encoding='utf-8') as f:
    code = f.read()

# 1. Bring back self.overlay as a TOP-LEVEL widget
overlay_init = """        self.overlay = QWidget(self)
        self.overlay.setWindowFlags(Qt.Window | Qt.FramelessWindowHint | Qt.Tool)
        self.overlay.setAttribute(Qt.WA_TranslucentBackground)
        self.overlay.setStyleSheet("background: transparent;")
        self.overlay.hide()"""

code = re.sub(
    r'self\.overlay_rect = \{"x": 0, "y": 0, "w": 800, "h": 600\}',
    overlay_init,
    code
)

# 2. Fix environment variables
code = re.sub(
    r'env\.insert\("KH_WIDTH", str\(self\.mw\.overlay_rect\["w"\]\)\)\n\s*env\.insert\("KH_HEIGHT", str\(self\.mw\.overlay_rect\["h"\]\)\)',
    r'env.insert("KH_WIDTH", str(self.mw.overlay.width()))\n        env.insert("KH_HEIGHT", str(self.mw.overlay.height()))',
    code
)

# 3. Add overlay.show() and hide()
code = re.sub(
    r'# Ensure overlay is visible\n\s*# Overlay show removed',
    r'# Ensure overlay is visible\n        self.mw.overlay.show()',
    code
)
code = re.sub(
    r'# Hide overlay so the background icon/hint is visible again\n\s*# Overlay hide removed',
    r'# Hide overlay so the background icon/hint is visible again\n        self.mw.overlay.hide()',
    code
)

# 4. Fix _on_stdout embedding
replacement_stdout = """                        qt_hwnd = int(self.mw.overlay.winId())
                        ctypes.windll.user32.SetParent(hwnd, qt_hwnd)
                        w = self.mw.overlay.width()
                        h = self.mw.overlay.height()
                        ctypes.windll.user32.SetWindowPos(hwnd, 0, 0, 0, w, h, 0x0044)"""
                        
code = re.sub(
    r'qt_hwnd = int\(self\.mw\.winId\(\)\)\n\s*ctypes\.windll\.user32\.SetParent\(hwnd, qt_hwnd\)\n\s*w = self\.mw\.overlay_rect\[\'w\'\]\n\s*h = self\.mw\.overlay_rect\[\'h\'\]\n\s*x = self\.mw\.overlay_rect\[\'x\'\]\n\s*y = self\.mw\.overlay_rect\[\'y\'\]\n\s*ctypes\.windll\.user32\.SetWindowPos\(hwnd, 0, x, y, w, h, 0x0044\)',
    replacement_stdout,
    code
)

# 5. Fix update_overlay_geometry
replacement_geom = """    def update_overlay_geometry(self, x, y, w, h):
        from PyQt5.QtCore import QPoint
        global_pos = self.browser.mapToGlobal(QPoint(int(x), int(y)))
        self.overlay.setGeometry(global_pos.x(), global_pos.y(), int(w), int(h))
        if self.pygame_hwnd:
            import ctypes
            ctypes.windll.user32.SetWindowPos(self.pygame_hwnd, 0, 0, 0, int(w), int(h), 0x0044)"""

code = re.sub(
    r'    def update_overlay_geometry\(self, x, y, w, h\):\n.*?(?=\n    def resizeEvent)',
    replacement_geom + "\n",
    code,
    flags=re.DOTALL
)

with open('ui2.py', 'w', encoding='utf-8') as f:
    f.write(code)

print('Patched successfully!')
