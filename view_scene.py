"""
view_scene.py  —  عارض المشهد الحر (Scene Viewer)
===================================================
نظام رسومات يعتمد على PyQt5 QOpenGLWidget
"""

import sys
import os
import math
from PyQt5.QtWidgets import QOpenGLWidget
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QPoint
from PyQt5.QtGui import QCursor

from OpenGL.GL import *
from OpenGL.GLU import *

# ─────────────────────────────────────────────────────────────────
#  SceneObject: كائن بسيط في المشهد
# ─────────────────────────────────────────────────────────────────
class SceneObject:
    def __init__(self, name, pos=None, rot=None, scale=None, obj_type="generic", **kwargs):
        self.name = name
        self.pos   = list(pos   or [0.0, 0.0, 0.0])
        self.rot   = list(rot   or [0.0, 0.0, 0.0])
        self.scale = list(scale or [1.0, 1.0, 1.0])
        self.obj_type = obj_type   # "camera" | "generic" | "Cube" | "Sphere" | "CustomModel" etc
        self.selected = False
        
        # KH Properties
        self.label = ""
        self.color = [1.0, 1.0, 1.0]
        self.material = {"base": "", "normal": "", "metallic": "", "roughness": "", "ac": ""}
        self.show_collision = False
        self.gravity = False
        self.bounciness = False
        self.filepath = ""        # for CustomModel, Custom2D, Sound
        self.parent_name = kwargs.get("parent_name", "") # For UI elements hierarchy
        
        if obj_type in ("Button", "Text", "Canvas"):
            self.ui_text = "النص" if obj_type in ("Button", "Text") else ""
            self.ui_width = 100 if obj_type == "Button" else (200 if obj_type == "Canvas" else 0)
            self.ui_height = 40 if obj_type == "Button" else (200 if obj_type == "Canvas" else 0)
            self.ui_bg_color = [0.8, 0.8, 0.8, 1.0] if obj_type == "Button" else [0, 0, 0, 0]
            self.ui_text_color = [0, 0, 0, 1.0]
            self.ui_font_size = 14
            self.ui_align_h = "وسط"
            self.ui_align_v = "وسط"
            self.ui_offset = [0, 0]
            
        if obj_type == "Terrain":
            self.grid_size = kwargs.get("grid_size", 50)
            self.heightmap = kwargs.get("heightmap", [0.0] * (self.grid_size * self.grid_size))
        
        if obj_type == "camera":
            self.fov = 60.0
            self.near_clip = 0.1
            self.far_clip = 2000.0
        
        if obj_type == "light":
            self.light_type      = kwargs.get('light_type', "ضوء_موجه")
            self.light_intensity = 1.0
            self.light_direction = [0.0, -1.0, 0.0]
            self.color           = [1.0, 1.0, 1.0]
            self.spot_angle      = 30.0
            self.spot_sharpness  = 64.0


# ─────────────────────────────────────────────────────────────────
#  SceneViewerWidget: محرك عرض مشهد المحرر
# ─────────────────────────────────────────────────────────────────
class SceneViewerWidget(QOpenGLWidget):
    
    # الإشارات للتواصل مع واجهة UI
    object_selected = pyqtSignal(str)
    transform_updated = pyqtSignal(object)
    scene_props_updated = pyqtSignal()
    scene_tree_updated = pyqtSignal()

    GIZMO_LEN   = 1.4
    GIZMO_THICK = 3.0
    HIT_RADIUS  = 0.45

    def __init__(self, parent=None):
        super().__init__(parent)
        self.render_mode = "editor" # "editor" or "game"
        self.game_camera = None
        self.brush_mode = 0
        self.brush_radius = 2.0
        self.brush_strength = 0.5
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.StrongFocus)

        self.editor_cam_pos   = [0.0, 3.0, 8.0]
        self.editor_cam_yaw   = 0.0
        self.editor_cam_pitch = -15.0

        self.move_speed  = 8.0
        self.rot_speed   = 0.25
        self.zoom_speed  = 3.0

        self.right_mouse_down = False
        self.show_grid  = True
        self.show_axes  = True

        self._current_w = 800
        self._current_h = 600

        self.objects = [
            SceneObject("الكاميرا", pos=[0.0, 0.0, 0.0], obj_type="camera")
        ]
        self.selected_obj = None

        self._drag_axis  = None
        self._drag_start = None
        self._drag_obj_start_pos = None
        self._drag_obj_start_rot = None
        self._drag_obj_start_scale = None
        self.gizmo_mode = 'pos'
        
        self.keys_pressed = set()
        self.last_mouse_pos = None

        self.sky_color = [0.15, 0.15, 0.15]
        self.sky_cubemap = None

        self.timer = QTimer(self)
        self.timer.timeout.connect(self._update_loop)
        self.timer.start(16)
        
        self.undo_stack = []
        self.redo_stack = []

    def enterEvent(self, event):
        self.setFocus()
        super().enterEvent(event)

    # ── واجهة تحكم من الخارج ───────────────────────────────────────
    def set_gizmo_mode(self, mode):
        self.gizmo_mode = mode
        self.update()
        
    def select_by_name(self, name):
        if name == "المشهد":
            for o in self.objects: o.selected = False
            self.selected_obj = None
            self.object_selected.emit("المشهد")
            self.update()
            return
            
        for obj in self.objects:
            if obj.name == name:
                self._set_selection(obj)
                return
        self._set_selection(None)
        
    def set_transform(self, name, px, py, pz, rx, ry, rz, sx, sy, sz):
        self.push_undo_state()
        for obj in self.objects:
            if obj.name == name:
                obj.pos = [px, py, pz]
                obj.rot = [rx, ry, rz]
                obj.scale = [sx, sy, sz]
                break
        self.update()

    def delete_selected(self):
        if not self.selected_obj: return
        if getattr(self.selected_obj, "obj_type", "") in ('camera', 'المشهد'): return
        
        self.push_undo_state()
        
        if self.selected_obj in self.objects:
            self.objects.remove(self.selected_obj)
            
        self.selected_obj = None
        self.scene_tree_updated.emit()
        self.object_selected.emit("")
        self.update()

    def add_scene_object(self, obj_type, name=None, filepath="", **kwargs):
        self.push_undo_state()
        
        arabic_names = {
            "Cube": "مكعب", "Sphere": "كرة", "Plane": "سطح", "Pyramid": "هرم",
            "Cylinder": "اسطوانة", "Capsule": "كبسولة", "Square2D": "مربع",
            "Circle2D": "دائرة", "Triangle2D": "مثلث", "Sound": "صوت",
            "CustomModel": "مجسم", "Custom2D": "صورة", "light": "ضوء",
            "Canvas": "واجهة", "Button": "زر", "Text": "نص", "Terrain": "تضاريس"
        }
        base_name_ar = arabic_names.get(obj_type, "عنصر")

        if not name:
            # Generate a unique name
            idx = 1
            while any(o.name == f"{base_name_ar}{idx}" for o in self.objects):
                idx += 1
            name = f"{base_name_ar}{idx}"
            
        obj = SceneObject(name, obj_type=obj_type, **kwargs)
        if obj_type != "camera":
            obj.label = name # Use the same Arabic name for label
            
        if filepath:
            obj.filepath = filepath
            
        # Defaults based on type
        if obj_type in ["Square2D", "Circle2D", "Triangle2D", "Custom2D"]:
            obj.pos = [0.0, 0.0, 0.0]
            obj.scale = [1.0, 1.0, 1.0]
        else:
            obj.pos = [0.0, 0.0, -5.0]
            
        if obj_type == "camera":
            obj.pos = [0.0, 0.0, 0.0]
            
        self.objects.append(obj)
        self.scene_tree_updated.emit()
        self.select_by_name(name)
        self.update()
        return obj

    # ── Undo / Redo ──────────────────────────────────────────
    def _save_state(self):
        return {
            'objects': [
                {
                    'name': obj.name,
                    'obj_type': obj.obj_type,
                    'pos': list(obj.pos),
                    'rot': list(obj.rot),
                    'scale': list(obj.scale),
                    'fov': getattr(obj, 'fov', 60.0),
                    'near_clip': getattr(obj, 'near_clip', 0.1),
                    'far_clip': getattr(obj, 'far_clip', 2000.0),
                    'label': getattr(obj, 'label', ''),
                    'color': list(obj.color),
                    'material': obj.material,
                    'show_collision': obj.show_collision,
                    'gravity': obj.gravity,
                    'bounciness': obj.bounciness,
                    'filepath': obj.filepath,
                    'light_type': getattr(obj, 'light_type', 'ضوء_موجه'),
                    'light_intensity': getattr(obj, 'light_intensity', 1.0),
                    'light_direction': list(getattr(obj, 'light_direction', [0.0, -1.0, 0.0])),
                    'spot_angle': getattr(obj, 'spot_angle', 30.0),
                    'spot_sharpness': getattr(obj, 'spot_sharpness', 64.0),
                    'parent_name': getattr(obj, 'parent_name', ""),
                    'ui_text': getattr(obj, 'ui_text', ""),
                    'ui_width': getattr(obj, 'ui_width', 0),
                    'ui_height': getattr(obj, 'ui_height', 0),
                    'ui_bg_color': getattr(obj, 'ui_bg_color', [1,1,1,1]),
                    'ui_text_color': getattr(obj, 'ui_text_color', [0,0,0,1]),
                    'ui_font_size': getattr(obj, 'ui_font_size', 14),
                    'ui_align_h': getattr(obj, 'ui_align_h', 'وسط'),
                    'ui_align_v': getattr(obj, 'ui_align_v', 'وسط'),
                    'ui_offset': list(getattr(obj, 'ui_offset', [0, 0])),
                    'grid_size': getattr(obj, 'grid_size', 50),
                    'heightmap': list(getattr(obj, 'heightmap', [0.0] * (50*50))) if hasattr(obj, 'heightmap') else None,
                }
                for obj in self.objects
            ],
            'sky_color': list(self.sky_color),
            'sky_cubemap': self.sky_cubemap
        }

    def _load_state(self, state):
        if isinstance(state, list):
            obj_states = state
        else:
            obj_states = state.get('objects', [])
            if 'sky_color' in state:
                c = list(state['sky_color'])
                if c[0] < 0.01 and c[1] < 0.01 and c[2] < 0.01:
                    c = [0.15, 0.15, 0.15]
                self.sky_color = c
            if 'sky_cubemap' in state:
                self.sky_cubemap = state['sky_cubemap']
            self.scene_props_updated.emit()

        new_objects = []
        for s_obj in obj_states:
            obj = SceneObject(s_obj['name'], obj_type=s_obj.get('obj_type', 'generic'))
            obj.pos = list(s_obj['pos'])
            obj.rot = list(s_obj['rot'])
            obj.scale = list(s_obj['scale'])
            
            obj.label = s_obj.get('label', "")
            obj.color = list(s_obj.get('color', [1.0, 1.0, 1.0]))
            obj.material = s_obj.get('material', {"base": "", "normal": "", "metallic": "", "roughness": "", "ac": ""})
            if isinstance(obj.material, str): # Backward compatibility
                obj.material = {"base": "", "normal": "", "metallic": "", "roughness": "", "ac": ""}
            obj.show_collision = s_obj.get('show_collision', False)
            obj.gravity = s_obj.get('gravity', False)
            obj.bounciness = s_obj.get('bounciness', False)
            obj.filepath = s_obj.get('filepath', "")
            
            if obj.obj_type == 'camera':
                obj.fov = s_obj.get('fov', 60.0)
                obj.near_clip = s_obj.get('near_clip', 0.1)
                obj.far_clip = s_obj.get('far_clip', 2000.0)
            
            if obj.obj_type == 'light':
                obj.light_type      = s_obj.get('light_type', 'ضوء_موجه')
                obj.light_intensity = s_obj.get('light_intensity', 1.0)
                obj.light_direction = list(s_obj.get('light_direction', [0.0, -1.0, 0.0]))
                obj.spot_angle      = s_obj.get('spot_angle', 30.0)
                obj.spot_sharpness  = s_obj.get('spot_sharpness', 64.0)
                
            obj.parent_name     = s_obj.get('parent_name', "")
            obj.ui_text         = s_obj.get('ui_text', "")
            obj.ui_width        = s_obj.get('ui_width', 0)
            obj.ui_height       = s_obj.get('ui_height', 0)
            obj.ui_bg_color     = s_obj.get('ui_bg_color', [1,1,1,1])
            obj.ui_text_color   = s_obj.get('ui_text_color', [0,0,0,1])
            obj.ui_font_size    = s_obj.get('ui_font_size', 14)
            obj.ui_align_h      = s_obj.get('ui_align_h', 'وسط')
            obj.ui_align_v      = s_obj.get('ui_align_v', 'وسط')
            if 'ui_offset' in s_obj: obj.ui_offset = list(s_obj['ui_offset'])
            
            if obj.obj_type == "Terrain":
                obj.grid_size = s_obj.get('grid_size', 50)
                hm = s_obj.get('heightmap')
                if hm: obj.heightmap = list(hm)
                else: obj.heightmap = [0.0] * (obj.grid_size * obj.grid_size)
                
            new_objects.append(obj)
            
        self.objects = new_objects
        
        # Restore selection
        if self.selected_obj:
            still_exists = any(o.name == self.selected_obj.name for o in self.objects)
            if not still_exists:
                self.selected_obj = None
        
        if self.selected_obj:
            # Refresh reference
            for o in self.objects:
                if o.name == self.selected_obj.name:
                    self.selected_obj = o
                    o.selected = True
                    break
            self.transform_updated.emit(self.selected_obj)
        self.scene_tree_updated.emit()
        self.update()

    def push_undo_state(self):
        state = self._save_state()
        if not self.undo_stack or self.undo_stack[-1] != state:
            self.undo_stack.append(state)
            if len(self.undo_stack) > 50:
                self.undo_stack.pop(0)
            self.redo_stack.clear()

    def undo(self):
        if not self.undo_stack: return
        self.redo_stack.append(self._save_state())
        state = self.undo_stack.pop()
        self._load_state(state)

    def redo(self):
        if not self.redo_stack: return
        self.undo_stack.append(self._save_state())
        state = self.redo_stack.pop()
        self._load_state(state)

    def _set_selection(self, obj):
        for o in self.objects:
            o.selected = False
        self.selected_obj = obj
        if obj:
            obj.selected = True
            self.object_selected.emit(obj.name)
            self.transform_updated.emit(obj)
        else:
            self.object_selected.emit("")
        self.update()

    # ── Qt OpenGL Methods ──────────────────────────────────────────
    def initializeGL(self):
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_NORMALIZE)
        glEnable(GL_COLOR_MATERIAL)
        glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
        glShadeModel(GL_SMOOTH)
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glLightfv(GL_LIGHT0, GL_POSITION, [10.0, 20.0, 10.0, 0.0])
        glLightfv(GL_LIGHT0, GL_DIFFUSE,  [1.0, 1.0, 1.0, 1.0])
        glLightfv(GL_LIGHT0, GL_AMBIENT,  [0.3, 0.3, 0.3, 1.0])
        glLightfv(GL_LIGHT0, GL_SPECULAR, [0.5, 0.5, 0.5, 1.0])
        
        # Anti-aliasing (تنعيم الحواف)
        glEnable(GL_LINE_SMOOTH)
        glEnable(GL_POLYGON_SMOOTH)
        glHint(GL_LINE_SMOOTH_HINT, GL_NICEST)
        glHint(GL_POLYGON_SMOOTH_HINT, GL_NICEST)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        try:
            glEnable(0x809D) # GL_MULTISAMPLE
        except Exception:
            pass

    def _get_camera(self):
        for obj in self.objects:
            if obj.obj_type == "camera": return obj
        return None

    def resizeGL(self, w, h):
        self._current_w = w
        self._current_h = h
        if h == 0: h = 1
        glViewport(0, 0, w, h)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(60.0, float(w) / float(h), 0.1, 2000.0)
        glMatrixMode(GL_MODELVIEW)

    def paintGL(self):
        if self.render_mode == "game":
            self._render_game()
            return
            
        glClearColor(self.sky_color[0], self.sky_color[1], self.sky_color[2], 1.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        w, h = self._current_w, self._current_h
        if h == 0: h = 1

        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(60.0, float(w)/float(h), 0.1, 2000.0)
        
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

        fwd = self._forward()
        cx, cy, cz = self.editor_cam_pos
        gluLookAt(cx, cy, cz, cx+fwd[0], cy+fwd[1], cz+fwd[2], 0, 1, 0)

        if self.sky_cubemap:
            sky = self.sky_cubemap
            if not getattr(sky, 'textures', None):
                try:
                    import textures
                    sky.textures = [
                        textures.load_texture(sky.right),
                        textures.load_texture(sky.left),
                        textures.load_texture(sky.top),
                        textures.load_texture(sky.bottom),
                        textures.load_texture(sky.front),
                        textures.load_texture(sky.back)
                    ]
                except Exception as e:
                    print(f"Error loading cubemap: {e}")
                    sky.textures = [-1, -1, -1, -1, -1, -1]
            if sky.textures and sky.textures[0] != -1:
                glMatrixMode(GL_TEXTURE)
                glLoadIdentity()
                glMatrixMode(GL_MODELVIEW)
                
                glPushMatrix()
                glPushAttrib(GL_ENABLE_BIT)
                glDisable(GL_DEPTH_TEST)
                glDisable(GL_LIGHTING)
                glEnable(GL_TEXTURE_2D)
                glColor3f(1.0, 1.0, 1.0)
                glTranslatef(cx, cy, cz)
                s = 50.0
                glBindTexture(GL_TEXTURE_2D, sky.textures[4])
                glBegin(GL_QUADS); glTexCoord2f(0, 0); glVertex3f(-s,  s, -s); glTexCoord2f(1, 0); glVertex3f( s,  s, -s); glTexCoord2f(1, 1); glVertex3f( s, -s, -s); glTexCoord2f(0, 1); glVertex3f(-s, -s, -s); glEnd()
                glBindTexture(GL_TEXTURE_2D, sky.textures[5])
                glBegin(GL_QUADS); glTexCoord2f(0, 0); glVertex3f( s,  s,  s); glTexCoord2f(1, 0); glVertex3f(-s,  s,  s); glTexCoord2f(1, 1); glVertex3f(-s, -s,  s); glTexCoord2f(0, 1); glVertex3f( s, -s,  s); glEnd()
                glBindTexture(GL_TEXTURE_2D, sky.textures[1])
                glBegin(GL_QUADS); glTexCoord2f(0, 0); glVertex3f(-s,  s,  s); glTexCoord2f(1, 0); glVertex3f(-s,  s, -s); glTexCoord2f(1, 1); glVertex3f(-s, -s, -s); glTexCoord2f(0, 1); glVertex3f(-s, -s,  s); glEnd()
                glBindTexture(GL_TEXTURE_2D, sky.textures[0])
                glBegin(GL_QUADS); glTexCoord2f(0, 0); glVertex3f( s,  s, -s); glTexCoord2f(1, 0); glVertex3f( s,  s,  s); glTexCoord2f(1, 1); glVertex3f( s, -s,  s); glTexCoord2f(0, 1); glVertex3f( s, -s, -s); glEnd()
                glBindTexture(GL_TEXTURE_2D, sky.textures[2])
                glBegin(GL_QUADS); glTexCoord2f(0, 0); glVertex3f(-s,  s,  s); glTexCoord2f(1, 0); glVertex3f( s,  s,  s); glTexCoord2f(1, 1); glVertex3f( s,  s, -s); glTexCoord2f(0, 1); glVertex3f(-s,  s, -s); glEnd()
                glBindTexture(GL_TEXTURE_2D, sky.textures[3])
                glBegin(GL_QUADS); glTexCoord2f(0, 0); glVertex3f(-s, -s, -s); glTexCoord2f(1, 0); glVertex3f( s, -s, -s); glTexCoord2f(1, 1); glVertex3f( s, -s,  s); glTexCoord2f(0, 1); glVertex3f(-s, -s,  s); glEnd()
                glPopAttrib()
                glPopMatrix()

        # تطبيق موقع الضوء — إذا كان في المشهد كائن ضوء نستخدمه، وإلا نستخدم الافتراضي
        light_objs = [o for o in self.objects if getattr(o, 'obj_type', '') == 'light']
        if light_objs:
            lo = light_objs[0]
            ltype = getattr(lo, 'light_type', 'ضوء_موجه')
            intensity = getattr(lo, 'light_intensity', 1.0)
            lcolor = getattr(lo, 'color', [1.0, 1.0, 1.0])
            glLightfv(GL_LIGHT0, GL_DIFFUSE,  [lcolor[0]*intensity, lcolor[1]*intensity, lcolor[2]*intensity, 1.0])
            glLightfv(GL_LIGHT0, GL_SPECULAR, [lcolor[0]*intensity*0.5, lcolor[1]*intensity*0.5, lcolor[2]*intensity*0.5, 1.0])
            glLightfv(GL_LIGHT0, GL_AMBIENT,  [lcolor[0]*0.15, lcolor[1]*0.15, lcolor[2]*0.15, 1.0])
            if ltype == 'ضوء_نقطي':
                glLightfv(GL_LIGHT0, GL_POSITION, [lo.pos[0], lo.pos[1], lo.pos[2], 1.0])
                glLightf(GL_LIGHT0, GL_SPOT_CUTOFF, 180.0)
            elif ltype == 'ضوء_موجه':
                ldir = getattr(lo, 'light_direction', [0.0, -1.0, 0.0])
                glLightfv(GL_LIGHT0, GL_POSITION, [-ldir[0], -ldir[1], -ldir[2], 0.0])
                glLightf(GL_LIGHT0, GL_SPOT_CUTOFF, 180.0)
            elif ltype == 'ضوء_بقعي':
                glLightfv(GL_LIGHT0, GL_POSITION, [lo.pos[0], lo.pos[1], lo.pos[2], 1.0])
                ldir = getattr(lo, 'light_direction', [0.0, -1.0, 0.0])
                glLightfv(GL_LIGHT0, GL_SPOT_DIRECTION, [ldir[0], ldir[1], ldir[2]])
                glLightf(GL_LIGHT0, GL_SPOT_CUTOFF, getattr(lo, 'spot_angle', 30.0))
                glLightf(GL_LIGHT0, GL_SPOT_EXPONENT, getattr(lo, 'spot_sharpness', 64.0))
            else:
                # ضوء نقطي
                glLightfv(GL_LIGHT0, GL_POSITION, [lo.pos[0], lo.pos[1], lo.pos[2], 1.0])
                glLightf(GL_LIGHT0, GL_SPOT_CUTOFF, 180.0)
        else:
            # ضوء افتراضي ثابت إذا لم يكن هناك كائن ضوء
            glLightfv(GL_LIGHT0, GL_POSITION, [10.0, 20.0, 10.0, 0.0])
            glLightfv(GL_LIGHT0, GL_DIFFUSE,  [1.0, 1.0, 1.0, 1.0])
            glLightfv(GL_LIGHT0, GL_SPECULAR, [0.5, 0.5, 0.5, 1.0])
            glLightfv(GL_LIGHT0, GL_AMBIENT,  [0.3, 0.3, 0.3, 1.0])


        if self.show_grid:  self._draw_grid()
        if self.show_axes:  self._draw_axes()

        for obj in self.objects:
            self._draw_object(obj)

        if self.selected_obj:
            self._draw_gizmo(self.selected_obj)
            if self._drag_axis:
                self.transform_updated.emit(self.selected_obj)

        self._draw_hud(w, h)

    # ── Update Loop ────────────────────────────────────────────────
    def _update_loop(self):
        dt = 0.016
        if self._update_camera(dt):
            self.update()

    def _update_camera(self, dt):
        moved = False
        speed = self.move_speed * (3.0 if Qt.Key_Shift in self.keys_pressed else 1.0) * dt
        fwd   = self._forward()
        right = self._right()
        if Qt.Key_W in self.keys_pressed:
            for i in range(3): self.editor_cam_pos[i] += fwd[i]*speed
            moved = True
        if Qt.Key_S in self.keys_pressed:
            for i in range(3): self.editor_cam_pos[i] -= fwd[i]*speed
            moved = True
        if Qt.Key_A in self.keys_pressed:
            for i in range(3): self.editor_cam_pos[i] -= right[i]*speed
            moved = True
        if Qt.Key_D in self.keys_pressed:
            for i in range(3): self.editor_cam_pos[i] += right[i]*speed
            moved = True
        if Qt.Key_Q in self.keys_pressed:
            self.editor_cam_pos[1] -= speed
            moved = True
        if Qt.Key_E in self.keys_pressed:
            self.editor_cam_pos[1] += speed
            moved = True
        return moved

    # ── Event Handling ─────────────────────────────────────────────
    def keyPressEvent(self, event):
        self.keys_pressed.add(event.key())
        if event.key() == Qt.Key_Delete:
            self.delete_selected()
            return
        if event.key() == Qt.Key_G:
            self.show_grid = not self.show_grid
            self.update()
        elif event.key() == Qt.Key_Z and (event.modifiers() & Qt.ControlModifier):
            self.undo()
        elif event.key() == Qt.Key_Y and (event.modifiers() & Qt.ControlModifier):
            self.redo()
            
    def keyReleaseEvent(self, event):
        self.keys_pressed.discard(event.key())

    def mousePressEvent(self, event):
        pos = (event.x(), event.y())
        if event.button() == Qt.LeftButton:
            if self.selected_obj:
                axis = self._pick_gizmo_axis(pos)
                if axis:
                    self.push_undo_state()
                    self._drag_axis = axis
                    self._drag_start = pos
                    self._drag_obj_start_pos = list(self.selected_obj.pos)
                    self._drag_obj_start_rot = list(self.selected_obj.rot)
                    self._drag_obj_start_scale = list(self.selected_obj.scale)
                else:
                    if getattr(self.selected_obj, 'obj_type', '') == 'Terrain' and getattr(self, 'gizmo_mode', '') == 'sculpt':
                        direction = self._screen_to_ray(pos)
                        origin = self.editor_cam_pos
                        plane_p = self.selected_obj.pos
                        plane_n = [0.0, 1.0, 0.0]
                        hit = self._intersect_ray_plane(origin, direction, plane_p, plane_n)
                        if hit:
                            lx = (hit[0] - plane_p[0]) / self.selected_obj.scale[0]
                            lz = (hit[2] - plane_p[2]) / self.selected_obj.scale[2]
                            if -1.0 <= lx <= 1.0 and -1.0 <= lz <= 1.0:
                                self._is_sculpting = True
                                shift_pressed = bool(event.modifiers() & Qt.ShiftModifier)
                                self._apply_sculpt(self.selected_obj, hit, shift_pressed)
                                self.update()
                                try:
                                    import terrain
                                    filepath = self.selected_obj.filepath
                                    try:
                                        project_dir = getattr(self.window(), 'project_dir', None)
                                        if project_dir and not os.path.isabs(filepath):
                                            filepath = os.path.join(project_dir, filepath)
                                    except Exception: pass
                                    terrain.save_terrain_data(filepath, self.selected_obj.name, 
                                        self.selected_obj.scale[0], self.selected_obj.scale[2], 
                                        self.selected_obj.grid_size, self.selected_obj.heightmap)
                                except Exception as e:
                                    pass
                                return
                    
                    picked = self._pick_object(pos)
                    self._set_selection(picked)
            else:
                picked = self._pick_object(pos)
                self._set_selection(picked)
                
        elif event.button() == Qt.RightButton:
            self.right_mouse_down = True
            self.last_mouse_pos = event.globalPos()
            self.setCursor(Qt.BlankCursor)
            
        elif event.button() == Qt.MiddleButton:
            self.middle_mouse_down = True
            self.last_mouse_pos = event.globalPos()
            self.setCursor(Qt.ClosedHandCursor)
            
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_axis = None
            self._drag_start = None
            if getattr(self, '_is_sculpting', False):
                self._is_sculpting = False
                if getattr(self.selected_obj, 'obj_type', '') == 'Terrain':
                    try:
                        import terrain
                        filepath = self.selected_obj.filepath
                        try:
                            project_dir = getattr(self.window(), 'project_dir', None)
                            if project_dir and not os.path.isabs(filepath):
                                filepath = os.path.join(project_dir, filepath)
                        except Exception: pass
                        terrain.save_terrain_data(filepath, self.selected_obj.name, 
                            self.selected_obj.scale[0], self.selected_obj.scale[2], 
                            self.selected_obj.grid_size, self.selected_obj.heightmap)
                    except Exception as e:
                        print("Error saving terrain:", e)
        elif event.button() == Qt.RightButton:
            self.right_mouse_down = False
            self.unsetCursor()
        elif event.button() == Qt.MiddleButton:
            self.middle_mouse_down = False
            self.unsetCursor()
            
    def mouseMoveEvent(self, event):
        pos = (event.x(), event.y())
        
        if getattr(self, '_is_sculpting', False) and self.selected_obj:
            direction = self._screen_to_ray(pos)
            origin = self.editor_cam_pos
            plane_p = self.selected_obj.pos
            plane_n = [0.0, 1.0, 0.0]
            hit = self._intersect_ray_plane(origin, direction, plane_p, plane_n)
            if hit:
                shift_pressed = bool(event.modifiers() & Qt.ShiftModifier)
                if self._apply_sculpt(self.selected_obj, hit, shift_pressed):
                    self.update()
                    try:
                        import terrain
                        filepath = self.selected_obj.filepath
                        try:
                            project_dir = getattr(self.window(), 'project_dir', None)
                            if project_dir and not os.path.isabs(filepath):
                                filepath = os.path.join(project_dir, filepath)
                        except Exception: pass
                        
                        terrain.save_terrain_data(filepath, self.selected_obj.name, 
                            self.selected_obj.scale[0], self.selected_obj.scale[2], 
                            self.selected_obj.grid_size, self.selected_obj.heightmap)
                    except Exception as e:
                        print("Error saving terrain:", e)
            return
            
        if self._drag_axis and self.selected_obj:
            self._handle_gizmo_drag(pos)
            self.update()
            
        if self.right_mouse_down and self.last_mouse_pos:
            global_pos = event.globalPos()
            dx = global_pos.x() - self.last_mouse_pos.x()
            dy = global_pos.y() - self.last_mouse_pos.y()
            
            if dx != 0 or dy != 0:
                self.editor_cam_yaw   += dx * self.rot_speed
                self.editor_cam_pitch += dy * self.rot_speed
                self.editor_cam_pitch  = max(-89.0, min(89.0, self.editor_cam_pitch))
                
                QCursor.setPos(self.last_mouse_pos)
                self.update()
                
        if getattr(self, 'middle_mouse_down', False) and self.last_mouse_pos:
            global_pos = event.globalPos()
            dx = global_pos.x() - self.last_mouse_pos.x()
            dy = global_pos.y() - self.last_mouse_pos.y()
            if dx != 0 or dy != 0:
                right = self._right()
                up = self._up()
                pan_speed = 0.015
                for i in range(3):
                    self.editor_cam_pos[i] -= right[i] * dx * pan_speed
                    self.editor_cam_pos[i] += up[i] * dy * pan_speed
                self.last_mouse_pos = global_pos
                self.update()
                
    def wheelEvent(self, event):
        fwd = self._forward()
        if event.angleDelta().y() > 0:
            for i in range(3): self.editor_cam_pos[i] += fwd[i] * self.zoom_speed
        else:
            for i in range(3): self.editor_cam_pos[i] -= fwd[i] * self.zoom_speed
        self.update()

    # ── Math & Picking ─────────────────────────────────────────────
    def _forward(self):
        p = math.radians(self.editor_cam_pitch)
        y = math.radians(self.editor_cam_yaw)
        return [math.sin(y)*math.cos(p), -math.sin(p), -math.cos(y)*math.cos(p)]

    def _right(self):
        y = math.radians(self.editor_cam_yaw)
        return [math.cos(y), 0.0, math.sin(y)]

    def _up(self):
        fwd = self._forward(); right = self._right()
        return [right[1]*fwd[2]-right[2]*fwd[1], right[2]*fwd[0]-right[0]*fwd[2], right[0]*fwd[1]-right[1]*fwd[0]]

    def _get_world_pos(self, obj):
        if obj.obj_type in ("Button", "Text"):
            pname = getattr(obj, "parent_name", "")
            if pname:
                for o in self.objects:
                    if o.name == pname:
                        s = 0.02
                        return [o.pos[0] + obj.pos[0]*s, o.pos[1] - obj.pos[1]*s, o.pos[2] + obj.pos[2] + 0.01]
        return list(obj.pos)

    def _pick_object(self, screen_pos):
        ray = self._screen_to_ray(screen_pos)
        if ray is None: return None
        best, best_t = None, float('inf')
        for obj in self.objects:
            obj_scale = max(getattr(obj, 'scale', [1, 1, 1]))
            if getattr(obj, 'obj_type', '') in ('camera', 'Sound'): obj_scale = 1.0
            hit_radius = self.HIT_RADIUS * max(1.0, obj_scale)
            t = self._ray_sphere_intersect(self.editor_cam_pos, ray, self._get_world_pos(obj), hit_radius)
            if t is not None and t < best_t:
                best, best_t = obj, t
        return best

    def _screen_to_ray(self, screen_pos):
        w, h = self._current_w, self._current_h
        if h == 0: return None
        sx, sy = screen_pos
        nx = (2.0 * sx / w) - 1.0
        ny = 1.0 - (2.0 * sy / h)
        tan_half = math.tan(math.radians(60) / 2.0)
        aspect   = w / h
        fwd   = self._forward()
        right = self._right()
        up    = self._up()
        ray = [fwd[i] + right[i]*nx*tan_half*aspect + up[i]*ny*tan_half for i in range(3)]
        mag = math.sqrt(sum(v*v for v in ray))
        if mag == 0: return None
        return [v / mag for v in ray]

    def _ray_sphere_intersect(self, origin, direction, center, radius):
        oc = [origin[i] - center[i] for i in range(3)]
        a  = sum(d*d for d in direction)
        b  = 2.0 * sum(oc[i]*direction[i] for i in range(3))
        c  = sum(oc[i]**2 for i in range(3)) - radius**2
        disc = b*b - 4*a*c
        if disc < 0: return None
        t = (-b - math.sqrt(disc)) / (2*a)
        if t < 0: t = (-b + math.sqrt(disc)) / (2*a)
        return t if t >= 0 else None

    def _pick_gizmo_axis(self, screen_pos):
        if not self.selected_obj or not self.gizmo_mode: return None
        if self.gizmo_mode not in ('pos', 'rot', 'scl'): return None
        p = self._get_world_pos(self.selected_obj)
        ray = self._screen_to_ray(screen_pos)
        if not ray: return None
        
        # Scale gizmo length by object scale
        L = self.GIZMO_LEN * max(self.selected_obj.scale)
        if self.selected_obj.obj_type in ('camera', 'Sound'):
            L = self.GIZMO_LEN # Cameras/Sound don't scale gizmo
            if self.gizmo_mode == 'scl':
                return None # Disable scaling
            
        best_axis = None
        best_t = float('inf')
        
        if self.gizmo_mode == 'rot':
            # Check points around the circles for rotation gizmo
            for axis in ('X', 'Y', 'Z'):
                for i in range(12):
                    a = math.radians(i * 30)
                    if axis == 'X':
                        pt = [p[0], p[1] + math.cos(a)*L, p[2] + math.sin(a)*L]
                    elif axis == 'Y':
                        pt = [p[0] + math.cos(a)*L, p[1], p[2] + math.sin(a)*L]
                    else:
                        pt = [p[0] + math.cos(a)*L, p[1] + math.sin(a)*L, p[2]]
                    
                    t = self._ray_sphere_intersect(self.editor_cam_pos, ray, pt, 0.45) # Thicker radius
                    if t is not None and t < best_t:
                        best_t = t
                        best_axis = axis
        else:
            # Check lines for pos and scl gizmos
            checks = {
                'X': [p[0]+L, p[1], p[2]],
                'Y': [p[0], p[1]+L, p[2]],
                'Z': [p[0], p[1], p[2]-L],
            }
            mids = {
                'X': [p[0]+L*0.5, p[1], p[2]],
                'Y': [p[0], p[1]+L*0.5, p[2]],
                'Z': [p[0], p[1], p[2]-L*0.5],
            }
            
            # Check center cube for scale ALL
            if self.gizmo_mode == 'scl':
                t = self._ray_sphere_intersect(self.editor_cam_pos, ray, p, 0.3)
                if t is not None and t < best_t:
                    best_t = t
                    best_axis = 'ALL'

            for name in checks:
                t1 = self._ray_sphere_intersect(self.editor_cam_pos, ray, checks[name], 0.35)
                t2 = self._ray_sphere_intersect(self.editor_cam_pos, ray, mids[name], 0.35)
                for t in (t1, t2):
                    if t is not None and t < best_t:
                        best_t = t
                        best_axis = name
        
        return best_axis

    def _handle_gizmo_drag(self, current_pos):
        if not self._drag_start or not self.selected_obj: return
        dx = current_pos[0] - self._drag_start[0]
        dy = current_pos[1] - self._drag_start[1]
        
        # Calculate exactly 1:1 sensitivity based on camera FOV (60) and screen size
        dist = math.sqrt(sum((self._drag_obj_start_pos[i]-self.editor_cam_pos[i])**2 for i in range(3)))
        h = max(1, self._current_h)
        world_h = 2.0 * dist * math.tan(math.radians(30.0))
        sensitivity = world_h / h
        
        if self.gizmo_mode == 'pos':
            is_ui = self.selected_obj.obj_type in ("Button", "Text")
            s = 50.0 if is_ui else 1.0
            
            if self._drag_axis == 'X':
                self.selected_obj.pos[0] = self._drag_obj_start_pos[0] + dx * sensitivity * s
            elif self._drag_axis == 'Y':
                if is_ui:
                    self.selected_obj.pos[1] = self._drag_obj_start_pos[1] + dy * sensitivity * s
                else:
                    self.selected_obj.pos[1] = self._drag_obj_start_pos[1] - dy * sensitivity
            elif self._drag_axis == 'Z':
                self.selected_obj.pos[2] = self._drag_obj_start_pos[2] - dx * sensitivity * s
        elif self.gizmo_mode == 'rot':
            rot_sens = 0.25  # Make rotation smoother
            if self._drag_axis == 'X':
                self.selected_obj.rot[0] = self._drag_obj_start_rot[0] + dy * rot_sens
            elif self._drag_axis == 'Y':
                self.selected_obj.rot[1] = self._drag_obj_start_rot[1] + dx * rot_sens
            elif self._drag_axis == 'Z':
                self.selected_obj.rot[2] = self._drag_obj_start_rot[2] + dx * rot_sens
        elif self.gizmo_mode == 'scl':
            if self.selected_obj.obj_type in ('camera', 'Sound'):
                return # Prevent camera/sound scaling
                
            if self._drag_axis == 'ALL':
                delta = (dx - dy) * sensitivity
                self.selected_obj.scale[0] = max(0.01, self._drag_obj_start_scale[0] + delta)
                self.selected_obj.scale[1] = max(0.01, self._drag_obj_start_scale[1] + delta)
                self.selected_obj.scale[2] = max(0.01, self._drag_obj_start_scale[2] + delta)
            elif self._drag_axis == 'X':
                self.selected_obj.scale[0] = self._drag_obj_start_scale[0] + dx * sensitivity
            elif self._drag_axis == 'Y':
                self.selected_obj.scale[1] = self._drag_obj_start_scale[1] - dy * sensitivity
            elif self._drag_axis == 'Z':
                self.selected_obj.scale[2] = self._drag_obj_start_scale[2] + dx * sensitivity

    def _get_texture(self, filepath):
        if not filepath: return None
        if not hasattr(self, '_texture_cache'): self._texture_cache = {}
        if filepath in self._texture_cache: return self._texture_cache[filepath]
        try:
            from PyQt5.QtGui import QImage
            img = QImage(filepath)
            if img.isNull(): return None
            img = img.convertToFormat(QImage.Format_RGBA8888)
            w, h = img.width(), img.height()
            ptr = img.bits()
            ptr.setsize(img.byteCount())
            
            tex = glGenTextures(1)
            glBindTexture(GL_TEXTURE_2D, tex)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
            glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, w, h, 0, GL_RGBA, GL_UNSIGNED_BYTE, ptr.asstring())
            self._texture_cache[filepath] = tex
            return tex
        except Exception as e:
            print("Error loading texture:", e)
            self._texture_cache[filepath] = None
            return None

    def _get_obj_model(self, filepath):
        if not filepath: return None
        if not hasattr(self, '_obj_cache'): self._obj_cache = {}
        if filepath in self._obj_cache: return self._obj_cache[filepath]
        
        try:
            vertices = []
            normals = []
            texcoords = []
            faces = []
            
            with open(filepath, 'r') as f:
                for line in f:
                    if line.startswith('#'): continue
                    values = line.split()
                    if not values: continue
                    if values[0] == 'v':
                        vertices.append(list(map(float, values[1:4])))
                    elif values[0] == 'vn':
                        normals.append(list(map(float, values[1:4])))
                    elif values[0] == 'vt':
                        texcoords.append(list(map(float, values[1:3])))
                    elif values[0] == 'f':
                        face = []
                        for v in values[1:]:
                            w = v.split('/')
                            face.append((
                                int(w[0]) if w[0] else None,
                                int(w[1]) if len(w) > 1 and w[1] else None,
                                int(w[2]) if len(w) > 2 and w[2] else None
                            ))
                        faces.append(face)
                        
            display_list = glGenLists(1)
            glNewList(display_list, GL_COMPILE)
            
            glBegin(GL_TRIANGLES)
            for face in faces:
                # triangulate polygon on the fly if needed
                for i in range(1, len(face) - 1):
                    for j in (0, i, i + 1):
                        v_idx, t_idx, n_idx = face[j]
                        if n_idx is not None and n_idx - 1 < len(normals):
                            glNormal3fv(normals[n_idx - 1])
                        if t_idx is not None and t_idx - 1 < len(texcoords):
                            glTexCoord2fv(texcoords[t_idx - 1])
                        if v_idx is not None and v_idx - 1 < len(vertices):
                            glVertex3fv(vertices[v_idx - 1])
            glEnd()
            
            glEndList()
            self._obj_cache[filepath] = display_list
            return display_list
            
        except Exception as e:
            print("Error loading OBJ:", e)
            self._obj_cache[filepath] = None
            return None

    # ── Drawing ─────────────────────────────────────────────
    def _draw_object(self, obj):
        glPushMatrix()
        
        t = obj.obj_type
        if t in ("Button", "Text"):
            pname = getattr(obj, "parent_name", "")
            parent = None
            if pname:
                for o in self.objects:
                    if o.name == pname:
                        parent = o
                        break
            if parent:
                glTranslatef(*parent.pos)
                glRotatef(parent.rot[0], 1,0,0)
                glRotatef(parent.rot[1], 0,1,0)
                glRotatef(parent.rot[2], 0,0,1)
                glScalef(*parent.scale)
            
            s = 0.02
            glTranslatef(obj.pos[0]*s, -obj.pos[1]*s, obj.pos[2] + 0.01)
        else:
            glTranslatef(*obj.pos)
            glRotatef(obj.rot[0], 1,0,0)
            glRotatef(obj.rot[1], 0,1,0)
            glRotatef(obj.rot[2], 0,0,1)
            glScalef(*obj.scale)

        glPushAttrib(GL_ENABLE_BIT)
        glEnable(GL_COLOR_MATERIAL)
        glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)

        if obj.selected:
            glColor3f(1.0, 0.8, 0.0)
        else:
            glColor3f(*obj.color)

        tex = None
        t = obj.obj_type
        if t in ("Square2D", "Circle2D", "Triangle2D", "Custom2D"):
            tex_path = getattr(obj, "filepath", "")
            if tex_path:
                tex = self._get_texture(tex_path)
        elif isinstance(getattr(obj, 'material', None), dict):
            base_tex = obj.material.get('base')
            if base_tex:
                tex = self._get_texture(base_tex)
                
        glMatrixMode(GL_TEXTURE)
        glLoadIdentity()
        if tex:
            glEnable(GL_TEXTURE_2D)
            glBindTexture(GL_TEXTURE_2D, tex)
            
            ox, oy = 0.0, 0.0
            sx, sy = 1.0, 1.0
            mat = getattr(obj, 'material', None)
            if isinstance(mat, dict):
                try: ox = float(mat.get('offset_x', 0.0))
                except: pass
                try: oy = float(mat.get('offset_y', 0.0))
                except: pass
                try: sx = float(mat.get('scale_x', 1.0))
                except: pass
                try: sy = float(mat.get('scale_y', 1.0))
                except: pass
            
            glTranslatef(ox, oy, 0.0)
            glScalef(sx, sy, 1.0)
        else:
            glDisable(GL_TEXTURE_2D)
            
        glMatrixMode(GL_MODELVIEW)
            
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glEnable(GL_ALPHA_TEST)
        glAlphaFunc(GL_GREATER, 0.05)

        if t == "camera":
            # لون برتقالي ذهبي مشرق جداً للكاميرا مع خطوط سميكة
            glDisable(GL_LIGHTING)
            glDisable(GL_TEXTURE_2D)
            glLineWidth(3.0)
            if obj.selected:
                glColor3f(1.0, 1.0, 0.0)   # أصفر ساطع عند التحديد
            else:
                glColor3f(1.0, 0.65, 0.0)  # برتقالي ذهبي
            self._draw_camera_shape()
            glLineWidth(1.0)
        elif t == "Sphere":
            self._draw_sphere()
        elif t == "Plane":
            self._draw_plane()
        elif t == "Terrain":
            self._draw_terrain(obj)
        elif t == "Pyramid":
            self._draw_pyramid()
        elif t == "Cylinder":
            self._draw_cylinder()
        elif t == "Capsule":
            self._draw_capsule()
        elif t == "Square2D":
            self._draw_square2d()
        elif t == "Circle2D":
            self._draw_circle2d()
        elif t == "Triangle2D":
            self._draw_triangle2d()
        elif t == "Custom2D":
            self._draw_square2d()
        elif t == "Sound":
            self._draw_sound_icon()
        elif t in ("Canvas", "Button", "Text"):
            glDisable(GL_LIGHTING)
            glDisable(GL_TEXTURE_2D)
            uw = getattr(obj, "ui_width", 100)
            uh = getattr(obj, "ui_height", 40)
            
            if t == "Canvas" and getattr(obj, "ui_full_screen", False):
                uw = 800
                uh = 600

            # Scale it down so it fits nicely in the 3D world (100 pixels = 1 unit)
            s = 0.02
            uw *= s
            uh *= s

            bg_c = getattr(obj, "ui_bg_color", [0,0,0,0])
            if bg_c[3] > 0:
                glColor4f(bg_c[0], bg_c[1], bg_c[2], bg_c[3])
                glBegin(GL_QUADS)
                glVertex3f(0, 0, 0)
                glVertex3f(uw, 0, 0)
                glVertex3f(uw, -uh, 0)
                glVertex3f(0, -uh, 0)
                glEnd()
            
            if obj.selected:
                glColor4f(1.0, 0.8, 0.0, 1.0)
                glLineWidth(2.0)
            else:
                glColor4f(1.0, 1.0, 1.0, 0.5)
                glLineWidth(1.0)
                
            glBegin(GL_LINE_LOOP)
            glVertex3f(0, 0, 0)
            glVertex3f(uw, 0, 0)
            glVertex3f(uw, -uh, 0)
            glVertex3f(0, -uh, 0)
            glEnd()
            glLineWidth(1.0)
            
            if t in ("Button", "Text"):
                txt_c = getattr(obj, "ui_text_color", [0,0,0,1])
                text_str = getattr(obj, "ui_text", "نص")
                font_size = getattr(obj, "ui_font_size", 32)
                
                # Check for cached texture
                key = (text_str, font_size, tuple(txt_c))
                if not hasattr(self, '_text_textures'): self._text_textures = {}
                
                if key not in self._text_textures:
                    try:
                        import pygame
                        if not pygame.font.get_init(): pygame.font.init()
                        c = (int(txt_c[0]*255), int(txt_c[1]*255), int(txt_c[2]*255), int(txt_c[3]*255))
                        font = pygame.font.SysFont("tahoma", font_size)
                        
                        import bidi.algorithm as bidi
                        import arabic_reshaper
                        
                        # Reshape Arabic text if needed
                        def prep_arabic(txt):
                            try:
                                return bidi.get_display(arabic_reshaper.reshape(txt))
                            except:
                                return txt
                                
                        surf = font.render(prep_arabic(text_str), True, c)
                        tw, th = surf.get_width(), surf.get_height()
                        data = pygame.image.tostring(surf, "RGBA", True)
                        
                        tex = glGenTextures(1)
                        glBindTexture(GL_TEXTURE_2D, tex)
                        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
                        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
                        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, tw, th, 0, GL_RGBA, GL_UNSIGNED_BYTE, data)
                        
                        self._text_textures[key] = (tex, tw, th)
                    except Exception as e:
                        print("Text render error:", e)
                        self._text_textures[key] = (None, 0, 0)
                
                tex, tw, th = self._text_textures[key]
                
                if tex is not None:
                    glEnable(GL_TEXTURE_2D)
                    glBindTexture(GL_TEXTURE_2D, tex)
                    glColor4f(1, 1, 1, 1) # Color is baked in texture
                    
                    # Draw textured quad centered in the element
                    # Scale down text pixels to units
                    ts = 0.02
                    w_units = tw * ts
                    h_units = th * ts
                    tx = (uw - w_units) / 2
                    ty = -(uh - h_units) / 2
                    
                    glBegin(GL_QUADS)
                    glTexCoord2f(0, 1); glVertex3f(tx, ty, 0.01)
                    glTexCoord2f(1, 1); glVertex3f(tx + w_units, ty, 0.01)
                    glTexCoord2f(1, 0); glVertex3f(tx + w_units, ty - h_units, 0.01)
                    glTexCoord2f(0, 0); glVertex3f(tx, ty - h_units, 0.01)
                    glEnd()
                    glDisable(GL_TEXTURE_2D)
        elif t == "CustomModel":
            self._draw_obj_model(obj)
        elif t == "light":
            glDisable(GL_LIGHTING)
            glDisable(GL_TEXTURE_2D)
            glLineWidth(2.0)
            if obj.selected:
                glColor3f(1.0, 1.0, 0.0)   # أصفر عند التحديد
            else:
                glColor3f(1.0, 0.95, 0.4)  # لون الضوء الأصفر الدافئ
            self._draw_light_icon(getattr(obj, 'light_type', 'ضوء_موجه'))
            glLineWidth(1.0)
        else:
            self._draw_cube()
            
        if tex:
            glMatrixMode(GL_TEXTURE)
            glLoadIdentity()
            glMatrixMode(GL_MODELVIEW)
            glDisable(GL_TEXTURE_2D)
            
        glDisable(GL_BLEND)
        glDisable(GL_ALPHA_TEST)

        glPopAttrib()
        glPopMatrix()

    def _draw_camera_shape(self):
        sx, sy, sz = 0.45, 0.32, 0.5   # جسم الكاميرا أكبر

        # الوجه الخلفي (عدسة)
        glBegin(GL_LINE_LOOP)
        glVertex3f(-sx,-sy,-sz); glVertex3f( sx,-sy,-sz)
        glVertex3f( sx, sy,-sz); glVertex3f(-sx, sy,-sz)
        glEnd()

        # الوجه الأمامي
        glBegin(GL_LINE_LOOP)
        glVertex3f(-sx,-sy, sz); glVertex3f( sx,-sy, sz)
        glVertex3f( sx, sy, sz); glVertex3f(-sx, sy, sz)
        glEnd()

        # حواف جسم الكاميرا
        glBegin(GL_LINES)
        glVertex3f(-sx,-sy,-sz); glVertex3f(-sx,-sy, sz)
        glVertex3f( sx,-sy,-sz); glVertex3f( sx,-sy, sz)
        glVertex3f( sx, sy,-sz); glVertex3f( sx, sy, sz)
        glVertex3f(-sx, sy,-sz); glVertex3f(-sx, sy, sz)
        glEnd()

        # هرم الرؤية (frustum) واضح
        tip_z = sz + 0.7
        glBegin(GL_LINES)
        glVertex3f(-sx,-sy, sz); glVertex3f(0, 0, tip_z)
        glVertex3f( sx,-sy, sz); glVertex3f(0, 0, tip_z)
        glVertex3f( sx, sy, sz); glVertex3f(0, 0, tip_z)
        glVertex3f(-sx, sy, sz); glVertex3f(0, 0, tip_z)
        # تقاطع حواف الهرم (للوضوح)
        glVertex3f(-sx,-sy, sz); glVertex3f( sx, sy, sz)
        glVertex3f( sx,-sy, sz); glVertex3f(-sx, sy, sz)
        glEnd()

        # دائرة العدسة الأمامية
        import math
        r = 0.18
        glBegin(GL_LINE_LOOP)
        for a in range(0, 360, 18):
            rad = math.radians(a)
            glVertex3f(r*math.cos(rad), r*math.sin(rad), -sz - 0.05)
        glEnd()

        # مؤشر الأعلى (up indicator)
        glBegin(GL_LINES)
        glVertex3f(0, sy,  0.0); glVertex3f(0, sy + 0.4, 0.0)
        glVertex3f(0, sy + 0.4, 0.0); glVertex3f(-0.12, sy + 0.2, 0.0)
        glVertex3f(0, sy + 0.4, 0.0); glVertex3f( 0.12, sy + 0.2, 0.0)
        glEnd()

    def _draw_light_icon(self, light_type="ضوء_موجه"):
        """يرسم أيقونة الضوء بناء على نوعه"""
        import math
        
        if light_type == "ضوء_نقطي":
            r = 0.4
            
            # Circle XY
            glBegin(GL_LINE_LOOP)
            for i in range(24):
                a = math.radians(i * 15)
                glVertex3f(r * math.cos(a), r * math.sin(a), 0.0)
            glEnd()
            
            # Circle XZ
            glBegin(GL_LINE_LOOP)
            for i in range(24):
                a = math.radians(i * 15)
                glVertex3f(r * math.cos(a), 0.0, r * math.sin(a))
            glEnd()
            
            # Circle YZ
            glBegin(GL_LINE_LOOP)
            for i in range(24):
                a = math.radians(i * 15)
                glVertex3f(0.0, r * math.cos(a), r * math.sin(a))
            glEnd()
            
        elif light_type == "ضوء_بقعي":
            r = 0.3
            h = -0.6
            
            # The base circle
            glBegin(GL_LINE_LOOP)
            for i in range(24):
                a = math.radians(i * 15)
                glVertex3f(r * math.cos(a), h, r * math.sin(a))
            glEnd()
            
            # The lines from origin to the base
            glBegin(GL_LINES)
            for i in range(0, 24, 6): # 4 lines
                a = math.radians(i * 15)
                glVertex3f(0.0, 0.0, 0.0)
                glVertex3f(r * math.cos(a), h, r * math.sin(a))
            glEnd()
            
        else:
            r = 0.35
            ray_len = 0.55
    
            glBegin(GL_LINE_LOOP)
            for i in range(24):
                a = math.radians(i * 15)
                glVertex3f(r * math.cos(a), r * math.sin(a), 0.0)
            glEnd()
    
            glBegin(GL_LINES)
            for i in range(8):
                a = math.radians(i * 45)
                x_inner = (r + 0.1) * math.cos(a)
                y_inner = (r + 0.1) * math.sin(a)
                x_outer = ray_len * math.cos(a)
                y_outer = ray_len * math.sin(a)
                glVertex3f(x_inner, y_inner, 0.0)
                glVertex3f(x_outer, y_outer, 0.0)
            glEnd()

        # نقطة مركزية صغيرة
        glPointSize(5.0)
        glBegin(GL_POINTS)
        glVertex3f(0.0, 0.0, 0.0)
        glEnd()
        glPointSize(1.0)

    def _draw_cube(self):
        s = 1.0
        glBegin(GL_QUADS)
        # Front
        glNormal3f(0,0,1); glTexCoord2f(0,0); glVertex3f(-s,-s, s); glTexCoord2f(1,0); glVertex3f( s,-s, s); glTexCoord2f(1,1); glVertex3f( s, s, s); glTexCoord2f(0,1); glVertex3f(-s, s, s)
        # Back
        glNormal3f(0,0,-1); glTexCoord2f(1,0); glVertex3f(-s,-s,-s); glTexCoord2f(1,1); glVertex3f(-s, s,-s); glTexCoord2f(0,1); glVertex3f( s, s,-s); glTexCoord2f(0,0); glVertex3f( s,-s,-s)
        # Top
        glNormal3f(0,1,0); glTexCoord2f(0,1); glVertex3f(-s, s,-s); glTexCoord2f(0,0); glVertex3f(-s, s, s); glTexCoord2f(1,0); glVertex3f( s, s, s); glTexCoord2f(1,1); glVertex3f( s, s,-s)
        # Bottom
        glNormal3f(0,-1,0); glTexCoord2f(0,0); glVertex3f(-s,-s,-s); glTexCoord2f(1,0); glVertex3f( s,-s,-s); glTexCoord2f(1,1); glVertex3f( s,-s, s); glTexCoord2f(0,1); glVertex3f(-s,-s, s)
        # Right
        glNormal3f(1,0,0); glTexCoord2f(1,0); glVertex3f( s,-s,-s); glTexCoord2f(1,1); glVertex3f( s, s,-s); glTexCoord2f(0,1); glVertex3f( s, s, s); glTexCoord2f(0,0); glVertex3f( s,-s, s)
        # Left
        glNormal3f(-1,0,0); glTexCoord2f(0,0); glVertex3f(-s,-s,-s); glTexCoord2f(1,0); glVertex3f(-s,-s, s); glTexCoord2f(1,1); glVertex3f(-s, s, s); glTexCoord2f(0,1); glVertex3f(-s, s,-s)
        glEnd()
        
    def _draw_sphere(self):
        quad = gluNewQuadric()
        gluQuadricDrawStyle(quad, GLU_FILL)
        gluQuadricNormals(quad, GLU_SMOOTH)
        gluQuadricTexture(quad, GL_TRUE)
        gluSphere(quad, 1.0, 32, 32)
        gluDeleteQuadric(quad)
        
    def _draw_plane(self):
        s = 1.0
        glBegin(GL_QUADS)
        glNormal3f(0,1,0)
        glTexCoord2f(0,0); glVertex3f(-s, 0, -s)
        glTexCoord2f(1,0); glVertex3f( s, 0, -s)
        glTexCoord2f(1,1); glVertex3f( s, 0,  s)
        glTexCoord2f(0,1); glVertex3f(-s, 0,  s)
        glEnd()
        
    def _draw_terrain(self, obj):
        if not hasattr(obj, 'heightmap') or not hasattr(obj, 'grid_size'):
            self._draw_plane()
            return
            
        gs = obj.grid_size
        hm = obj.heightmap
        
        list_id = getattr(obj, 'terrain_list_id', None)
        if list_id is None:
            list_id = glGenLists(1)
            glNewList(list_id, GL_COMPILE)
            
            # The terrain will be from X=-1 to 1, Z=-1 to 1 to match Plane's scale
            # Each cell is 2.0 / (gs - 1)
            step = 2.0 / max(1, gs - 1)
            
            glBegin(GL_TRIANGLES)
            for z in range(gs - 1):
                for x in range(gs - 1):
                    i0 = z * gs + x
                    i1 = i0 + 1
                    i2 = (z + 1) * gs + x
                    i3 = i2 + 1
                    
                    x0 = -1.0 + x * step
                    x1 = -1.0 + (x + 1) * step
                    z0 = -1.0 + z * step
                    z1 = -1.0 + (z + 1) * step
                    
                    y00 = hm[i0]
                    y10 = hm[i1]
                    y01 = hm[i2]
                    y11 = hm[i3]
                    
                    # Simple up normal for now
                    glNormal3f(0, 1, 0)
                    
                    # Triangle 1
                    glTexCoord2f(x/gs, z/gs); glVertex3f(x0, y00, z0)
                    glTexCoord2f((x+1)/gs, z/gs); glVertex3f(x1, y10, z0)
                    glTexCoord2f(x/gs, (z+1)/gs); glVertex3f(x0, y01, z1)
                    
                    # Triangle 2
                    glTexCoord2f((x+1)/gs, z/gs); glVertex3f(x1, y10, z0)
                    glTexCoord2f((x+1)/gs, (z+1)/gs); glVertex3f(x1, y11, z1)
                    glTexCoord2f(x/gs, (z+1)/gs); glVertex3f(x0, y01, z1)
            glEnd()
            glEndList()
            setattr(obj, 'terrain_list_id', list_id)
            
        glCallList(list_id)
        
    def _draw_pyramid(self):
        s = 1.0
        glBegin(GL_QUADS)
        # Base
        glNormal3f(0,-1,0); glTexCoord2f(0,0); glVertex3f(-s,-s,-s); glTexCoord2f(1,0); glVertex3f( s,-s,-s); glTexCoord2f(1,1); glVertex3f( s,-s, s); glTexCoord2f(0,1); glVertex3f(-s,-s, s)
        glEnd()
        glBegin(GL_TRIANGLES)
        # Front
        glNormal3f(0,0.5,0.8); glTexCoord2f(0,0); glVertex3f(-s,-s, s); glTexCoord2f(1,0); glVertex3f( s,-s, s); glTexCoord2f(0.5,1); glVertex3f(0,s,0)
        # Back
        glNormal3f(0,0.5,-0.8); glTexCoord2f(1,0); glVertex3f( s,-s,-s); glTexCoord2f(0,0); glVertex3f(-s,-s,-s); glTexCoord2f(0.5,1); glVertex3f(0,s,0)
        # Right
        glNormal3f(0.8,0.5,0); glTexCoord2f(0,0); glVertex3f( s,-s, s); glTexCoord2f(1,0); glVertex3f( s,-s,-s); glTexCoord2f(0.5,1); glVertex3f(0,s,0)
        # Left
        glNormal3f(-0.8,0.5,0); glTexCoord2f(0,0); glVertex3f(-s,-s,-s); glTexCoord2f(1,0); glVertex3f(-s,-s, s); glTexCoord2f(0.5,1); glVertex3f(0,s,0)
        glEnd()
        
    def _draw_capsule(self):
        quad = gluNewQuadric()
        gluQuadricDrawStyle(quad, GLU_FILL)
        gluQuadricNormals(quad, GLU_SMOOTH)
        gluQuadricTexture(quad, GL_TRUE)
        glPushMatrix()
        glRotatef(-90, 1, 0, 0)
        glTranslatef(0, 0, -1.0)
        gluSphere(quad, 1.0, 32, 32)
        gluCylinder(quad, 1.0, 1.0, 2.0, 32, 1)
        glTranslatef(0, 0, 2.0)
        gluSphere(quad, 1.0, 32, 32)
        glPopMatrix()
        gluDeleteQuadric(quad)

    def _draw_cylinder(self):
        quad = gluNewQuadric()
        gluQuadricDrawStyle(quad, GLU_FILL)
        gluQuadricNormals(quad, GLU_SMOOTH)
        gluQuadricTexture(quad, GL_TRUE)
        glPushMatrix()
        glRotatef(-90, 1, 0, 0)
        glTranslatef(0, 0, -1.0)
        gluCylinder(quad, 1.0, 1.0, 2.0, 32, 1)
        glPopMatrix()
        gluDeleteQuadric(quad)
        
    def _draw_square2d(self):
        s = 0.5
        glBegin(GL_QUADS)
        glNormal3f(0,0,1)
        glTexCoord2f(0,0); glVertex3f(-s, -s, 0)
        glTexCoord2f(1,0); glVertex3f( s, -s, 0)
        glTexCoord2f(1,1); glVertex3f( s,  s, 0)
        glTexCoord2f(0,1); glVertex3f(-s,  s, 0)
        glEnd()
        
    def _draw_obj_model(self, obj):
        filepath = getattr(obj, "filepath", "")
        display_list = self._get_obj_model(filepath)
        if display_list:
            glCallList(display_list)
        else:
            self._draw_custom_model_placeholder()

    def _draw_custom_model_placeholder(self):
        # Draw a wireframe box to indicate a custom 3D model placeholder
        s = 0.5
        glPushAttrib(GL_ENABLE_BIT)
        glDisable(GL_TEXTURE_2D)
        glBegin(GL_QUADS)
        # Front
        glVertex3f(-s,-s, s); glVertex3f( s,-s, s); glVertex3f( s, s, s); glVertex3f(-s, s, s)
        # Back
        glVertex3f(-s,-s,-s); glVertex3f(-s, s,-s); glVertex3f( s, s,-s); glVertex3f( s,-s,-s)
        # Top
        glVertex3f(-s, s,-s); glVertex3f(-s, s, s); glVertex3f( s, s, s); glVertex3f( s, s,-s)
        # Bottom
        glVertex3f(-s,-s,-s); glVertex3f( s,-s,-s); glVertex3f( s,-s, s); glVertex3f(-s,-s, s)
        # Right
        glVertex3f( s,-s,-s); glVertex3f( s, s,-s); glVertex3f( s, s, s); glVertex3f( s,-s, s)
        # Left
        glVertex3f(-s,-s,-s); glVertex3f(-s,-s, s); glVertex3f(-s, s, s); glVertex3f(-s, s,-s)
        glEnd()
        
        # Draw diagonals
        glBegin(GL_LINES)
        glVertex3f(-s,-s,-s); glVertex3f(s,s,s)
        glVertex3f(s,-s,-s); glVertex3f(-s,s,s)
        glVertex3f(-s,-s,s); glVertex3f(s,s,-s)
        glVertex3f(s,-s,s); glVertex3f(-s,s,-s)
        glEnd()
        glPopAttrib()
        
    def _draw_sound_icon(self):
        s = 0.4
        glPushAttrib(GL_ENABLE_BIT)
        glDisable(GL_TEXTURE_2D)
        # Speaker body
        glBegin(GL_QUADS)
        glNormal3f(0,0,1)
        glVertex3f(-s, -s*0.4, 0); glVertex3f(-s*0.3, -s*0.4, 0)
        glVertex3f(-s*0.3,  s*0.4, 0); glVertex3f(-s,  s*0.4, 0)
        glEnd()
        glBegin(GL_TRIANGLES)
        glVertex3f(-s*0.3, -s*0.4, 0); glVertex3f(s*0.2, -s, 0); glVertex3f(-s*0.3, s*0.4, 0)
        glVertex3f(-s*0.3, s*0.4, 0); glVertex3f(s*0.2, -s, 0); glVertex3f(s*0.2, s, 0)
        glEnd()
        
        # Sound waves
        glLineWidth(3.0)
        glBegin(GL_LINE_STRIP)
        for i in range(11):
            a = -0.8 + i * (1.6 / 10)
            glVertex3f(s*0.4 + math.cos(a)*s*0.4, math.sin(a)*s*0.4, 0)
        glEnd()
        glBegin(GL_LINE_STRIP)
        for i in range(11):
            a = -1.0 + i * (2.0 / 10)
            glVertex3f(s*0.5 + math.cos(a)*s*0.8, math.sin(a)*s*0.8, 0)
        glEnd()
        glLineWidth(1.0)
        glPopAttrib()
        
    def _draw_circle2d(self):
        glBegin(GL_TRIANGLE_FAN)
        glNormal3f(0,0,1)
        glVertex3f(0, 0, 0)
        for i in range(33):
            angle = 2 * math.pi * i / 32
            glVertex3f(0.5 * math.cos(angle), 0.5 * math.sin(angle), 0)
        glEnd()
        
    def _draw_triangle2d(self):
        glBegin(GL_TRIANGLES)
        glNormal3f(0,0,1)
        glVertex3f(-0.5, -0.5, 0); glVertex3f(0.5, -0.5, 0); glVertex3f(0, 0.5, 0)
        glEnd()

    def _draw_gizmo(self, obj):
        if not self.gizmo_mode: return
        glPushAttrib(GL_ENABLE_BIT | GL_LINE_BIT)
        glDisable(GL_LIGHTING)
        glDisable(GL_DEPTH_TEST)
        glDisable(GL_TEXTURE_2D)
        glLineWidth(self.GIZMO_THICK)
        ox, oy, oz = self._get_world_pos(obj)
        
        L = self.GIZMO_LEN * max(obj.scale)
        if obj.obj_type == 'camera':
            L = self.GIZMO_LEN
            
        if self.gizmo_mode == 'pos':
            glBegin(GL_LINES)
            glColor3f(0.9,0.2,0.2); glVertex3f(ox,oy,oz); glVertex3f(ox+L,oy,oz)
            glColor3f(0.2,0.9,0.2); glVertex3f(ox,oy,oz); glVertex3f(ox,oy+L,oz)
            glColor3f(0.2,0.4,0.95); glVertex3f(ox,oy,oz); glVertex3f(ox,oy,oz-L)
            glEnd()
            glColor3f(0.9,0.2,0.2);  self._draw_arrow_head(ox+L, oy, oz, 'X')
            glColor3f(0.2,0.9,0.2);  self._draw_arrow_head(ox, oy+L, oz, 'Y')
            glColor3f(0.2,0.4,0.95); self._draw_arrow_head(ox, oy, oz-L, 'Z')
        elif self.gizmo_mode == 'rot':
            self._draw_circle(ox, oy, oz, L, 'X', (0.9,0.2,0.2))
            self._draw_circle(ox, oy, oz, L, 'Y', (0.2,0.9,0.2))
            self._draw_circle(ox, oy, oz, L, 'Z', (0.2,0.4,0.95))
        elif self.gizmo_mode == 'scl':
            if obj.obj_type in ('camera', 'Sound'):
                glLineWidth(1.0)
                glPopAttrib()
                return
                
            glBegin(GL_LINES)
            glColor3f(0.9,0.2,0.2); glVertex3f(ox,oy,oz); glVertex3f(ox+L,oy,oz)
            glColor3f(0.2,0.9,0.2); glVertex3f(ox,oy,oz); glVertex3f(ox,oy+L,oz)
            glColor3f(0.2,0.4,0.95); glVertex3f(ox,oy,oz); glVertex3f(ox,oy,oz-L)
            glEnd()
            glColor3f(0.9,0.2,0.2);  self._draw_cube_head(ox+L, oy, oz)
            glColor3f(0.2,0.9,0.2);  self._draw_cube_head(ox, oy+L, oz)
            glColor3f(0.2,0.4,0.95); self._draw_cube_head(ox, oy, oz-L)
            # Center cube for uniform scale
            glColor3f(0.8, 0.8, 0.2); self._draw_cube_head(ox, oy, oz)

        glLineWidth(1.0)
        glPopAttrib()

    def _draw_circle(self, x, y, z, r, axis, color):
        glColor3f(*color)
        glBegin(GL_LINE_LOOP)
        for i in range(36):
            a = math.radians(i * 10)
            if axis == 'X':
                glVertex3f(x, y + math.cos(a)*r, z + math.sin(a)*r)
            elif axis == 'Y':
                glVertex3f(x + math.cos(a)*r, y, z + math.sin(a)*r)
            elif axis == 'Z':
                glVertex3f(x + math.cos(a)*r, y + math.sin(a)*r, z)
        glEnd()

    def _draw_cube_head(self, x, y, z):
        s = 0.1
        glBegin(GL_LINE_LOOP)
        glVertex3f(x-s,y-s,z-s); glVertex3f(x+s,y-s,z-s); glVertex3f(x+s,y+s,z-s); glVertex3f(x-s,y+s,z-s)
        glEnd()
        glBegin(GL_LINE_LOOP)
        glVertex3f(x-s,y-s,z+s); glVertex3f(x+s,y-s,z+s); glVertex3f(x+s,y+s,z+s); glVertex3f(x-s,y+s,z+s)
        glEnd()
        glBegin(GL_LINES)
        glVertex3f(x-s,y-s,z-s); glVertex3f(x-s,y-s,z+s)
        glVertex3f(x+s,y-s,z-s); glVertex3f(x+s,y-s,z+s)
        glVertex3f(x+s,y+s,z-s); glVertex3f(x+s,y+s,z+s)
        glVertex3f(x-s,y+s,z-s); glVertex3f(x-s,y+s,z+s)
        glEnd()

    def _draw_arrow_head(self, x, y, z, axis):
        s = 0.12
        glBegin(GL_LINES)
        if axis == 'X':
            glVertex3f(x,y,z); glVertex3f(x-s,y+s,z)
            glVertex3f(x,y,z); glVertex3f(x-s,y-s,z)
        elif axis == 'Y':
            glVertex3f(x,y,z); glVertex3f(x+s,y-s,z)
            glVertex3f(x,y,z); glVertex3f(x-s,y-s,z)
        elif axis == 'Z':
            glVertex3f(x,y,z); glVertex3f(x,y+s,z+s)
            glVertex3f(x,y,z); glVertex3f(x,y-s,z+s)
        glEnd()


    def _render_game(self):
        import graphics
        from math_types import Vector3, Color
        if not hasattr(self, 'game_engine') or not self.game_engine:
            self.game_engine = graphics.GraphicsEngine()
        
        engine = self.game_engine
        engine.is_editor_preview = True
        engine._current_w = self._current_w
        engine._current_h = self._current_h
        
        # Calculate scene hash to avoid rebuilding and rebaking AO every frame
        import json
        scene_state = []
        for o in self.objects:
            state = {
                't': o.obj_type,
                'p': o.pos,
                'r': o.rot,
                's': o.scale,
                'c': getattr(o, 'color', [1,1,1]),
                'lt': getattr(o, 'light_type', ''),
                'ld': getattr(o, 'light_direction', []),
                'li': getattr(o, 'light_intensity', 1.0)
            }
            if hasattr(o, 'material'):
                state['m'] = o.material
            scene_state.append(state)
        
        sky_state = {
            'sc': getattr(self, 'sky_color', []),
            'cubemap': getattr(self.sky_cubemap, 'right', '') if getattr(self, 'sky_cubemap', None) else ''
        }
        
        current_hash = hash(json.dumps(scene_state, sort_keys=True) + json.dumps(sky_state, sort_keys=True))
        
        if getattr(self, '_last_scene_hash', None) != current_hash:
            self._last_scene_hash = current_hash
            
            engine.objects = []
            engine.objects_2d = []
            
            # Set Sky
            if getattr(self, 'sky_cubemap', None):
                engine.sky_cubemap = self.sky_cubemap
                engine.sky_color = None
            else:
                engine.sky_color = Color(*self.sky_color)
                engine.sky_cubemap = None
            
            for obj in self.objects:
                g_obj = None
                t = obj.obj_type
                if t == 'Cube': g_obj = graphics.Cube()
                elif t == 'Sphere': g_obj = graphics.Sphere()
                elif t == 'Plane': g_obj = graphics.Plane()
                elif t == 'Pyramid': g_obj = graphics.Pyramid()
                elif t == 'Cylinder': g_obj = graphics.Cylinder()
                elif t == 'Capsule': g_obj = graphics.Capsule()
                elif t == 'CustomModel' and obj.filepath: g_obj = graphics.CustomModel(obj.filepath)
                elif t == 'Custom2D' and obj.filepath: g_obj = graphics.Custom2D(obj.filepath)
                elif t == 'Square2D': g_obj = graphics.Square2D()
                elif t == 'Circle2D': g_obj = graphics.Circle2D()
                elif t == 'Triangle2D': g_obj = graphics.Triangle2D()
                elif t == 'light':
                    new_l = graphics.Light()
                    new_l.النوع = getattr(obj, 'light_type', 'ضوء_موجه')
                    new_l.الموقع = Vector3(*obj.pos)
                    ldir = getattr(obj, 'light_direction', [0,-1,0])
                    new_l.الاتجاه = Vector3(*ldir)
                    c = getattr(obj, 'color', [1,1,1])
                    new_l.اللون = Color(*c)
                    new_l.الشدة = getattr(obj, 'light_intensity', 1.0)
                    engine.lights.append(new_l)
                    continue
                    
                if g_obj:
                    g_obj.الموقع = Vector3(*obj.pos)
                    g_obj.الدوران = Vector3(*obj.rot)
                    g_obj.الحجم = Vector3(*obj.scale)
                    c = getattr(obj, 'color', [1,1,1])
                    g_obj.اللون = Color(*c)
                    if hasattr(obj, 'material') and hasattr(g_obj, 'الخامة'):
                        g_obj.الخامة.base = obj.material.get('base', '')
                        g_obj.الخامة.normal = obj.material.get('normal', '')
                        g_obj.الخامة.metallic = obj.material.get('metallic', '')
                        g_obj.الخامة.roughness = obj.material.get('roughness', '')
                        g_obj.الخامة.ambient_occlusion = obj.material.get('ac', '')
                    
                    if '2D' in t: engine.objects_2d.append(g_obj)
                    else: engine.objects.append(g_obj)
                    
            if engine.ao_enabled and len(engine.objects) > 0:
                engine.ao_baker.bake(engine.objects)
            elif len(engine.objects) > 0:
                for o in engine.objects:
                    o.ao_factors = [1.0] * 6
                    
        engine.camera.الموقع = Vector3(*self.editor_cam_pos)
        engine.camera.الدوران = Vector3(self.editor_cam_pitch, self.editor_cam_yaw, 0)
        
        engine.render_scene()

    def _draw_grid(self):
        glPushAttrib(GL_ENABLE_BIT)
        glDisable(GL_LIGHTING); glDisable(GL_TEXTURE_2D)
        glEnable(GL_BLEND); glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        size, step = 20, 1
        glLineWidth(1.0)
        glBegin(GL_LINES)
        for i in range(-size, size+1, step):
            t = 0.5 if i == 0 else 0.25
            if i==0: glColor4f(0.3,0.45,0.7,0.9)
            else: glColor4f(0.28,0.32,0.4,t)
            glVertex3f(float(i),0,float(-size)); glVertex3f(float(i),0,float(size))
            if i==0: glColor4f(0.7,0.3,0.3,0.9)
            else: glColor4f(0.28,0.32,0.4,t)
            glVertex3f(float(-size),0,float(i)); glVertex3f(float(size),0,float(i))
        glEnd()
        glPopAttrib()

    def _draw_axes(self):
        glPushAttrib(GL_ENABLE_BIT)
        glDisable(GL_LIGHTING); glLineWidth(2.5)
        glBegin(GL_LINES)
        glColor3f(0.9,0.25,0.25); glVertex3f(0,0.01,0); glVertex3f(2,0.01,0)
        glColor3f(0.25,0.9,0.25); glVertex3f(0,0.01,0); glVertex3f(0,2.01,0)
        glColor3f(0.25,0.45,0.9); glVertex3f(0,0.01,0); glVertex3f(0,0.01,2)
        glEnd()
        glLineWidth(1.0); glPopAttrib()

    def _draw_hud(self, w, h):
        glPushAttrib(GL_ENABLE_BIT)
        glDisable(GL_DEPTH_TEST); glDisable(GL_LIGHTING)
        glEnable(GL_BLEND); glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        
        # Original HUD (drawn bottom-left)
        glMatrixMode(GL_PROJECTION); glPushMatrix(); glLoadIdentity()
        glOrtho(0, w, 0, h, -1, 1)
        glMatrixMode(GL_MODELVIEW); glPushMatrix(); glLoadIdentity()
        bx, by, bw, bh = 10, 10, 270, 55
        glColor4f(0.05,0.08,0.13,0.75)
        glBegin(GL_QUADS)
        glVertex2f(bx,by); glVertex2f(bx+bw,by); glVertex2f(bx+bw,by+bh); glVertex2f(bx,by+bh)
        glEnd()
        glColor4f(0.3,0.4,0.6,0.5)
        glBegin(GL_LINE_LOOP)
        glVertex2f(bx,by); glVertex2f(bx+bw,by); glVertex2f(bx+bw,by+bh); glVertex2f(bx,by+bh)
        glEnd()
        glPopMatrix(); glMatrixMode(GL_PROJECTION); glPopMatrix()
        glMatrixMode(GL_MODELVIEW); glPopAttrib()

    def _intersect_ray_plane(self, origin, direction, plane_p, plane_n):
        denom = sum(plane_n[i] * direction[i] for i in range(3))
        if abs(denom) > 1e-6:
            num = sum(plane_n[i] * (plane_p[i] - origin[i]) for i in range(3))
            t = num / denom
            if t >= 0:
                return [origin[i] + direction[i] * t for i in range(3)]
        return None

    def _apply_sculpt(self, obj, hit_world, shift_pressed=False):
        lx = (hit_world[0] - obj.pos[0]) / obj.scale[0]
        lz = (hit_world[2] - obj.pos[2]) / obj.scale[2]
        
        gs = getattr(obj, 'grid_size', 50)
        hm = getattr(obj, 'heightmap', None)
        if not hm: 
            hm = [0.0] * (gs * gs)
            setattr(obj, 'heightmap', hm)
        
        rad = self.brush_radius / max(0.001, obj.scale[0])
        strength = self.brush_strength * 0.1
        mode = getattr(self, 'brush_mode', 0)
        
        if shift_pressed:
            if mode == 0: mode = 1
            elif mode == 1: mode = 0
        
        modified = False
        step = 2.0 / max(1, gs - 1)
        for z in range(gs):
            for x in range(gs):
                vx = -1.0 + x * step
                vz = -1.0 + z * step
                
                dist = math.sqrt((vx - lx)**2 + (vz - lz)**2)
                if dist < rad:
                    idx = z * gs + x
                    falloff = 1.0 - (dist / rad)
                    amount = strength * falloff
                    
                    if mode == 0:
                        hm[idx] += amount
                        modified = True
                    elif mode == 1:
                        hm[idx] -= amount
                        modified = True
                    elif mode == 2:
                        count = 0
                        total = 0
                        for dz in [-1, 0, 1]:
                            for dx in [-1, 0, 1]:
                                nx, nz = x + dx, z + dz
                                if 0 <= nx < gs and 0 <= nz < gs:
                                    total += hm[nz * gs + nx]
                                    count += 1
                        avg = total / count
                        hm[idx] = hm[idx] * (1.0 - amount) + avg * amount
                        modified = True
                        
        if modified:
            list_id = getattr(obj, 'terrain_list_id', None)
            if list_id is not None:
                glDeleteLists(list_id, 1)
                setattr(obj, 'terrain_list_id', None)
                
        return modified
