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
    QInputDialog, QMessageBox, QDialog, QCompleter
)
from PyQt5.QtCore import (
    Qt, QSize, QRect, QProcess, QProcessEnvironment, QTimer, QRegularExpression, QThread, pyqtSignal, QStringListModel
)
from PyQt5.QtGui import (
    QFont, QFontMetricsF, QColor, QTextCharFormat, QPainter,
    QSyntaxHighlighter, QTextCursor, QTextFormat, QKeySequence,
    QPalette, QLinearGradient, QGradient, QTextOption, QIcon
)


# ════════════════════════════════════════════════════════════════
#  🎨  Palette
# ════════════════════════════════════════════════════════════════
BG          = "#1e1e1e"
BG_PANEL    = "#252526"
BG_EDITOR   = "#1e1e1e"
BG_CONSOLE  = "#1e1e1e"
TOOLBAR_BG  = "#333333"
BORDER      = "#3c3c3c"
BORDER2     = "#4d4d4d"

ACCENT      = "#007acc"
ACCENT2     = "#c586c0"
GREEN       = "#6a9955"
GREEN_DARK  = "#4d703d"
RED         = "#f48771"

TEXT        = "#cccccc"
TEXT_DIM    = "#858585"
TEXT_MED    = "#a6a6a6"

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
        add(r"[+\-*/=<>!]+|[()،,]", S_OPERATOR)

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
    "Object3D": ["الاسم", "الموقع", "الدوران", "المقياس", "اللون", "الخامة", "تصادم", "جاذبية", "صدام"],
    "FBXModel": ["الاسم", "الموقع", "الدوران", "المقياس", "اللون", "الخامة", "تصادم", "جاذبية", "صدام", "المكون"],
    "ضوء": ["النوع", "الموقع", "الاتجاه", "اللون", "الشدة", "زاوية_البقعة", "حدة_البقعة", "التضاؤل_الثابت", "التضاؤل_الخطي", "التضاؤل_التربيعي"],
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
    "صنع_مربع2D": "Object3D",
    "صنع_دائرة2D": "Object3D",
    "صنع_مثلث2D": "Object3D",
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

        font = QFont("Consolas", 14)
        font.setStyleHint(QFont.Monospace)
        self.setFont(font)
        self.setTabStopDistance(QFontMetricsF(self.font()).horizontalAdvance(" ") * 4)
        self.setLineWrapMode(QPlainTextEdit.NoWrap)
        
        # RTL text direction for Arabic programming
        opt = self.document().defaultTextOption()
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
        return 20 + self.fontMetrics().horizontalAdvance("9") * digits

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
        p.fillRect(event.rect(), QColor("#0a0a18"))

        block  = self.firstVisibleBlock()
        num    = block.blockNumber()
        top    = round(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom = top + round(self.blockBoundingRect(block).height())
        cur    = self.textCursor().blockNumber()

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                color = TEXT if num == cur else TEXT_DIM
                p.setPen(QColor(color))
                p.drawText(0, top, self._gutter.width() - 8,
                           self.fontMetrics().height(),
                           Qt.AlignRight, str(num + 1))
            block  = block.next()
            top    = bottom
            bottom = top + round(self.blockBoundingRect(block).height())
            num   += 1

    def _highlight_line(self):
        sel = QTextEdit.ExtraSelection()
        sel.format.setBackground(QColor("#14142a"))
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
        font.setPointSize(12)
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
        self.setMinimumSize(900, 600)

        self._apply_palette()
        self._build_toolbar()
        self._build_central()
        self._build_statusbar()

        # Connect editor changes for dirty flag
        # Delay so initial load doesn't mark dirty
        QTimer.singleShot(200, lambda:
            self.editor.document().contentsChanged.connect(self._mark_dirty))

    # ── Global palette / style ────────────────────────────────
    def _apply_palette(self):
        pal = QPalette()
        pal.setColor(QPalette.Window,      QColor(BG))
        pal.setColor(QPalette.Base,        QColor(BG_EDITOR))
        pal.setColor(QPalette.Text,        QColor(TEXT))
        pal.setColor(QPalette.WindowText,  QColor(TEXT))
        pal.setColor(QPalette.Button,      QColor(BG_PANEL))
        pal.setColor(QPalette.ButtonText,  QColor(TEXT))
        pal.setColor(QPalette.Highlight,   QColor(ACCENT))
        pal.setColor(QPalette.HighlightedText, QColor(TEXT))
        QApplication.setPalette(pal)

        self.setStyleSheet(f"""
            * {{
                font-family: "Segoe UI", "Tahoma", "Cairo", sans-serif;
            }}
            QMainWindow, QWidget {{
                background: {BG};
                color: {TEXT};
            }}
            QScrollBar:vertical {{
                background: {BG_PANEL};
                width: 8px;
                border-radius: 4px;
            }}
            QScrollBar::handle:vertical {{
                background: {BORDER2};
                border-radius: 4px;
                min-height: 20px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {TEXT_DIM};
            }}
            QScrollBar:horizontal {{
                background: {BG_PANEL};
                height: 8px;
                border-radius: 4px;
            }}
            QScrollBar::handle:horizontal {{
                background: {BORDER2};
                border-radius: 4px;
            }}
            QScrollBar::add-line, QScrollBar::sub-line {{
                width: 0; height: 0;
            }}
            QToolTip {{
                background: {BG_PANEL};
                color: {TEXT};
                border: 1px solid {BORDER2};
                border-radius: 4px;
                padding: 4px 8px;
            }}
        """)

    # ── Toolbar ───────────────────────────────────────────────
    def _build_toolbar(self):
        tb = QToolBar()
        tb.setMovable(False)
        tb.setFloatable(False)
        tb.setIconSize(QSize(18, 18))
        tb.setStyleSheet(f"""
            QToolBar {{
                background: #09090b;
                border-bottom: none;
                padding: 12px 20px;
                spacing: 12px;
            }}
            QToolButton {{
                background: transparent;
                border: none;
                color: {TEXT_MED};
                padding: 8px 16px;
                border-radius: 8px;
                font-size: 13px;
                font-weight: 500;
            }}
            QToolButton:hover {{
                background: rgba(255, 255, 255, 0.08);
                color: {TEXT};
            }}
            QToolButton:pressed {{
                background: rgba(255, 255, 255, 0.12);
            }}
        """)

        # ── Logo ──
        logo = QLabel("  🌵  Cactus Engine IDE")
        logo.setStyleSheet(f"""
            color: {ACCENT2};
            font-size: 15px;
            font-weight: 700;
            letter-spacing: 1px;
            padding-right: 12px;
        """)
        tb.addWidget(logo)

        def sep():
            f = QFrame()
            f.setFrameShape(QFrame.VLine)
            f.setFixedHeight(22)
            f.setStyleSheet(f"color: {BORDER};")
            tb.addWidget(f)

        sep()

        def btn(label, tip, shortcut=None, slot=None):
            b = QToolButton()
            b.setText(label)
            b.setToolTip(tip)
            if shortcut:
                b.setShortcut(QKeySequence(shortcut))
            if slot:
                b.clicked.connect(slot)
            tb.addWidget(b)
            return b

        btn("⊕  جديد",  "مشروع جديد",      "Ctrl+N", self.new_project_toolbar)
        btn("📂  فتح",  "فتح ملف .kh",   "Ctrl+O", self.open_file)
        btn("💾  حفظ",  "حفظ الملف",      "Ctrl+S", self.save_file)

        sep()

        # ── Run button ─────────────────────────────────────────
        self.btn_run = QToolButton()
        self.btn_run.setText("  ▶  تشغيل")
        self.btn_run.setToolTip("تشغيل البرنامج  [F5]")
        self.btn_run.setShortcut(QKeySequence("F5"))
        self.btn_run.setStyleSheet(f"""
            QToolButton {{
                background: {ACCENT};
                color: #ffffff;
                font-weight: 600;
                font-size: 13px;
                padding: 8px 24px;
                border-radius: 16px; /* Pill shape */
                letter-spacing: 0.5px;
            }}
            QToolButton:hover  {{ background: #008ae6; }}
            QToolButton:pressed {{ background: #006bb3; }}
            QToolButton:disabled {{
                background: #1d3c52;
                color: #557c96;
            }}
        """)
        self.btn_run.clicked.connect(self.run_code)
        tb.addWidget(self.btn_run)

        # ── Stop button ────────────────────────────────────────
        self.btn_stop = QToolButton()
        self.btn_stop.setText("  ■  إيقاف")
        self.btn_stop.setToolTip("إيقاف البرنامج  [F6]")
        self.btn_stop.setShortcut(QKeySequence("F6"))
        self.btn_stop.setEnabled(False)
        self.btn_stop.setStyleSheet(f"""
            QToolButton {{
                background: #202028;
                color: {TEXT_DIM};
                font-weight: 600;
                font-size: 13px;
                padding: 8px 24px;
                border-radius: 16px;
            }}
            QToolButton:enabled {{
                background: {RED};
                color: #fff;
            }}
            QToolButton:enabled:hover  {{ background: #dc2626; }}
            QToolButton:enabled:pressed {{ background: #b91c1c; }}
        """)
        self.btn_stop.clicked.connect(self.stop_code)
        tb.addWidget(self.btn_stop)

        # ── Export button ────────────────────────────────────────
        self.btn_export = QToolButton()
        self.btn_export.setText("  📦  تصدير")
        self.btn_export.setToolTip("تصدير اللعبة كملف تنفيذي (.exe)")
        self.btn_export.setStyleSheet(f"""
            QToolButton {{
                background: {GREEN};
                color: #ffffff;
                font-weight: 600;
                font-size: 13px;
                padding: 8px 24px;
                border-radius: 16px;
            }}
            QToolButton:hover  {{ background: {GREEN_DARK}; }}
        """)
        self.btn_export.clicked.connect(self.export_game)
        tb.addWidget(self.btn_export)

        # right spacer
        sp = QWidget()
        sp.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        tb.addWidget(sp)

        self.main_toolbar = tb
        self.addToolBar(tb)

    # ── Central widget ────────────────────────────────────────
    def _build_central(self):
        root = QWidget()
        root.setStyleSheet("background: #09090b;")
        self.setCentralWidget(root)

        root_lay = QHBoxLayout(root)
        self.root_lay = root_lay
        root_lay.setContentsMargins(12, 12, 12, 12)
        root_lay.setSpacing(12)

        # ── Main splitter H ────────────────────────────────────
        self.h_split = QSplitter(Qt.Horizontal)
        self.h_split.setHandleWidth(12)
        self.h_split.setStyleSheet("QSplitter::handle { background: transparent; }")

        # ──────────────────────────────────────────────────────
        # LEFT: Editor
        # ──────────────────────────────────────────────────────
        self.editor_wrap = QFrame()
        self.editor_wrap.setObjectName("editorCard")
        self.editor_wrap.setStyleSheet(f"""
            #editorCard {{
                background: {BG_EDITOR};
                border-radius: 12px;
                border: 1px solid {BORDER};
            }}
        """)
        e_lay = QVBoxLayout(self.editor_wrap)
        e_lay.setContentsMargins(0, 0, 0, 0)
        e_lay.setSpacing(0)

        # tab bar
        e_header = QWidget()
        e_header.setFixedHeight(40)
        e_header.setStyleSheet(f"background: transparent; border-bottom: 1px solid {BORDER};")
        eh_lay = QHBoxLayout(e_header)
        eh_lay.setContentsMargins(0, 0, 16, 0)

        self.tab_label = QLabel()
        self.tab_label.setStyleSheet(f"""
            color: {TEXT};
            padding: 0 20px;
            font-size: 13px;
            border-right: 1px solid {BORDER};
        """)
        self.tab_label.setFixedHeight(40)
        self.tab_label.setText("  ●  hello.kh")
        eh_lay.addWidget(self.tab_label)
        eh_lay.addStretch()
        e_lay.addWidget(e_header)

        self.editor = CodeEditor()
        self.editor.setStyleSheet(f"""
            QPlainTextEdit {{
                background: transparent;
                color: {TEXT};
                border: none;
                padding: 10px 4px;
                selection-background-color: #312e81;
                selection-color: {TEXT};
            }}
        """)
        self.editor.setPlaceholderText("# اكتب كود .kh هنا…")
        e_lay.addWidget(self.editor)

        # ── AI Assistant Panel ─────────────────────────────────
        '''
        self.ai_panel = QFrame()
        self.ai_panel.setFixedHeight(50)
        self.ai_panel.setStyleSheet(f"""
            background: {BG_PANEL};
            border-top: 1px solid {BORDER};
            border-bottom-left-radius: 12px;
            border-bottom-right-radius: 12px;
        """)
        ai_lay = QHBoxLayout(self.ai_panel)
        ai_lay.setContentsMargins(12, 8, 12, 8)
        ai_lay.setSpacing(8)

        ai_label = QLabel("✨ مساعد الكود:")
        ai_label.setStyleSheet(f"color: {ACCENT2}; font-weight: bold; font-size: 12px;")
        ai_lay.addWidget(ai_label)

        self.ai_input = QLineEdit()
        self.ai_input.setPlaceholderText("اطلب من الذكاء الاصطناعي تعديل أو كتابة كود...")
        self.ai_input.setStyleSheet(f"""
            QLineEdit {{
                background: {BG_EDITOR};
                color: {TEXT};
                border: 1px solid {BORDER};
                border-radius: 6px;
                padding: 4px 10px;
                font-size: 13px;
            }}
            QLineEdit:focus {{
                border: 1px solid {ACCENT};
            }}
        """)
        ai_lay.addWidget(self.ai_input)

        self.ai_btn = QPushButton("إرسال")
        self.ai_btn.setCursor(Qt.PointingHandCursor)
        self.ai_btn.setStyleSheet(f"""
            QPushButton {{
                background: {ACCENT};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 6px 16px;
                font-weight: bold;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background: #008ae6;
            }}
            QPushButton:pressed {{
                background: #006bb3;
            }}
        """)
        self.ai_btn.clicked.connect(self._send_ai_prompt)
        self.ai_input.returnPressed.connect(self._send_ai_prompt)
        ai_lay.addWidget(self.ai_btn)

        e_lay.addWidget(self.ai_panel)
        '''
        # ──────────────────────────────────────────────────────
        # RIGHT: Preview + Console
        # ──────────────────────────────────────────────────────
        right_wrap = QWidget()
        right_wrap.setStyleSheet("background: transparent;")
        right_wrap.setFixedWidth(800)
        r_lay = QVBoxLayout(right_wrap)
        r_lay.setContentsMargins(0, 0, 0, 0)
        r_lay.setSpacing(0)

        self.v_split = QSplitter(Qt.Vertical)
        self.v_split.setHandleWidth(12)
        self.v_split.setStyleSheet("QSplitter::handle { background: transparent; }")

        # ── Preview panel ──────────────────────────────────────
        preview = QFrame()
        self.preview_frame = preview
        preview.setFixedHeight(450)
        preview.setObjectName("previewCard")
        preview.setStyleSheet(f"""
            #previewCard {{
                background: {BG_PANEL};
                border-radius: 12px;
                border: 1px solid {BORDER};
            }}
        """)
        pv_lay = QVBoxLayout(preview)
        pv_lay.setContentsMargins(0, 0, 0, 0)
        pv_lay.setSpacing(0)

        pv_hdr = self._panel_header("⬡  شاشة العرض", full_btn=True)
        self.preview_header = pv_hdr
        pv_lay.addWidget(pv_hdr)

        self.pv_body = QWidget()
        self.pv_body.setStyleSheet("background: transparent;")
        self.pv_body.installEventFilter(self)
        pv_body_lay = QVBoxLayout(self.pv_body)
        pv_body_lay.setAlignment(Qt.AlignCenter)

        self.preview_icon = QLabel("⬡")
        self.preview_icon.setAlignment(Qt.AlignCenter)
        self.preview_icon.setStyleSheet(f"color: #1a1a40; font-size: 80px;")

        self.preview_hint = QLabel("اضغط  ▶  لتشغيل البرنامج")
        self.preview_hint.setAlignment(Qt.AlignCenter)
        self.preview_hint.setStyleSheet(f"color: {TEXT_DIM}; font-size: 14px; margin-top: 8px;")

        pv_body_lay.addStretch()
        pv_body_lay.addWidget(self.preview_icon)
        pv_body_lay.addWidget(self.preview_hint)
        pv_body_lay.addStretch()
        pv_lay.addWidget(self.pv_body)

        self.v_split.addWidget(preview)

        # ── Console panel ──────────────────────────────────────
        self.console_wrap = QFrame()
        self.console_wrap.setObjectName("consoleCard")
        self.console_wrap.setStyleSheet(f"""
            #consoleCard {{
                background: {BG_CONSOLE};
                border-radius: 12px;
                border: 1px solid {BORDER};
            }}
        """)
        cv_lay = QVBoxLayout(self.console_wrap)
        cv_lay.setContentsMargins(0, 0, 0, 0)
        cv_lay.setSpacing(0)

        cv_hdr = self._panel_header("▪  المخرجات", clear_btn=True)
        cv_lay.addWidget(cv_hdr)

        self.console = Console()
        self.console.setStyleSheet(f"""
            QPlainTextEdit {{
                background: transparent;
                color: {TEXT};
                border: none;
                padding: 12px 16px;
            }}
        """)
        cv_lay.addWidget(self.console)

        self.v_split.addWidget(self.console_wrap)
        self.v_split.setSizes([540, 220])

        r_lay.addWidget(self.v_split)
        
        # ── Sidebar ────────────────────────────────────────────
        self.sidebar_wrap = QFrame()
        self.sidebar_wrap.setObjectName("sidebarCard")
        self.sidebar_wrap.setStyleSheet(f"""
            #sidebarCard {{
                background: {BG_PANEL};
                border-radius: 12px;
                border: 1px solid {BORDER};
            }}
        """)
        sb_lay = QVBoxLayout(self.sidebar_wrap)
        sb_lay.setContentsMargins(0, 0, 0, 0)
        sb_lay.setSpacing(0)
        
        sb_hdr = QWidget()
        sb_hdr.setFixedHeight(36)
        sb_hdr.setStyleSheet(f"background: transparent; border-bottom: 1px solid {BORDER};")
        sb_hdr_lay = QHBoxLayout(sb_hdr)
        sb_hdr_lay.setContentsMargins(16, 0, 12, 0)
        
        sb_lbl = QLabel("📁 ملفات المشروع")
        sb_lbl.setStyleSheet(f"color: {TEXT_MED}; font-size: 12px; letter-spacing: 0.5px;")
        sb_hdr_lay.addWidget(sb_lbl)
        
        sb_hdr_lay.addStretch()
        
        btn_add_file = QToolButton()
        btn_add_file.setText("+")
        btn_add_file.setToolTip("إضافة ملف جديد")
        btn_add_file.setStyleSheet(f"""
            QToolButton {{
                color: {TEXT};
                background: transparent;
                border: none;
                font-size: 18px;
                font-weight: bold;
                padding-bottom: 2px;
            }}
            QToolButton:hover {{
                color: {ACCENT};
            }}
        """)
        btn_add_file.clicked.connect(self.new_file)
        sb_hdr_lay.addWidget(btn_add_file)
        
        sb_lay.addWidget(sb_hdr)
        
        self.sidebar_list = QListWidget()
        self.sidebar_list.setStyleSheet(f"""
            QListWidget {{
                background: transparent;
                border: none;
                color: {TEXT};
                padding: 8px;
                font-size: 13px;
            }}
            QListWidget::item {{
                padding: 6px;
                border-radius: 4px;
            }}
            QListWidget::item:hover {{
                background: rgba(255, 255, 255, 0.05);
            }}
            QListWidget::item:selected {{
                background: {ACCENT};
                color: white;
            }}
        """)
        self.sidebar_list.itemClicked.connect(self._on_sidebar_item_clicked)
        sb_lay.addWidget(self.sidebar_list)

        # Add Right Wrap (Preview) first, then Editor Wrap (Editor), then Sidebar
        self.h_split.addWidget(right_wrap)
        self.h_split.addWidget(self.editor_wrap)
        self.h_split.addWidget(self.sidebar_wrap)
        self.h_split.setSizes([800, 600, 200])

        root_lay.addWidget(self.h_split)

    def _send_ai_prompt(self):
        prompt = self.ai_input.text().strip()
        if not prompt:
            return
        
        self.console.info(f"\\n[AI Prompt]: {prompt}\\n")
        self.console.out("جاري التفكير والاتصال بـ Claude... (يرجى الانتظار)\\n")
        self.ai_input.clear()
        
        self.ai_worker = AIWorker(prompt, self.editor.toPlainText())
        self.ai_worker.finished.connect(self._on_ai_finished)
        self.ai_worker.start()

    def _on_ai_finished(self, result):
        self.console.out("\\n--- إجابة Claude ---\\n")
        self.console.out(result + "\\n\\n")
        
        if "```kh" in result:
            code_parts = result.split("```kh")
            for i in range(1, len(code_parts)):
                code = code_parts[i].split("```")[0].strip()
                if code:
                    self.editor.setPlainText(code)

    def _panel_header(self, title, clear_btn=False, full_btn=False):
        hdr = QWidget()
        hdr.setFixedHeight(36)
        hdr.setStyleSheet(f"""
            background: transparent;
            border-bottom: 1px solid {BORDER};
        """)
        lay = QHBoxLayout(hdr)
        lay.setContentsMargins(16, 0, 12, 0)

        lbl = QLabel(title)
        lbl.setStyleSheet(f"color: {TEXT_MED}; font-size: 12px; letter-spacing: 0.5px;")
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

        if full_btn:
            fbtn = QToolButton()
            fbtn.setText("تكبير الشاشة 🗖")
            fbtn.setStyleSheet(f"""
                QToolButton {{
                    color: {ACCENT2};
                    background: transparent;
                    border: 1px solid {BORDER};
                    border-radius: 4px;
                    padding: 2px 10px;
                    font-size: 11px;
                }}
                QToolButton:hover {{
                    color: #fff;
                    background: rgba(99,102,241,0.2);
                    border-color: {ACCENT};
                }}
            """)
            fbtn.clicked.connect(self._toggle_fullscreen)
            lay.addWidget(fbtn)

        return hdr

    def _toggle_fullscreen(self):
        if self.isFullScreen():
            self.showNormal()
            self.editor_wrap.show()
            self.console_wrap.show()
            self.main_toolbar.show()
            self.statusBar().show()
            if hasattr(self, 'sidebar_wrap'): self.sidebar_wrap.show()
            if hasattr(self, 'preview_header'): self.preview_header.show()
            if hasattr(self, 'root_lay'): self.root_lay.setContentsMargins(12, 12, 12, 12)
            if hasattr(self, 'preview_frame'):
                self.preview_frame.setStyleSheet(f"""
                    #previewCard {{
                        background: {BG_PANEL};
                        border-radius: 12px;
                        border: 1px solid {BORDER};
                    }}
                """)
        else:
            self.showFullScreen()
            self.editor_wrap.hide()
            self.console_wrap.hide()
            self.main_toolbar.hide()
            self.statusBar().hide()
            if hasattr(self, 'sidebar_wrap'): self.sidebar_wrap.hide()
            if hasattr(self, 'preview_header'): self.preview_header.hide()
            if hasattr(self, 'root_lay'): self.root_lay.setContentsMargins(0, 0, 0, 0)
            if hasattr(self, 'preview_frame'):
                self.preview_frame.setStyleSheet("#previewCard { background: #000; border: none; border-radius: 0px; }")

    # ── Status bar ────────────────────────────────────────────
    def _build_statusbar(self):
        sb = self.statusBar()
        sb.setStyleSheet(f"""
            QStatusBar {{
                background: {TOOLBAR_BG};
                color: {TEXT_DIM};
                border-top: 1px solid {BORDER};
                font-size: 12px;
                padding: 0 8px;
            }}
            QStatusBar::item {{ border: none; }}
        """)

        self.status_text = QLabel("جاهز")
        sb.addWidget(self.status_text)

        sb.addPermanentWidget(QLabel("  "))

        # Branch / lang indicator
        lang_lbl = QLabel("  ⬡ KH  ")
        lang_lbl.setStyleSheet(f"""
            background: {ACCENT};
            color: #fff;
            padding: 0 10px;
            font-size: 11px;
            font-weight: bold;
            border-radius: 3px;
        """)
        sb.addPermanentWidget(lang_lbl)

        self.cursor_label = QLabel("سطر 1، عمود 1  ")
        self.cursor_label.setStyleSheet(f"color: {TEXT_DIM}; font-size: 12px;")
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
            import ctypes
            w = self.pv_body.width()
            h = self.pv_body.height()
            ctypes.windll.user32.SetWindowPos(self.pygame_hwnd, 0, 0, 0, w, h, 0x0044)
            lparam = (h << 16) | (w & 0xFFFF)
            ctypes.windll.user32.SendMessageW(self.pygame_hwnd, 0x0005, 0, lparam)

    def _update_cursor(self):
        c = self.editor.textCursor()
        self.cursor_label.setText(f"سطر {c.blockNumber()+1}، عمود {c.columnNumber()+1}  ")

    def _set_status(self, msg, timeout_ms=0):
        self.status_text.setText(msg)
        if timeout_ms:
            QTimer.singleShot(timeout_ms, lambda: self.status_text.setText("جاهز"))

    # ── Dirty flag ────────────────────────────────────────────
    def _mark_dirty(self):
        if not self._is_dirty:
            self._is_dirty = True
            name = os.path.basename(self.current_file) if self.current_file else "ملف جديد"
            self.tab_label.setText(f"  ●  {name} *")

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
                    pass
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
        import glob
        kh_files = glob.glob(os.path.join(directory, "*.kh"))
        for f in kh_files:
            item = QListWidgetItem(os.path.basename(f))
            item.setData(Qt.UserRole, f)
            self.sidebar_list.addItem(item)
        
        if kh_files:
            self.open_file_path(kh_files[0])
        else:
            self.new_file()

    def _on_sidebar_item_clicked(self, item):
        path = item.data(Qt.UserRole)
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

    # ── Run / Stop ────────────────────────────────────────────
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
        self.btn_stop.setEnabled(True)
        self._set_status("⬡  جاري التشغيل…")
        
        # Reset preview icon state
        self.preview_icon.setFixedSize(QSize(16777215, 16777215))
        from PyQt5.QtGui import QPixmap
        self.preview_icon.setPixmap(QPixmap())
        self.preview_icon.setText("▶")
        self.preview_icon.setStyleSheet(f"color: {GREEN}; font-size: 80px;")
        self.preview_icon.show()
        
        self.preview_hint.setText("البرنامج يعمل الآن في نافذة منفصلة")
        self.preview_hint.show()

    def export_game(self):
        if not getattr(self, "current_file", None):
            QMessageBox.warning(self, "تنبيه", "الرجاء حفظ الملف أولاً قبل التصدير.")
            return

        dlg = QDialog(self)
        dlg.setWindowTitle("إعدادات تصدير اللعبة")
        dlg.setMinimumWidth(450)
        
        layout = QVBoxLayout(dlg)
        
        layout.addWidget(QLabel("اسم اللعبة:"))
        game_name = QLineEdit()
        game_name.setText("Game")
        layout.addWidget(game_name)
        
        layout.addWidget(QLabel("اسم صاحب اللعبة (اختياري):"))
        author_name = QLineEdit()
        layout.addWidget(author_name)
        
        layout.addWidget(QLabel("شعار اللعبة (اختياري):"))
        icon_layout = QHBoxLayout()
        icon_path_edit = QLineEdit()
        icon_path_edit.setReadOnly(True)
        icon_btn = QPushButton("استعراض...")
        def _choose_icon():
            path, _ = QFileDialog.getOpenFileName(dlg, "اختر الشعار", "", "Images (*.ico *.png *.jpg *.jpeg)")
            if path: icon_path_edit.setText(path)
        icon_btn.clicked.connect(_choose_icon)
        icon_layout.addWidget(icon_path_edit)
        icon_layout.addWidget(icon_btn)
        layout.addLayout(icon_layout)
        
        layout.addWidget(QLabel("مسار التصدير (موقع اللعبة):"))
        loc_layout = QHBoxLayout()
        loc_edit = QLineEdit()
        loc_edit.setReadOnly(True)
        loc_btn = QPushButton("استعراض...")
        def _choose_loc():
            path = QFileDialog.getExistingDirectory(dlg, "اختر مجلد التصدير")
            if path: loc_edit.setText(path)
        loc_btn.clicked.connect(_choose_loc)
        loc_layout.addWidget(loc_edit)
        loc_layout.addWidget(loc_btn)
        layout.addLayout(loc_layout)
        
        btn_layout = QHBoxLayout()
        btn_ok = QPushButton("تصدير")
        btn_ok.setStyleSheet(f"background-color: {GREEN}; color: white; padding: 6px; font-weight: bold;")
        btn_cancel = QPushButton("إلغاء")
        btn_ok.clicked.connect(lambda: dlg.accept() if loc_edit.text() else QMessageBox.warning(dlg, "تنبيه", "الرجاء اختيار مسار التصدير."))
        btn_cancel.clicked.connect(dlg.reject)
        btn_layout.addStretch()
        btn_layout.addWidget(btn_ok)
        btn_layout.addWidget(btn_cancel)
        layout.addLayout(btn_layout)
        
        if dlg.exec_() != QDialog.Accepted:
            return
            
        export_dir = loc_edit.text()
        icon_path = icon_path_edit.text()
        g_name = game_name.text().strip() or "Game"
        a_name = author_name.text().strip()
            
        self.save_file()
        
        self.console.clear()
        self.console.info(f"▶  بدء التصدير إلى: {export_dir}\n")
        self.console.info(f"الرجاء الانتظار، جاري بناء '{g_name}'...\n")
        
        script_dir = os.path.dirname(os.path.abspath(self.current_file))
        kh_dir = os.path.dirname(os.path.abspath(__file__))
        
        runner_path = os.path.join(export_dir, "game_runner.py")
        with open(runner_path, "w", encoding="utf-8") as f:
            f.write(f"""# اسم اللعبة: {g_name}
# المطور: {a_name}
import sys
import os
import pygame
from OpenGL.GL import *
from OpenGL.GLU import *
sys.path.append(r'{kh_dir}')
from interpreter import Interpreter

if getattr(sys, 'frozen', False):
    if hasattr(sys, '_MEIPASS'):
        app_path = sys._MEIPASS
    else:
        app_path = os.path.dirname(sys.executable)
else:
    app_path = os.path.dirname(os.path.abspath(__file__))

os.chdir(app_path)

filename = "{os.path.basename(self.current_file)}"
try:
    with open(filename, "r", encoding="utf-8") as file:
        code = file.read()

    scene_codes = []
    for fname in os.listdir(app_path):
        if fname.endswith(".khscene") and fname != filename:
            try:
                with open(fname, "r", encoding="utf-8") as fs:
                    scene_codes.append(fs.read())
            except Exception:
                pass

    if scene_codes:
        code = "\\n\\n".join(scene_codes) + "\\n\\n" + code

    interpreter = Interpreter()
    interpreter.execute(code)
except Exception as e:
    import traceback
    with open("error_log.txt", "w", encoding="utf-8") as error_f:
        traceback.print_exc(file=error_f)
""")

        self.export_process = QProcess(self)
        self.export_process.setWorkingDirectory(export_dir)
        
        self.export_process.readyReadStandardOutput.connect(
            lambda: self.console.out(bytes(self.export_process.readAllStandardOutput()).decode("utf-8", "replace"))
        )
        self.export_process.readyReadStandardError.connect(
            lambda: self.console._write(bytes(self.export_process.readAllStandardError()).decode("utf-8", "replace"), "#3b82f6")
        )
        
        def on_export_finished(exit_code, exit_status):
            if exit_code == 0:
                self.console.success("\\n✓ تم التصدير بنجاح!\\n")
                self.console.info(f"تجد اللعبة في: {{os.path.join(export_dir, 'dist', g_name)}}\\n")
            else:
                self.console.err("\\n❌ فشل التصدير.\\n")
                
            try:
                if os.path.exists(runner_path):
                    os.remove(runner_path)
            except:
                pass
                
            self.btn_export.setEnabled(True)
            self._set_status("✓ انتهى التصدير")

        self.export_process.finished.connect(on_export_finished)
        
        self.btn_export.setEnabled(False)
        self._set_status("⬡  جاري التصدير…")
        
        pyinstaller_args = [
            "-m", "PyInstaller",
            "--noconfirm",
            "--onedir",
            "--windowed",
            "--name", g_name,
            "--hidden-import", "pygame",
            "--hidden-import", "OpenGL",
            "--hidden-import", "interpreter",
            "--hidden-import", "graphics",
            "--hidden-import", "rigidbody",
            "--hidden-import", "terrain",
            "--hidden-import", "math_types",
            "--hidden-import", "keyboard",
            "--hidden-import", "mouse",
            "--hidden-import", "arabic_reshaper",
            "--hidden-import", "bidi.algorithm",
            "--paths", kh_dir,
        ]
        
        for fname in os.listdir(script_dir):
            if fname.lower().endswith(('.png', '.jpg', '.jpeg', '.obj', '.fbx', '.kh', '.khscene', '.ttf', '.wav', '.mp3', '.ogg')):
                asset_path = os.path.join(script_dir, fname)
                pyinstaller_args.extend(["--add-data", f"{asset_path};."])
                
        if icon_path:
            pyinstaller_args.extend(["--icon", icon_path])
                
        pyinstaller_args.append(runner_path)
        self.export_process.start(sys.executable, pyinstaller_args)

    def closeEvent(self, event):
        self.stop_code()
        event.accept()
        import sys
        sys.exit(0)

    def stop_code(self):
        if self.process and self.process.state() != QProcess.NotRunning:
            self._is_stopping = True
            self.process.kill()

    def _on_stdout(self):
        raw = self.process.readAllStandardOutput().data().decode("utf-8", errors="replace")
        
        # Check for our HWND injection
        if "__KH_HWND__:" in raw:
            for line in raw.splitlines():
                if line.startswith("__KH_HWND__:"):
                    try:
                        hwnd = int(line.split(":")[1])
                        self.pygame_hwnd = hwnd
                        import ctypes
                        qt_hwnd = int(self.pv_body.winId())
                        # Embed the pygame window!
                        ctypes.windll.user32.SetParent(hwnd, qt_hwnd)
                        
                        # Resize to fit the preview body
                        w = self.pv_body.width()
                        h = self.pv_body.height()
                        # SWP_NOZORDER = 0x0004, SWP_SHOWWINDOW = 0x0040
                        ctypes.windll.user32.SetWindowPos(hwnd, 0, 0, 0, w, h, 0x0044)
                        
                        # Hide the icon and hint
                        self.preview_icon.hide()
                        self.preview_hint.hide()
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
        self.btn_stop.setEnabled(False)
        
        self.preview_icon.show()
        self.preview_hint.show()

        if code == 0 or self._is_stopping:
            self.console.success("\n✓  انتهى البرنامج\n")
            self._set_status("✓  انتهى", 4000)
            
            self.preview_icon.setFixedSize(QSize(16777215, 16777215)) # Reset max size
            self.preview_icon.setText("⬡")
            self.preview_icon.setStyleSheet(f"color: #1a1a40; font-size: 80px;")
            self.preview_hint.setText("اضغط  ▶  لتشغيل البرنامج")
            self.preview_hint.show()
        else:
            self.console.err(f"\n✗  انتهى بخطأ  (كود: {code})\n")
            self._set_status(f"✗  خطأ", 4000)
            self.preview_icon.setFixedSize(QSize(16777215, 16777215))
            self.preview_icon.setText("⚠")
            self.preview_icon.setStyleSheet(f"color: {RED}; font-size: 72px;")
            self.preview_hint.setText("راجع المخرجات أدناه")
            self.preview_hint.show()
            
        self._is_stopping = False

    # ── Keyboard shortcuts ────────────────────────────────────
    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Escape:
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
                color: {ACCENT2};
                font-size: 26px;
                font-weight: bold;
                margin-top: 20px;
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
        
        title = QLabel("🌵 Cactus Engine IDE")
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
        
        btn_skip = QPushButton("استمرار بدون مشروع ➔")
        btn_skip.setCursor(Qt.PointingHandCursor)
        btn_skip.clicked.connect(self.accept_skip)
        btn_skip.setStyleSheet(f"""
            QPushButton {{ background-color: transparent; border: none; color: {TEXT_DIM}; margin-top: 15px; font-weight: normal; }}
            QPushButton:hover {{ color: {TEXT}; text-decoration: underline; background-color: transparent; border: none; }}
        """)
        
        lay.addWidget(title)
        lay.addWidget(subtitle)
        lay.addWidget(btn_open)
        lay.addWidget(btn_new)
        lay.addWidget(btn_skip)
        
    def accept_skip(self):
        self.selected_dir = None
        self.accept()

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
            bg_color = ctypes.c_int(0x001E1E1E)
            ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 35, ctypes.byref(bg_color), ctypes.sizeof(bg_color))
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
        ide.show()
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
