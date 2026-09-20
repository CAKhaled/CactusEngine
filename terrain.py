import os
import json
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QDoubleSpinBox, QPushButton, QMessageBox
from PyQt5.QtCore import Qt

class TerrainDialog(QDialog):
    def __init__(self, project_dir, parent=None):
        super().__init__(parent)
        self.project_dir = project_dir
        self.setWindowTitle("إضافة تضاريس")
        self.setStyleSheet("background: #0E1622; color: #E7EDF5; font-family: 'Segoe UI';")
        self.resize(300, 150)
        
        layout = QVBoxLayout(self)
        
        # Name
        lay_name = QHBoxLayout()
        lbl_name = QLabel("اسم التضاريس:")
        self.le_name = QLineEdit("Terrain1")
        self.le_name.setStyleSheet("background: #0A111B; border: 1px solid #243449; border-radius: 4px; padding: 4px;")
        lay_name.addWidget(lbl_name)
        lay_name.addWidget(self.le_name)
        layout.addLayout(lay_name)
        
        # Dimensions
        lay_size = QHBoxLayout()
        lbl_x = QLabel("العرض (X):")
        self.sp_x = QDoubleSpinBox()
        self.sp_x.setRange(1, 10000)
        self.sp_x.setValue(10)
        self.sp_x.setStyleSheet("background: #0A111B; border: 1px solid #243449; border-radius: 4px; padding: 4px;")
        
        lbl_y = QLabel("الطول (Y):")
        self.sp_y = QDoubleSpinBox()
        self.sp_y.setRange(1, 10000)
        self.sp_y.setValue(10)
        self.sp_y.setStyleSheet("background: #0A111B; border: 1px solid #243449; border-radius: 4px; padding: 4px;")
        
        lay_size.addWidget(lbl_x)
        lay_size.addWidget(self.sp_x)
        lay_size.addWidget(lbl_y)
        lay_size.addWidget(self.sp_y)
        layout.addLayout(lay_size)
        
        # Buttons
        lay_btn = QHBoxLayout()
        btn_ok = QPushButton("موافق")
        btn_ok.setStyleSheet("background: #8B5CF6; color: white; border: none; border-radius: 4px; padding: 6px;")
        btn_ok.clicked.connect(self.on_ok)
        
        btn_cancel = QPushButton("إلغاء")
        btn_cancel.setStyleSheet("background: #30445D; color: white; border: none; border-radius: 4px; padding: 6px;")
        btn_cancel.clicked.connect(self.reject)
        
        lay_btn.addWidget(btn_ok)
        lay_btn.addWidget(btn_cancel)
        layout.addLayout(lay_btn)
        
        self.data = {}

    def on_ok(self):
        name = self.le_name.text().strip()
        if not name:
            QMessageBox.warning(self, "خطأ", "يجب إدخال اسم للتضاريس.")
            return
            
        if not self.project_dir or not os.path.exists(self.project_dir):
            QMessageBox.warning(self, "خطأ", "مسار المشروع غير صالح.")
            return
            
        file_path = os.path.join(self.project_dir, f"{name}.khterrain")
        if os.path.exists(file_path):
            QMessageBox.warning(self, "خطأ", "يوجد تضاريس بهذا الاسم مسبقاً.")
            return
            
        self.data = {
            "name": name,
            "size_x": self.sp_x.value(),
            "size_y": self.sp_y.value(),
            "grid_size": 50,
            "heightmap": [0.0] * (50 * 50)
        }
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, ensure_ascii=False, indent=4)
        except Exception as e:
            QMessageBox.warning(self, "خطأ", f"فشل في حفظ الملف: {e}")
            return
            
        self.accept()

def scan_terrains(project_dir):
    terrains = []
    if not project_dir or not os.path.exists(project_dir):
        return terrains
        
    for filename in os.listdir(project_dir):
        if filename.endswith(".khterrain"):
            filepath = os.path.join(project_dir, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    data['filepath'] = filepath
                    terrains.append(data)
            except Exception:
                pass
    return terrains

def add_terrains_to_scene(scene_viewer, project_dir):
    terrains = scan_terrains(project_dir)
    existing_terrains = [obj.name for obj in getattr(scene_viewer, "objects", []) if getattr(obj, "obj_type", "") == "Terrain"]
    
    for t in terrains:
        name = t.get("name", "Terrain")
        if name not in existing_terrains:
            obj = scene_viewer.add_scene_object("Terrain", name=name, filepath=t.get("filepath", ""))
            obj.scale = [t.get("size_x", 10.0), 1.0, t.get("size_y", 10.0)]
            obj.grid_size = t.get("grid_size", 50)
            obj.heightmap = t.get("heightmap", [0.0] * (obj.grid_size * obj.grid_size))

def save_terrain_data(filepath, name, size_x, size_y, grid_size, heightmap):
    if not filepath:
        return
    d = os.path.dirname(filepath)
    if d and not os.path.exists(d):
        return
    data = {
        "name": name,
        "size_x": size_x,
        "size_y": size_y,
        "grid_size": grid_size,
        "heightmap": heightmap
    }
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except Exception:
        pass

def load_terrain_data(filepath):
    if not filepath:
        print(f"TERRAIN ERROR: filepath is empty")
        return 10.0, 10.0, 50, [0.0] * (50 * 50)
    if not os.path.exists(filepath):
        print(f"TERRAIN ERROR: file does not exist at {filepath}")
        return 10.0, 10.0, 50, [0.0] * (50 * 50)
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            sx = data.get("size_x", 10.0)
            sy = data.get("size_y", 10.0)
            gs = data.get("grid_size", 50)
            hm = data.get("heightmap", [0.0] * (gs * gs))
            return sx, sy, gs, hm
    except Exception as e:
        print(f"TERRAIN ERROR: Exception reading {filepath}: {e}")
        return 10.0, 10.0, 50, [0.0] * (50 * 50)
