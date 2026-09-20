"""
ui.py  —  KH Engine IDE
========================
بيئة تطوير متكاملة للغة .kh
"""

import sys
import os
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QToolBar, QToolButton,
    QSplitter, QPlainTextEdit, QVBoxLayout, QHBoxLayout,
    QLabel, QFileDialog, QFrame, QSizePolicy, QTextEdit,
    QStatusBar, QLineEdit, QPushButton, QListWidget, QListWidgetItem,
    QInputDialog, QMessageBox, QDialog, QCompleter, QTreeWidget, QTreeWidgetItem, QShortcut
)
from view_scene_ui import SceneUI
from PyQt5.QtCore import (
    Qt, QSize, QRect, QProcess, QProcessEnvironment, QTimer, QRegularExpression, QThread, pyqtSignal, QStringListModel
)
from PyQt5.QtGui import (
    QFont, QFontMetricsF, QColor, QTextCharFormat, QPainter,
    QSyntaxHighlighter, QTextCursor, QTextFormat, QKeySequence,
    QPalette, QLinearGradient, QGradient, QTextOption, QIcon, QPixmap, QPainter, QPen, QBrush, QPainterPath
)


# ════════════════════════════════════════════════════════════════
#  🎨  Palette
# ════════════════════════════════════════════════════════════════
BG          = "#090F17"
BG_PANEL    = "#101822"
BG_EDITOR   = "#0C131C"
BG_CONSOLE  = "#080E15"
TOOLBAR_BG  = "#101821"
BORDER      = "#2D3948"
BORDER2     = "#465467"

ACCENT      = "#8B5CF6"
ACCENT2     = "#A855F7"
GREEN       = "#55D66B"
GREEN_DARK  = "#2F8A46"
RED         = "#F06A75"

TEXT        = "#E9EDF3"
TEXT_DIM    = "#7E8999"
TEXT_MED    = "#B7C0CC"

# ─── Syntax colours ───────────────────────────────────────────
S_KEYWORD   = "#c586c0"
S_BUILTIN   = "#dcdcaa"
S_STRING    = "#ce9178"
S_NUMBER    = "#b5cea8"
S_COMMENT   = "#6a9955"
S_OPERATOR  = "#d4d4d4"
S_PROPERTY  = "#9cdcfe"
S_VARIABLE  = "#9cdcfe"
S_VALUE     = "#b5cea8"
S_FUNCTION  = "#dcdcaa"
S_OBJECT    = "#4ec9b0"


# ════════════════════════════════════════════════════════════════
#  📝  Syntax Highlighter  (.kh)
# ════════════════════════════════════════════════════════════════
from ai_agent import ask_claude

class AIWorker(QThread):
    finished = pyqtSignal(str)
    
    def __init__(self, prompt, editor_code=""):
        super().__init__()
        self.prompt = prompt
        self.editor_code = editor_code
        
    def run(self):
        result = ask_claude(self.prompt, self.editor_code)
        self.finished.emit(result)

class KHHighlighter(QSyntaxHighlighter):

    def __init__(self, doc):
        super().__init__(doc)
        self._rules = []

        def add(pattern, color, bold=False, italic=False):
            fmt = QTextCharFormat()
            fmt.setForeground(QColor(color))
            if bold:
                fmt.setFontWeight(QFont.Bold)
            if italic:
                fmt.setFontItalic(True)
            self._rules.append((QRegularExpression(pattern), fmt))

        # Arabic-aware word character: letters, numbers, underscore
        w = r"[\p{L}\p{N}_]"

        # 1. Variables (Catch-all for all words, overwritten by rules below)
        add(rf"(?<!{w})({w}+)(?!{w})", S_VARIABLE)

        # 2. Properties (after dot)
        add(rf"\.{w}+", S_PROPERTY)

        # 3. Objects (before dot)
        add(rf"(?<!{w})({w}+)(?=\.)", S_OBJECT)

        # 4. Functions (before open parenthesis)
        add(rf"(?<!{w})({w}+)(?=\()", S_FUNCTION)

        # 5. Keywords
        kws = "|".join([
            "ابغا", "اطبع", "تشغيل", r"كل_فريم", "كل فريم",
            "إذا", "اذا", "وإلا", "غير_ذلك", "كرر", "توقف", "دالة", "ارجع", "ارجاع",
            "كلاس", "كائن", "بناء"
        ])
        add(rf"(?<!{w}|\.)({kws})(?!{w})", S_KEYWORD, bold=True)

        # 6. Built-in Types & Pre-defined Objects
        builtins = "|".join(["متجه2", "متجه3", "لون"])
        add(rf"(?<!{w}|\.)({builtins})(?=\()", S_BUILTIN)
        
        objects = "|".join(["ماوس", "كيبورد", "هذا"])
        add(rf"(?<!{w}|\.)({objects})(?!{w})", S_OBJECT, italic=True)

        # 7. Values (Booleans)
        values = "|".join(["مفعل", "مقفل", "True", "False"])
        add(rf"(?<!{w}|\.)({values})(?!{w})", S_VALUE, bold=True)

        # 8. Strings
        add(r'"[^"\n]*"', S_STRING)
        add(r"'[^'\n]*'", S_STRING)

        # 9. Numbers
        add(r"\b\d+(\.\d+)?\b", S_NUMBER)

        # 10. Operators
        add(r"[+\-*/=<>!]+|[().,]", S_OPERATOR)

        # 11. Comments (must be last to override everything)
        add(r"#[^\n]*", S_COMMENT, italic=True)

    def highlightBlock(self, text):
        for pattern, fmt in self._rules:
            it = pattern.globalMatch(text)
            while it.hasNext():
                m = it.next()
                self.setFormat(m.capturedStart(), m.capturedLength(), fmt)


# ════════════════════════════════════════════════════════════════
#  🔢  Line Number Gutter
# ════════════════════════════════════════════════════════════════
class LineNumbers(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor

    def sizeHint(self):
        return QSize(self.editor._gutter_width(), 0)

    def paintEvent(self, e):
        self.editor._paint_gutter(e)


# ════════════════════════════════════════════════════════════════
#  💡  IntelliSense Schema
# ════════════════════════════════════════════════════════════════
KH_SCHEMA = {
    "واجهة": ["اضافة_نص", "اضافة_زر", "كامل_الشاشة", "لون_الخلفية", "شفافية_الخلفية", "المقياس", "الموقع"],
    "مصفوفة": ["ضف", "احذف", "احذف_فهرس", "طول"],
    "UIElement": ["الموقع", "المقياس", "لون_النص", "الخامة", "مضغوط", "النص", "ازاحة", "افقي", "عمودي", "حجم_الخط", "اسم_الخط", "لون_الخلفية", "شفافية_الخلفية"],
    "Object2D": ["الاسم", "الموقع", "الدوران", "المقياس", "اللون", "الصورة", "تصادم", "جاذبية", "صدام"],
    "Object3D": ["الاسم", "الموقع", "الدوران", "المقياس", "اللون", "الخامة", "تصادم", "جاذبية", "صدام"],
    "FBXModel": ["الاسم", "الموقع", "الدوران", "المقياس", "اللون", "الخامة", "تصادم", "جاذبية", "صدام", "المكون"],
    "ضوء": ["النوع", "الموقع", "الاتجاه", "اللون", "الشدة"],
    "ضوء_بقعي": ["النوع", "الموقع", "الاتجاه", "اللون", "الشدة", "زاوية_البقعة", "حدة_البقعة"],
    "صوت": ["تشغيل"],
    "كاميرا": ["الموقع", "الدوران", "الأمام", "اليمين", "أعلى", "زاوية_الرؤية", "اشعاع"],
    "متجه3": ["x", "y", "z", "الأمام", "اليمين"],
    "متجه2": ["x", "y", "الأمام", "اليمين"],
    "ماوس": ["أفقي", "عمودي", "حركة_أفقية", "حركة_عمودية", "ضغط_يسار", "ضغط_يمين", "معلق"],
    "كيبورد": ["مضغوط"],
    "وقت": ["دلتا", "دلتا_مصلح"],
    "رياضيات": ["lerp", "sin", "cos", "abs", "حركة_سلسة"],
    "الخامة": ["base", "metallic", "roughness", "normal", "AC"]
}

KH_RETURN_TYPES = {
    "صنع_واجهة": "واجهة",
    "اضافة_نص": "UIElement",
    "اضافة_زر": "UIElement",
    "صنع_مكعب": "Object3D",
    "صنع_كرة": "Object3D",
    "صنع_سطح": "Object3D",
    "صنع_هرم": "Object3D",
    "صنع_اسطوانة": "Object3D",
    "صنع_كبسولة": "Object3D",
    "صنع_مربع2D": "Object2D",
    "صنع_دائرة2D": "Object2D",
    "صنع_مثلث2D": "Object2D",
    "صنع_مخصص": "Object3D",
    "صنع_fbx": "FBXModel",
    "صنع_Fbx": "FBXModel",
    "صنع_FBX": "FBXModel",
    "صنع_مخصص2D": "Object3D",
    "صنع_ضوء": "ضوء",
    "صنع_صوت": "صوت",
    "متجه3": "متجه3",
    "متجه2": "متجه2",
    "اشعاع": "Object3D",
}

KH_GLOBALS = {
    "ماوس": "ماوس",
    "كيبورد": "كيبورد",
    "الكاميرا": "كاميرا",
    "متجه3": "متجه3",
    "متجه2": "متجه2",
    "وقت": "وقت",
    "رياضيات": "رياضيات"
}

# ════════════════════════════════════════════════════════════════
#  📄  Code Editor
# ════════════════════════════════════════════════════════════════
class CodeEditor(QPlainTextEdit):

    def __init__(self):
        super().__init__()
        self._gutter = LineNumbers(self)
        self.blockCountChanged.connect(self._update_gutter_width)
        self.updateRequest.connect(self._update_gutter)
        self.cursorPositionChanged.connect(self._highlight_line)

        self._update_gutter_width(0)
        self._highlight_line()

        font = QFont("Segoe UI", 15)
        font.setStyleHint(QFont.SansSerif)
        font.setHintingPreference(QFont.PreferNoHinting)
        font.setWeight(QFont.Normal)
        self.setFont(font)
        self.setTabStopDistance(QFontMetricsF(self.font()).horizontalAdvance(" ") * 4)
        self.setLineWrapMode(QPlainTextEdit.NoWrap)
        
        # Keep the document direction natural so Arabic and English glyphs
        # are rendered by the platform text engine without forced pixel-like RTL layout.
        opt = self.document().defaultTextOption()
        opt.setWrapMode(QTextOption.NoWrap)
        opt.setTextDirection(Qt.RightToLeft)
        opt.setAlignment(Qt.AlignRight)
        self.document().setDefaultTextOption(opt)

        self._highlighter = KHHighlighter(self.document())

        self.completer = QCompleter(self)
        self.completer.setWidget(self)
        self.completer.setCompletionMode(QCompleter.PopupCompletion)
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.completer.activated.connect(self.insertCompletion)
        self.completer_model = QStringListModel()
        self.completer.setModel(self.completer_model)

    # ── Gutter helpers ────────────────────────────────────────
    def _gutter_width(self):
        digits = max(3, len(str(self.blockCount())))
        return 28 + self.fontMetrics().horizontalAdvance("9") * digits

    def _update_gutter_width(self, _):
        self.setViewportMargins(self._gutter_width(), 0, 0, 0)

    def _update_gutter(self, rect, dy):
        if dy:
            self._gutter.scroll(0, dy)
        else:
            self._gutter.update(0, rect.y(), self._gutter.width(), rect.height())
        if rect.contains(self.viewport().rect()):
            self._update_gutter_width(0)

    def wheelEvent(self, e):
        if e.modifiers() & Qt.ControlModifier:
            delta = e.angleDelta().y()
            if delta > 0:
                self.zoomIn(1)
            elif delta < 0:
                self.zoomOut(1)
            self._update_gutter_width(0)
            return
        super().wheelEvent(e)

    def resizeEvent(self, e):
        super().resizeEvent(e)
        cr = self.contentsRect()
        self._gutter.setGeometry(QRect(cr.left(), cr.top(), self._gutter_width(), cr.height()))

    def _paint_gutter(self, event):
        p = QPainter(self._gutter)
        p.fillRect(event.rect(), QColor("#0A1018"))

        block  = self.firstVisibleBlock()
        num    = block.blockNumber()
        top    = round(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom = top + round(self.blockBoundingRect(block).height())
        cur    = self.textCursor().blockNumber()

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                color = "#F3F6FA" if num == cur else "#788596"
                p.setPen(QColor(color))
                p.drawText(0, top, self._gutter.width() - 10,
                           self.fontMetrics().height(),
                           Qt.AlignRight, str(num + 1))
            block  = block.next()
            top    = bottom
            bottom = top + round(self.blockBoundingRect(block).height())
            num   += 1

    def _highlight_line(self):
        sel = QTextEdit.ExtraSelection()
        sel.format.setBackground(QColor("#111B29"))
        sel.format.setProperty(QTextFormat.FullWidthSelection, True)
        sel.cursor = self.textCursor()
        sel.cursor.clearSelection()
        self.setExtraSelections([sel])

    def insertCompletion(self, completion):
        if self.completer.widget() is not self:
            return
        tc = self.textCursor()
        extra = len(completion) - len(self.completer.completionPrefix())
        tc.movePosition(QTextCursor.Left)
        tc.movePosition(QTextCursor.EndOfWord)
        tc.insertText(completion[-extra:])
        self.setTextCursor(tc)

    def _infer_type(self, var_name, depth=0):
        if depth > 5: return None
        if var_name == "الخامة": return "الخامة"
        import re
        if var_name in KH_GLOBALS:
            return KH_GLOBALS[var_name]
        
        doc_text = self.toPlainText()
        
        if hasattr(self, 'ide') and getattr(self.ide, 'project_dir', None):
            import os
            proj_dir = self.ide.project_dir
            try:
                for fname in os.listdir(proj_dir):
                    if fname.endswith(".khscene"):
                        try:
                            with open(os.path.join(proj_dir, fname), "r", encoding="utf-8") as f:
                                doc_text = f.read() + "\n" + doc_text
                        except Exception:
                            pass
            except Exception:
                pass
        
        array_match = re.search(r'^(.+)\[.*\]$', var_name)
        if array_match:
            base_name = array_match.group(1).strip()
            
            add_pattern = r'\b' + re.escape(base_name) + r'\.(?:ضف|إضافة)\s*\(\s*([^)]+)\s*\)'
            add_matches = list(re.finditer(add_pattern, doc_text))
            if add_matches:
                last_added = add_matches[-1].group(1).strip()
                return self._infer_type(last_added, depth + 1)
                
            assign_pattern = r'\b' + re.escape(base_name) + r'\[.*?\]\s*=\s*([^\n]+)'
            assign_matches = list(re.finditer(assign_pattern, doc_text))
            if assign_matches:
                last_assign = assign_matches[-1].group(1).strip()
                for func_name, ret_type in KH_RETURN_TYPES.items():
                    if last_assign.startswith(func_name):
                        return ret_type
                return self._infer_type(last_assign, depth + 1)
                
            init_pattern = r'\b' + re.escape(base_name) + r'\b\s*=\s*\[(.*?)\]'
            init_matches = list(re.finditer(init_pattern, doc_text))
            if init_matches:
                items_str = init_matches[-1].group(1).strip()
                if items_str:
                    first_item = items_str.split(",")[0].strip()
                    return self._infer_type(first_item, depth + 1)
                    
            return None

        pattern = r"(?:ابغا\s+)?(?:.*?,\s*)*\b" + re.escape(var_name) + r"\b\s*=\s*([^\n]+)"
        matches = list(re.finditer(pattern, doc_text))
        if not matches:
            return None
            
        last_assignment = matches[-1].group(1).strip()
        
        if last_assignment.startswith("[") and last_assignment.endswith("]"):
            return "مصفوفة"
        
        for func_name, ret_type in KH_RETURN_TYPES.items():
            if last_assignment.startswith(func_name):
                return ret_type
                
        if "." in last_assignment:
            parts = last_assignment.split(".")
            if len(parts) >= 2:
                method_part = parts[1].split("(")[0].strip()
                for func_name, ret_type in KH_RETURN_TYPES.items():
                    if method_part == func_name:
                        return ret_type
                        
        if re.match(r'^[\w\[\]]+$', last_assignment):
            return self._infer_type(last_assignment, depth + 1)
            
        return None

    # ── Auto indent and Autocomplete ──────────────────────────────
    def keyPressEvent(self, e):
        if self.completer.popup().isVisible():
            if e.key() in (Qt.Key_Enter, Qt.Key_Return, Qt.Key_Escape, Qt.Key_Tab, Qt.Key_Backtab):
                e.ignore()
                return

        is_shortcut = (e.modifiers() == Qt.ControlModifier and e.key() == Qt.Key_Space)

        if e.key() == Qt.Key_Return and not self.completer.popup().isVisible():
            cursor  = self.textCursor()
            line    = cursor.block().text()
            indent  = len(line) - len(line.lstrip())
            spaces  = " " * indent
            if line.rstrip().endswith(":"):
                spaces += "    "
            super().keyPressEvent(e)
            self.insertPlainText(spaces)
            return

        super().keyPressEvent(e)

        ctrl_or_shift = e.modifiers() & (Qt.ControlModifier | Qt.ShiftModifier)
        if ctrl_or_shift and not e.text():
            return
            
        import re
        tc = self.textCursor()
        line_text = tc.block().text()
        cursor_pos = tc.positionInBlock()
        text_up_to_cursor = line_text[:cursor_pos]
        
        should_show = False
        options = []
        completion_prefix = ""
        
        match = re.search(r'([\w\[\]]+)\.(\w*)$', text_up_to_cursor)
        if match:
            var_name = match.group(1)
            completion_prefix = match.group(2)
            var_type = self._infer_type(var_name)
            
            if var_type == "ضوء":
                doc_text = self.toPlainText()
                if re.search(r'\b' + re.escape(var_name) + r'\.النوع\s*=\s*["\']ضوء_بقعي["\']', doc_text):
                    var_type = "ضوء_بقعي"
                    
            if var_type and var_type in KH_SCHEMA:
                options = KH_SCHEMA[var_type]
                should_show = True
            
        if not should_show and not is_shortcut:
            self.completer.popup().hide()
            return
            
        self.completer_model.setStringList(options)
        
        if completion_prefix != self.completer.completionPrefix():
            self.completer.setCompletionPrefix(completion_prefix)
            self.completer.popup().setCurrentIndex(self.completer.completionModel().index(0, 0))

        cr = self.cursorRect()
        cr.setWidth(self.completer.popup().sizeHintForColumn(0) + self.completer.popup().verticalScrollBar().sizeHint().width())
        self.completer.complete(cr)


# ════════════════════════════════════════════════════════════════
#  🖥  Console
# ════════════════════════════════════════════════════════════════
class Console(QPlainTextEdit):

    def __init__(self):
        super().__init__()
        self.setReadOnly(True)
        font = QFont()
        font.setFamilies(["Cascadia Code", "Consolas", "Fira Code", "Courier New"])
        font.setPointSize(11)
        self.setFont(font)

    def _write(self, text, color):
        cur = self.textCursor()
        cur.movePosition(QTextCursor.End)
        fmt = QTextCharFormat()
        fmt.setForeground(QColor(color))
        cur.setCharFormat(fmt)
        cur.insertText(text)
        self.setTextCursor(cur)
        self.ensureCursorVisible()

    def out(self, text):
        self._write(text, TEXT)

    def err(self, text):
        self._write(text, "#f87171")

    def info(self, text):
        self._write(text, ACCENT2)

    def success(self, text):
        self._write(text, GREEN)



# ════════════════════════════════════════════════════════════════
#  ✦  Crisp UI Icons
# ════════════════════════════════════════════════════════════════
TOOL_ICON_COLORS = {
    "new": "#6CB6FF",
    "open": "#F5C451",
    "save": "#63D7A0",
    "saveas": "#A78BFA",
    "run": "#FFFFFF",
    "stop": "#FF7A8A",
    "more": "#C3CCD8",
}

ACTIVITY_ICON_COLORS = {
    "code": "#7DD3FC",
    "scene": "#C4B5FD",
    "programming": "#7DD3FC",
    "scene_view": "#C4B5FD",
}

def make_ui_icon(kind, color="#B8C2D0", size=24):
    """Draw small anti-aliased vector-like icons instead of emoji glyphs."""
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)

    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing, True)
    p.setRenderHint(QPainter.SmoothPixmapTransform, True)
    pen = QPen(QColor(color))
    pen.setWidthF(1.8)
    pen.setCapStyle(Qt.RoundCap)
    pen.setJoinStyle(Qt.RoundJoin)
    p.setPen(pen)
    p.setBrush(Qt.NoBrush)

    r = 4
    c = int(size / 2)

    if kind == "code":
        p.drawLine(8, 7, 3, c)
        p.drawLine(3, c, 8, size - 7)
        p.drawLine(size - 8, 7, size - 3, c)
        p.drawLine(size - 3, c, size - 8, size - 7)
        p.drawLine(c + 3, 5, c - 3, size - 5)
    elif kind == "scene":
        p.drawLine(10, 16, 10, 6)     # Y-axis
        p.drawLine(10, 16, 20, 16)    # X-axis
        p.drawLine(10, 16, 4, 22)     # Z-axis
        
        # Draw small arrow heads
        p.drawLine(10, 6, 7, 9)
        p.drawLine(10, 6, 13, 9)
        
        p.drawLine(20, 16, 17, 13)
        p.drawLine(20, 16, 17, 19)
    elif kind == "search":
        p.drawEllipse(4, 4, 12, 12)
        p.drawLine(14, 14, 20, 20)
    elif kind == "file":
        p.drawRect(6, 4, 11, 16)
        p.drawLine(13, 4, 17, 8)
        p.drawLine(13, 4, 13, 8)
        p.drawLine(13, 8, 17, 8)
    elif kind == "folder":
        p.drawRoundedRect(3, 6, size - 6, size - 9, 3, 3)
        p.drawLine(4, 8, 10, 8)
        p.drawLine(8, 5, 12, 5)
        p.drawLine(12, 5, 14, 8)
    elif kind == "new":
        p.drawRect(5, 4, 11, 16)
        p.drawLine(13, 4, 16, 7)
        p.drawLine(13, 4, 13, 7)
        p.drawLine(13, 7, 16, 7)
        p.drawLine(c, 11, c, 17)
        p.drawLine(9, 14, 15, 14)
    elif kind == "open":
        p.drawRoundedRect(3, 7, 18, 13, 2, 2)
        p.drawLine(4, 7, 9, 7)
        p.drawLine(8, 5, 13, 5)
        p.drawLine(13, 5, 15, 8)
    elif kind == "save":
        p.drawRect(4, 4, 16, 16)
        p.drawRect(7, 5, 13, 6)
        p.drawRect(8, 14, 8, 5)
    elif kind == "saveas":
        p.drawRect(4, 4, 16, 16)
        p.drawLine(12, 9, 12, 17)
        p.drawLine(8, 13, 12, 17)
        p.drawLine(16, 13, 12, 17)
    elif kind == "play":
        path = QPainterPath()
        path.moveTo(7, 5)
        path.lineTo(16, c)
        path.lineTo(7, size - 5)
        path.closeSubpath()
        p.setBrush(QColor(color))
        p.drawPath(path)
    elif kind == "stop":
        p.setBrush(QColor(color))
        p.drawRoundedRect(6, 6, 12, 12, 2, 2)
    elif kind == "settings":
        p.drawEllipse(6, 6, 12, 12)
        p.drawEllipse(10, 10, 4, 4)
        for x1, y1, x2, y2 in [(12,2,12,5),(12,19,12,22),(2,12,5,12),(19,12,22,12)]:
            p.drawLine(x1,y1,x2,y2)
    elif kind == "bell":
        p.drawArc(6, 5, 12, 13, 0, 180 * 16)
        p.drawLine(6, 11, 6, 15)
        p.drawLine(18, 11, 18, 15)
        p.drawLine(5, 16, 19, 16)
        p.drawEllipse(10, 18, 4, 3)
    elif kind == "more":
        p.setBrush(QColor(color))
        for y in (7, 12, 17):
            p.drawEllipse(10, y, 4, 4)

    p.end()
    return QIcon(pm)


def make_cactus_logo(size=64):
    """Crisp anti-aliased Cactus Engine logo."""
    size = int(size)
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)

    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing, True)
    p.setRenderHint(QPainter.SmoothPixmapTransform, True)

    def line(x1, y1, x2, y2):
        p.drawLine(int(x1), int(y1), int(x2), int(y2))

    glow = QColor("#69E5B0")
    glow.setAlpha(38)
    gp = QPen(glow)
    gp.setWidthF(9.0)
    gp.setCapStyle(Qt.RoundCap)
    p.setPen(gp)

    line(size*.50, size*.82, size*.50, size*.27)
    line(size*.50, size*.47, size*.31, size*.47)
    line(size*.31, size*.47, size*.31, size*.60)
    line(size*.50, size*.56, size*.69, size*.56)
    line(size*.69, size*.56, size*.69, size*.43)

    pen = QPen(QColor("#63E2AE"))
    pen.setWidthF(5.0)
    pen.setCapStyle(Qt.RoundCap)
    pen.setJoinStyle(Qt.RoundJoin)
    p.setPen(pen)

    line(size*.50, size*.82, size*.50, size*.27)
    line(size*.50, size*.46, size*.31, size*.46)
    line(size*.31, size*.46, size*.31, size*.60)
    line(size*.50, size*.56, size*.69, size*.56)
    line(size*.69, size*.56, size*.69, size*.43)
    line(size*.37, size*.84, size*.63, size*.84)

    p.end()
    return pm

# ════════════════════════════════════════════════════════════════
#  🏠  Main Window
# ════════════════════════════════════════════════════════════════
class KHIde(QMainWindow):

    def __init__(self):
        super().__init__()
        self.current_file  = None
        self.project_dir   = None
        self._is_dirty     = False
        self.process       = None
        self._is_stopping  = False

        self.setWindowTitle("Cactus Engine IDE")
        self.resize(1600, 900)

        self._apply_palette()
        self._build_toolbar()
        self._build_central()
        self._build_statusbar()

        # Connect editor changes for dirty flag
        # Delay so initial load doesn't mark dirty
        QTimer.singleShot(200, lambda:
            self.editor.document().contentsChanged.connect(self._mark_dirty))
            
        # Global shortcuts for Fullscreen exit
        self.esc_shortcut = QShortcut(QKeySequence(Qt.Key_Escape), self)
        self.esc_shortcut.setContext(Qt.ApplicationShortcut)
        self.esc_shortcut.activated.connect(self._handle_global_esc)
        
        self.f_shortcut = QShortcut(QKeySequence(Qt.Key_F), self)
        self.f_shortcut.setContext(Qt.ApplicationShortcut)
        self.f_shortcut.activated.connect(self._handle_global_f)

    # ── Global palette / style ────────────────────────────────
    def _apply_palette(self):
        pal = QPalette()
        pal.setColor(QPalette.Window, QColor(BG))
        pal.setColor(QPalette.Base, QColor(BG_EDITOR))
        pal.setColor(QPalette.Text, QColor(TEXT))
        pal.setColor(QPalette.WindowText, QColor(TEXT))
        pal.setColor(QPalette.Button, QColor(BG_PANEL))
        pal.setColor(QPalette.ButtonText, QColor(TEXT))
        pal.setColor(QPalette.Highlight, QColor(ACCENT))
        pal.setColor(QPalette.HighlightedText, QColor("#FFFFFF"))
        QApplication.setPalette(pal)

        self.setStyleSheet(f"""
            * {{
                font-family: "Segoe UI", "Cairo", "Tahoma", sans-serif;
            }}
            QMainWindow, QWidget {{
                background: {BG};
                color: {TEXT};
            }}
            QScrollBar:vertical {{
                background: #0B1119;
                width: 8px;
                border: none;
            }}
            QScrollBar::handle:vertical {{
                background: {BORDER2};
                border-radius: 4px;
                min-height: 26px;
                margin: 2px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: #667386;
            }}
            QScrollBar:horizontal {{
                background: #0B1119;
                height: 8px;
                border: none;
            }}
            QScrollBar::handle:horizontal {{
                background: {BORDER2};
                border-radius: 4px;
                min-width: 26px;
                margin: 2px;
            }}
            QScrollBar::add-line, QScrollBar::sub-line {{
                width: 0; height: 0;
            }}
            QToolTip {{
                background: #151D28;
                color: {TEXT};
                border: 1px solid {BORDER2};
                border-radius: 5px;
                padding: 6px 9px;
            }}
        """)

    # ── Top command bar ───────────────────────────────────────
    def _build_toolbar(self):
        class TopBar(QFrame):
            def mousePressEvent(self, event):
                from PyQt5.QtCore import Qt
                if event.button() == Qt.LeftButton:
                    import ctypes
                    hwnd = int(self.window().winId())
                    ctypes.windll.user32.ReleaseCapture()
                    ctypes.windll.user32.SendMessageW(hwnd, 0x00A1, 2, 0) # WM_NCLBUTTONDOWN = 0xA1, HTCAPTION = 2
                super().mousePressEvent(event)
                
            def mouseDoubleClickEvent(self, event):
                from PyQt5.QtCore import Qt
                if event.button() == Qt.LeftButton:
                    if self.window().isMaximized():
                        self.window().showNormal()
                    else:
                        self.window().showMaximized()
                super().mouseDoubleClickEvent(event)

        bar = TopBar()
        bar.setObjectName("TopCommandBar")
        bar.setFixedHeight(70)
        bar.setStyleSheet(f"""
            QFrame#TopCommandBar {{
                background: {BG};
                border: none;
            }}
            QToolButton {{
                background: transparent;
                color: {TEXT_MED};
                border: 1px solid transparent;
                border-radius: 7px;
                padding: 8px 11px;
                font-size: 13px;
                font-weight: 500;
            }}
            QToolButton:hover {{
                color: #FFFFFF;
                background: #18212D;
                border-color: #2A3747;
            }}
        """)

        lay = QHBoxLayout(bar)
        lay.setContentsMargins(14, 8, 12, 8)
        lay.setSpacing(5)

        logo_wrap = QWidget()
        logo_lay = QHBoxLayout(logo_wrap)
        logo_lay.setContentsMargins(2, 0, 13, 0)
        logo_lay.setSpacing(7)

        logo_icon = QLabel()
        pm = QPixmap(os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon.png"))
        if not pm.isNull():
            pm = pm.scaled(28, 28, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo_icon.setPixmap(pm)
        else:
            logo_icon.setPixmap(make_cactus_logo(28))
        logo_icon.setFixedSize(28, 28)
        logo_lay.addWidget(logo_icon)

        logo = QLabel("Cactus Engine IDE")
        logo.setStyleSheet("""
            color:#E9EDF3;
            font-family:"Segoe UI","Tahoma",sans-serif;
            font-size:15px;
            font-weight:700;
        """)
        logo_lay.addWidget(logo)
        lay.addWidget(logo_wrap)

        line = QFrame()
        line.setFrameShape(QFrame.VLine)
        line.setFixedHeight(30)
        line.setStyleSheet(f"border-left: 1px solid {BORDER};")
        lay.addWidget(line)

        def add_btn(kind, label, tip, slot=None, shortcut=None, badge=None, badge_color="#6F7B8B"):
            wrap = QWidget()
            wrap.setAttribute(Qt.WA_TranslucentBackground, True)
            wl = QHBoxLayout(wrap)
            wl.setContentsMargins(0, 0, 2, 0)
            wl.setSpacing(2)

            b = QToolButton()
            b.setIcon(make_ui_icon(kind, TOOL_ICON_COLORS.get(kind, "#D6DEE9"), 22))
            b.setIconSize(QSize(20, 20))
            b.setText(label)
            b.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
            b.setToolTip(tip)
            if shortcut:
                b.setShortcut(QKeySequence(shortcut))
            if slot:
                b.clicked.connect(slot)
            wl.addWidget(b)

            if badge is not None:
                bd = QLabel(str(badge))
                bd.setAlignment(Qt.AlignCenter)
                bd.setFixedSize(14, 14)
                bd.setStyleSheet(
                    f"background:{badge_color}; color:#FFFFFF; border-radius:7px; "
                    "font-size:8px; font-weight:700;"
                )
                wl.addWidget(bd)

            lay.addWidget(wrap)
            return b

        add_btn("new", "جديد", "مشروع جديد", self.new_project_toolbar, "Ctrl+N")
        add_btn("open", "فتح", "فتح ملف KH", self.open_file, "Ctrl+O")
        add_btn("save", "حفظ", "حفظ الملف", self.save_file, "Ctrl+S")
        add_btn("saveas", "حفظ باسم", "حفظ باسم", self.save_file_as)

        sep = QFrame()
        sep.setFrameShape(QFrame.VLine)
        sep.setFixedHeight(30)
        sep.setStyleSheet(f"border-left: 1px solid {BORDER};")
        lay.addWidget(sep)

        self.btn_run = QToolButton()
        self.btn_run.setIcon(make_ui_icon("play", "#FFFFFF", 20))
        self.btn_run.setIconSize(QSize(19,19))
        self.btn_run.setText("تشغيل")
        self.btn_run.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.btn_run.setToolTip("تشغيل البرنامج [F5]")
        self.btn_run.setShortcut(QKeySequence("F5"))
        self.btn_run.setStyleSheet("""
            QToolButton {
                background:#7546C8;
                color:#FFFFFF;
                border:1px solid #9568E0;
                border-radius:6px;
                padding:6px 16px;
                font-size:13px;
                font-weight:bold;
            }
            QToolButton:hover { background:#8756DB; border-color:#A578F0; }
            QToolButton:pressed { background:#6338AC; }
            QToolButton:disabled { background:#34264D; color:#8C7AA6; border-color:#45366D; }
        """)
        self.btn_run.clicked.connect(self.run_code)
        lay.addWidget(self.btn_run)

        self.btn_stop = QToolButton()
        self.btn_stop.setIcon(make_ui_icon("stop", "#A8B2C0", 20))
        self.btn_stop.setIconSize(QSize(18,18))
        self.btn_stop.setText("إيقاف")
        self.btn_stop.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.btn_stop.setToolTip("إيقاف البرنامج [F6]")
        self.btn_stop.setShortcut(QKeySequence("F6"))
        self.btn_stop.setEnabled(False)
        self.btn_stop.setStyleSheet(f"""
            QToolButton {{
                background:#151D27;
                color:{TEXT_DIM};
                border:1px solid {BORDER};
                border-radius:6px;
                padding:6px 16px;
                font-size:13px;
                font-weight:bold;
            }}
            QToolButton:enabled {{
                color:#F38B95;
                border-color:#553039;
                background:#21161A;
            }}
            QToolButton:enabled:hover {{
                background:#311B22;
                border-color:#753A47;
            }}
            QToolButton:enabled:pressed {{
                background:#1A1114;
            }}
        """)
        self.btn_stop.clicked.connect(self.stop_code)
        lay.addWidget(self.btn_stop)

        # IMPORTANT: transparent spacer prevents the ugly grey rectangle.
        spacer = QWidget()
        spacer.setAttribute(Qt.WA_TranslucentBackground, True)
        spacer.setStyleSheet("background:transparent;")
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        lay.addWidget(spacer)

        self.main_toolbar = bar
        self.setMenuWidget(bar)

    # ── Central workspace ─────────────────────────────────────
    def _build_central(self):
        root = QWidget()
        root.setObjectName("Workspace")
        root.setStyleSheet(f"QWidget#Workspace {{ background: {BG}; }}")
        self.setCentralWidget(root)

        root_lay = QHBoxLayout(root)
        self.root_lay = root_lay
        root_lay.setContentsMargins(7, 7, 7, 7)
        root_lay.setSpacing(7)

        # ── Activity bar: Programming + Scene only ───────────────
        activity = QFrame()
        self.activity_bar = activity
        activity.setObjectName("ActivityBar")
        activity.setFixedWidth(64)
        activity.setStyleSheet(f"""
            QFrame#ActivityBar {{
                background:#101822;
                border:1px solid {BORDER};
                border-radius:9px;
            }}
            QToolButton {{
                background:transparent;
                color:#AEB8C6;
                border:none;
                border-left:2px solid transparent;
                border-radius:5px;
                margin:2px 0;
                min-height:74px;
                max-height:74px;
                padding:5px 2px;
                font-family:"Segoe UI","Tahoma",sans-serif;
                font-size:12px;
                font-weight:700;
            }}
            QToolButton:hover {{
                background:#19222E;
                color:#FFFFFF;
            }}
            QToolButton:checked {{
                background:#20283A;
                color:#FFFFFF;
                border-left-color:{ACCENT};
            }}
        """)
        act_lay = QVBoxLayout(activity)
        act_lay.setContentsMargins(3, 9, 3, 8)
        act_lay.setSpacing(2)

        def activity_button(kind, title):
            b = QToolButton()
            b.setIcon(make_ui_icon(kind, ACTIVITY_ICON_COLORS.get(kind, "#DCE5F2"), 30))
            b.setIconSize(QSize(28,28))
            b.setText(title)
            b.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
            b.setCheckable(True)
            b.setCursor(Qt.PointingHandCursor)
            act_lay.addWidget(b)
            return b

        self.activity_buttons = []
        self.btn_programming = activity_button("code", "البرمجة")
        self.btn_scene = activity_button("scene", "المشهد")
        self.activity_buttons.extend([self.btn_programming, self.btn_scene])

        self.btn_programming.setChecked(True)
        self.btn_programming.toggled.connect(self._toggle_view_mode)
        self.btn_scene.toggled.connect(self._toggle_view_mode)

        act_lay.addStretch()
        root_lay.addWidget(activity)

        # ── Three-column workspace ─────────────────────────────
        self.h_split = QSplitter(Qt.Horizontal)
        self.h_split.setHandleWidth(1)
        self.h_split.setStyleSheet(f"""
            QSplitter::handle {{ background: {BORDER}; }}
            QSplitter::handle:hover {{ background: #596579; }}
        """)

        # Left: viewport + output
        self.left_wrap = QWidget()
        self.left_wrap.setMinimumWidth(910)
        self.left_wrap.setMaximumWidth(910)
        self.left_lay = QVBoxLayout(self.left_wrap)
        self.left_lay.setContentsMargins(0, 0, 0, 0)
        self.left_lay.setSpacing(7)

        preview = QFrame()
        self.preview_frame = preview
        preview.setObjectName("previewCard")
        preview.setStyleSheet(f"""
            QFrame#previewCard {{
                background: {BG_PANEL};
                border: 1px solid {BORDER2};
                border-radius: 9px;
            }}
        """)
        pv_lay = QVBoxLayout(preview)
        pv_lay.setContentsMargins(0, 0, 0, 0)
        pv_lay.setSpacing(0)
        self.preview_header = self._panel_header("◷  شاشة العرض")
        pv_lay.addWidget(self.preview_header)

        self.pv_body = QWidget()
        self.pv_body.setObjectName("Viewport")
        self.pv_body.setStyleSheet(
            "background: #080E15; border-bottom-left-radius: 8px; border-bottom-right-radius: 8px;"
        )
        self.pv_body.installEventFilter(self)

        pv_body_lay = QVBoxLayout(self.pv_body)
        pv_body_lay.setContentsMargins(25, 15, 25, 20)
        pv_body_lay.setAlignment(Qt.AlignCenter)

        # Reference-like welcome screen.
        self.welcome_widget = QWidget()
        welcome_lay = QVBoxLayout(self.welcome_widget)
        welcome_lay.setContentsMargins(0, 0, 0, 0)
        welcome_lay.setSpacing(6)

        cactus = QLabel()
        cactus.setAlignment(Qt.AlignCenter)
        pm = QPixmap(os.path.join(os.path.dirname(os.path.abspath(__file__)), "icontr.png"))
        if not pm.isNull():
            pm = pm.scaled(88, 88, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            cactus.setPixmap(pm)
        else:
            cactus.setPixmap(make_cactus_logo(88))
        cactus.setMinimumHeight(90)
        welcome_lay.addWidget(cactus)

        welcome_title = QLabel(
            "<span style='color:#5DDF73'>Cactus</span> "
            "<span style='color:#5AA8FF'>Engine</span> "
            "<span style='color:#A56BFF'>IDE</span>"
        )
        welcome_title.setTextFormat(Qt.RichText)
        welcome_title.setAlignment(Qt.AlignCenter)
        welcome_title.setStyleSheet("font-size:23px; font-weight:800; padding-top:3px;")
        welcome_lay.addWidget(welcome_title)

        welcome_sub = QLabel("ابدأ بإنشاء ملف جديد أو فتح ملف موجود")
        welcome_sub.setAlignment(Qt.AlignCenter)
        welcome_sub.setStyleSheet(f"color:{TEXT_DIM}; font-size:12px; padding-bottom:15px;")
        welcome_lay.addWidget(welcome_sub)

        welcome_buttons = QHBoxLayout()
        welcome_buttons.setSpacing(10)

        def welcome_btn(icon_name, title, color, slot):
            b = QToolButton()
            b.setIcon(make_ui_icon(icon_name, color, 28))
            b.setIconSize(QSize(24, 24))
            b.setText(title)
            b.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
            b.setCursor(Qt.PointingHandCursor)
            b.setMinimumSize(112, 74)
            b.setStyleSheet(f"""
                QToolButton {{
                    background: #141C27;
                    color: {TEXT_MED};
                    border: 1px solid {BORDER};
                    border-radius: 9px;
                    font-size: 11px;
                    font-weight: 600;
                    padding-top: 8px;
                }}
                QToolButton:hover {{
                    background: #1A2330;
                    border-color: {color};
                    color: #FFFFFF;
                }}
            """)
            b.clicked.connect(slot)
            welcome_buttons.addWidget(b)
            return b

        welcome_btn("new", "ملف جديد", "#A855F7", self.new_file)
        welcome_btn("open", "فتح ملف", "#F0B429", self.open_file)
        welcome_btn("folder", "استيراد مشروع", "#8B5CF6", self.new_project_toolbar)

        welcome_lay.addLayout(welcome_buttons)
        pv_body_lay.addWidget(self.welcome_widget, 0, Qt.AlignCenter)

        # Keep the old preview widgets for the runtime logic.
        self.preview_icon = QLabel("")
        self.preview_icon.setAlignment(Qt.AlignCenter)
        self.preview_hint = QLabel("")
        self.preview_hint.setAlignment(Qt.AlignCenter)
        self.preview_icon.hide()
        self.preview_hint.hide()
        pv_body_lay.addWidget(self.preview_icon)
        pv_body_lay.addWidget(self.preview_hint)
        pv_lay.addWidget(self.pv_body)
        self.left_lay.addWidget(preview, 3)

        self.console_wrap = QFrame()
        self.console_wrap.setObjectName("consoleCard")
        self.console_wrap.setStyleSheet(f"""
            QFrame#consoleCard {{
                background: {BG_CONSOLE};
                border: 1px solid {BORDER2};
                border-radius: 9px;
            }}
        """)
        cv_lay = QVBoxLayout(self.console_wrap)
        cv_lay.setContentsMargins(0, 0, 0, 0)
        cv_lay.setSpacing(0)
        cv_lay.addWidget(self._panel_header("⚙  المخرجات", clear_btn=True))

        self.console = Console()
        self.console.setStyleSheet(f"""
            QPlainTextEdit {{
                background: #090E15;
                color: {TEXT};
                border: none;
                padding: 10px 13px;
                selection-background-color: #283450;
            }}
        """)
        cv_lay.addWidget(self.console)
        self.left_lay.addWidget(self.console_wrap, 1)

        # Center: code editor
        self.editor_wrap = QFrame()
        self.editor_wrap.setObjectName("editorCard")
        self.editor_wrap.setMinimumWidth(600)
        self.editor_wrap.setMaximumWidth(600)
        self.editor_wrap.setStyleSheet(f"""
            QFrame#editorCard {{
                background: {BG_EDITOR};
                border: 1px solid {BORDER};
                border-radius: 9px;
            }}
        """)
        e_lay = QVBoxLayout(self.editor_wrap)
        e_lay.setContentsMargins(0, 0, 0, 0)
        e_lay.setSpacing(0)

        e_header = QWidget()
        e_header.setFixedHeight(48)
        e_header.setStyleSheet(f"""
            background: #111822;
            border-bottom: 1px solid {BORDER};
        """)
        eh_lay = QHBoxLayout(e_header)
        eh_lay.setContentsMargins(10, 0, 7, 0)

        self.tab_label = QLabel("  hello.kh     ×")
        self.tab_label.setStyleSheet(f"""
            color: {TEXT};
            background: #0D131B;
            border: none;
            border-bottom: 2px solid {ACCENT};
            padding: 0 17px;
            font-family: "Segoe UI", "Cairo", sans-serif;
            font-size: 13px;
            font-weight: 600;
        """)
        self.tab_label.setMinimumWidth(130)
        self.tab_label.setFixedHeight(47)
        eh_lay.addWidget(self.tab_label)

        new_tab = QToolButton()
        new_tab.setText("+")
        new_tab.setToolTip("ملف جديد")
        new_tab.clicked.connect(self.new_file)
        new_tab.setStyleSheet(f"""
            QToolButton {{
                color:{TEXT_DIM};
                background:transparent;
                border:1px solid transparent;
                border-radius:5px;
                font-size:20px;
                padding:2px 9px;
            }}
            QToolButton:hover {{ color:#FFFFFF; background:#1A2230; }}
        """)
        eh_lay.addWidget(new_tab)
        eh_lay.addStretch()

        for symbol, tip in [("</>", "أدوات المحرر"), ("☼", "مظهر المحرر"), ("⋮", "المزيد")]:
            b = QToolButton()
            b.setText(symbol)
            b.setToolTip(tip)
            b.setStyleSheet(f"""
                QToolButton {{
                    color:{TEXT_DIM};
                    background:transparent;
                    border:none;
                    font-size:16px;
                    padding:6px 8px;
                }}
                QToolButton:hover {{ color:#FFFFFF; background:#1A2230; }}
            """)
            eh_lay.addWidget(b)

        e_lay.addWidget(e_header)

        self.editor = CodeEditor()
        self.editor.setStyleSheet(f"""
            QPlainTextEdit {{
                background: {BG_EDITOR};
                color: {TEXT};
                border: none;
                padding: 10px 8px;
                selection-background-color: #273657;
                selection-color: #FFFFFF;
            }}
        """)
        self.editor.setPlaceholderText("# اكتب كود .kh هنا…")
        self.editor.ide = self
        e_lay.addWidget(self.editor)
        
        # Center: scene viewer
        self.scene_ui = SceneUI(self)

        # Right: project explorer
        self.sidebar_wrap = QFrame()
        self.sidebar_wrap.setObjectName("sidebarCard")
        self.sidebar_wrap.setStyleSheet(f"""
            QFrame#sidebarCard {{
                background: #101721;
                border: 1px solid {BORDER};
                border-radius: 9px;
            }}
        """)
        sb_lay = QVBoxLayout(self.sidebar_wrap)
        sb_lay.setContentsMargins(0, 0, 0, 0)
        sb_lay.setSpacing(0)

        sb_hdr = QWidget()
        sb_hdr.setFixedHeight(48)
        sb_hdr.setStyleSheet(f"background:#111822; border-bottom:1px solid {BORDER};")
        sb_hdr_lay = QHBoxLayout(sb_hdr)
        sb_hdr_lay.setContentsMargins(13, 0, 8, 0)

        sb_lbl = QLabel("ملفات المشروع")
        sb_lbl.setStyleSheet(f"color:{TEXT}; font-size:12px; font-weight:700;")
        sb_hdr_lay.addWidget(sb_lbl)
        sb_hdr_lay.addStretch()

        for symbol, tip in [("↻", "تحديث"), ("+", "ملف جديد")]:
            b = QToolButton()
            b.setText(symbol)
            b.setToolTip(tip)
            b.setStyleSheet(f"""
                QToolButton {{
                    color:{TEXT_DIM};
                    background:transparent;
                    border:none;
                    font-size:17px;
                    padding:4px 7px;
                }}
                QToolButton:hover {{ color:#FFFFFF; background:#1A2230; }}
            """)
            if symbol == "+":
                b.clicked.connect(self.new_file)
            sb_hdr_lay.addWidget(b)
        sb_lay.addWidget(sb_hdr)

        # Search field like the reference.
        search_row = QWidget()
        sr_lay = QHBoxLayout(search_row)
        sr_lay.setContentsMargins(10, 8, 10, 6)
        self.project_search = QLineEdit()
        self.project_search.setPlaceholderText("بحث في الملفات...")
        self.project_search.setStyleSheet(f"""
            QLineEdit {{
                background:#0B1119;
                color:{TEXT};
                border:1px solid {BORDER};
                border-radius:6px;
                padding:7px 10px;
                font-size:12px;
            }}
            QLineEdit:focus {{ border-color:#596579; }}
        """)
        sr_lay.addWidget(self.project_search)
        sb_lay.addWidget(search_row)

        self.sidebar_list = QTreeWidget()
        self.sidebar_list.setHeaderHidden(True)
        self.sidebar_list.setIndentation(15)
        self.sidebar_list.setRootIsDecorated(True)
        self.sidebar_list.setAnimated(True)
        self.sidebar_list.setStyleSheet(f"""
            QTreeWidget {{
                background:#101721;
                border:none;
                color:#D1D7E0;
                padding:5px 7px 8px 7px;
                outline:none;
                font-family:"Segoe UI","Cairo",sans-serif;
                font-size:11px;
            }}
            QTreeWidget::item {{
                height:29px;
                padding:2px 6px;
                margin:1px 0;
                border-radius:5px;
            }}
            QTreeWidget::item:hover {{
                background:#1A2230;
                color:#FFFFFF;
            }}
            QTreeWidget::item:selected {{
                background:#252E3D;
                color:#FFFFFF;
                border:1px solid #344052;
            }}
            QTreeWidget::branch {{ background:transparent; }}
        """)
        self.sidebar_list.itemClicked.connect(self._on_sidebar_item_clicked)
        sb_lay.addWidget(self.sidebar_list)

        # Global shortcuts for Fullscreen exit
        self.esc_shortcut = QShortcut(QKeySequence(Qt.Key_Escape), self)
        self.esc_shortcut.setContext(Qt.ApplicationShortcut)
        self.esc_shortcut.activated.connect(self._handle_global_esc)
        
        self.f_shortcut = QShortcut(QKeySequence(Qt.Key_F), self)
        self.f_shortcut.setContext(Qt.ApplicationShortcut)
        self.f_shortcut.activated.connect(self._handle_global_f)

        self.h_split.addWidget(self.left_wrap)
        self.h_split.addWidget(self.editor_wrap)
        self.h_split.addWidget(self.scene_ui)
        self.h_split.addWidget(self.sidebar_wrap)
        # Initial sizes
        self.h_split.setSizes([800, 600, 0, 200, 0])
        # Prevent the preview screen from being collapsed/minimized
        self.h_split.setCollapsible(0, False)
        root_lay.addWidget(self.h_split, 1)

        # Search filters visible project items.
        self.project_search.textChanged.connect(self._filter_project_tree)

    def _filter_project_tree(self, query):
        query = query.strip().lower()
        root = self.sidebar_list.invisibleRootItem()
        def walk(item):
            text_ = item.text(0).lower()
            child_visible = False
            for i in range(item.childCount()):
                if walk(item.child(i)):
                    child_visible = True
            visible = (not query) or (query in text_) or child_visible
            item.setHidden(not visible)
            if query and child_visible:
                item.setExpanded(True)
            return visible
        for i in range(root.childCount()):
            walk(root.child(i))

    def _send_ai_prompt(self):
        prompt = self.ai_input.text().strip()
        if not prompt:
            return
        
        self.console.info(f"\n[AI Prompt]: {prompt}\n")
        self.console.out("جاري التفكير والاتصال بـ Claude... (يرجى الانتظار)\n")
        self.ai_input.clear()
        
        self.ai_worker = AIWorker(prompt, self.editor.toPlainText())
        self.ai_worker.finished.connect(self._on_ai_finished)
        self.ai_worker.start()

    def _on_ai_finished(self, result):
        self.console.out("\n--- إجابة Claude ---\n")
        self.console.out(result + "\n\n")
        
        if "```kh" in result:
            code_parts = result.split("```kh")
            for i in range(1, len(code_parts)):
                code = code_parts[i].split("```")[0].strip()
                if code:
                    self.editor.setPlainText(code)

    def _panel_header(self, title, clear_btn=False, full_btn=False):
        hdr = QWidget()
        hdr.setFixedHeight(42)
        hdr.setStyleSheet(f"""
            background: transparent;
            border-bottom: 1px solid {BORDER};
        """)
        lay = QHBoxLayout(hdr)
        lay.setContentsMargins(13, 0, 10, 0)

        lbl = QLabel(title)
        lbl.setStyleSheet(f"color: {TEXT_MED}; font-size: 11px; font-weight: 600;")
        lay.addWidget(lbl)
        lay.addStretch()

        if clear_btn:
            btn = QToolButton()
            btn.setText("مسح")
            btn.setStyleSheet(f"""
                QToolButton {{
                    color: {TEXT_DIM};
                    background: transparent;
                    border: 1px solid {BORDER};
                    border-radius: 4px;
                    padding: 1px 8px;
                    font-size: 11px;
                }}
                QToolButton:hover {{
                    color: {TEXT};
                    border-color: {BORDER2};
                }}
            """)
            btn.clicked.connect(lambda: self.console.clear())
            lay.addWidget(btn)

        return hdr

    def _start_embed_watchdog(self):
        """Timer that enforces correct pygame window every 200ms while game runs."""
        if not hasattr(self, "_watchdog_timer"):
            self._watchdog_timer = QTimer()
            self._watchdog_timer.timeout.connect(self._do_pygame_resize)
        self._watchdog_timer.start(200)

    def _stop_embed_watchdog(self):
        if hasattr(self, "_watchdog_timer"):
            self._watchdog_timer.stop()

    def _update_cursor(self):
        c = self.editor.textCursor()
        self.cursor_label.setText(f"سطر {c.blockNumber()+1}، عمود {c.columnNumber()+1}  ")

    def eventFilter(self, obj, event):
        if obj == getattr(self, "pv_body", None) and event.type() == event.Resize:
            if getattr(self, "pygame_hwnd", None):
                if not hasattr(self, "_resize_timer"):
                    self._resize_timer = QTimer()
                    self._resize_timer.setSingleShot(True)
                    self._resize_timer.timeout.connect(self._do_pygame_resize)
                self._resize_timer.start(150)
        return super().eventFilter(obj, event)

    def _do_pygame_resize(self):
        if getattr(self, "pygame_hwnd", None) and getattr(self, "pv_body", None):
            if self.isMinimized():
                return
                
            import ctypes
            dpr = self.pv_body.devicePixelRatioF()
            w = int(self.pv_body.width() * dpr)
            h = int(self.pv_body.height() * dpr)
            
            if w <= 0 or h <= 0:
                return
            
            # Hide specific Qt children that might overlap pygame
            if hasattr(self, 'welcome_widget') and self.welcome_widget.isVisible():
                self.welcome_widget.hide()
            if hasattr(self, 'preview_icon') and self.preview_icon.isVisible():
                self.preview_icon.hide()
            if hasattr(self, 'preview_hint') and self.preview_hint.isVisible():
                self.preview_hint.hide()
            # Resize and bring to top (HWND_TOP = 0)
            ctypes.windll.user32.SetWindowPos(self.pygame_hwnd, 0, 0, 0, w, h, 0x0044)
            # Bring pygame window to top of Z-order
            ctypes.windll.user32.BringWindowToTop(self.pygame_hwnd)
            # Notify pygame of new size
            lParam = (h << 16) | (w & 0xFFFF)
            ctypes.windll.user32.SendMessageW(self.pygame_hwnd, 0x0005, 0, lParam)

    def _handle_global_esc(self):
        if self.isFullScreen():
            self._toggle_fullscreen()
        elif self.process:
            self.stop_code()
            
    def _handle_global_f(self):
        if self.isFullScreen():
            self._toggle_fullscreen()

    def _poll_keys(self):
        import ctypes
        # High bit is set if the key is currently down
        if ctypes.windll.user32.GetAsyncKeyState(0x1B) & 0x8000 or ctypes.windll.user32.GetAsyncKeyState(0x46) & 0x8000:
            if self.isFullScreen():
                # Prevent multiple triggers
                self._key_poll_timer.stop()
                self._toggle_fullscreen()

    def _toggle_fullscreen(self):
        if self.isFullScreen():
            self.showNormal()
            self.editor_wrap.show()
            self.console_wrap.show()
            self.main_toolbar.show()
            self.statusBar().show()
            if hasattr(self, 'sidebar_wrap'): self.sidebar_wrap.show()
            if hasattr(self, 'activity_bar'): self.activity_bar.show()
            if hasattr(self, 'preview_header'): self.preview_header.show()
            if hasattr(self, 'root_lay'): self.root_lay.setContentsMargins(7, 7, 7, 7)
            if hasattr(self, 'left_wrap'):
                self.left_wrap.setMinimumWidth(910)
                self.left_wrap.setMaximumWidth(910)
            if hasattr(self, 'preview_frame'):
                self.preview_frame.setStyleSheet(f"QFrame#previewCard {{ background: {BG_PANEL}; border: 1px solid {BORDER2}; border-radius: 9px; }}")
                self.preview_frame.setFixedSize(910, 650)
            if hasattr(self, 'pv_body'):
                self.pv_body.setStyleSheet("background: #080E15; border-bottom-left-radius: 8px; border-bottom-right-radius: 8px;")
                self.pv_body.setFixedSize(910, 650)
            if hasattr(self, 'left_lay'):
                from PyQt5.QtCore import Qt
                self.left_lay.setAlignment(self.preview_frame, Qt.Alignment(0))
                
            # Hide the fullscreen hint if it exists
            if hasattr(self, 'fs_hint'):
                self.fs_hint.hide()
            
            # If game is running, re-apply the embed fixes after layout settles
            if getattr(self, "pygame_hwnd", None):
                # Re-hide all pv_body Qt children that may have reappeared
                from PyQt5.QtWidgets import QWidget as _QW
                for child in self.pv_body.findChildren(_QW):
                    child.hide()
                # Resize pygame window after layout settles (150ms delay)
                QTimer.singleShot(200, self._do_pygame_resize)
                
            if hasattr(self, '_key_poll_timer'):
                self._key_poll_timer.stop()
        else:
            self.showFullScreen()
            self.editor_wrap.hide()
            self.console_wrap.hide()
            self.main_toolbar.hide()
            self.statusBar().hide()
            if hasattr(self, 'sidebar_wrap'): self.sidebar_wrap.hide()
            if hasattr(self, 'activity_bar'): self.activity_bar.hide()
            if hasattr(self, 'preview_header'): self.preview_header.hide()
            if hasattr(self, 'root_lay'): self.root_lay.setContentsMargins(0, 0, 0, 0)
            if hasattr(self, 'left_wrap'):
                self.left_wrap.setMinimumWidth(0)
                self.left_wrap.setMaximumWidth(16777215)
            
            # Allow the preview frame to expand to fill the entire monitor in fullscreen
            if hasattr(self, 'preview_frame'):
                # Add a border to the preview frame to make it look nice in fullscreen
                self.preview_frame.setStyleSheet(f"QFrame#previewCard {{ background: #000; border: 2px solid {ACCENT}; border-radius: 8px; }}")
                
                self.preview_frame.setMinimumSize(0, 0)
                self.preview_frame.setMaximumSize(16777215, 16777215)
                if hasattr(self, 'pv_body'):
                    self.pv_body.setStyleSheet("background: #000; border: none; border-radius: 8px;")
                    self.pv_body.setMinimumSize(0, 0)
                    self.pv_body.setMaximumSize(16777215, 16777215)
                if hasattr(self, 'left_lay'):
                    from PyQt5.QtCore import Qt
                    self.left_lay.setAlignment(self.preview_frame, Qt.Alignment(0))
                    
                # Create and show the exit hint
                if not hasattr(self, 'fs_hint'):
                    self.fs_hint = QLabel("اضغط ESC أو F للخروج من وضع ملء الشاشة")
                    self.fs_hint.setStyleSheet(f"color: {TEXT_MED}; font-size: 14px; background: rgba(0,0,0,150); padding: 8px; border-radius: 4px;")
                    self.fs_hint.setAlignment(Qt.AlignCenter)
                    self.left_lay.insertWidget(0, self.fs_hint, 0, Qt.AlignCenter)
                self.fs_hint.show()
                
                # Start keyboard polling for ESC (0x1B) and F (0x46)
                if not hasattr(self, '_key_poll_timer'):
                    self._key_poll_timer = QTimer(self)
                    self._key_poll_timer.timeout.connect(self._poll_keys)
                self._key_poll_timer.start(50)
            else:
                    if hasattr(self, 'pv_body'):
                        self.pv_body.setStyleSheet("background: #000; border: none; border-radius: 0px;")

    # ── Status bar ────────────────────────────────────────────
    def _build_statusbar(self):
        sb = self.statusBar()
        sb.setStyleSheet(f"""
            QStatusBar {{
                background:#111820;
                color:{TEXT_DIM};
                border:1px solid {BORDER};
                font-size:11px;
                padding:0 8px;
            }}
            QStatusBar::item {{ border:none; }}
        """)

        self.status_text = QLabel("●  جاهز")
        self.status_text.setStyleSheet(f"color:{GREEN}; padding-left:3px;")
        sb.addWidget(self.status_text)

        sb.addPermanentWidget(QLabel("UTF-8   •   KH   •   "))
        self.cursor_label = QLabel("مسافات: 4   •   سطر 1، عمود 1")
        self.cursor_label.setStyleSheet(f"color:{TEXT_MED}; padding-right:8px;")
        sb.addPermanentWidget(self.cursor_label)
        self.editor.cursorPositionChanged.connect(self._update_cursor)

    def eventFilter(self, obj, event):
        if obj == getattr(self, "pv_body", None) and event.type() == event.Resize:
            if getattr(self, "pygame_hwnd", None):
                if not hasattr(self, "_resize_timer"):
                    self._resize_timer = QTimer()
                    self._resize_timer.setSingleShot(True)
                    self._resize_timer.timeout.connect(self._do_pygame_resize)
                self._resize_timer.start(150)
        return super().eventFilter(obj, event)

    def _do_pygame_resize(self):
        if getattr(self, "pygame_hwnd", None) and getattr(self, "pv_body", None):
            if self.isMinimized():
                return
                
            import ctypes
            dpr = self.pv_body.devicePixelRatioF()
            w = int(self.pv_body.width() * dpr)
            h = int(self.pv_body.height() * dpr)
            
            if w <= 0 or h <= 0:
                return
                
            ctypes.windll.user32.SetWindowPos(self.pygame_hwnd, 0, 0, 0, w, h, 0x0044)
            lparam = (h << 16) | (w & 0xFFFF)
            ctypes.windll.user32.SendMessageW(self.pygame_hwnd, 0x0005, 0, lparam)

    def _set_status(self, msg, timeout_ms=0):
        self.status_text.setText(msg)
        if timeout_ms:
            QTimer.singleShot(timeout_ms, lambda: self.status_text.setText("جاهز"))

    # ── Dirty flag ────────────────────────────────────────────
    def _mark_dirty(self):
        if not self._is_dirty:
            self._is_dirty = True
            name = os.path.basename(self.current_file) if self.current_file else "ملف جديد"
            self.tab_label.setText(f"  ●  {name}  *")

    def _clear_dirty(self):
        self._is_dirty = False
        name = os.path.basename(self.current_file) if self.current_file else "ملف جديد"
        self.tab_label.setText(f"  ●  {name}")

    # ── Project & File ops ────────────────────────────────────
    def load_project(self, directory):
        if hasattr(self, '_mainscene_handle') and self._mainscene_handle:
            try:
                self._mainscene_handle.close()
            except Exception:
                pass

        scene_file = os.path.join(directory, "mainscene.khscene")
        import stat
        if not os.path.exists(scene_file):
            try:
                with open(scene_file, 'w', encoding='utf-8') as f:
                    # ضوء موجه افتراضي يُضاف تلقائياً لكل مشروع جديد
                    f.write("ابغا ضوء1 = صنع_ضوء()\n")
                    f.write('ضوء1.النوع = "ضوء_موجه"\n')
                    f.write("ضوء1.الموقع = متجه3(0.0, 10.0, 0.0)\n")
                    f.write("ضوء1.الاتجاه = متجه3(-0.5, -1.0, -0.3)\n")
                    f.write("ضوء1.الشدة = 1.0\n")
                    f.write("ضوء1.اللون = لون(1.0, 1.0, 1.0)\n")
            except Exception as e:
                print(f"Error creating mainscene.khscene: {e}")
        try:
            os.chmod(scene_file, stat.S_IREAD)
        except Exception as e:
            print(f"Error making mainscene.khscene read-only: {e}")
            
        try:
            self._mainscene_handle = open(scene_file, 'r')
        except Exception as e:
            print(f"Error locking mainscene.khscene: {e}")

        self.project_dir = directory
        self.sidebar_list.clear()

        root_name = os.path.basename(os.path.normpath(directory)) or "المشروع"
        root = QTreeWidgetItem(self.sidebar_list, [root_name])
        root.setIcon(0, make_ui_icon("folder", "#F2C14E", 19))
        root.setData(0, Qt.UserRole, directory)
        root.setExpanded(True)

        # Keep the tree structure while walking the project.
        tree_items = {os.path.normpath(directory): root}
        first_kh = None

        for current_root, dirs, files in os.walk(directory):
            dirs[:] = sorted(
                d for d in dirs
                if d not in {".git", "__pycache__", ".venv"}
            )
            files = sorted(files)

            current_root = os.path.normpath(current_root)
            parent = tree_items.get(current_root, root)

            # Add folders first.
            for folder in dirs:
                folder_path = os.path.normpath(os.path.join(current_root, folder))
                folder_item = QTreeWidgetItem(parent, [folder])
                folder_item.setIcon(0, make_ui_icon("folder", "#F2C14E", 18))
                folder_item.setData(0, Qt.UserRole, folder_path)
                folder_item.setExpanded(True)
                tree_items[folder_path] = folder_item

            # Then add KH files.
            for name in files:
                if not name.endswith(".kh"):
                    continue
                path = os.path.normpath(os.path.join(current_root, name))
                item = QTreeWidgetItem(parent, [name])
                item.setIcon(0, make_ui_icon("file", "#AEB8C6", 18))
                item.setData(0, Qt.UserRole, path)
                if first_kh is None:
                    first_kh = path

        if first_kh:
            self.open_file_path(first_kh)
        else:
            self.new_file()

        # Update visual scene
        if hasattr(self, 'scene_ui'):
            try:
                import code_reader
                self.scene_ui._is_loading_scene = True
                code_reader.read_scene_from_kh(self.scene_ui.scene_viewer, directory)
                self.scene_ui.scene_viewer.scene_tree_updated.emit()
            except Exception as e:
                print(f"Error reading scene: {e}")
            finally:
                self.scene_ui._is_loading_scene = False

    def _on_sidebar_item_clicked(self, item, column=0):
        path = item.data(0, Qt.UserRole)
        if path and os.path.exists(path):
            if self._is_dirty and self.current_file:
                self.save_file()
            self.open_file_path(path)

    def new_project_toolbar(self):
        d = QFileDialog.getExistingDirectory(self, "اختر مكان حفظ المشروع الجديد (مجلد آخر)")
        if d:
            self.load_project(d)

    def new_file(self):
        if not getattr(self, 'project_dir', None):
            proj = QFileDialog.getExistingDirectory(self, "اختر مجلد المشروع لإنشاء الملف")
            if proj:
                self.load_project(proj)
            else:
                self.editor.setPlainText("")
                self.current_file = None
                self._clear_dirty()
                self.setWindowTitle("Cactus Engine IDE")
                return

        name, ok = QInputDialog.getText(self, "ملف جديد", "اسم الملف (بدون .kh):")
        if ok and name:
            if not name.endswith('.kh'):
                name += '.kh'
            path = os.path.join(self.project_dir, name)
            with open(path, "w", encoding="utf-8") as f:
                f.write("")
            self.load_project(self.project_dir)
            self.open_file_path(path)

    def open_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "فتح ملف", self.project_dir or "", "KH Files (*.kh);;All Files (*)")
        if not path:
            return
        self.open_file_path(path)

    def open_file_path(self, path):
        with open(path, "r", encoding="utf-8") as f:
            self.editor.setPlainText(f.read())
        self.current_file = path
        self._clear_dirty()
        name = os.path.basename(path)
        self.setWindowTitle(f"Cactus Engine IDE — {name}")
        self._set_status(f"فُتح: {name}", 3000)

    def save_file(self):
        if not self.current_file:
            path, _ = QFileDialog.getSaveFileName(
                self, "حفظ ملف", "", "KH Files (*.kh);;All Files (*)")
            if not path:
                return
            self.current_file = path

        def format_kh_code(text):
            lines = text.split('\n')
            formatted = []
            for line in lines:
                line = line.replace('\t', '    ')
                stripped = line.lstrip()
                if not stripped:
                    formatted.append("")
                    continue
                leading_spaces = len(line) - len(stripped)
                new_indent = int(round(leading_spaces / 4.0)) * 4
                formatted.append((" " * new_indent) + stripped.rstrip())
            return '\n'.join(formatted)

        original_code = self.editor.toPlainText()
        formatted_code = format_kh_code(original_code)
        
        if original_code != formatted_code:
            cursor = self.editor.textCursor()
            pos = cursor.position()
            self.editor.setPlainText(formatted_code)
            cursor.setPosition(min(pos, len(formatted_code)))
            self.editor.setTextCursor(cursor)

        with open(self.current_file, "w", encoding="utf-8") as f:
            f.write(formatted_code)

        self._clear_dirty()
        name = os.path.basename(self.current_file)
        self.setWindowTitle(f"Cactus Engine IDE — {name}")
        self._set_status("✓ تم الحفظ", 3000)

    def save_file_as(self):
        path, _ = QFileDialog.getSaveFileName(
            self,
            "حفظ باسم",
            self.project_dir or "",
            "KH Files (*.kh);;All Files (*)"
        )
        if not path:
            return
        if not path.lower().endswith(".kh"):
            path += ".kh"
        self.current_file = path
        self.save_file()

    # ── Run / Stop ─────────────────────────────────────────────
    def run_code(self):
        # Save before running
        if self.current_file:
            self.save_file()
        else:
            import tempfile
            tmp = tempfile.NamedTemporaryFile(
                suffix=".kh", delete=False, mode="w", encoding="utf-8")
            tmp.write(self.editor.toPlainText())
            tmp.close()
            self.current_file = tmp.name

        self.console.clear()
        
        # Save splitter sizes before hiding the welcome widget so it doesn't collapse permanently
        if hasattr(self, 'h_split'):
            self._saved_h_split = self.h_split.sizes()
            
        if hasattr(self, "welcome_widget"):
            self.welcome_widget.hide()
        self.console.info(f"▶  تشغيل:  {os.path.basename(self.current_file)}\n")
        self.console.info("─" * 52 + "\n")

        kh_dir    = os.path.dirname(os.path.abspath(__file__))
        kh_script = os.path.join(kh_dir, "kh.py")

        self.pygame_hwnd = None
        self.process = QProcess(self)
        
        env = QProcessEnvironment.systemEnvironment()
        env.insert("KH_EMBEDDED", "1")
        env.insert("KH_WIDTH", str(self.pv_body.width()))
        env.insert("KH_HEIGHT", str(self.pv_body.height()))
        env.insert("PYTHONUNBUFFERED", "1")
        self.process.setProcessEnvironment(env)
        
        self.process.setWorkingDirectory(kh_dir)
        self.process.readyReadStandardOutput.connect(self._on_stdout)
        self.process.readyReadStandardError.connect(self._on_stderr)
        self.process.finished.connect(self._on_finished)
        self.process.start(sys.executable, [kh_script, self.current_file])

        self.btn_run.setEnabled(False)
        self.btn_run.setIcon(make_ui_icon("play", "#8C7AA6", 20))
        self.btn_stop.setEnabled(True)
        self.btn_stop.setIcon(make_ui_icon("stop", "#F38B95", 20))
        self._set_status("⬡  جاري التشغيل…")
        
        # Switch to programming mode automatically and lock scene view
        self.btn_programming.setChecked(True)
        self.btn_scene.setEnabled(False)
        
        # Reset preview icon state
        self.preview_icon.setFixedSize(QSize(16777215, 16777215))
        self.preview_icon.setPixmap(QPixmap())
        self.preview_icon.setText("▶")
        self.preview_icon.setStyleSheet(f"color: {GREEN}; font-size: 80px;")
        self.preview_icon.show()
        
        self.preview_hint.setText("البرنامج قيد التشغيل")
        self.preview_hint.show()

    def closeEvent(self, event):
        self.stop_code()
        event.accept()

    def _on_scene_element_clicked(self, item, column):
        """عند الضغط على عنصر من قائمة العناصر، نرسل أمر SELECT للمشهد."""
        name = item.text(0)
        self._send_scene_command(f"SELECT:{name}")

    def _send_scene_command(self, cmd):
        """إرسال أمر نصي إلى view_scene.py عبر stdin."""
        proc = getattr(self, 'scene_process', None)
        if proc and proc.state() == QProcess.Running:
            try:
                data = (cmd + '\n').encode('utf-8')
                proc.write(data)
            except Exception as e:
                print("Error sending command to scene:", e)
        
    def _toggle_view_mode(self, checked=False):
        sender = self.sender()
        if not checked: return

        if hasattr(self, 'btn_programming') and sender == self.btn_programming:
            if hasattr(self, 'btn_scene'):
                self.btn_scene.blockSignals(True)
                self.btn_scene.setChecked(False)
                self.btn_scene.blockSignals(False)
            if hasattr(self, 'scene_ui'): self.scene_ui.hide()
            if hasattr(self, 'left_wrap'): self.left_wrap.show()
            if hasattr(self, 'editor_wrap'): self.editor_wrap.show()
            if hasattr(self, 'sidebar_wrap'): self.sidebar_wrap.show()
            self.h_split.setSizes([800, 600, 0, 200, 0])
            # لا نوقف المشهد - يستمر في الخلفية
        elif hasattr(self, 'btn_scene') and sender == self.btn_scene:
            if hasattr(self, 'btn_programming'):
                self.btn_programming.blockSignals(True)
                self.btn_programming.setChecked(False)
                self.btn_programming.blockSignals(False)
            if hasattr(self, 'left_wrap'): self.left_wrap.hide()
            if hasattr(self, 'editor_wrap'): self.editor_wrap.hide()
            if hasattr(self, 'sidebar_wrap'): self.sidebar_wrap.hide()
            if hasattr(self, 'scene_ui'): self.scene_ui.show()
            self.h_split.setSizes([0, 0, 1000, 0])
            # self.scene_ui._ensure_scene_viewer()



    def stop_code(self):
        if self.process and self.process.state() != QProcess.NotRunning:
            self._is_stopping = True
            self.process.kill()

    def _on_stdout(self):
        raw = self.process.readAllStandardOutput().data().decode("utf-8", errors="replace")
        
        # External window: user explicitly called نافذة() - detach and show as floating window
        if "__KH_EXTERNAL__:" in raw:
            for line in raw.splitlines():
                if line.startswith("__KH_EXTERNAL__:"):
                    try:
                        parts = line.split(":")
                        hwnd = int(parts[1])
                        import ctypes
                        # فك الربط مع الـ IDE (إن كان مرتبطاً)
                        ctypes.windll.user32.SetParent(hwnd, 0)
                        # إظهار النافذة بشكل مستقل
                        SW_SHOWNORMAL = 1
                        ctypes.windll.user32.ShowWindow(hwnd, SW_SHOWNORMAL)
                        ctypes.windll.user32.BringWindowToTop(hwnd)
                        # إخبار المستخدم
                        self.console.info("▶  اللعبة تعمل في نافذة خارجية مستقلة\n")
                        # إظهار شاشة الترحيب في الـ IDE
                        if hasattr(self, 'welcome_widget'):
                            self.welcome_widget.show()
                        if hasattr(self, 'preview_icon'):
                            self.preview_icon.hide()
                        if hasattr(self, 'preview_hint'):
                            self.preview_hint.hide()
                    except Exception as ex:
                        self.console.info(f"▶  اللعبة تعمل في نافذة خارجية\n")
                        self.console.err(f"External window error: {ex}\n")
                else:
                    if line.strip():
                        self.console.out(line + "\n")
            return
        
        # Check for our HWND injection (default/embedded window)
        if "__KH_HWND__:" in raw:
            for line in raw.splitlines():
                if line.startswith("__KH_HWND__:"):
                    try:
                        parts = line.split(":")
                        hwnd = int(parts[1])
                        self.pygame_hwnd = hwnd
                        
                        import ctypes
                        qt_hwnd = int(self.pv_body.winId())
                        # Embed the pygame window!
                        ctypes.windll.user32.SetParent(hwnd, qt_hwnd)

                        # Parse original game dimensions
                        self._kh_original_w = 800
                        self._kh_original_h = 600
                        if len(parts) >= 4:
                            self._kh_original_w = int(parts[2])
                            self._kh_original_h = int(parts[3])

                        # Hide specific widgets so nothing renders over pygame
                        if hasattr(self, 'welcome_widget'): self.welcome_widget.hide()
                        if hasattr(self, 'preview_icon'): self.preview_icon.hide()
                        if hasattr(self, 'preview_hint'): self.preview_hint.hide()
                        if hasattr(self, 'preview_header'): self.preview_header.hide()

                        # Remove pv_body internal margins so game fills edge-to-edge
                        pv_body_lay = self.pv_body.layout()
                        if pv_body_lay:
                            pv_body_lay.setContentsMargins(0, 0, 0, 0)

                        # Force container to exactly 910x650
                        self.pv_body.setFixedSize(910, 650)
                        if hasattr(self, 'preview_frame'):
                            self.preview_frame.setFixedSize(910, 650)

                        # Use exact pv_body size for the pygame window
                        w = self.pv_body.width()
                        h = self.pv_body.height()

                        # Position and resize the embedded pygame window
                        ctypes.windll.user32.SetWindowPos(hwnd, 0, 0, 0, w, h, 0x0044)

                        # Send WM_SIZE so pygame updates its viewport
                        WM_SIZE = 0x0005
                        lParam = (h << 16) | (w & 0xFFFF)
                        ctypes.windll.user32.PostMessageW(hwnd, WM_SIZE, 0, lParam)

                        # Start watchdog to keep pygame on top and correctly sized
                        self._start_embed_watchdog()
                    except Exception as e:
                        self.console.err(f"Embed error: {e}\n")
                else:
                    self.console.out(line + "\n")
        else:
            self.console.out(raw)

    def _on_stderr(self):
        raw = self.process.readAllStandardError().data().decode("utf-8", errors="replace")
        # Filter out noisy pygame / setuptools warnings
        skip = ("UserWarning", "pkg_resources", "setuptools", "pygame community",
                "Hello from", "pkgdata")
        lines = [l for l in raw.splitlines()
                 if not any(s in l for s in skip)]
        if lines:
            self.console.err("\n".join(lines) + "\n")

    def _on_finished(self, code, _):
        self.btn_run.setEnabled(True)
        self.btn_run.setIcon(make_ui_icon("play", "#FFFFFF", 20))
        self.btn_stop.setEnabled(False)
        self.btn_stop.setIcon(make_ui_icon("stop", "#A8B2C0", 20))
        self.btn_scene.setEnabled(True)

        self.pygame_hwnd = None
        self._stop_embed_watchdog()
        

        # Unfreeze sizes
        if hasattr(self, 'pv_body'):
            self.pv_body.setMinimumSize(0, 0)
            self.pv_body.setMaximumSize(16777215, 16777215)
            # Restore internal margins
            pv_body_lay = self.pv_body.layout()
            if pv_body_lay:
                pv_body_lay.setContentsMargins(25, 15, 25, 20)
        if hasattr(self, 'preview_frame'):
            self.preview_frame.setMinimumSize(0, 0)
            self.preview_frame.setMaximumSize(16777215, 16777215)
        if hasattr(self, 'preview_header'):
            self.preview_header.show()
        if hasattr(self, 'left_lay'):
            from PyQt5.QtCore import Qt
            self.left_lay.setAlignment(self.preview_frame, Qt.Alignment(0))

        # Show the welcome widget again (was hidden by watchdog)
        if hasattr(self, 'welcome_widget'):
            self.welcome_widget.show()
            
        # Restore splitter sizes after layout settles
        if hasattr(self, '_saved_h_split') and hasattr(self, 'h_split'):
            QTimer.singleShot(50, lambda: self.h_split.setSizes(self._saved_h_split))

        if self._is_stopping:
            self.console.info("\n⏹  تم إيقاف البرنامج\n")
            self._set_status("⏹  تم الإيقاف", 4000)
            if hasattr(self, "welcome_widget"):
                self.welcome_widget.show()
            self.preview_icon.hide()
            self.preview_hint.hide()
            
            if hasattr(self, 'btn_scene') and hasattr(self, 'btn_programming'):
                self.btn_scene.setChecked(True)
                QTimer.singleShot(100, lambda: self.btn_programming.setChecked(True))
        elif code == 0:
            self.console.success("\n✓  انتهى البرنامج\n")
            self._set_status("✓  انتهى", 4000)
            if hasattr(self, "welcome_widget"):
                self.welcome_widget.show()
            self.preview_icon.hide()
            self.preview_hint.hide()
        else:
            self.console.err(f"\n✗  انتهى بخطأ  (كود: {code})\n")
            self._set_status(f"✗  خطأ", 4000)
            if hasattr(self, "welcome_widget"):
                self.welcome_widget.hide()
            self.preview_icon.show()
            self.preview_hint.show()
            self.preview_icon.setFixedSize(QSize(16777215, 16777215))
            self.preview_icon.setText("⚠")
            self.preview_icon.setStyleSheet(f"color: {RED}; font-size: 72px;")
            self.preview_hint.setText("راجع المخرجات أدناه")
            
        self._is_stopping = False

    # ── Keyboard shortcuts ────────────────────────────────────
    def keyPressEvent(self, e):
        if e.key() in (Qt.Key_Escape, Qt.Key_F):
            if self.isFullScreen():
                self._toggle_fullscreen()
                return
            elif self.process:
                self.stop_code()
        super().keyPressEvent(e)


# ════════════════════════════════════════════════════════════════
#  🚀  Entry Point
# ════════════════════════════════════════════════════════════════
class WelcomeDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("مرحباً بك في Cactus Engine")
        self.setFixedSize(540, 360)
        self.setWindowFlags(Qt.Window)
        
        self.selected_dir = None
        
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {BG};
                border: 1px solid {BORDER2};
                border-radius: 12px;
            }}
            QLabel#title {{
                color: {TEXT};
                font-size: 26px;
                font-weight: bold;
                margin-top: 15px;
            }}
            QLabel#subtitle {{
                color: {TEXT_DIM};
                font-size: 14px;
                margin-bottom: 25px;
            }}
            QPushButton {{
                background-color: {BG_PANEL};
                color: {TEXT};
                border: 1px solid {BORDER};
                border-radius: 8px;
                padding: 12px;
                font-size: 15px;
                font-weight: bold;
                margin: 5px 40px;
            }}
            QPushButton:hover {{
                background-color: {ACCENT};
                color: white;
                border-color: {ACCENT};
            }}
        """)
        
        lay = QVBoxLayout(self)
        lay.setAlignment(Qt.AlignCenter)
        
        logo = QLabel()
        logo.setAlignment(Qt.AlignCenter)
        import os
        pm = QPixmap(os.path.join(os.path.dirname(os.path.abspath(__file__)), "icontr.png"))
        if not pm.isNull():
            pm = pm.scaled(72, 72, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo.setPixmap(pm)
        lay.addWidget(logo)
        
        title = QLabel("Cactus Engine")
        title.setObjectName("title")
        title.setAlignment(Qt.AlignCenter)
        
        subtitle = QLabel("بيئة التطوير المتكاملة للغة برمجة KH")
        subtitle.setObjectName("subtitle")
        subtitle.setAlignment(Qt.AlignCenter)
        
        btn_open = QPushButton("📂 فتح مشروع موجود")
        btn_open.setCursor(Qt.PointingHandCursor)
        btn_open.clicked.connect(self.open_project)
        
        btn_new = QPushButton("➕ مشروع جديد")
        btn_new.setCursor(Qt.PointingHandCursor)
        btn_new.clicked.connect(self.new_project)
        
        lay.addWidget(title)
        lay.addWidget(subtitle)
        lay.addWidget(btn_open)
        lay.addWidget(btn_new)

    def open_project(self):
        d = QFileDialog.getExistingDirectory(self, "اختر مجلد المشروع")
        if d:
            self.selected_dir = d
            self.accept()
            
    def new_project(self):
        d = QFileDialog.getExistingDirectory(self, "اختر مكان حفظ المشروع الجديد")
        if d:
            self.selected_dir = d
            self.accept()


def resource_path(relative_path):
    import sys, os
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

def main():
    # Crisp Windows/Qt text and icons on high-DPI displays.
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    import ctypes
    import sys

    # --- منع فتح أكثر من نسخة (Single Instance) ---
    mutex_name = "CactusEngineIDE_Mutex_Global_Instance_Lock"
    mutex = ctypes.windll.kernel32.CreateMutexW(None, False, mutex_name)
    last_error = ctypes.windll.kernel32.GetLastError()
    if last_error == 183:  # ERROR_ALREADY_EXISTS
        sys.exit(0)
        
    try:
        myappid = 'cactus.engine.ide.1'
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    except Exception:
        pass

    # High-DPI support
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps,    True)

    app = QApplication(sys.argv)
    app.setFont(QFont("Segoe UI", 10))

    app.setApplicationName("Cactus Engine IDE")
    
    icon_path = resource_path("icon.ico")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
        
    app.setStyle("Fusion")
    
    # تعيين الخط الافتراضي للبرنامج ككل (خط النظام الحديث)
    app_font = QFont("Segoe UI", 10)
    app.setFont(app_font)
    
    app.setStyleSheet(f"""
        QScrollBar:vertical {{
            border: none;
            background: {BG_PANEL};
            width: 12px;
            margin: 0px 0px 0px 0px;
        }}
        QScrollBar::handle:vertical {{
            background: {BORDER2};
            min-height: 30px;
            border-radius: 5px;
            margin: 2px;
        }}
        QScrollBar::handle:vertical:hover {{
            background: {TEXT_DIM};
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0px;
        }}
        QScrollBar:horizontal {{
            border: none;
            background: {BG_PANEL};
            height: 12px;
            margin: 0px 0px 0px 0px;
        }}
        QScrollBar::handle:horizontal {{
            background: {BORDER2};
            min-width: 30px;
            border-radius: 5px;
            margin: 2px;
        }}
        QScrollBar::handle:horizontal:hover {{
            background: {TEXT_DIM};
        }}
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
            width: 0px;
        }}
        QToolTip {{
            background: {BG_PANEL};
            color: {TEXT};
            border: 1px solid {BORDER2};
            padding: 4px;
            border-radius: 4px;
        }}
        QSplitter::handle {{
            background: {BORDER};
        }}
    """)

    ide = KHIde()

    def apply_dark_title_bar(window):
        try:
            import ctypes
            hwnd = int(window.winId())
            val = ctypes.c_int(1)
            ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 20, ctypes.byref(val), ctypes.sizeof(val))
            ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 19, ctypes.byref(val), ctypes.sizeof(val))
            bg_color = ctypes.c_uint32(0x00221810)
            ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 35, ctypes.byref(bg_color), ctypes.sizeof(bg_color))
            
            # إجبار Windows على تحديث شريط العنوان فوراً
            SWP_FRAMECHANGED = 0x0020
            SWP_NOMOVE = 0x0002
            SWP_NOSIZE = 0x0001
            SWP_NOZORDER = 0x0004
            ctypes.windll.user32.SetWindowPos(
                hwnd, 0, 0, 0, 0, 0,
                SWP_FRAMECHANGED | SWP_NOMOVE | SWP_NOSIZE | SWP_NOZORDER
            )
        except Exception:
            pass

    dlg = WelcomeDialog()
    apply_dark_title_bar(dlg)
    res = dlg.exec_()
    
    if res == QDialog.Accepted:
        if dlg.selected_dir:
            ide.load_project(dlg.selected_dir)
        else:
            default = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hello.kh")
            if os.path.exists(default):
                ide.open_file_path(default)
        ide.showMaximized()
        # تشغيل عارض المشهد تلقائياً في الخلفية فور فتح البرنامج
        # QTimer.singleShot(800, ide.scene_ui._start_scene_viewer)
    else:
        sys.exit(0)
    
    apply_dark_title_bar(ide)

    sys.exit(app.exec_())


if __name__ == "__main__":
    import sys
    # --- PyInstaller Subprocess Fix ---
    # When packaged as .exe, sys.executable points to the .exe itself, not python.exe
    # The IDE attempts to run: sys.executable path/to/kh.py script.kh
    # If we detect that the first argument is kh.py, run the interpreter logic instead of opening the IDE again.
    if len(sys.argv) >= 2 and sys.argv[1].endswith("kh.py"):
        sys.argv = sys.argv[1:]
        import kh
        sys.exit(0)
        
    main()
