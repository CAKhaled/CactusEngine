"""
ui2.py  —  KH Engine IDE (WebEngine Version)
============================================
بيئة تطوير متكاملة للغة .kh باستخدام QtWebEngine و HTML/CSS/JS
"""

import sys
import os
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QFileDialog
from PyQt5.QtCore import Qt, QUrl, pyqtSlot, pyqtSignal, QObject, QProcess, QProcessEnvironment, QSize
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEnginePage

class CustomWebEnginePage(QWebEnginePage):
    def javaScriptConsoleMessage(self, level, msg, line, source):
        print(f"JS Console: {msg} (line {line} in {source})")
        with open("js_debug.log", "a", encoding="utf-8") as lf:
            lf.write(f"JS Console: {msg} (line {line} in {source})\\n")

from PyQt5.QtWebChannel import QWebChannel


class Backend(QObject):
    """
    This object bridges Python and JavaScript.
    It handles logic like File IO, Running processes, and tracking the preview div bounds.
    """
    
    # Signals to call JS functions from Python (since we can't directly call JS from backend methods easily)
    # We will pass a reference to the WebEngineView's page() to run JavaScript.
    
    def __init__(self, main_window):
        super().__init__()
        self.mw = main_window
        self.process = None
        self._is_stopping = False
        self.current_file = None

    @pyqtSlot()
    def new_file(self):
        self.current_file = None
        self.mw.run_js(f"window.ide.setEditorContent('# اكتب كود .kh هنا...');")
        self.mw.run_js(f"window.ide.setTabName('ملف جديد');")

    @pyqtSlot()
    def open_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self.mw, "فتح ملف", "", "KH Files (*.kh);;All Files (*)")
        if not path:
            return
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
            
        self.current_file = path
        # Escape for JS
        import json
        escaped_content = json.dumps(content)
        self.mw.run_js(f"window.ide.setEditorContent({escaped_content});")
        self.mw.run_js(f"window.ide.setTabName('{os.path.basename(path)}');")

    @pyqtSlot(str)
    def save_file(self, content):
        if not self.current_file:
            path, _ = QFileDialog.getSaveFileName(
                self.mw, "حفظ ملف", "", "KH Files (*.kh);;All Files (*)")
            if not path:
                return
            self.current_file = path

        with open(self.current_file, "w", encoding="utf-8") as f:
            f.write(content)
        
        self.mw.run_js(f"window.ide.setTabName('{os.path.basename(self.current_file)}');")
        self.mw.run_js(f"window.ide.consoleSucc('✓ تم الحفظ\\n');")

    @pyqtSlot(str)
    def run_code(self, content):
        # Save before running
        if self.current_file:
            self.save_file(content)
        else:
            import tempfile
            tmp = tempfile.NamedTemporaryFile(
                suffix=".kh", delete=False, mode="w", encoding="utf-8")
            tmp.write(content)
            tmp.close()
            self.current_file = tmp.name

        self.mw.run_js("window.ide.clearConsole();")
        
        name = os.path.basename(self.current_file)
        self.mw.run_js(f"window.ide.consoleInfo('▶ تشغيل: {name}\\n');")
        self.mw.run_js(f"window.ide.consoleInfo('─'.repeat(52) + '\\n');")

        kh_dir = os.path.dirname(os.path.abspath(__file__))
        kh_script = os.path.join(kh_dir, "kh.py")

        self.mw.pygame_hwnd = None
        self.process = QProcess(self)
        
        env = QProcessEnvironment.systemEnvironment()
        env.insert("KH_EMBEDDED", "1")
        env.insert("KH_WIDTH", str(self.mw.overlay.width()))
        env.insert("KH_HEIGHT", str(self.mw.overlay.height()))
        env.insert("PYTHONUNBUFFERED", "1")
        self.process.setProcessEnvironment(env)
        
        self.process.setWorkingDirectory(kh_dir)
        self.process.readyReadStandardOutput.connect(self._on_stdout)
        self.process.readyReadStandardError.connect(self._on_stderr)
        self.process.finished.connect(self._on_finished)
        
        self.process.start(sys.executable, [kh_script, self.current_file])

        self.mw.run_js("window.ide.setRunState(true);")
        # Ensure overlay is visible
        self.mw.overlay.show()

    @pyqtSlot()
    def stop_code(self):
        if self.process and self.process.state() != QProcess.NotRunning:
            self._is_stopping = True
            self.process.kill()

    @pyqtSlot(float, float, float, float)
    def update_preview_bounds(self, x, y, w, h):
        # JS reports the bounding client rect of the preview-body div
        # We need to map this to the WebEngineView coordinates and move the overlay
        self.mw.update_overlay_geometry(int(x), int(y), int(w), int(h))

    def _on_stdout(self):
        raw = self.process.readAllStandardOutput().data().decode("utf-8", errors="replace")
        
        if "__KH_HWND__:" in raw:
            for line in raw.splitlines():
                if line.startswith("__KH_HWND__:"):
                    try:
                        hwnd = int(line.split(":")[1])
                        self.mw.pygame_hwnd = hwnd
                        import ctypes
                        qt_hwnd = int(self.mw.overlay.winId())
                        ctypes.windll.user32.SetParent(hwnd, qt_hwnd)
                        w = self.mw.overlay.width()
                        h = self.mw.overlay.height()
                        ctypes.windll.user32.SetWindowPos(hwnd, 0, 0, 0, w, h, 0x0044)
                    except Exception as e:
                        self._send_err(f"Embed error: {e}\n")
                else:
                    self._send_out(line + "\\n")
        else:
            self._send_out(raw)

    def _on_stderr(self):
        raw = self.process.readAllStandardError().data().decode("utf-8", errors="replace")
        skip = ("UserWarning", "pkg_resources", "setuptools", "pygame community",
                "Hello from", "pkgdata")
        lines = [l for l in raw.splitlines() if not any(s in l for s in skip)]
        if lines:
            self._send_err("\\n".join(lines) + "\\n")

    def _on_finished(self, code, _):
        self.mw.run_js("window.ide.setRunState(false);")
        if code == 0 or self._is_stopping:
            self._send_succ("\\n✓ انتهى البرنامج\\n")
        else:
            self._send_err(f"\\n✗ انتهى بخطأ (كود: {code})\\n")
            self.mw.run_js("window.ide.setErrorState();")
            
        self._is_stopping = False
        
        # Hide overlay so the background icon/hint is visible again
        self.mw.overlay.hide()

    def _send_out(self, text):
        import json
        self.mw.run_js(f"window.ide.consoleOut({json.dumps(text)});")

    def _send_err(self, text):
        import json
        self.mw.run_js(f"window.ide.consoleErr({json.dumps(text)});")

    def _send_info(self, text):
        import json
        self.mw.run_js(f"window.ide.consoleInfo({json.dumps(text)});")
        
    def _send_succ(self, text):
        import json
        self.mw.run_js(f"window.ide.consoleSucc({json.dumps(text)});")


class KHIdeWeb(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("KH Engine IDE (Web Version)")
        self.resize(1440, 860)
        self.setMinimumSize(900, 600)
        
        # Load High DPI settings
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

        # Setup WebEngineView
        self.browser = QWebEngineView(self)
        self.browser.setPage(CustomWebEnginePage(self.browser))
        
        # Allow file:/// to access https:// (fixes Monaco CDN loading)
        from PyQt5.QtWebEngineWidgets import QWebEngineSettings
        settings = self.browser.settings()
        settings.setAttribute(QWebEngineSettings.LocalContentCanAccessRemoteUrls, True)
        settings.setAttribute(QWebEngineSettings.LocalContentCanAccessFileUrls, True)
        
        self.setCentralWidget(self.browser)

        # Disable context menu for cleaner feel
        self.browser.setContextMenuPolicy(Qt.NoContextMenu)

        # Setup Overlay for Pygame
        # It's a child of the browser, so it floats on top of the web content.
        self.overlay = QWidget(self)
        self.overlay.setWindowFlags(Qt.Window | Qt.FramelessWindowHint | Qt.Tool)
        self.overlay.setAttribute(Qt.WA_TranslucentBackground)
        self.overlay.setStyleSheet("background: transparent;")
        self.overlay.hide()
        
        # Pygame Window Handle
        self.pygame_hwnd = None

        # Setup WebChannel
        self.channel = QWebChannel()
        self.backend = Backend(self)
        self.channel.registerObject("backend", self.backend)
        self.browser.page().setWebChannel(self.channel)

        # Load ui2.html
        html_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ui2.html")
        self.browser.setUrl(QUrl.fromLocalFile(html_path))

        # Load default file if exists
        default = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hello.kh")
        if os.path.exists(default):
            self.backend.current_file = default
            # We must wait for page load to set content
            self.browser.loadFinished.connect(self._on_load_finished)

    def _on_load_finished(self, ok):
        if ok and self.backend.current_file:
            try:
                with open(self.backend.current_file, "r", encoding="utf-8") as f:
                    content = f.read()
                import json
                escaped_content = json.dumps(content)
                self.run_js(f"window.ide.setEditorContent({escaped_content});")
                self.run_js(f"window.ide.setTabName('{os.path.basename(self.backend.current_file)}');")
            except Exception as e:
                print(f"Error loading initial file: {e}")

    def run_js(self, script):
        self.browser.page().runJavaScript(script)

    def update_overlay_geometry(self, x, y, w, h):
        from PyQt5.QtCore import QPoint
        global_pos = self.browser.mapToGlobal(QPoint(int(x), int(y)))
        self.overlay.setGeometry(global_pos.x(), global_pos.y(), int(w), int(h))
        if self.pygame_hwnd:
            import ctypes
            ctypes.windll.user32.SetWindowPos(self.pygame_hwnd, 0, 0, 0, int(w), int(h), 0x0044)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Note: JS ResizeObserver will trigger and call update_preview_bounds automatically.

def main():
    QApplication.setAttribute(Qt.AA_DontCreateNativeWidgetSiblings, True)
    app = QApplication(sys.argv)
    
    ide = KHIdeWeb()
    
    # Enable Windows Dark Mode Titlebar
    try:
        import ctypes
        hwnd = int(ide.winId())
        val = ctypes.c_int(1)
        ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 20, ctypes.byref(val), ctypes.sizeof(val))
        ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 19, ctypes.byref(val), ctypes.sizeof(val))
    except Exception:
        pass

    ide.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
