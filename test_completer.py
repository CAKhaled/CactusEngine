import sys
import re
from PyQt5.QtWidgets import QApplication
from ui import CodeEditor

app = QApplication(sys.argv)
editor = CodeEditor()
editor.show()

editor.insertPlainText("ابغا واجهة = صنع_واجهة()\nواجهة.")

tc = editor.textCursor()
line_text = tc.block().text()
cursor_pos = tc.positionInBlock()
text_up_to_cursor = line_text[:cursor_pos]
print(f"text_up_to_cursor: '{text_up_to_cursor}'")

# regex to find if we are typing after a dot
# e.g., "واجهة." or "واجهة.اضا"
match = re.search(r'([a-zA-Z_أ-ي0-9]+)\.([a-zA-Z_أ-ي0-9]*)$', text_up_to_cursor)
if match:
    var_name = match.group(1)
    completion_prefix = match.group(2)
    print(f"var_name: '{var_name}'")
    print(f"completion_prefix: '{completion_prefix}'")
    print(f"type: {editor._infer_type(var_name)}")
else:
    print("No match")
