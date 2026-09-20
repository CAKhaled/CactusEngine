from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel,
    QPushButton, QSplitter, QTreeWidget, QTreeWidgetItem,
    QToolButton, QSizePolicy, QLineEdit, QMenu,
    QAbstractSpinBox, QDoubleSpinBox, QSpinBox
)
from PyQt5.QtCore import Qt, QSize, QTimer, pyqtSignal, QPoint
from PyQt5.QtGui import QFont, QColor, QPainter, QPen, QIcon, QPixmap

from view_scene import SceneViewerWidget
# =========================================================
# ألوان Cactus Engine
# =========================================================

SCENE_BG = "#0A1018"
PANEL_BG = "#0E1622"
HEADER_BG = "#101A27"

BORDER = "#243449"
BORDER_LIGHT = "#30445D"

TEXT = "#E7EDF5"
TEXT_DIM = "#8D9AAF"
TEXT_FAINT = "#65748A"

PURPLE = "#8B5CF6"
PURPLE_HOVER = "#9D6CFF"
PURPLE_BG = "#251A45"

BLUE = "#38BDF8"
GREEN = "#4ADE80"
RED = "#F87171"
YELLOW = "#FACC15"


# =========================================================
# أيقونات بسيطة مرسومة داخل البرنامج
# =========================================================

def make_scene_icon(kind, color="#AAB8CA", size=18):

    pix = QPixmap(size, size)
    pix.fill(Qt.transparent)

    painter = QPainter(pix)
    painter.setRenderHint(QPainter.Antialiasing, True)

    pen = QPen(QColor(color))
    pen.setWidth(1)
    pen.setCapStyle(Qt.RoundCap)
    pen.setJoinStyle(Qt.RoundJoin)

    painter.setPen(pen)
    painter.setBrush(Qt.NoBrush)

    c = size / 2

    if kind == "move":
        # سهم X
        painter.drawLine(int(c), 3, int(c), size - 3)
        painter.drawLine(3, int(c), size - 3, int(c))

        painter.drawLine(3, int(c), 6, int(c - 3))
        painter.drawLine(3, int(c), 6, int(c + 3))

        painter.drawLine(size - 3, int(c), size - 6, int(c - 3))
        painter.drawLine(size - 3, int(c), size - 6, int(c + 3))

        painter.drawLine(int(c), 3, int(c - 3), 6)
        painter.drawLine(int(c), 3, int(c + 3), 6)

        painter.drawLine(int(c), size - 3, int(c - 3), size - 6)
        painter.drawLine(int(c), size - 3, int(c + 3), size - 6)

    elif kind == "rotate":
        painter.drawArc(3, 3, size - 6, size - 6, 35 * 16, 285 * 16)

        painter.drawLine(size - 4, 5, size - 4, 10)
        painter.drawLine(size - 4, 5, size - 9, 5)

    elif kind == "scale":
        painter.drawRect(4, 4, size - 8, size - 8)

        painter.drawLine(2, 7, 2, 2)
        painter.drawLine(2, 2, 7, 2)

        painter.drawLine(size - 2, size - 7, size - 2, size - 2)
        painter.drawLine(size - 2, size - 2, size - 7, size - 2)

    elif kind == "select":
        points = [
            (4, 2),
            (4, size - 4),
            (size - 3, size - 8),
            (8, size - 10)
        ]

        for i in range(len(points)):
            p1 = points[i]
            p2 = points[(i + 1) % len(points)]
            painter.drawLine(
                int(p1[0]),
                int(p1[1]),
                int(p2[0]),
                int(p2[1])
            )

    elif kind == "camera":
        painter.drawRoundedRect(
            3, 5, size - 8, size - 8, 2, 2
        )
        painter.drawLine(
            size - 5, 8,
            size - 2, 6
        )
        painter.drawLine(
            size - 2, 6,
            size - 2, size - 4
        )

    elif kind == "object":
        painter.drawRect(
            4, 4, size - 8, size - 8
        )

    elif kind == "scene":
        painter.drawLine(3, size - 4, size - 3, size - 4)
        painter.drawLine(5, size - 4, 5, 5)
        painter.drawLine(5, 5, size - 5, 5)
        
    elif kind == "brush":
        painter.drawLine(size - 4, 4, 6, size - 8)
        painter.drawEllipse(3, size - 9, 5, 5)

    painter.end()

    return QIcon(pix)


# =========================================================
# Cubemap Slot
# =========================================================
from PyQt5.QtWidgets import QFileDialog, QMessageBox
from PyQt5.QtGui import QDragEnterEvent, QDropEvent

class CubemapSlotWidget(QWidget):
    image_changed = pyqtSignal(str, str)
    
    def __init__(self, face_id, face_name, parent=None):
        super().__init__(parent)
        self.face_id = face_id
        self.path = None
        self.setAcceptDrops(True)
        self.setStyleSheet(f"background: {SCENE_BG}; border: 1px solid {BORDER}; border-radius: 4px;")
        
        lay = QHBoxLayout(self)
        lay.setContentsMargins(6, 6, 6, 6)
        lay.setSpacing(8)
        
        self.lbl_name = QLabel(face_name)
        self.lbl_name.setStyleSheet(f"color: {TEXT_DIM}; font-size: 11px; font-weight: bold; border: none; font-family: 'Segoe UI';")
        self.lbl_name.setFixedWidth(30)
        lay.addWidget(self.lbl_name)
        
        self.lbl_path = QLabel("لم يتم التحديد")
        self.lbl_path.setStyleSheet(f"color: {TEXT_FAINT}; font-size: 10px; border: none; font-family: 'Segoe UI';")
        lay.addWidget(self.lbl_path, 1)
        
        self.btn_browse = QPushButton("...")
        self.btn_browse.setFixedSize(24, 24)
        self.btn_browse.setStyleSheet(f"background: {BORDER}; color: {TEXT}; border: none; border-radius: 4px; font-weight: bold;")
        self.btn_browse.setCursor(Qt.PointingHandCursor)
        self.btn_browse.clicked.connect(self._browse)
        lay.addWidget(self.btn_browse)
        
    def _browse(self):
        file, _ = QFileDialog.getOpenFileName(self, "اختر صورة", "", "Images (*.png *.jpg *.jpeg *.bmp)")
        if file:
            self._set_image(file)
            
    def _set_image(self, path):
        self.path = path
        import os
        self.lbl_path.setText(os.path.basename(path))
        self.image_changed.emit(self.face_id, path)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if urls and urls[0].isLocalFile():
                ext = urls[0].toLocalFile().lower().split('.')[-1]
                if ext in ['png', 'jpg', 'jpeg', 'bmp']:
                    event.acceptProposedAction()
                    return
        event.ignore()

    def dropEvent(self, event: QDropEvent):
        urls = event.mimeData().urls()
        if urls and urls[0].isLocalFile():
            self._set_image(urls[0].toLocalFile())

# =========================================================
# Scene UI
# =========================================================

class SceneUI(QSplitter):

    def __init__(self, parent=None):
        super().__init__(Qt.Horizontal, parent)

        self.ide = parent
        self.selected_scene_obj = None
        self._ignore_transform_updates = False

        self.setObjectName("SceneUI")
        self.setHandleWidth(1)

        self._build_ui()

    # -----------------------------------------------------
    # Main UI
    # -----------------------------------------------------

    def _build_ui(self):

        # =================================================
        # Viewport
        # =================================================

        self.scene_wrap = QFrame()
        self.scene_wrap.setObjectName("sceneViewportCard")

        self.scene_wrap.setStyleSheet(f"""
            QFrame#sceneViewportCard {{
                background: {SCENE_BG};
                border: 1px solid {BORDER};
                border-radius: 7px;
            }}
        """)

        scene_layout = QVBoxLayout(self.scene_wrap)
        scene_layout.setContentsMargins(0, 0, 0, 0)
        scene_layout.setSpacing(0)

        # =================================================
        # Scene Header
        # =================================================

        header = QFrame()
        header.setObjectName("sceneHeader")
        header.setFixedHeight(42)

        header.setStyleSheet(f"""
            QFrame#sceneHeader {{
                background: {HEADER_BG};
                border: none;
                border-bottom: 1px solid {BORDER};
                border-top-left-radius: 7px;
                border-top-right-radius: 7px;
            }}
        """)

        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(12, 0, 12, 0)
        header_layout.setSpacing(6)

        # عنوان المشهد

        title = QLabel("عرض المشهد")
        title.setStyleSheet(f"""
            QLabel {{
                color: {TEXT};
                font-family: "Segoe UI";
                font-size: 12px;
                font-weight: 600;
                background: transparent;
                border: none;
            }}
        """)

        header_layout.addWidget(title)

        header_layout.addStretch()

        # =================================================
        # أدوات المشهد
        # =================================================

        tools = QFrame()
        tools.setStyleSheet("background: transparent; border: none;")

        tools_layout = QHBoxLayout(tools)
        tools_layout.setContentsMargins(0, 0, 0, 0)
        tools_layout.setSpacing(2)

        self.btn_gizmo_sel = self._create_scene_tool(
            "select",
            "تحديد",
            "Q"
        )

        self.btn_gizmo_pos = self._create_scene_tool(
            "move",
            "تحريك",
            "W"
        )

        self.btn_gizmo_rot = self._create_scene_tool(
            "rotate",
            "دوران",
            "E"
        )

        self.btn_gizmo_scl = self._create_scene_tool(
            "scale",
            "تكبير",
            "R"
        )

        self.btn_gizmo_pos.setChecked(True)
        
        self.btn_gizmo_sel.clicked.connect(lambda: self._set_gizmo_mode("sel"))
        self.btn_gizmo_pos.clicked.connect(lambda: self._set_gizmo_mode("pos"))
        self.btn_gizmo_rot.clicked.connect(lambda: self._set_gizmo_mode("rot"))
        self.btn_gizmo_scl.clicked.connect(lambda: self._set_gizmo_mode("scl"))

        self.btn_sculpt_mode = self._create_scene_tool(
            "brush",
            "نحت التضاريس",
            "B"
        )
        self.btn_sculpt_mode.hide()
        
        # Sculpt menu popup
        self.sculpt_menu = QMenu(self.btn_sculpt_mode)
        self.sculpt_menu.setStyleSheet(f"""
            QMenu {{
                background: {SCENE_BG};
                color: {TEXT};
                border: 1px solid {BORDER};
                border-radius: 5px;
            }}
        """)
        from PyQt5.QtWidgets import QWidgetAction
        sculpt_widget = QWidget()
        sculpt_lay = QVBoxLayout(sculpt_widget)
        sculpt_lay.setContentsMargins(10, 10, 10, 10)
        
        lbl_rad = QLabel("حجم الفرشاة:")
        sp_rad = QDoubleSpinBox()
        sp_rad.setRange(0.1, 50.0); sp_rad.setValue(2.0)
        sp_rad.valueChanged.connect(lambda v: setattr(self.scene_viewer, 'brush_radius', v))
        
        lbl_str = QLabel("قوة الفرشاة:")
        sp_str = QDoubleSpinBox()
        sp_str.setRange(0.01, 10.0); sp_str.setValue(0.5)
        sp_str.valueChanged.connect(lambda v: setattr(self.scene_viewer, 'brush_strength', v))
        
        sculpt_lay.addWidget(lbl_rad); sculpt_lay.addWidget(sp_rad)
        sculpt_lay.addWidget(lbl_str); sculpt_lay.addWidget(sp_str)
        
        wa = QWidgetAction(self.btn_sculpt_mode)
        wa.setDefaultWidget(sculpt_widget)
        self.sculpt_menu.addAction(wa)
        
        def _on_sculpt_clicked():
            self._set_gizmo_mode("sculpt")
            self.sculpt_menu.exec_(self.btn_sculpt_mode.mapToGlobal(QPoint(0, self.btn_sculpt_mode.height())))
            
        self.btn_sculpt_mode.clicked.connect(_on_sculpt_clicked)

        tools_layout.addWidget(self.btn_gizmo_sel)
        tools_layout.addWidget(self.btn_gizmo_pos)
        tools_layout.addWidget(self.btn_gizmo_rot)
        tools_layout.addWidget(self.btn_gizmo_scl)
        tools_layout.addWidget(self.btn_sculpt_mode)

        header_layout.addWidget(tools)

        header_layout.addStretch()

        # =================================================
        # زر خيارات العرض
        # =================================================

        self.view_button = QToolButton()
        self.view_button.setText("⋮")
        self.view_button.setFixedSize(28, 28)
        self.view_button.setCursor(Qt.PointingHandCursor)

        self.view_button.setStyleSheet(f"""
            QToolButton {{
                background: transparent;
                color: {TEXT_DIM};
                border: 1px solid transparent;
                border-radius: 5px;
                font-size: 18px;
            }}

            QToolButton:hover {{
                background: #182334;
                color: {TEXT};
            }}
        """)

        menu = QMenu(self.view_button)

        menu.setStyleSheet(f"""
            QMenu {{
                background: #111B29;
                color: {TEXT};
                border: 1px solid {BORDER};
                padding: 5px;
            }}

            QMenu::item {{
                padding: 7px 22px;
                border-radius: 4px;
            }}

            QMenu::item:selected {{
                background: {PURPLE_BG};
                color: white;
            }}
        """)

        menu.addAction("منظور Perspective")
        menu.addAction("عرض أمامي")
        menu.addAction("عرض جانبي")
        menu.addAction("عرض علوي")

        self.view_button.setMenu(menu)

        self.btn_render_mode = QPushButton("طريقة العرض: المحرر")
        self.btn_render_mode.setStyleSheet(f"""
            QPushButton {{
                background: {BLUE};
                color: white;
                border: none;
                border-radius: 4px;
                padding: 4px 10px;
                font-family: 'Segoe UI';
                font-weight: bold;
                font-size: 11px;
            }}
            QPushButton:hover {{ background: #5E6A77; }}
        """)
        self.btn_render_mode.setCursor(Qt.PointingHandCursor)
        self.btn_render_mode.clicked.connect(self._toggle_render_mode)

        header_layout.addWidget(self.btn_render_mode)
        header_layout.addWidget(self.view_button)
        
        # تعطيل زر طريقة العرض مؤقتا بناء على طلب المستخدم
        self.btn_render_mode.hide()

        scene_layout.addWidget(header)

        # =================================================
        # Viewport
        # =================================================

        self.scene_viewer = SceneViewerWidget(self)

        self.scene_viewer.setStyleSheet("""
            background: #080E15;
            border: none;
        """)

        scene_layout.addWidget(self.scene_viewer, 1)

        # =================================================
        # Floating notification
        # =================================================

        self.notif_label = QLabel(self.scene_viewer)

        self.notif_label.setStyleSheet(f"""
            QLabel {{
                background: rgba(14, 22, 34, 235);
                color: {TEXT};
                border: 1px solid {PURPLE};
                border-radius: 7px;
                padding: 7px 15px;
                font-family: "Segoe UI";
                font-size: 11px;
                font-weight: 600;
            }}
        """)

        self.notif_label.hide()

        self.notif_timer = QTimer(self)
        self.notif_timer.setSingleShot(True)
        self.notif_timer.timeout.connect(
            self.notif_label.hide
        )

        self.addWidget(self.scene_wrap)

        # =================================================
        # Scene hierarchy
        # =================================================

        self.scene_sidebar_wrap = QFrame()
        self.scene_sidebar_wrap.setObjectName("sceneHierarchy")

        self.scene_sidebar_wrap.setStyleSheet(f"""
            QFrame#sceneHierarchy {{
                background: {PANEL_BG};
                border: 1px solid {BORDER};
                border-radius: 7px;
            }}
        """)

        hierarchy_layout = QVBoxLayout(
            self.scene_sidebar_wrap
        )

        hierarchy_layout.setContentsMargins(
            0, 0, 0, 0
        )

        hierarchy_layout.setSpacing(0)

        # =================================================
        # Hierarchy header
        # =================================================

        hierarchy_header = QFrame()
        hierarchy_header.setFixedHeight(42)

        hierarchy_header.setStyleSheet(f"""
            QFrame {{
                background: {HEADER_BG};
                border: none;
                border-bottom: 1px solid {BORDER};
                border-top-left-radius: 7px;
                border-top-right-radius: 7px;
            }}
        """)

        hierarchy_header_layout = QHBoxLayout(
            hierarchy_header
        )

        hierarchy_header_layout.setContentsMargins(
            12, 0, 8, 0
        )

        hierarchy_title = QLabel("العناصر")

        hierarchy_title.setStyleSheet(f"""
            QLabel {{
                color: {TEXT};
                font-family: "Segoe UI";
                font-size: 12px;
                font-weight: 600;
                background: transparent;
                border: none;
            }}
        """)

        hierarchy_header_layout.addWidget(
            hierarchy_title
        )

        hierarchy_header_layout.addStretch()

        refresh_button = QToolButton()
        refresh_button.setText("↻")
        refresh_button.setFixedSize(28, 28)

        refresh_button.setStyleSheet(f"""
            QToolButton {{
                background: transparent;
                color: {TEXT_DIM};
                border: none;
                font-size: 17px;
            }}

            QToolButton:hover {{
                background: #182334;
                color: {TEXT};
                border-radius: 5px;
            }}
        """)

        hierarchy_header_layout.addWidget(
            refresh_button
        )

        add_button = QToolButton()
        add_button.setText("+")
        add_button.setFixedSize(28, 28)

        add_button.setStyleSheet(f"""
            QToolButton {{
                background: transparent;
                color: {TEXT_DIM};
                border: none;
                font-size: 18px;
            }}

            QToolButton:hover {{
                background: {PURPLE_BG};
                color: {PURPLE_HOVER};
                border-radius: 5px;
            }}
        """)

        hierarchy_header_layout.addWidget(
            add_button
        )

        hierarchy_layout.addWidget(
            hierarchy_header
        )

        # =================================================
        # Search
        # =================================================

        search_container = QFrame()
        search_container.setStyleSheet(
            "background: transparent; border: none;"
        )

        search_layout = QHBoxLayout(
            search_container
        )

        search_layout.setContentsMargins(
            10, 10, 10, 8
        )

        self.scene_search = QLineEdit()
        self.scene_search.setPlaceholderText(
            "بحث في العناصر..."
        )

        self.scene_search.setClearButtonEnabled(True)

        self.scene_search.setStyleSheet(f"""
            QLineEdit {{
                background: #0A111B;
                color: {TEXT};
                border: 1px solid {BORDER};
                border-radius: 5px;
                padding: 7px 9px;
                font-family: "Segoe UI";
                font-size: 11px;
            }}

            QLineEdit:hover {{
                border-color: {BORDER_LIGHT};
            }}

            QLineEdit:focus {{
                border-color: {PURPLE};
            }}
        """)

        search_layout.addWidget(
            self.scene_search
        )

        hierarchy_layout.addWidget(
            search_container
        )

        # =================================================
        # Tree
        # =================================================

        self.scene_sidebar_list = QTreeWidget()

        self.scene_sidebar_list.setHeaderHidden(True)
        self.scene_sidebar_list.setIndentation(17)
        self.scene_sidebar_list.setAnimated(True)

        self.scene_sidebar_list.setStyleSheet(f"""
            QTreeWidget {{
                background: transparent;
                border: none;
                outline: none;
                color: {TEXT_DIM};
                font-family: "Segoe UI";
                font-size: 11px;
            }}

            QTreeWidget::item {{
                height: 31px;
                padding: 0px 5px;
                margin: 1px 6px;
                border-radius: 5px;
            }}

            QTreeWidget::item:hover {{
                background: #162233;
                color: {TEXT};
            }}

            QTreeWidget::item:selected {{
                background: {PURPLE_BG};
                color: #FFFFFF;
                border-left: 2px solid {PURPLE};
            }}

            QTreeWidget::branch {{
                background: transparent;
            }}
        """)

        self.scene_sidebar_list.itemClicked.connect(
            self._on_scene_element_clicked
        )
        
        self.scene_sidebar_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.scene_sidebar_list.customContextMenuRequested.connect(self._show_tree_context_menu)
        self.scene_sidebar_list.customContextMenuRequested.connect(self._show_scene_context_menu)

        hierarchy_layout.addWidget(
            self.scene_sidebar_list,
            1
        )
        
        # =================================================
        # Properties Section
        # =================================================
        from PyQt5.QtWidgets import QComboBox

        props_wrap = QWidget()
        props_wrap.setStyleSheet(f"background: {HEADER_BG}; border-top: 1px solid {BORDER}; border-bottom-left-radius: 7px; border-bottom-right-radius: 7px;")
        props_lay = QVBoxLayout(props_wrap)
        props_lay.setContentsMargins(16, 16, 16, 16)
        props_lay.setSpacing(12)

        lbl_props = QLabel("الخصائص")
        lbl_props.setStyleSheet(f"color:{TEXT_DIM}; font-size:11px; font-weight:bold; border:none; font-family: 'Segoe UI';")
        props_lay.addWidget(lbl_props)

        self.lbl_selected_name = QLabel("لا يوجد تحديد")
        self.lbl_selected_name.setStyleSheet(f"color:{PURPLE}; font-size:12px; font-weight:bold; border:none; font-family: 'Segoe UI';")
        props_lay.addWidget(self.lbl_selected_name)

        lbl_transform = QLabel("تحويل")
        lbl_transform.setStyleSheet(f"color:{TEXT}; font-size:11px; font-weight:bold; margin-top:8px; border:none; font-family: 'Segoe UI';")
        props_lay.addWidget(lbl_transform)

        from PyQt5.QtCore import QEvent
        class NoUndoLineEdit(QLineEdit):
            def event(self, e):
                if e.type() == QEvent.ShortcutOverride:
                    if e.modifiers() & Qt.ControlModifier and e.key() in (Qt.Key_Z, Qt.Key_Y):
                        e.ignore()
                        return False
                return super().event(e)
                
        def _make_xyz_input(label):
            w = QWidget()
            w.setStyleSheet("border:none;")
            l = QHBoxLayout(w)
            l.setContentsMargins(0,0,0,0)
            l.setSpacing(8)
            lbl = QLabel(label)
            lbl.setStyleSheet(f"color:{TEXT_DIM}; font-size:10px; font-family: 'Segoe UI';")
            lbl.setFixedWidth(40)
            l.addWidget(lbl)
            
            spins = []
            inputs_widget = QWidget()
            il = QHBoxLayout(inputs_widget)
            il.setContentsMargins(0,0,0,0)
            il.setSpacing(6)
            
            for ax, col in zip(('X', 'Y', 'Z'), (RED, GREEN, BLUE)):
                box = QWidget()
                box.setStyleSheet(f"background:{SCENE_BG}; border:1px solid {BORDER}; border-radius:4px;")
                bl = QHBoxLayout(box)
                bl.setContentsMargins(6,2,6,2)
                bl.setSpacing(4)
                
                al = QLabel(ax)
                al.setStyleSheet(f"color:{col}; font-size:10px; font-weight:bold; border:none; background:transparent; font-family: 'Segoe UI';")
                bl.addWidget(al)
                
                sp = NoUndoLineEdit("0.00")
                sp.setStyleSheet(f"background:transparent; border:none; color:{TEXT}; font-size:11px; font-family: 'Segoe UI';")
                bl.addWidget(sp)
                spins.append(sp)
                il.addWidget(box)
            
            l.addWidget(inputs_widget)
            return w, spins

        pos_w, self.spins_pos = _make_xyz_input("الموقع")
        props_lay.addWidget(pos_w)
        rot_w, self.spins_rot = _make_xyz_input("الدوران")
        props_lay.addWidget(rot_w)
        scl_w, self.spins_scl = _make_xyz_input("المقياس")
        self.scl_w = scl_w
        props_lay.addWidget(scl_w)

        # Connect spins
        def _on_transform_edit():
            if not getattr(self, 'selected_scene_obj', None): return
            if getattr(self, '_ignore_transform_updates', False): return
            try:
                px, py, pz = float(self.spins_pos[0].text()), float(self.spins_pos[1].text()), float(self.spins_pos[2].text())
                rx, ry, rz = float(self.spins_rot[0].text()), float(self.spins_rot[1].text()), float(self.spins_rot[2].text())
                sx, sy, sz = float(self.spins_scl[0].text()), float(self.spins_scl[1].text()), float(self.spins_scl[2].text())
                if hasattr(self, 'scene_viewer'):
                    self.scene_viewer.set_transform(self.selected_scene_obj, px, py, pz, rx, ry, rz, sx, sy, sz)
            except ValueError:
                pass

        for sp in self.spins_pos + self.spins_rot + self.spins_scl:
            sp.editingFinished.connect(_on_transform_edit)

        self.obj_props_widget = QWidget()
        obj_lay = QVBoxLayout(self.obj_props_widget)
        obj_lay.setContentsMargins(0, 0, 0, 0)
        obj_lay.setSpacing(12)

        self.dyn_widgets = {}
        
        def _make_prop(key, label_text, widget, is_layout=False, parent_lay=None):
            if parent_lay is None:
                parent_lay = obj_lay
            w = QWidget()
            l = QVBoxLayout(w)
            l.setContentsMargins(0,0,0,0)
            l.setSpacing(4)
            lbl = QLabel(label_text)
            lbl.setStyleSheet(f"color:{TEXT_DIM}; font-size:10px; font-family: 'Segoe UI';")
            l.addWidget(lbl)
            if is_layout:
                l.addLayout(widget)
            else:
                l.addWidget(widget)
            parent_lay.addWidget(w)
            self.dyn_widgets[key] = w
            return widget
            
        # Label & Name
        self.le_label = QLineEdit("")
        self.le_label.setStyleSheet(f"background:transparent; color:{TEXT_DIM}; border:none; font-size:11px; font-family: 'Segoe UI';")
        self.le_label.setReadOnly(True)
        _make_prop('label', "معرف العنصر (Label)", self.le_label)

        self.le_name = NoUndoLineEdit("")
        self.le_name.setStyleSheet(f"background:{SCENE_BG}; color:{TEXT}; border:1px solid {BORDER}; border-radius:4px; padding:6px; font-size:11px; font-family: 'Segoe UI';")
        _make_prop('name', "الاسم", self.le_name)

        # Color
        self.btn_obj_color = QPushButton("اختيار اللون")
        self.btn_obj_color.setStyleSheet(f"background:{SCENE_BG}; color:{TEXT}; border:1px solid {BORDER}; border-radius:4px; padding:6px; font-size:11px; font-family: 'Segoe UI';")
        self.btn_obj_color.setCursor(Qt.PointingHandCursor)
        _make_prop('color', "اللون", self.btn_obj_color)
        
        # Material
        mat_w = QWidget()
        mat_l = QVBoxLayout(mat_w)
        mat_l.setContentsMargins(0,0,0,0)
        mat_l.setSpacing(4)
        self.mat_fields = {}
        for m_key in ["base", "normal", "ac", "metallic", "roughness", "scale_x", "scale_y"]:
            hl = QHBoxLayout()
            le = NoUndoLineEdit("")
            le.setPlaceholderText(m_key)
            le.setStyleSheet(f"background:{SCENE_BG}; color:{TEXT}; border:1px solid {BORDER}; border-radius:4px; padding:6px; font-size:10px; font-family: 'Segoe UI';")
            
            is_file = m_key in ["base", "normal", "ac", "metallic", "roughness"]
            if is_file:
                le.setReadOnly(True)
                btn = QPushButton("...")
                btn.setStyleSheet(f"background:{PURPLE}; color:white; border:none; border-radius:4px; padding:6px; font-weight:bold;")
                btn.setCursor(Qt.PointingHandCursor)
                
                btn_del = QPushButton("X")
                btn_del.setStyleSheet(f"background:#900; color:white; border:none; border-radius:4px; padding:6px; font-weight:bold;")
                btn_del.setCursor(Qt.PointingHandCursor)
                btn_del.setFixedWidth(24)
                
                hl.addWidget(le)
                hl.addWidget(btn)
                hl.addWidget(btn_del)
                self.mat_fields[m_key] = le
                
                btn.clicked.connect(lambda checked, k=m_key: self._on_dyn_mat_browse(k))
                btn_del.clicked.connect(lambda checked, k=m_key: self._on_dyn_mat_clear(k))
            else:
                from PyQt5.QtGui import QDoubleValidator
                validator = QDoubleValidator()
                le.setValidator(validator)
                if not le.text(): le.setText("1")
                le.setReadOnly(False)
                hl.addWidget(le)
                self.mat_fields[m_key] = le
                le.textChanged.connect(lambda txt, k=m_key: self._on_dyn_mat_text_changed(k, txt))
                
            mat_l.addLayout(hl)
        _make_prop('material', "الخامة (Material)", mat_w)
        
        # Collision & Physics
        from PyQt5.QtWidgets import QCheckBox
        self.chk_show_collision = QCheckBox("رؤية صدام")
        self.chk_show_collision.setStyleSheet(f"color:{TEXT}; font-size:11px; font-family: 'Segoe UI';")
        _make_prop('show_collision', "رؤية صندوق التصادم", self.chk_show_collision)
        
        self.chk_gravity = QCheckBox("جاذبية مفعلة")
        self.chk_gravity.setStyleSheet(f"color:{TEXT}; font-size:11px; font-family: 'Segoe UI';")
        _make_prop('gravity', "الجاذبية", self.chk_gravity)
        
        self.chk_bounciness = QCheckBox("صدام مفعل")
        self.chk_bounciness.setStyleSheet(f"color:{TEXT}; font-size:11px; font-family: 'Segoe UI';")
        _make_prop('bounciness', "صدام (الارتداد)", self.chk_bounciness)
        
        # Filepath
        fp_lay = QHBoxLayout()
        fp_lay.setContentsMargins(0,0,0,0)
        self.le_filepath = NoUndoLineEdit("")
        self.le_filepath.setStyleSheet(f"background:{SCENE_BG}; color:{TEXT}; border:1px solid {BORDER}; border-radius:4px; padding:6px; font-size:11px; font-family: 'Segoe UI';")
        self.le_filepath.setReadOnly(True)
        self.btn_browse = QPushButton("...")
        self.btn_browse.setStyleSheet(f"background:{PURPLE}; color:white; border:none; border-radius:4px; padding:6px; font-weight:bold;")
        self.btn_browse.setCursor(Qt.PointingHandCursor)
        
        self.btn_filepath_del = QPushButton("X")
        self.btn_filepath_del.setStyleSheet(f"background:#900; color:white; border:none; border-radius:4px; padding:6px; font-weight:bold;")
        self.btn_filepath_del.setCursor(Qt.PointingHandCursor)
        self.btn_filepath_del.setFixedWidth(24)
        
        fp_lay.addWidget(self.le_filepath)
        fp_lay.addWidget(self.btn_browse)
        fp_lay.addWidget(self.btn_filepath_del)
        _make_prop('filepath', "مسار الملف", fp_lay, is_layout=True)
        
        # Connect signals for these properties
        self.le_name.editingFinished.connect(self._on_dyn_name_changed)
        self.btn_obj_color.clicked.connect(self._on_dyn_color_clicked)
        self.chk_show_collision.toggled.connect(self._on_dyn_prop_changed)
        self.chk_gravity.toggled.connect(self._on_dyn_prop_changed)
        self.chk_bounciness.toggled.connect(self._on_dyn_prop_changed)
        self.btn_browse.clicked.connect(self._on_dyn_browse_clicked)
        self.btn_filepath_del.clicked.connect(self._on_dyn_filepath_clear)

        props_lay.addWidget(self.obj_props_widget)
        self.obj_props_widget.hide()

        # Camera Properties
        self.cam_props_widget = QWidget()
        from PyQt5.QtWidgets import QSlider, QShortcut
        from PyQt5.QtGui import QKeySequence

        # Undo / Redo Shortcuts
        QShortcut(QKeySequence("Ctrl+Z"), self).activated.connect(self.scene_viewer.undo)
        QShortcut(QKeySequence("Ctrl+Y"), self).activated.connect(self.scene_viewer.redo)

        def _make_slider(label_text, min_val, max_val, default_val, scale=1.0):
            w = QWidget()
            l = QVBoxLayout(w)
            l.setContentsMargins(0,0,0,0)
            l.setSpacing(4)
            
            header_lay = QHBoxLayout()
            lbl = QLabel(label_text)
            lbl.setStyleSheet(f"color:{TEXT_DIM}; font-size:10px; font-family: 'Segoe UI';")
            val_lbl = QLabel(str(default_val))
            val_lbl.setStyleSheet(f"color:{TEXT}; font-size:10px; font-weight:bold; font-family: 'Segoe UI';")
            header_lay.addWidget(lbl)
            header_lay.addStretch()
            header_lay.addWidget(val_lbl)
            l.addLayout(header_lay)
            
            slider = QSlider(Qt.Horizontal)
            slider.setMinimum(int(min_val * scale))
            slider.setMaximum(int(max_val * scale))
            slider.setValue(int(default_val * scale))
            slider.setStyleSheet(f"""
                QSlider::groove:horizontal {{
                    border: 1px solid {BORDER};
                    height: 4px;
                    background: {SCENE_BG};
                    border-radius: 2px;
                }}
                QSlider::handle:horizontal {{
                    background: {PURPLE};
                    border: 1px solid {PURPLE};
                    width: 12px;
                    margin: -5px 0;
                    border-radius: 6px;
                }}
            """)
            l.addWidget(slider)
            return w, slider, val_lbl, scale

        cam_lay = QVBoxLayout(self.cam_props_widget)
        cam_lay.setContentsMargins(0, 0, 0, 0)
        cam_lay.setSpacing(12)

        self.fov_w, self.fov_slider, self.fov_val, self.fov_scale = _make_slider("مجال الرؤية (FOV)", 1, 179, 60.0, 1.0)
        cam_lay.addWidget(self.fov_w)
        
        self.near_w, self.near_slider, self.near_val, self.near_scale = _make_slider("القطع القريب (Near Clip)", 0.1, 100.0, 0.1, 10.0)
        cam_lay.addWidget(self.near_w)
        
        self.far_w, self.far_slider, self.far_val, self.far_scale = _make_slider("القطع البعيد (Far Clip)", 100.0, 10000.0, 2000.0, 1.0)
        cam_lay.addWidget(self.far_w)

        self.fov_slider.sliderPressed.connect(self._on_cam_slider_pressed)
        self.near_slider.sliderPressed.connect(self._on_cam_slider_pressed)
        self.far_slider.sliderPressed.connect(self._on_cam_slider_pressed)

        self.fov_slider.valueChanged.connect(self._on_cam_slider_changed)
        self.near_slider.valueChanged.connect(self._on_cam_slider_changed)
        self.far_slider.valueChanged.connect(self._on_cam_slider_changed)

        props_lay.addWidget(self.cam_props_widget)
        self.cam_props_widget.setEnabled(False) # As requested, disabled for now
        self.cam_props_widget.hide()

        # Scene Properties
        self.scene_props_widget = QWidget()
        scene_lay = QVBoxLayout(self.scene_props_widget)
        scene_lay.setContentsMargins(0, 0, 0, 0)
        scene_lay.setSpacing(12)

        lbl_sky = QLabel("لون السماء")
        lbl_sky.setStyleSheet(f"color:{{TEXT_DIM}}; font-size:10px; margin-top:8px; border:none; font-family: 'Segoe UI';")
        scene_lay.addWidget(lbl_sky)
        
        self.btn_sky_color = QPushButton("اختيار لون السماء")
        self.btn_sky_color.setStyleSheet(f"background:{{SCENE_BG}}; color:{{TEXT}}; border:1px solid {{BORDER}}; border-radius:4px; padding:6px; font-size:11px; font-family: 'Segoe UI';")
        self.btn_sky_color.setCursor(Qt.PointingHandCursor)
        scene_lay.addWidget(self.btn_sky_color)

        lbl_cubemap = QLabel("مكعب السماء (Cubemap)")
        lbl_cubemap.setStyleSheet(f"color:{{TEXT_DIM}}; font-size:10px; margin-top:8px; border:none; font-family: 'Segoe UI';")
        scene_lay.addWidget(lbl_cubemap)
        
        self.cubemap_faces = {}
        faces = [
            ("right", "يمين"),
            ("left", "يسار"),
            ("top", "أعلى"),
            ("bottom", "أسفل"),
            ("front", "أمام"),
            ("back", "خلف")
        ]
        
        self.cubemap_slots = []
        for face_id, face_name in faces:
            slot = CubemapSlotWidget(face_id, face_name)
            slot.image_changed.connect(self._on_cubemap_slot_changed)
            scene_lay.addWidget(slot)
            self.cubemap_slots.append(slot)

        self.btn_sky_color.clicked.connect(self._choose_sky_color)

        self.btn_remove_cubemap = QPushButton("إزالة Cubemap")
        self.btn_remove_cubemap.setStyleSheet(f"background:{{RED}}; color:{{TEXT}}; border:none; border-radius:4px; padding:6px; font-size:11px; font-weight:bold; font-family: 'Segoe UI';")
        self.btn_remove_cubemap.setCursor(Qt.PointingHandCursor)
        self.btn_remove_cubemap.hide()
        self.btn_remove_cubemap.clicked.connect(self._remove_cubemap)
        scene_lay.addWidget(self.btn_remove_cubemap)

        props_lay.addWidget(self.scene_props_widget)
        self.scene_props_widget.hide()

        # =================================================
        # Light Properties Panel
        # =================================================
        from PyQt5.QtWidgets import QSlider

        self.light_props_widget = QWidget()
        light_lay = QVBoxLayout(self.light_props_widget)
        light_lay.setContentsMargins(0, 0, 0, 0)
        light_lay.setSpacing(12)

        # --- نوع الضوء ---
        from PyQt5.QtWidgets import QComboBox
        lbl_ltype = QLabel("نوع الضوء (Type)")
        lbl_ltype.setStyleSheet(f"color:{TEXT_DIM}; font-size:10px; font-family: 'Segoe UI';")
        light_lay.addWidget(lbl_ltype)

        self.cb_light_type = QComboBox()
        self.cb_light_type.addItems(["ضوء_موجه", "ضوء_نقطي", "ضوء_بقعي"])
        self.cb_light_type.setStyleSheet(f"background:{SCENE_BG}; color:{TEXT}; border: 1px solid {BORDER}; border-radius:4px; padding: 4px;")
        light_lay.addWidget(self.cb_light_type)

        def _on_ltype_changed(text):
            obj = self._get_selected_light_obj()
            if obj:
                self.scene_viewer.push_undo_state()
                obj.light_type = text
                self._on_scene_transform_update(obj)
                self.scene_viewer.update()
                self._update_kh_code()
        
        self.cb_light_type.currentTextChanged.connect(_on_ltype_changed)

        # --- لون الضوء ---
        lbl_lcolor = QLabel("لون الضوء")
        lbl_lcolor.setStyleSheet(f"color:{TEXT_DIM}; font-size:10px; font-family: 'Segoe UI';")
        light_lay.addWidget(lbl_lcolor)

        self.btn_light_color = QPushButton("اختيار لون الضوء")
        self.btn_light_color.setStyleSheet(
            f"background: rgb(255,242,102); color: #111; border: 1px solid {BORDER}; "
            f"border-radius:4px; padding:6px; font-size:11px; font-family: 'Segoe UI'; font-weight:bold;"
        )
        self.btn_light_color.setCursor(Qt.PointingHandCursor)
        self.btn_light_color.clicked.connect(self._on_light_color_clicked)
        light_lay.addWidget(self.btn_light_color)

        # --- شدة الضوء ---
        def _make_light_slider(label_text, min_v, max_v, default_v, scale=100.0):
            w = QWidget()
            l2 = QVBoxLayout(w)
            l2.setContentsMargins(0, 0, 0, 0)
            l2.setSpacing(4)
            hl = QHBoxLayout()
            lbl2 = QLabel(label_text)
            lbl2.setStyleSheet(f"color:{TEXT_DIM}; font-size:10px; font-family: 'Segoe UI';")
            val_lbl2 = QLabel(str(default_v))
            val_lbl2.setStyleSheet(f"color:{TEXT}; font-size:10px; font-weight:bold; font-family: 'Segoe UI';")
            hl.addWidget(lbl2)
            hl.addStretch()
            hl.addWidget(val_lbl2)
            l2.addLayout(hl)
            slider2 = QSlider(Qt.Horizontal)
            slider2.setMinimum(int(min_v * scale))
            slider2.setMaximum(int(max_v * scale))
            slider2.setValue(int(default_v * scale))
            slider2.setStyleSheet(f"""
                QSlider::groove:horizontal {{
                    border: 1px solid {BORDER}; height: 4px;
                    background: {SCENE_BG}; border-radius: 2px;
                }}
                QSlider::handle:horizontal {{
                    background: {YELLOW}; border: 1px solid {YELLOW};
                    width: 12px; margin: -5px 0; border-radius: 6px;
                }}
            """)
            l2.addWidget(slider2)
            return w, slider2, val_lbl2, scale

        self.lint_w, self.lint_slider, self.lint_val, self.lint_scale = _make_light_slider(
            "شدة الضوء (Intensity)", 0.0, 5.0, 1.0, 100.0
        )
        light_lay.addWidget(self.lint_w)

        def _on_lint_changed(v):
            real = v / self.lint_scale
            self.lint_val.setText(f"{real:.2f}")
            obj = self._get_selected_light_obj()
            if obj:
                self.scene_viewer.push_undo_state()
                obj.light_intensity = real
                self.scene_viewer.update()
                self._update_kh_code()

        self.lint_slider.valueChanged.connect(_on_lint_changed)

        # --- اتجاه الضوء XYZ ---
        self.lbl_ldir = QLabel("اتجاه الضوء (Direction)")
        self.lbl_ldir.setStyleSheet(f"color:{TEXT_DIM}; font-size:10px; font-family: 'Segoe UI';")
        light_lay.addWidget(self.lbl_ldir)

        self.dir_widget = QWidget()
        dir_lay = QHBoxLayout(self.dir_widget)
        dir_lay.setContentsMargins(0, 0, 0, 0)
        dir_lay.setSpacing(6)

        self.spins_ldir = []
        for ax, col, default in zip(('X', 'Y', 'Z'), (RED, GREEN, BLUE), (-0.5, -1.0, -0.3)):
            box = QWidget()
            box.setStyleSheet(f"background:{SCENE_BG}; border:1px solid {BORDER}; border-radius:4px;")
            bl = QHBoxLayout(box)
            bl.setContentsMargins(6, 2, 6, 2)
            bl.setSpacing(4)
            al = QLabel(ax)
            al.setStyleSheet(f"color:{col}; font-size:10px; font-weight:bold; border:none; background:transparent; font-family: 'Segoe UI';")
            bl.addWidget(al)
            sp = QLineEdit(str(default))
            sp.setStyleSheet(f"background:transparent; border:none; color:{TEXT}; font-size:11px; font-family: 'Segoe UI';")
            bl.addWidget(sp)
            self.spins_ldir.append(sp)
            dir_lay.addWidget(box)

        light_lay.addWidget(self.dir_widget)

        def _on_ldir_changed():
            obj = self._get_selected_light_obj()
            if not obj: return
            try:
                dx = float(self.spins_ldir[0].text())
                dy = float(self.spins_ldir[1].text())
                dz = float(self.spins_ldir[2].text())
                self.scene_viewer.push_undo_state()
                obj.light_direction = [dx, dy, dz]
                self.scene_viewer.update()
                self._update_kh_code()
            except ValueError:
                pass

        for sp in self.spins_ldir:
            sp.editingFinished.connect(_on_ldir_changed)

        # --- زاوية البقعة ---
        self.spot_angle_w, self.spot_angle_slider, self.spot_angle_val, self.spot_angle_scale = _make_light_slider(
            "زاوية البقعة (Spot Angle)", 1.0, 90.0, 30.0, 10.0
        )
        light_lay.addWidget(self.spot_angle_w)

        def _on_sangle_changed(v):
            real = v / self.spot_angle_scale
            self.spot_angle_val.setText(f"{real:.1f}")
            obj = self._get_selected_light_obj()
            if obj:
                self.scene_viewer.push_undo_state()
                obj.spot_angle = real
                self.scene_viewer.update()
                self._update_kh_code()
        self.spot_angle_slider.valueChanged.connect(_on_sangle_changed)

        # --- حدة البقعة ---
        self.spot_sharp_w, self.spot_sharp_slider, self.spot_sharp_val, self.spot_sharp_scale = _make_light_slider(
            "حدة البقعة (Spot Sharpness)", 0.0, 128.0, 64.0, 1.0
        )
        light_lay.addWidget(self.spot_sharp_w)

        def _on_ssharp_changed(v):
            real = v / self.spot_sharp_scale
            self.spot_sharp_val.setText(f"{real:.1f}")
            obj = self._get_selected_light_obj()
            if obj:
                self.scene_viewer.push_undo_state()
                obj.spot_sharpness = real
                self.scene_viewer.update()
                self._update_kh_code()
        self.spot_sharp_slider.valueChanged.connect(_on_ssharp_changed)

        props_lay.addWidget(self.light_props_widget)
        self.light_props_widget.hide()

        # ==================================
        # UI Properties Widget
        # ==================================
        self.ui_props_widget = QWidget()
        ui_lay = QVBoxLayout(self.ui_props_widget)
        ui_lay.setContentsMargins(0, 0, 0, 0)
        ui_lay.setSpacing(12)
        
        # UI Text
        self.le_ui_text = QLineEdit()
        self.le_ui_text.setStyleSheet(f"background:{SCENE_BG}; color:{TEXT}; border: 1px solid {BORDER}; border-radius:4px; padding: 4px;")
        _make_prop("ui_text", "النص:", self.le_ui_text, parent_lay=ui_lay)
        self.le_ui_text.textChanged.connect(lambda t: self._on_ui_prop_changed('ui_text', t))
        
        # UI Pos X, Y
        ui_pos_lay = QHBoxLayout()
        self.sp_ui_x = QDoubleSpinBox(); self.sp_ui_x.setRange(-9999, 9999); self.sp_ui_x.setSingleStep(1)
        self.sp_ui_y = QDoubleSpinBox(); self.sp_ui_y.setRange(-9999, 9999); self.sp_ui_y.setSingleStep(1)
        for sp in (self.sp_ui_x, self.sp_ui_y):
            sp.setStyleSheet(self.spins_pos[0].styleSheet())
            sp.valueChanged.connect(lambda v, sp=sp: self._on_ui_prop_changed('pos_x' if sp==self.sp_ui_x else 'pos_y', v))
        ui_pos_lay.addWidget(self.sp_ui_x); ui_pos_lay.addWidget(self.sp_ui_y)
        _make_prop("ui_pos", "الموضع (X, Y):", ui_pos_lay, is_layout=True, parent_lay=ui_lay)
        
        # UI Size W, H
        ui_size_lay = QHBoxLayout()
        self.sp_ui_w = QDoubleSpinBox(); self.sp_ui_w.setRange(0, 9999); self.sp_ui_w.setSingleStep(1)
        self.sp_ui_h = QDoubleSpinBox(); self.sp_ui_h.setRange(0, 9999); self.sp_ui_h.setSingleStep(1)
        for sp in (self.sp_ui_w, self.sp_ui_h):
            sp.setStyleSheet(self.spins_pos[0].styleSheet())
            sp.valueChanged.connect(lambda v, sp=sp: self._on_ui_prop_changed('ui_width' if sp==self.sp_ui_w else 'ui_height', v))
        ui_size_lay.addWidget(self.sp_ui_w); ui_size_lay.addWidget(self.sp_ui_h)
        _make_prop("ui_size", "المقياس (W, H):", ui_size_lay, is_layout=True, parent_lay=ui_lay)
        
        # UI Full Screen
        self.chk_ui_full_screen = QCheckBox("تعبئة الشاشة بالكامل")
        self.chk_ui_full_screen.setStyleSheet(f"color:{TEXT}; font-family: 'Segoe UI'; font-size: 11px;")
        self.chk_ui_full_screen.toggled.connect(lambda v: self._on_ui_prop_changed('ui_full_screen', v))
        _make_prop("ui_full_screen", "", self.chk_ui_full_screen, parent_lay=ui_lay)
        
        # UI Font Size
        self.sp_ui_font_size = QSpinBox()
        self.sp_ui_font_size.setRange(1, 999)
        self.sp_ui_font_size.setStyleSheet(self.spins_pos[0].styleSheet())
        self.sp_ui_font_size.valueChanged.connect(lambda v: self._on_ui_prop_changed('ui_font_size', v))
        _make_prop("ui_font_size", "حجم الخط:", self.sp_ui_font_size, parent_lay=ui_lay)

        # UI Text Color
        self.btn_ui_text_color = QPushButton("اختيار لون النص")
        self.btn_ui_text_color.setStyleSheet(f"background: {SCENE_BG}; color: {TEXT}; border: 1px solid {BORDER}; border-radius:4px; padding:6px; font-size:11px; font-family: 'Segoe UI';")
        self.btn_ui_text_color.setCursor(Qt.PointingHandCursor)
        self.btn_ui_text_color.clicked.connect(self._on_ui_text_color_clicked)
        _make_prop("ui_text_color", "لون النص:", self.btn_ui_text_color, parent_lay=ui_lay)
        
        # UI Bg Color
        self.btn_ui_bg_color = QPushButton("اختيار لون الخلفية")
        self.btn_ui_bg_color.setStyleSheet(f"background: {SCENE_BG}; color: {TEXT}; border: 1px solid {BORDER}; border-radius:4px; padding:6px; font-size:11px; font-family: 'Segoe UI';")
        self.btn_ui_bg_color.setCursor(Qt.PointingHandCursor)
        self.btn_ui_bg_color.clicked.connect(self._on_ui_bg_color_clicked)
        _make_prop("ui_bg_color", "لون الخلفية:", self.btn_ui_bg_color, parent_lay=ui_lay)

        # UI Align Horizontal
        from PyQt5.QtWidgets import QComboBox
        self.cb_ui_align_h = QComboBox()
        self.cb_ui_align_h.addItems(["وسط", "يسار", "يمين"])
        self.cb_ui_align_h.setStyleSheet(f"background:{SCENE_BG}; color:{TEXT}; border: 1px solid {BORDER}; border-radius:4px; padding: 4px;")
        self.cb_ui_align_h.currentTextChanged.connect(lambda t: self._on_ui_prop_changed('ui_align_h', t))
        _make_prop("ui_align_h", "أفقي:", self.cb_ui_align_h, parent_lay=ui_lay)

        # UI Align Vertical
        self.cb_ui_align_v = QComboBox()
        self.cb_ui_align_v.addItems(["وسط", "فوق", "تحت"])
        self.cb_ui_align_v.setStyleSheet(f"background:{SCENE_BG}; color:{TEXT}; border: 1px solid {BORDER}; border-radius:4px; padding: 4px;")
        self.cb_ui_align_v.currentTextChanged.connect(lambda t: self._on_ui_prop_changed('ui_align_v', t))
        _make_prop("ui_align_v", "عمودي:", self.cb_ui_align_v, parent_lay=ui_lay)

        # UI Offset X, Y
        ui_offset_lay = QHBoxLayout()
        self.sp_ui_offset_x = QDoubleSpinBox(); self.sp_ui_offset_x.setRange(-9999, 9999); self.sp_ui_offset_x.setSingleStep(1)
        self.sp_ui_offset_y = QDoubleSpinBox(); self.sp_ui_offset_y.setRange(-9999, 9999); self.sp_ui_offset_y.setSingleStep(1)
        for sp in (self.sp_ui_offset_x, self.sp_ui_offset_y):
            sp.setStyleSheet(self.spins_pos[0].styleSheet())
            sp.setButtonSymbols(QAbstractSpinBox.NoButtons)
            sp.valueChanged.connect(lambda v, sp=sp: self._on_ui_prop_changed('ui_offset_x' if sp==self.sp_ui_offset_x else 'ui_offset_y', v))
        ui_offset_lay.addWidget(self.sp_ui_offset_x); ui_offset_lay.addWidget(self.sp_ui_offset_y)
        _make_prop("ui_offset", "الإزاحة (X, Y):", ui_offset_lay, is_layout=True, parent_lay=ui_lay)
        
        # UI Material
        ui_mat_w = QWidget()
        ui_mat_l = QVBoxLayout(ui_mat_w)
        ui_mat_l.setContentsMargins(0,0,0,0)
        ui_mat_l.setSpacing(4)
        self.ui_mat_fields = {}
        for m_key in ["base", "normal", "ac", "metallic", "roughness", "scale_x", "scale_y"]:
            hl = QHBoxLayout()
            le = NoUndoLineEdit("")
            le.setPlaceholderText(m_key)
            le.setStyleSheet(f"background:{SCENE_BG}; color:{TEXT}; border:1px solid {BORDER}; border-radius:4px; padding:6px; font-size:10px; font-family: 'Segoe UI';")
            
            is_file = m_key in ["base", "normal", "ac", "metallic", "roughness"]
            if is_file:
                le.setReadOnly(True)
                btn = QPushButton("...")
                btn.setStyleSheet(f"background:{PURPLE}; color:white; border:none; border-radius:4px; padding:6px; font-weight:bold;")
                btn.setCursor(Qt.PointingHandCursor)
                
                btn_del = QPushButton("X")
                btn_del.setStyleSheet(f"background:#900; color:white; border:none; border-radius:4px; padding:6px; font-weight:bold;")
                btn_del.setCursor(Qt.PointingHandCursor)
                btn_del.setFixedWidth(24)
                
                hl.addWidget(le)
                hl.addWidget(btn)
                hl.addWidget(btn_del)
                self.ui_mat_fields[m_key] = le
                
                btn.clicked.connect(lambda checked, k=m_key: self._on_ui_mat_browse(k))
                btn_del.clicked.connect(lambda checked, k=m_key: self._on_ui_mat_clear(k))
            else:
                from PyQt5.QtGui import QDoubleValidator
                validator = QDoubleValidator()
                le.setValidator(validator)
                if not le.text(): le.setText("1")
                le.setReadOnly(False)
                hl.addWidget(le)
                self.ui_mat_fields[m_key] = le
                le.textChanged.connect(lambda txt, k=m_key: self._on_ui_mat_text_changed(k, txt))
                
            ui_mat_l.addLayout(hl)
        _make_prop('ui_material', "الخامة (Material)", ui_mat_w, parent_lay=ui_lay)
        
        props_lay.addWidget(self.ui_props_widget)
        self.ui_props_widget.hide()

        # ==================================
        # Terrain Properties Widget
        # ==================================
        self.terrain_props_widget = QWidget()
        terrain_lay = QVBoxLayout(self.terrain_props_widget)
        terrain_lay.setContentsMargins(0, 0, 0, 0)
        terrain_lay.setSpacing(12)
        
        self.btn_activate_sculpt = QPushButton("تفعيل وضع النحت")
        self.btn_activate_sculpt.setStyleSheet(f"""
            QPushButton {{
                background: {PURPLE};
                color: white;
                border-radius: 4px;
                padding: 6px;
                font-weight: bold;
            }}
            QPushButton:hover {{ background: {PURPLE_HOVER}; }}
            QPushButton:checked {{ background: {GREEN}; color: black; }}
        """)
        self.btn_activate_sculpt.setCheckable(True)
        self.btn_activate_sculpt.clicked.connect(lambda checked: self._set_gizmo_mode("sculpt" if checked else "pos"))
        terrain_lay.addWidget(self.btn_activate_sculpt)
        
        self.cb_brush_mode = QComboBox()
        self.cb_brush_mode.addItems(["رفع (Raise)", "خفض (Lower)", "تنعيم (Smooth)"])
        self.cb_brush_mode.setStyleSheet(f"background:{SCENE_BG}; color:{TEXT}; border: 1px solid {BORDER}; border-radius:4px; padding: 4px;")
        self.cb_brush_mode.currentIndexChanged.connect(lambda idx: setattr(self.scene_viewer, 'brush_mode', idx))
        _make_prop("brush_mode", "أداة النحت:", self.cb_brush_mode, parent_lay=terrain_lay)
        
        self.sp_brush_radius = QDoubleSpinBox()
        self.sp_brush_radius.setRange(0.1, 50.0)
        self.sp_brush_radius.setValue(2.0)
        self.sp_brush_radius.setStyleSheet(self.spins_pos[0].styleSheet())
        self.sp_brush_radius.valueChanged.connect(lambda v: setattr(self.scene_viewer, 'brush_radius', v))
        _make_prop("brush_radius", "حجم الفرشاة:", self.sp_brush_radius, parent_lay=terrain_lay)
        
        self.sp_brush_strength = QDoubleSpinBox()
        self.sp_brush_strength.setRange(0.01, 10.0)
        self.sp_brush_strength.setValue(0.5)
        self.sp_brush_strength.setStyleSheet(self.spins_pos[0].styleSheet())
        self.sp_brush_strength.valueChanged.connect(lambda v: setattr(self.scene_viewer, 'brush_strength', v))
        _make_prop("brush_strength", "قوة الفرشاة:", self.sp_brush_strength, parent_lay=terrain_lay)
        
        props_lay.addWidget(self.terrain_props_widget)
        self.terrain_props_widget.hide()

        # Add a stretch so everything aligns to top inside the scroll area
        props_lay.addStretch(1)

        from PyQt5.QtWidgets import QScrollArea
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(props_wrap)
        scroll_area.setStyleSheet(f"QScrollArea {{ border: none; background: transparent; }} QScrollBar:vertical {{ width: 8px; }}")

        scroll_area.setMinimumHeight(250)
        hierarchy_layout.addWidget(scroll_area, 1)

        self.addWidget(
            self.scene_sidebar_wrap
        )

        # =================================================
        # Splitter
        # =================================================

        self.setSizes([800, 500])

        self.setStretchFactor(0, 1)
        self.setStretchFactor(1, 0)

        # =================================================
        # Signals
        # =================================================

        self.scene_viewer.object_selected.connect(
            self._on_scene_selected
        )

        self.scene_viewer.transform_updated.connect(
            self._on_scene_transform_update
        )
        self.scene_viewer.scene_props_updated.connect(
            self._on_scene_props_update
        )
        self.scene_viewer.scene_tree_updated.connect(
            self._init_scene_elements
        )

        self.scene_viewer.transform_updated.connect(self._update_kh_code)
        self.scene_viewer.scene_props_updated.connect(self._update_kh_code)
        self.scene_viewer.scene_tree_updated.connect(self._update_kh_code)
        
        self.scene_viewer.setContextMenuPolicy(Qt.CustomContextMenu)
        self.scene_viewer.customContextMenuRequested.connect(self._show_scene_context_menu)

        try:
            import terrain
            project_dir = getattr(self.ide, 'project_dir', '') if hasattr(self, 'ide') else ''
            if project_dir:
                terrain.add_terrains_to_scene(self.scene_viewer, project_dir)
        except Exception as e:
            print("Error loading terrains:", e)

        self._init_scene_elements()

        self.scene_search.textChanged.connect(
            self._filter_scene_tree
        )

    # -----------------------------------------------------
    # Render Mode
    # -----------------------------------------------------

    def _toggle_render_mode(self):
        mode = getattr(self.scene_viewer, "render_mode", "editor")
        new_mode = "game" if mode == "editor" else "editor"
        self.scene_viewer.render_mode = new_mode
        self.btn_render_mode.setText(f"طريقة العرض: {'اللعبة' if new_mode == 'game' else 'المحرر'}")
        self.scene_viewer.update()

    def _update_kh_code(self, *args):
        if getattr(self, '_is_loading_scene', False):
            return
        try:
            import coder_writer
            if hasattr(self, 'ide') and self.ide and hasattr(self.ide, 'project_dir'):
                coder_writer.write_scene_to_kh(self.scene_viewer, self.ide.project_dir)
        except Exception as e:
            print(f"Error calling coder_writer: {e}")

    # =====================================================
    # Context Menus
    # =====================================================
    def _show_scene_context_menu(self, pos):
        from PyQt5.QtWidgets import QMenu
        menu = QMenu(self)
        menu.setStyleSheet(f"QMenu {{ background: {SCENE_BG}; color: {TEXT}; border: 1px solid {BORDER}; }} QMenu::item:selected {{ background: {PURPLE_BG}; }}")
        
        menu_3d = menu.addMenu("أشكال هندسية 3D")
        for shape in ["Cube", "Sphere", "Plane", "Pyramid", "Cylinder", "Capsule"]:
            menu_3d.addAction(shape).triggered.connect(lambda checked, s=shape: self.scene_viewer.add_scene_object(s))
            
        menu_2d = menu.addMenu("أشكال هندسية 2D")
        for shape in ["Square2D", "Circle2D", "Triangle2D"]:
            menu_2d.addAction(shape).triggered.connect(lambda checked, s=shape: self.scene_viewer.add_scene_object(s))
            
        menu_sound = menu.addMenu("صوت")
        menu_sound.addAction("إضافة صوت...").triggered.connect(self._add_sound_object)
        
        menu_custom = menu.addMenu("أشكال مخصصة")
        menu_custom.addAction("شكل 3D مخصص (FBX/OBJ)...").triggered.connect(self._add_custom_3d)
        
        menu.addAction("إضافة تضاريس").triggered.connect(self._show_terrain_dialog)
        
        menu_light = menu.addMenu("إضاءة")
        menu_light.addAction("ضوء موجه").triggered.connect(lambda: self.scene_viewer.add_scene_object("light", light_type="ضوء_موجه"))
        menu_light.addAction("ضوء نقطي").triggered.connect(lambda: self.scene_viewer.add_scene_object("light", light_type="ضوء_نقطي"))
        menu_light.addAction("ضوء بقعي").triggered.connect(lambda: self.scene_viewer.add_scene_object("light", light_type="ضوء_بقعي"))
        
        menu.addSeparator()
        menu_ui = menu.addMenu("واجهة المستخدم UI")
        menu_ui.addAction("واجهة (Canvas)").triggered.connect(self._add_canvas)
        
        sender = self.sender()
        menu.exec_(sender.mapToGlobal(pos))

    def _add_canvas(self):
        if hasattr(self, 'scene_viewer'):
            for obj in self.scene_viewer.objects:
                if getattr(obj, 'obj_type', '') == 'Canvas':
                    self.show_notification("لا يمكن إضافة أكثر من واجهة (Canvas) واحدة في المشهد")
                    return
            self.scene_viewer.add_scene_object("Canvas")

    def _add_sound_object(self):
        from PyQt5.QtWidgets import QFileDialog
        path, _ = QFileDialog.getOpenFileName(self, "اختر ملف صوت", "", "Sound Files (*.wav *.mp3 *.ogg)")
        if path:
            self.scene_viewer.add_scene_object("Sound", filepath=path)

    def _add_custom_3d(self):
        from PyQt5.QtWidgets import QFileDialog
        path, _ = QFileDialog.getOpenFileName(self, "اختر مجسم 3D", "", "3D Models (*.obj *.fbx)")
        if path:
            self.scene_viewer.add_scene_object("CustomModel", filepath=path)

    def _show_terrain_dialog(self):
        project_dir = getattr(self.ide, 'project_dir', '') if hasattr(self, 'ide') else ''
        if not project_dir:
            self.show_notification("لا يوجد مشروع مفتوح لحفظ التضاريس")
            return
            
        try:
            import terrain
            dialog = terrain.TerrainDialog(project_dir, self)
            if dialog.exec_():
                data = dialog.data
                obj = self.scene_viewer.add_scene_object("Terrain", name=data['name'])
                obj.filepath = f"{data['name']}.khterrain"
                obj.scale = [data['size_x'], 1.0, data['size_y']]
                self.scene_viewer.update()
                self._update_kh_code()
        except Exception as e:
            print("Error opening terrain dialog:", e)



    # =====================================================
    # Scene Tool Button
    # =====================================================

    def _create_scene_tool(
        self,
        icon_kind,
        tooltip,
        shortcut
    ):

        button = QToolButton()

        button.setCheckable(True)
        button.setAutoExclusive(True)

        button.setToolTip(
            f"{tooltip} ({shortcut})"
        )

        button.setIcon(
            make_scene_icon(
                icon_kind,
                "#9AA8BB",
                17
            )
        )

        button.setIconSize(
            QSize(17, 17)
        )

        button.setFixedSize(31, 28)

        button.setCursor(
            Qt.PointingHandCursor
        )

        button.setStyleSheet(f"""
            QToolButton {{
                background: transparent;
                color: {TEXT_DIM};
                border: 1px solid transparent;
                border-radius: 5px;
            }}

            QToolButton:hover {{
                background: #192537;
                border-color: #263950;
            }}

            QToolButton:checked {{
                background: {PURPLE_BG};
                border: 1px solid {PURPLE};
            }}
        """)

        return button

    # =====================================================
    # Scene tree
    # =====================================================

    def _init_scene_elements(self):

        self.scene_sidebar_list.clear()

        root = QTreeWidgetItem(
            self.scene_sidebar_list,
            ["المشهد"]
        )

        root.setExpanded(True)

        root.setIcon(
            0,
            make_scene_icon(
                "scene",
                "#A8B5C7",
                16
            )
        )

        camera = None
        
        if hasattr(self, 'scene_viewer') and self.scene_viewer:
            items_dict = {}
            # First pass: Create items
            for obj in self.scene_viewer.objects:
                item = QTreeWidgetItem([obj.name])
                items_dict[obj.name] = (item, obj)
                
                # Assign icon based on type
                if obj.obj_type == "camera":
                    camera = item
                    item.setIcon(0, make_scene_icon("camera", BLUE, 16))
                elif obj.obj_type in ["Square2D", "Circle2D", "Triangle2D", "Custom2D", "Canvas", "Button", "Text"]:
                    item.setIcon(0, make_scene_icon("scene", PURPLE, 16))
                elif obj.obj_type == "Sound":
                    item.setIcon(0, make_scene_icon("scene", "#FFA500", 16))
                else:
                    item.setIcon(0, make_scene_icon("cube", GREEN, 16))
                    
            # Second pass: Build hierarchy
            for name, (item, obj) in items_dict.items():
                if hasattr(obj, 'parent_name') and obj.parent_name and obj.parent_name in items_dict:
                    parent_item = items_dict[obj.parent_name][0]
                    parent_item.addChild(item)
                else:
                    root.addChild(item)
                    
        if not camera: # Fallback if no camera object exists yet
            camera = QTreeWidgetItem(root, ["الكاميرا"])
            camera.setIcon(0, make_scene_icon("camera", BLUE, 16))

        self.scene_sidebar_list.expandAll()
        
        if getattr(self, "selected_scene_obj", None):
            self._on_scene_selected(self.selected_scene_obj)

    # =====================================================
    # Search
    # =====================================================


    def _show_tree_context_menu(self, pos):
        item = self.scene_sidebar_list.itemAt(pos)
        if not item or item.text(0) in ("المشهد", "الكاميرا"): return
        
        from PyQt5.QtWidgets import QMenu
        menu = QMenu(self)
        menu.setStyleSheet(f"QMenu {{ background: {SCENE_BG}; color: {TEXT}; border: 1px solid {BORDER}; }} QMenu::item:selected {{ background: {PURPLE_BG}; }}")
        
        # Check if the clicked item is a Canvas
        obj_name = item.text(0)
        scene_obj = None
        for o in self.scene_viewer.objects:
            if o.name == obj_name:
                scene_obj = o
                break
                
        add_btn_action = None
        add_txt_action = None
        if scene_obj and scene_obj.obj_type == "Canvas":
            add_btn_action = menu.addAction("إضافة زر")
            add_txt_action = menu.addAction("إضافة نص")
            menu.addSeparator()
            
        delete_action = menu.addAction("حذف العنصر")
        action = menu.exec_(self.scene_sidebar_list.mapToGlobal(pos))
        
        if action:
            if action == delete_action:
                self.scene_viewer.select_by_name(obj_name)
                self.scene_viewer.delete_selected()
            elif action == add_btn_action:
                self.scene_viewer.add_scene_object("Button", parent_name=obj_name)
            elif action == add_txt_action:
                self.scene_viewer.add_scene_object("Text", parent_name=obj_name)

    def _filter_scene_tree(self, text):

        text = text.strip().lower()

        root = self.scene_sidebar_list.invisibleRootItem()

        def filter_item(item):

            visible = (
                not text or
                text in item.text(0).lower()
            )

            for i in range(item.childCount()):

                child = item.child(i)

                child_visible = filter_item(
                    child
                )

                visible = (
                    visible or
                    child_visible
                )

            item.setHidden(not visible)

            return visible

        for i in range(root.childCount()):

            filter_item(
                root.child(i)
            )

    # =====================================================
    # Notification
    # =====================================================

    def show_notification(self, text):

        self.notif_label.setText(text)

        self.notif_label.adjustSize()

        viewport_width = (
            self.scene_viewer.width()
        )

        viewport_height = (
            self.scene_viewer.height()
        )

        x = (
            viewport_width -
            self.notif_label.width()
        ) // 2

        y = viewport_height - 48

        self.notif_label.move(
            max(10, x),
            max(10, y)
        )

        self.notif_label.show()
        self.notif_label.raise_()

        self.notif_timer.start(2200)

    # =====================================================
    # Gizmo
    # =====================================================

    def _set_gizmo_mode(self, mode):

        self.btn_gizmo_pos.setChecked(
            mode == "pos"
        )

        self.btn_gizmo_rot.setChecked(
            mode == "rot"
        )

        self.btn_gizmo_scl.setChecked(
            mode == "scl"
        )

        self.btn_gizmo_sel.setChecked(
            mode == "sel"
        )

        names = {
            "pos": "التحريك",
            "rot": "الدوران",
            "scl": "التكبير",
            "sel": "التحديد"
        }

        self.show_notification(
            f"أداة {names.get(mode, '')}"
        )

        if mode == "sel":
            mode = None

        if hasattr(
            self.scene_viewer,
            "set_gizmo_mode"
        ):
            self.scene_viewer.set_gizmo_mode(
                mode
            )

    # =====================================================
    # Tree selection
    # =====================================================

    def _on_scene_element_clicked(
        self,
        item,
        column
    ):

        name = item.text(0)

        self.selected_scene_obj = name

        self.scene_viewer.select_by_name(
            name
        )

    # =====================================================
    # Scene selection
    # =====================================================

    def _on_ui_prop_changed(self, prop, val):
        if not self.selected_scene_obj: return
        obj = None
        for o in self.scene_viewer.objects:
            if o.name == self.selected_scene_obj:
                obj = o
                break
        if not obj: return
        
        if prop == 'ui_text': obj.ui_text = val
        elif prop == 'pos_x': obj.pos[0] = val
        elif prop == 'pos_y': obj.pos[1] = val
        elif prop == 'ui_width': obj.ui_width = val
        elif prop == 'ui_height': obj.ui_height = val
        elif prop == 'ui_font_size': obj.ui_font_size = val
        elif prop == 'ui_align_h': obj.ui_align_h = val
        elif prop == 'ui_align_v': obj.ui_align_v = val
        elif prop == 'ui_offset_x': obj.ui_offset[0] = val
        elif prop == 'ui_offset_y': obj.ui_offset[1] = val
        elif prop == 'ui_full_screen':
            obj.ui_full_screen = val
            if obj.obj_type == 'Canvas' and hasattr(self, 'dyn_widgets') and 'ui_size' in self.dyn_widgets:
                if val:
                    self.dyn_widgets['ui_size'].hide()
                else:
                    self.dyn_widgets['ui_size'].show()
        
        if hasattr(self.scene_viewer, "_save_state"):
            self.scene_viewer._save_state()
        self.scene_viewer.update()
        self._update_kh_code()

    def _on_scene_selected(self, name):

        self.selected_scene_obj = (
            name if name else None
        )
        
        if hasattr(self, 'lbl_selected_name'):
            self.lbl_selected_name.setText(name if name else "لا يوجد تحديد")

        # Toggle visibility of properties
        if hasattr(self, 'cam_props_widget') and hasattr(self, 'obj_props_widget') and hasattr(self, 'scene_props_widget'):
            self.cam_props_widget.hide()
            self.obj_props_widget.hide()
            self.scene_props_widget.hide()
            if hasattr(self, 'light_props_widget'): self.light_props_widget.hide()
            if hasattr(self, 'ui_props_widget'): self.ui_props_widget.hide()
            if hasattr(self, 'btn_sculpt_mode'): self.btn_sculpt_mode.hide()
            
            if name == "الكاميرا":
                self.cam_props_widget.show()
                if hasattr(self, 'scl_w'): self.scl_w.hide()
            elif name == "المشهد":
                self.scene_props_widget.show()
                if hasattr(self, 'scl_w'): self.scl_w.hide()
            elif name:
                # Check if it's a light object or UI object
                obj = None
                if hasattr(self, 'scene_viewer'):
                    for o in self.scene_viewer.objects:
                        if o.name == name:
                            obj = o
                            break
                            
                if obj is not None and getattr(obj, 'obj_type', '') == 'light':
                    if hasattr(self, 'light_props_widget'):
                        self.light_props_widget.show()
                    if hasattr(self, 'scl_w'): self.scl_w.hide()
                elif obj is not None and getattr(obj, 'obj_type', '') in ('Canvas', 'Button', 'Text'):
                    self.obj_props_widget.show()
                    self.ui_props_widget.show()
                    if hasattr(self, 'scl_w'): self.scl_w.hide()
                    
                elif obj is not None and getattr(obj, 'obj_type', '') == 'Terrain':
                    self.obj_props_widget.show()
                    if hasattr(self, 'terrain_props_widget'):
                        self.terrain_props_widget.show()
                    if hasattr(self, 'scl_w'): self.scl_w.show()
                    if hasattr(self, 'btn_sculpt_mode'): self.btn_sculpt_mode.show()
                    
                    if 'color' in self.dyn_widgets: self.dyn_widgets['color'].hide()
                    if 'material' in self.dyn_widgets: self.dyn_widgets['material'].hide()
                    if 'show_collision' in self.dyn_widgets: self.dyn_widgets['show_collision'].hide()
                    
                    if obj:
                        self.le_ui_text.blockSignals(True)
                        self.sp_ui_x.blockSignals(True)
                        self.sp_ui_y.blockSignals(True)
                        self.sp_ui_w.blockSignals(True)
                        self.sp_ui_h.blockSignals(True)
                        self.sp_ui_font_size.blockSignals(True)
                        self.cb_ui_align_h.blockSignals(True)
                        self.cb_ui_align_v.blockSignals(True)
                        self.sp_ui_offset_x.blockSignals(True)
                        self.sp_ui_offset_y.blockSignals(True)
                        
                        self.le_ui_text.setText(getattr(obj, 'ui_text', ''))
                        self.sp_ui_x.setValue(obj.pos[0])
                        self.sp_ui_y.setValue(obj.pos[1])
                        self.sp_ui_w.setValue(getattr(obj, 'ui_width', 0))
                        self.sp_ui_h.setValue(getattr(obj, 'ui_height', 0))
                        
                        self.chk_ui_full_screen.blockSignals(True)
                        self.chk_ui_full_screen.setChecked(getattr(obj, 'ui_full_screen', False))
                        self.chk_ui_full_screen.blockSignals(False)
                        
                        self.sp_ui_font_size.setValue(getattr(obj, 'ui_font_size', 14))
                        
                        align_h = getattr(obj, 'ui_align_h', 'وسط')
                        idx_h = self.cb_ui_align_h.findText(align_h)
                        if idx_h >= 0: self.cb_ui_align_h.setCurrentIndex(idx_h)
                        
                        align_v = getattr(obj, 'ui_align_v', 'وسط')
                        idx_v = self.cb_ui_align_v.findText(align_v)
                        if idx_v >= 0: self.cb_ui_align_v.setCurrentIndex(idx_v)
                        
                        offset = getattr(obj, 'ui_offset', [0, 0])
                        self.sp_ui_offset_x.setValue(offset[0])
                        self.sp_ui_offset_y.setValue(offset[1])
                        
                        tc = getattr(obj, 'ui_text_color', [0,0,0,1])
                        self.btn_ui_text_color.setStyleSheet(f"background: rgba({int(tc[0]*255)}, {int(tc[1]*255)}, {int(tc[2]*255)}, {int(tc[3]*255)}); border: 1px solid {BORDER}; border-radius:4px; padding:6px; font-size:11px; font-family: 'Segoe UI';")
                        bc = getattr(obj, 'ui_bg_color', [1,1,1,1])
                        self.btn_ui_bg_color.setStyleSheet(f"background: rgba({int(bc[0]*255)}, {int(bc[1]*255)}, {int(bc[2]*255)}, {int(bc[3]*255)}); border: 1px solid {BORDER}; border-radius:4px; padding:6px; font-size:11px; font-family: 'Segoe UI';")
                        
                        if getattr(obj, 'obj_type', '') == 'Button':
                            if 'ui_material' in self.dyn_widgets:
                                self.dyn_widgets['ui_material'].show()
                            if isinstance(getattr(obj, 'material', {}), dict):
                                for k, le in self.ui_mat_fields.items():
                                    le.blockSignals(True)
                                    le.setText(str(obj.material.get(k, "")))
                                    le.blockSignals(False)
                            else:
                                for le in self.ui_mat_fields.values():
                                    le.blockSignals(True)
                                    le.setText("")
                                    le.blockSignals(False)
                        else:
                            if 'ui_material' in self.dyn_widgets:
                                self.dyn_widgets['ui_material'].hide()
                        
                        self.le_ui_text.blockSignals(False)
                        self.sp_ui_x.blockSignals(False)
                        self.sp_ui_y.blockSignals(False)
                        self.sp_ui_w.blockSignals(False)
                        self.sp_ui_h.blockSignals(False)
                        self.sp_ui_font_size.blockSignals(False)
                        self.cb_ui_align_h.blockSignals(False)
                        self.cb_ui_align_v.blockSignals(False)
                        self.sp_ui_offset_x.blockSignals(False)
                        self.sp_ui_offset_y.blockSignals(False)
                else:
                    self.obj_props_widget.show()
                    if hasattr(self, 'scl_w'): self.scl_w.show()
                    
                    if 'color' in self.dyn_widgets: self.dyn_widgets['color'].show()
                    if 'material' in self.dyn_widgets: self.dyn_widgets['material'].show()
                    if 'show_collision' in self.dyn_widgets: self.dyn_widgets['show_collision'].show()
            else:
                self.scene_sidebar_list.clearSelection()

        if name:
            self.show_notification(
                f"تم تحديد: {name}"
            )

        root = (
            self.scene_sidebar_list
            .invisibleRootItem()
        )

        def find_item(parent, target):

            for i in range(
                parent.childCount()
            ):

                item = parent.child(i)

                if item.text(0) == target:
                    return item

                found = find_item(
                    item,
                    target
                )

                if found:
                    return found

            return None

        if name:

            item = find_item(
                root,
                name
            )

            if item:

                self.scene_sidebar_list.blockSignals(
                    True
                )

                self.scene_sidebar_list.setCurrentItem(
                    item
                )

                self.scene_sidebar_list.blockSignals(
                    False
                )

    # =====================================================
    # Transform update
    # =====================================================

    def _on_scene_transform_update(
        self,
        obj
    ):
        self.selected_scene_obj = getattr(
            obj,
            "name",
            self.selected_scene_obj
        )

        if not hasattr(self, 'spins_pos'): return
        
        self._ignore_transform_updates = True
        try:
            self.spins_pos[0].setText(f"{obj.pos[0]:.2f}")
            self.spins_pos[1].setText(f"{obj.pos[1]:.2f}")
            self.spins_pos[2].setText(f"{obj.pos[2]:.2f}")
            self.spins_rot[0].setText(f"{obj.rot[0]:.2f}")
            self.spins_rot[1].setText(f"{obj.rot[1]:.2f}")
            self.spins_rot[2].setText(f"{obj.rot[2]:.2f}")
            self.spins_scl[0].setText(f"{obj.scale[0]:.2f}")
            self.spins_scl[1].setText(f"{obj.scale[1]:.2f}")
            self.spins_scl[2].setText(f"{obj.scale[2]:.2f}")
            
            if getattr(obj, "obj_type", "") == "camera" and hasattr(self, "fov_slider"):
                self.fov_slider.blockSignals(True)
                self.near_slider.blockSignals(True)
                self.far_slider.blockSignals(True)
                
                fov = getattr(obj, "fov", 60.0)
                near = getattr(obj, "near_clip", 0.1)
                far = getattr(obj, "far_clip", 2000.0)
                
                self.fov_slider.setValue(int(fov * self.fov_scale))
                self.fov_val.setText(f"{fov:.1f}")
                
                self.near_slider.setValue(int(near * self.near_scale))
                self.near_val.setText(f"{near:.1f}")
                
                self.far_slider.setValue(int(far * self.far_scale))
                self.far_val.setText(f"{far:.1f}")
                
                self.fov_slider.blockSignals(False)
                self.near_slider.blockSignals(False)
                self.far_slider.blockSignals(False)
                
            # Update dynamic properties
            if hasattr(self, "dyn_widgets"):
                # Hide all first
                for w in self.dyn_widgets.values():
                    w.hide()
                    
                t = getattr(obj, "obj_type", "generic")
                
                def _show(key):
                    if key in self.dyn_widgets:
                        self.dyn_widgets[key].show()
                        
                # Update values silently
                self._ignore_transform_updates = True
                
                self.le_name.setText(obj.name)
                self.le_label.setText(getattr(obj, "label", ""))
                _show("name")
                if getattr(obj, "label", ""):
                    _show("label")
                
                if t in ["Cube", "Sphere", "Plane", "Pyramid", "Cylinder", "Capsule", "CustomModel", "Terrain"]:
                    _show("color")
                    c = getattr(obj, "color", [1,1,1])
                    self.btn_obj_color.setStyleSheet(f"background: rgb({int(c[0]*255)}, {int(c[1]*255)}, {int(c[2]*255)}); color: white;")
                    _show("material")
                    mat = getattr(obj, "material", {})
                    for k, le in self.mat_fields.items():
                        le.blockSignals(True)
                    if isinstance(mat, dict):
                        for k, le in self.mat_fields.items():
                            v = mat.get(k, "")
                            if v is None or str(v).strip() == "":
                                if k in ["scale_x", "scale_y"]: v = "1"
                                
                                else: v = ""
                            le.setText(str(v))
                    else:
                        for k, le in self.mat_fields.items():
                            v = "1" if k in ["scale_x", "scale_y"] else ""
                            le.setText(v)
                    for k, le in self.mat_fields.items():
                        le.blockSignals(False)
                    _show("show_collision")
                    self.chk_show_collision.setChecked(getattr(obj, "show_collision", False))
                    _show("gravity")
                    self.chk_gravity.setChecked(getattr(obj, "gravity", False))
                    _show("bounciness")
                    self.chk_bounciness.setChecked(getattr(obj, "bounciness", False))
                    
                if t in ["Square2D", "Circle2D", "Triangle2D", "Custom2D"]:
                    _show("color")
                    c = getattr(obj, "color", [1,1,1])
                    self.btn_obj_color.setStyleSheet(f"background: rgb({int(c[0]*255)}, {int(c[1]*255)}, {int(c[2]*255)}); color: white;")
                    _show("show_collision")
                    self.chk_show_collision.setChecked(getattr(obj, "show_collision", False))
                    _show("gravity")
                    self.chk_gravity.setChecked(getattr(obj, "gravity", False))
                    _show("bounciness")
                    self.chk_bounciness.setChecked(getattr(obj, "bounciness", False))
                    
                if t in ["CustomModel", "Custom2D", "Sound", "Square2D", "Circle2D", "Triangle2D"]:
                    _show("filepath")
                    self.le_filepath.setText(getattr(obj, "filepath", ""))

                if t in ["Canvas", "Button", "Text"]:
                    if t == "Canvas":
                        _show("ui_full_screen")
                        if not getattr(obj, "ui_full_screen", False):
                            _show("ui_size")
                    else:
                        _show("ui_pos")
                        _show("ui_size")
                        _show("ui_font_size")
                        _show("ui_text_color")
                        _show("ui_bg_color")
                        _show("ui_align_h")
                        _show("ui_align_v")
                        _show("ui_offset")
                        
                    if t in ["Button", "Text"]:
                        _show("ui_text")
                    if t == "Button":
                        _show("ui_material")

                # Light properties
                if t == "light" and hasattr(self, 'light_props_widget'):
                    # تحديث نوع الضوء
                    ltype = getattr(obj, 'light_type', 'ضوء_موجه')
                    if hasattr(self, 'cb_light_type'):
                        self.cb_light_type.blockSignals(True)
                        self.cb_light_type.setCurrentText(ltype)
                        self.cb_light_type.blockSignals(False)

                        if ltype == 'ضوء_نقطي':
                            self.lbl_ldir.hide()
                            self.dir_widget.hide()
                            self.spot_angle_w.hide()
                            self.spot_sharp_w.hide()
                        elif ltype == 'ضوء_موجه':
                            self.lbl_ldir.show()
                            self.dir_widget.show()
                            self.spot_angle_w.hide()
                            self.spot_sharp_w.hide()
                        elif ltype == 'ضوء_بقعي':
                            self.lbl_ldir.show()
                            self.dir_widget.show()
                            self.spot_angle_w.show()
                            self.spot_sharp_w.show()

                    # تحديث الألوان وبقية الخصائص
                    c = getattr(obj, 'color', [1.0, 1.0, 1.0])
                    self.btn_light_color.setStyleSheet(
                        f"background: rgb({int(c[0]*255)}, {int(c[1]*255)}, {int(c[2]*255)}); "
                        f"color: {'#111' if sum(c) > 1.5 else 'white'}; border: 1px solid {BORDER}; "
                        f"border-radius:4px; padding:6px; font-size:11px; font-family: 'Segoe UI'; font-weight:bold;"
                    )
                    intensity = getattr(obj, 'light_intensity', 1.0)
                    self.lint_slider.blockSignals(True)
                    self.lint_slider.setValue(int(intensity * self.lint_scale))
                    self.lint_val.setText(f"{intensity:.2f}")
                    self.lint_slider.blockSignals(False)
                    
                    if hasattr(self, 'spins_ldir') and ltype in ('ضوء_موجه', 'ضوء_بقعي'):
                        ldir = getattr(obj, 'light_direction', [0.0, -1.0, 0.0])
                        for i, sp in enumerate(self.spins_ldir):
                            sp.blockSignals(True)
                            sp.setText(f"{ldir[i]:.3f}")
                            sp.blockSignals(False)

                    if ltype == 'ضوء_بقعي' and hasattr(self, 'spot_angle_slider'):
                        sang = getattr(obj, 'spot_angle', 30.0)
                        ssharp = getattr(obj, 'spot_sharpness', 64.0)
                        
                        self.spot_angle_slider.blockSignals(True)
                        self.spot_angle_slider.setValue(int(sang * self.spot_angle_scale))
                        self.spot_angle_val.setText(f"{sang:.1f}")
                        self.spot_angle_slider.blockSignals(False)
                        
                        self.spot_sharp_slider.blockSignals(True)
                        self.spot_sharp_slider.setValue(int(ssharp * self.spot_sharp_scale))
                        self.spot_sharp_val.setText(f"{ssharp:.1f}")
                        self.spot_sharp_slider.blockSignals(False)
        except Exception:
            pass
        self._ignore_transform_updates = False

    # =====================================================
    # Dynamic Properties Updates
    # =====================================================
    def _on_dyn_name_changed(self):
        if not self.selected_scene_obj: return
        obj = None
        for o in self.scene_viewer.objects:
            if o.name == self.selected_scene_obj:
                obj = o
                break
        if not obj: return
        
        new_name = self.le_name.text().strip()
        if not new_name or new_name == obj.name: return
        
        # Check duplicates
        for o in self.scene_viewer.objects:
            if o != obj and o.name == new_name:
                self.le_name.setText(obj.name)
                return
                
        self.scene_viewer.push_undo_state()
        obj.name = new_name
        self.selected_scene_obj = new_name
        self.scene_viewer.scene_tree_updated.emit()
        self.scene_viewer.select_by_name(new_name)
        self._update_kh_code()
        
    def _on_dyn_mat_clear(self, key):
        if not self.selected_scene_obj: return
        obj = None
        for o in self.scene_viewer.objects:
            if o.name == self.selected_scene_obj:
                obj = o
                break
        if not obj: return
        if not isinstance(obj.material, dict): return
        
        self.scene_viewer.push_undo_state()
        obj.material[key] = ""
        self._on_scene_transform_update(obj)
        self.scene_viewer.update()
        self._update_kh_code()


    def _on_dyn_mat_text_changed(self, key, text):
        if not self.scene_viewer or not self.scene_viewer.selected_obj: return
        if getattr(self.scene_viewer.selected_obj, "obj_type", "") in ("light", "sky", "audio"): return
        
        obj = self.scene_viewer.selected_obj
        
        val = 0.0
        try:
            val = float(text)
        except ValueError:
            pass
            
        mat = getattr(obj, "material", None)
        if not isinstance(mat, dict):
            mat = {}
            if hasattr(obj, "material") and obj.material and isinstance(obj.material, dict):
                mat = obj.material.copy()
        
        mat[key] = val
        obj.material = mat
        
        if hasattr(self.scene_viewer, "_save_state"):
            self.scene_viewer._save_state()
        self.scene_viewer.update()
        self._update_kh_code()

    def _on_dyn_mat_browse(self, key):
        if not self.selected_scene_obj: return
        obj = None
        for o in self.scene_viewer.objects:
            if o.name == self.selected_scene_obj:
                obj = o
                break
        if not obj: return
        
        from PyQt5.QtWidgets import QFileDialog
        path, _ = QFileDialog.getOpenFileName(self, f"اختر صورة لـ {key}", "", "Images (*.png *.jpg *.jpeg *.bmp *.tga)")
        if path:
            self.scene_viewer.push_undo_state()
            if not isinstance(obj.material, dict):
                obj.material = {"base": "", "normal": "", "metallic": "", "roughness": "", "ac": ""}
            obj.material[key] = path
            self._on_scene_transform_update(obj)
            self.scene_viewer.update()
            self._update_kh_code()

    def _on_dyn_color_clicked(self):
        if not self.selected_scene_obj: return
        obj = None
        for o in self.scene_viewer.objects:
            if o.name == self.selected_scene_obj:
                obj = o
                break
        if not obj: return
        
        from PyQt5.QtWidgets import QColorDialog
        from PyQt5.QtGui import QColor
        curr = getattr(obj, "color", [1,1,1])
        init_color = QColor(int(curr[0]*255), int(curr[1]*255), int(curr[2]*255))
        color = QColorDialog.getColor(init_color, self)
        if color.isValid():
            self.scene_viewer.push_undo_state()
            obj.color = [color.redF(), color.greenF(), color.blueF()]
            self.scene_viewer.update()
            self._on_scene_transform_update(obj)
            self._update_kh_code()
            
    def _on_dyn_prop_changed(self):
        if not getattr(self, "selected_scene_obj", None): return
        if getattr(self, "_ignore_transform_updates", False): return
        
        obj = None
        for o in getattr(self, "scene_viewer").objects:
            if o.name == self.selected_scene_obj:
                obj = o
                break
        if not obj: return
        
        self.scene_viewer.push_undo_state()
        
        try:
            if hasattr(self, 'chk_show_collision'):
                obj.show_collision = self.chk_show_collision.isChecked()
            if hasattr(self, 'chk_gravity'):
                obj.gravity = self.chk_gravity.isChecked()
            if hasattr(self, 'chk_bounciness'):
                obj.bounciness = self.chk_bounciness.isChecked()
        except ValueError:
            pass
            
        self.scene_viewer.update()
        self._update_kh_code()
        
    def _on_dyn_filepath_clear(self):
        if not self.selected_scene_obj: return
        obj = None
        for o in self.scene_viewer.objects:
            if o.name == self.selected_scene_obj:
                obj = o
                break
        if not obj: return
        
        self.scene_viewer.push_undo_state()
        obj.filepath = ""
        self._on_scene_transform_update(obj)
        self.scene_viewer.update()
        self._update_kh_code()

    def _on_dyn_browse_clicked(self):
        if not self.selected_scene_obj: return
        obj = None
        for o in self.scene_viewer.objects:
            if o.name == self.selected_scene_obj:
                obj = o
                break
        if not obj: return
        
        from PyQt5.QtWidgets import QFileDialog, QMessageBox
        path, _ = QFileDialog.getOpenFileName(self, "تغيير الملف", getattr(obj, "filepath", ""))
        if path:
            if path.lower().endswith(".fbx"):
                QMessageBox.warning(self, "صيغة غير مدعومة", "عذراً! صيغة FBX غير مدعومة حالياً نظراً لأنها صيغة مغلقة تتطلب مكتبات معقدة. يرجى تحويل المجسم إلى صيغة OBJ وسيعمل معك بشكل مثالي!")
                return
                
            self.scene_viewer.push_undo_state()
            obj.filepath = path
            self._on_scene_transform_update(obj)
            self.scene_viewer.update()
            self._update_kh_code()

    # =====================================================
    # Resize
    # =====================================================

    def resizeEvent(self, event):

        super().resizeEvent(event)

        if self.notif_label.isVisible():

            x = (
                self.scene_viewer.width()
                -
                self.notif_label.width()
            ) // 2

            y = (
                self.scene_viewer.height()
                - 48
            )

            self.notif_label.move(
                max(10, x),
                max(10, y)
            )

    # =====================================================
    # Scene Properties
    # =====================================================

    def _choose_sky_color(self):
        from PyQt5.QtWidgets import QColorDialog
        from PyQt5.QtGui import QColor
        curr = self.scene_viewer.sky_color
        init_color = QColor(int(curr[0]*255), int(curr[1]*255), int(curr[2]*255))
        color = QColorDialog.getColor(init_color, self)
        if color.isValid():
            self.scene_viewer.push_undo_state()
            r, g, b = color.redF(), color.greenF(), color.blueF()
            self.scene_viewer.sky_color = [r, g, b]
            self.scene_viewer.sky_cubemap = None
            self.scene_viewer.update()
            self.show_notification("تم تغيير لون السماء")
            self._update_kh_code()

    def _on_scene_props_update(self):
        if getattr(self.scene_viewer, "sky_cubemap", None):
            self.btn_sky_color.setDisabled(True)
            self.btn_remove_cubemap.show()
        else:
            self.btn_sky_color.setDisabled(False)
            self.btn_remove_cubemap.hide()
            self.cubemap_faces.clear()
            for slot in getattr(self, "cubemap_slots", []):
                slot.path = None
                slot.lbl_path.setText("لم يتم التحديد")

    def _on_cubemap_slot_changed(self, face_id, path):
        self.cubemap_faces[face_id] = path
        
        faces = ["right", "left", "top", "bottom", "front", "back"]
        if all(self.cubemap_faces.get(f) for f in faces):
            self.scene_viewer.push_undo_state()
            class DummyCubemap:
                pass
            cubemap = DummyCubemap()
            cubemap.right = self.cubemap_faces["right"]
            cubemap.left = self.cubemap_faces["left"]
            cubemap.top = self.cubemap_faces["top"]
            cubemap.bottom = self.cubemap_faces["bottom"]
            cubemap.front = self.cubemap_faces["front"]
            cubemap.back = self.cubemap_faces["back"]
            cubemap.textures = None
            
            self.scene_viewer.sky_cubemap = cubemap
            self.scene_viewer.update()
            
            self.btn_sky_color.setDisabled(True)
            self.btn_remove_cubemap.show()
            self.show_notification("تم تعيين مكعب السماء بنجاح")
            self._update_kh_code()

    def _remove_cubemap(self):
        self.scene_viewer.push_undo_state()
        self.scene_viewer.sky_cubemap = None
        self.scene_viewer.update()
        
        self.btn_sky_color.setDisabled(False)
        self.btn_remove_cubemap.hide()
        self.cubemap_faces.clear()
        
        for slot in getattr(self, "cubemap_slots", []):
            slot.path = None
            slot.lbl_path.setText("لم يتم التحديد")
            
        self.show_notification("تم إزالة مكعب السماء")
        self._update_kh_code()

    def _on_cam_slider_pressed(self):
        if hasattr(self, 'scene_viewer'):
            self.scene_viewer.push_undo_state()
            
    def _on_cam_slider_changed(self):
        if not hasattr(self, 'fov_slider'): return
        fov = self.fov_slider.value() / self.fov_scale
        near = self.near_slider.value() / self.near_scale
        far = self.far_slider.value() / self.far_scale
        
        self.fov_val.setText(f"{fov:.1f}")
        self.near_val.setText(f"{near:.1f}")
        self.far_val.setText(f"{far:.1f}")
        
        for obj in self.scene_viewer.objects:
            if obj.obj_type == 'camera':
                obj.fov = fov
                obj.near_clip = near
                obj.far_clip = far
                self.scene_viewer.update()
                self._update_kh_code()
                break

    # =====================================================
    # Light Properties Helpers
    # =====================================================

    def _get_selected_light_obj(self):
        """يُعيد كائن الضوء المحدد حالياً في المشهد، أو None إذا لم يكن محدداً."""
        if not self.selected_scene_obj: return None
        for o in self.scene_viewer.objects:
            if o.name == self.selected_scene_obj and getattr(o, 'obj_type', '') == 'light':
                return o
        return None

    def _on_light_color_clicked(self):
        """يفتح نافذة اختيار اللون لكائن الضوء."""
        obj = self._get_selected_light_obj()
        if not obj: return
        from PyQt5.QtWidgets import QColorDialog
        from PyQt5.QtGui import QColor
        c = getattr(obj, 'color', [1.0, 1.0, 1.0])
        init_color = QColor(int(c[0]*255), int(c[1]*255), int(c[2]*255))
        color = QColorDialog.getColor(init_color, self, "اختر لون الضوء")
        if color.isValid():
            self.scene_viewer.push_undo_state()
            obj.color = [color.redF(), color.greenF(), color.blueF()]
            rc = int(obj.color[0]*255)
            gc = int(obj.color[1]*255)
            bc = int(obj.color[2]*255)
            brightness = obj.color[0]*0.299 + obj.color[1]*0.587 + obj.color[2]*0.114
            txt_color = "#111" if brightness > 0.5 else "white"
            self.btn_light_color.setStyleSheet(
                f"background: rgb({rc},{gc},{bc}); color: {txt_color}; "
                f"border: 1px solid {BORDER}; border-radius:4px; padding:6px; "
                f"font-size:11px; font-family: 'Segoe UI'; font-weight:bold;"
            )
            self.scene_viewer.update()
            self.show_notification("تم تغيير لون الضوء")
            self._update_kh_code()

    def _on_ui_text_color_clicked(self):
        from PyQt5.QtWidgets import QColorDialog
        obj = self._get_selected_ui_obj()
        if not obj: return
        
        c = obj.ui_text_color
        init_color = QColor(int(c[0]*255), int(c[1]*255), int(c[2]*255), int(c[3]*255))
        color = QColorDialog.getColor(init_color, self, "اختيار لون النص", QColorDialog.ShowAlphaChannel)
        if color.isValid():
            self.scene_viewer.push_undo_state()
            obj.ui_text_color = [color.redF(), color.greenF(), color.blueF(), color.alphaF()]
            self.btn_ui_text_color.setStyleSheet(
                f"background: rgba({color.red()}, {color.green()}, {color.blue()}, {color.alpha()}); "
                f"border: 1px solid {BORDER}; border-radius:4px; padding:6px; font-size:11px; font-family: 'Segoe UI';"
            )
            self.scene_viewer.update()
            self._update_kh_code()

    def _on_ui_bg_color_clicked(self):
        from PyQt5.QtWidgets import QColorDialog
        obj = self._get_selected_ui_obj()
        if not obj: return
        
        c = obj.ui_bg_color
        init_color = QColor(int(c[0]*255), int(c[1]*255), int(c[2]*255), int(c[3]*255))
        color = QColorDialog.getColor(init_color, self, "اختيار لون الخلفية", QColorDialog.ShowAlphaChannel)
        if color.isValid():
            self.scene_viewer.push_undo_state()
            obj.ui_bg_color = [color.redF(), color.greenF(), color.blueF(), color.alphaF()]
            self.btn_ui_bg_color.setStyleSheet(
                f"background: rgba({color.red()}, {color.green()}, {color.blue()}, {color.alpha()}); "
                f"border: 1px solid {BORDER}; border-radius:4px; padding:6px; font-size:11px; font-family: 'Segoe UI';"
            )
            self.scene_viewer.update()
            self._update_kh_code()

    def _get_selected_ui_obj(self):
        if not self.selected_scene_obj: return None
        for o in self.scene_viewer.objects:
            if o.name == self.selected_scene_obj and getattr(o, 'obj_type', '') in ('Canvas', 'Button', 'Text'):
                return o
        return None

    def _on_ui_mat_browse(self, key):
        from PyQt5.QtWidgets import QFileDialog
        obj = self._get_selected_ui_obj()
        if not obj: return
        
        path, _ = QFileDialog.getOpenFileName(self, f"اختيار خريطة {key}", "", "Images (*.png *.jpg *.jpeg *.tga *.bmp)")
        if path:
            import os
            try:
                rel = os.path.relpath(path, start=os.getcwd())
                path = rel
            except:
                pass
            path = path.replace('\\', '/')
            self.ui_mat_fields[key].setText(path)
            self.scene_viewer.push_undo_state()
            if not isinstance(getattr(obj, 'material', None), dict): obj.material = {}
            obj.material[key] = path
            self.scene_viewer.update()
            self._update_kh_code()

    def _on_ui_mat_clear(self, key):
        obj = self._get_selected_ui_obj()
        if not obj: return
        self.ui_mat_fields[key].setText("")
        self.scene_viewer.push_undo_state()
        if not isinstance(getattr(obj, 'material', None), dict): obj.material = {}
        obj.material[key] = ""
        self.scene_viewer.update()
        self._update_kh_code()

    def _on_ui_mat_text_changed(self, key, text):
        obj = self._get_selected_ui_obj()
        if not obj: return
        if not isinstance(getattr(obj, 'material', None), dict): obj.material = {}
        if obj.material.get(key, "") != text:
            obj.material[key] = text
            self.scene_viewer.update()
            self._update_kh_code()
