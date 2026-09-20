import sys
import time
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QPixmap

def take_screenshot():
    # Find the main window
    import ui2
    app = QApplication(sys.argv)
    
    # We will instantiate the KHIde
    ide = ui2.KHIde()
    ide.show()
    
    def actions():
        try:
            # 1. Add Canvas
            ide.scene_ui.scene_viewer.add_scene_object("Canvas")
            # 2. Add Text to Canvas
            ide.scene_ui.scene_viewer.add_scene_object("Text", parent_name="واجهة1")
            
            # Find the actual name
            text_obj_name = None
            for obj in ide.scene_ui.scene_viewer.objects:
                if obj.obj_type == "Text":
                    text_obj_name = obj.name
                    break
            
            print(f"Selecting object: {text_obj_name}")
            # 3. Select the Text object
            ide.scene_ui._on_scene_selected(text_obj_name)
            
            # Wait for layout to update
            QApplication.processEvents()
            
            # 4. Take screenshot of the sidebar (hierarchy_layout)
            # The properties panel is in the right dock or splitter.
            # Let's take a screenshot of the whole main window.
            pixmap = ide.grab()
            pixmap.save("C:\\Users\\Khaled 2\\.gemini\\antigravity-ide\\brain\\3122c731-775b-4894-8176-1b73d9b9c6e7\\scratch\\app_screenshot.png")
            print("Screenshot saved to artifacts scratch!")
        except Exception as e:
            print(f"Error in actions: {e}")
        finally:
            ide.close()
            app.quit()

    # Run actions after a short delay
    QTimer.singleShot(1000, actions)
    app.exec_()

if __name__ == "__main__":
    take_screenshot()
