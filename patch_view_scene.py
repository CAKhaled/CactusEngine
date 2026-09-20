content = open('view_scene.py', encoding='utf-8').read()
delete_func = '''    def delete_selected(self):
        if not self.selected_obj: return
        if getattr(self.selected_obj, "obj_type", "") in ('camera', 'المشهد'): return
        
        self.push_undo_state()
        
        if self.selected_obj in self.objects:
            self.objects.remove(self.selected_obj)
            
        self.selected_obj = None
        self.scene_tree_updated.emit()
        self.object_selected.emit("")
        self.update()

'''
if 'def delete_selected(self):' not in content:
    content = content.replace('    def add_scene_object(self, obj_type, name=None, filepath=""):', delete_func + '    def add_scene_object(self, obj_type, name=None, filepath=""):')

key_press = '''    def keyPressEvent(self, event):
        from PyQt5.QtCore import Qt
        if event.key() == Qt.Key_Delete:
            self.delete_selected()
            return
            
        if event.key() == Qt.Key_Z and event.modifiers() == Qt.ControlModifier:'''

if 'def keyPressEvent(self, event):' in content and 'Qt.Key_Delete' not in content:
    content = content.replace('''    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Z and event.modifiers() == Qt.ControlModifier:''', key_press)

open('view_scene.py', 'w', encoding='utf-8').write(content)
print('Done')
