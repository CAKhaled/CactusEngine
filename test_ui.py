import sys
import time
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer

def test_ui():
    import ui2
    app = QApplication(sys.argv)
    ide = ui2.KHIde()
    ide.show()
    
    def actions():
        try:
            ide.scene_ui.scene_viewer.add_scene_object("Canvas")
            ide.scene_ui.scene_viewer.add_scene_object("Text", parent_name="واجهة1")
            
            text_obj_name = None
            for obj in ide.scene_ui.scene_viewer.objects:
                if obj.obj_type == "Text":
                    text_obj_name = obj.name
                    break
            
            ide.scene_ui._on_scene_selected(text_obj_name)
            QApplication.processEvents()
            
            print(f"ui_props_widget isVisible: {ide.scene_ui.ui_props_widget.isVisible()}")
            print(f"ui_props_widget geometry: {ide.scene_ui.ui_props_widget.geometry()}")
            
            ui_lay = ide.scene_ui.ui_props_widget.layout()
            print(f"ui_lay child count: {ui_lay.count()}")
            
            for i in range(ui_lay.count()):
                item = ui_lay.itemAt(i)
                w = item.widget()
                if w:
                    print(f"Child {i} isVisible: {w.isVisible()} sizeHint: {w.sizeHint()}")
                    
        except Exception as e:
            print(f"Error: {e}")
        finally:
            ide.close()
            app.quit()

    QTimer.singleShot(1000, actions)
    app.exec_()

if __name__ == "__main__":
    test_ui()
