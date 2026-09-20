import re

with open('ui2.py', 'r', encoding='utf-8') as f:
    code = f.read()

page_class = """from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEnginePage

class CustomWebEnginePage(QWebEnginePage):
    def javaScriptConsoleMessage(self, level, msg, line, source):
        print(f"JS Console: {msg} (line {line} in {source})")
        with open("js_debug.log", "a", encoding="utf-8") as lf:
            lf.write(f"JS Console: {msg} (line {line} in {source})\\n")
"""

# Replace QWebEngineView import and add CustomWebEnginePage
code = re.sub(
    r'from PyQt5\.QtWebEngineWidgets import QWebEngineView',
    page_class,
    code
)

# Replace self.browser = QWebEngineView(self)
code = re.sub(
    r'self\.browser = QWebEngineView\(self\)',
    r'self.browser = QWebEngineView(self)\n        self.browser.setPage(CustomWebEnginePage(self.browser))',
    code
)

with open('ui2.py', 'w', encoding='utf-8') as f:
    f.write(code)

print('Patched for JS debugging!')
