import re

# 1. Update view_scene_ui.py
content = open('view_scene_ui.py', encoding='utf-8').read()

# Context menu: remove Custom2D
content = content.replace('menu_custom.addAction("شكل 2D مخصص (صورة)...").triggered.connect(self._add_custom_2d)', '')
content = content.replace('''    def _add_custom_2d(self):
        from PyQt5.QtWidgets import QFileDialog
        path, _ = QFileDialog.getOpenFileName(self, "اختر صورة", "", "Images (*.png *.jpg *.jpeg)")
        if path:
            self.scene_viewer.add_scene_object("Custom2D", filepath=path)''', '')

# Make 2D shapes show filepath property instead of Custom2D alone
content = content.replace('if t in ["CustomModel", "Custom2D", "Sound"]:', 'if t in ["CustomModel", "Custom2D", "Sound", "Square2D", "Circle2D", "Triangle2D"]:')

# Right click on tree list to delete
tree_menu_patch = '''
    def _show_tree_context_menu(self, pos):
        item = self.scene_sidebar_list.itemAt(pos)
        if not item or item.text(0) in ("المشهد", "الكاميرا"): return
        
        from PyQt5.QtWidgets import QMenu
        menu = QMenu(self)
        menu.setStyleSheet(f"QMenu {{ background: {SCENE_BG}; color: {TEXT}; border: 1px solid {BORDER}; }} QMenu::item:selected {{ background: {PURPLE_BG}; }}")
        
        delete_action = menu.addAction("حذف العنصر")
        action = menu.exec_(self.scene_sidebar_list.mapToGlobal(pos))
        
        if action == delete_action:
            self.scene_viewer.select_by_name(item.text(0))
            self.scene_viewer.delete_selected()
'''
# I will just replace `def _show_tree_context_menu` with my implementation.
old_tree_menu = '''    def _show_tree_context_menu(self, pos):
        pass'''

if old_tree_menu in content:
    content = content.replace(old_tree_menu, tree_menu_patch)
else:
    # Just insert it before _filter_scene_tree
    content = content.replace('    def _filter_scene_tree(self, text):', tree_menu_patch + '\n    def _filter_scene_tree(self, text):')

# Also enable context menu on the tree view
content = content.replace('self.scene_sidebar_list.setContextMenuPolicy(Qt.CustomContextMenu)', 'self.scene_sidebar_list.setContextMenuPolicy(Qt.CustomContextMenu)\n        self.scene_sidebar_list.customContextMenuRequested.connect(self._show_tree_context_menu)')
# Remove duplicate connection if already there
content = content.replace('self.scene_sidebar_list.customContextMenuRequested.connect(self._show_tree_context_menu)\n        self.scene_sidebar_list.customContextMenuRequested.connect(self._show_tree_context_menu)', 'self.scene_sidebar_list.customContextMenuRequested.connect(self._show_tree_context_menu)')


open('view_scene_ui.py', 'w', encoding='utf-8').write(content)

# 2. Update view_scene.py for delete_selected and keyPressEvent
content2 = open('view_scene.py', encoding='utf-8').read()

delete_func = '''    def delete_selected(self):
        if not self.selected_obj: return
        if self.selected_obj.obj_type in ('camera', 'المشهد'): return
        
        self.push_undo_state()
        
        if self.selected_obj in self.objects:
            self.objects.remove(self.selected_obj)
            
        self.selected_obj = None
        self.scene_tree_updated.emit()
        self.object_selected.emit("")
        self.update()

'''

if "def delete_selected(self):" not in content2:
    # Insert it near add_scene_object
    content2 = content2.replace('    def add_scene_object(self, obj_type, filepath=""):', delete_func + '    def add_scene_object(self, obj_type, filepath=""):')

# Update keypress event
key_press = '''    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Delete:
            self.delete_selected()
            return
            
        if event.key() == Qt.Key_Z and event.modifiers() == Qt.ControlModifier:'''

if 'def keyPressEvent(self, event):' in content2 and 'Qt.Key_Delete' not in content2:
    content2 = content2.replace('''    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Z and event.modifiers() == Qt.ControlModifier:''', key_press)

open('view_scene.py', 'w', encoding='utf-8').write(content2)
print("Done")
