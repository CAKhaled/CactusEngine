class Vec2:
    def __init__(self, x=0.0, y=0.0):
        self.x = float(x)
        self.y = float(y)
    def __repr__(self):
        return f"({self.x}, {self.y})"

from rigidbody import PhysicsEngine
from math_types import Vector3, Vector2, Color, TimeInfo
from ambient_occlusion import AOBaker
from mouse import Mouse
from keyboard import Keyboard
import pygame
from model_loader import load_obj

from pygame.locals import DOUBLEBUF, OPENGL

from OpenGL.GL import *
from OpenGL.GLU import *

try:
    import arabic_reshaper
    from bidi.algorithm import get_display
    HAS_ARABIC = True
except ImportError:
    HAS_ARABIC = False

try:
    import assimp_py
    HAS_PYASSIMP = True
except:
    HAS_PYASSIMP = False

def assimp_to_objmesh(assimp_mesh):
    from model_loader import OBJMesh
    out = OBJMesh()
    verts = list(assimp_mesh.vertices)
    for i in range(0, len(verts), 3):
        out.vertices.append((float(verts[i]), float(verts[i+1]), float(verts[i+2])))
    if hasattr(assimp_mesh, 'normals') and assimp_mesh.normals:
        norms = list(assimp_mesh.normals)
        if len(norms) > 0:
            for i in range(0, len(norms), 3):
                out.normals.append((float(norms[i]), float(norms[i+1]), float(norms[i+2])))
    if hasattr(assimp_mesh, 'texcoords') and assimp_mesh.texcoords and len(assimp_mesh.texcoords) > 0:
        texs = list(assimp_mesh.texcoords[0])
        if len(texs) > 0:
            for i in range(0, len(texs), 3):
                out.texcoords.append((float(texs[i]), float(texs[i+1])))
    indices = list(assimp_mesh.indices)
    for i in range(0, len(indices), 3):
        face_v = [int(indices[i]), int(indices[i+1]), int(indices[i+2])]
        face_t = face_v if hasattr(assimp_mesh, 'texcoords') and assimp_mesh.texcoords else [-1, -1, -1]
        face_n = face_v if hasattr(assimp_mesh, 'normals') and assimp_mesh.normals else [-1, -1, -1]
        out.faces.append((face_v, face_t, face_n))
    return out


def _compute_mesh_local_aabb(vertices_list):
    """يحسب AABB المحلي الضيق من قائمة النقاط (x,y,z)"""
    if not vertices_list:
        return (-1, -1, -1), (1, 1, 1)
    xs = [v[0] for v in vertices_list]
    ys = [v[1] for v in vertices_list]
    zs = [v[2] for v in vertices_list]
    return (min(xs), min(ys), min(zs)), (max(xs), max(ys), max(zs))


class CubeMapSky:
    def __init__(self, right, left, top, bottom, front, back):
        self.الاسم = ""
        self.الاسم = ""
        self.right = right
        self.left = left
        self.top = top
        self.bottom = bottom
        self.front = front
        self.back = back
        self.textures = None

class Material:
    def __init__(self):
        self.base = None
        self.metallic = None
        self.roughness = None
        self.normal = None
        self.AC = None
        self.offset = Vec2(0.0, 0.0)
        self.scale = Vec2(1.0, 1.0)

    def __repr__(self):
        return f"Material(base={self.base}, metallic={self.metallic}, roughness={self.roughness}, normal={self.normal}, AC={self.AC}, offset=({self.offset.x}, {self.offset.y}), scale=({self.scale.x}, {self.scale.y}))"

class Canvas:
    def __init__(self):
        self.elements = []
        self.كامل_الشاشة = False
        from math_types import Vector2, Color
        self.المقياس = Vector2(200, 200)
        self.الموقع = Vector2(0, 0)
        self.لون_الخلفية = Color(0, 0, 0)
        
    def اضافة_نص(self, text):
        obj = UIText(text)
        self.elements.append(obj)
        return obj

    def اضافة_زر(self, text):
        obj = UIButton(text)
        self.elements.append(obj)
        return obj

class UIText:
    def __init__(self, text):
        self.النص = str(text)
        self.عمودي = "فوق" # فوق, وسط, تحت
        self.افقي = "يسار" # يمين, وسط, يسار
        self.ازاحة = Vector2(0, 0)
        self.لون_النص = Color(1, 1, 1)
        self.الصورة = ""
        self.حجم_الخط = 32
        self.اسم_الخط = "tahoma"
        
        # Internal rendering properties
        self.texture_id = None
        self._last_text = None
        self._last_color = None
        self._last_size = None
        self._last_font_name = None
        self.width = 0
        self.height = 0

    @property
    def الموقع(self):
        return self.ازاحة

    @الموقع.setter
    def الموقع(self, value):
        self.ازاحة = value

class UIButton(UIText):
    def __init__(self, text):
        super().__init__(text)
        self.لون_الخلفية = Color(0.3, 0.3, 0.3)
        self.المقياس = Vector2(0, 0)
        self.الخامة = None
        self.مضغوط = False
        self._hover = False
        self.texture_id_bg = None


class Camera:
    def __init__(self):
        self.الموقع = Vector3(0, 0, 0)
        self.الدوران = Vector3(0, 0, 0)
        self.زاوية_الرؤية = 60.0
        self.engine = None
        
        # خصائص الفيزياء
        self.الاسم = "الكاميرا"
        self.المقياس = Vector3(0.5, 1.0, 0.5)
        self.تصادم = False
        self.جاذبية = 0
        self.صدام = 0
        self._velocity = Vector3(0, 0, 0)
        
    def اشعاع(self, مدى=1000.0):
        if self.engine is None:
            return None
        return self.engine.physics_engine._raycast(self.الموقع, self.الأمام, self.engine.objects, مدى)

    def __repr__(self):
        return f"Camera(Pos={self.الموقع}, Rot={self.الدوران})"

    @property
    def الأمام(self):
        import math
        pitch = math.radians(self.الدوران.x)
        yaw = math.radians(self.الدوران.y)
        dx = math.sin(yaw) * math.cos(pitch)
        dy = -math.sin(pitch)
        dz = -math.cos(yaw) * math.cos(pitch)
        return Vector3(dx, dy, dz)

    @property
    def اليمين(self):
        import math
        yaw = math.radians(self.الدوران.y)
        dx = math.cos(yaw)
        dy = 0
        dz = math.sin(yaw)
        return Vector3(dx, dy, dz)

class Cube:

    def __init__(self):
        self.الاسم = ""
        self.الموقع = Vector3(0, 0, -5)
        self.الدوران = Vector3(0, 0, 0)
        self.المقياس = Vector3(1, 1, 1)

        self.اللون = Color(1,1,1)

        self.الخامة = Material()
        self.تصادم = False
        self.جاذبية = 0
        self.صدام = 0
        self._velocity = Vector3(0, 0, 0)

    def __repr__(self):
        return f"Cube(Pos={self.الموقع}, Rot={self.الدوران}, Scale={self.المقياس})"

class CustomModel:
    def __init__(self, filename):
        self.الاسم = ""
        self.الاسم = ""
        self.الموقع = Vector3(0, 0, 0)
        self.الدوران = Vector3(0, 0, 0)
        self.المقياس = Vector3(1, 1, 1)
        self.اللون = Color(1,1,1)
        self.الخامة = Material()
        self.تصادم = False
        self.جاذبية = 0
        self.صدام = 0
        self._velocity = Vector3(0, 0, 0)
        
        self.mesh = load_obj(filename)
        self.display_list = None

    def __repr__(self):
        return f"CustomModel(Pos={self.الموقع}, Rot={self.الدوران}, Scale={self.المقياس})"

class FBXComponent(CustomModel):
    def __init__(self, name, mesh, parent=None):
        self.الاسم = name
        self.الموقع = Vector3(0, 0, 0)
        self.الدوران = Vector3(0, 0, 0)
        self.المقياس = Vector3(1, 1, 1)
        self.اللون = Color(1,1,1)
        self.الخامة = Material()
        self.تصادم = False
        self.جاذبية = 0
        self.صدام = 0
        self._velocity = Vector3(0, 0, 0)
        self.mesh = mesh
        self.display_list = None
        self.parent = parent
        # مكونات فرعية (للدعم المستقبلي للتسلسل الهرمي في FBX)
        self._sub_components = {}
        self.المكون = SubComponentAccessor(self)
    
    def __repr__(self):
        return f"FBXComponent(Name={self.الاسم}, Pos={self.الموقع})"


class ComponentAccessor(list):
    """
    يعمل كقائمة وكدالة في آن واحد:
      سيارة.المكون          → قائمة بجميع المكونات
      سيارة.المكون[0]       → المكون الأول
      سيارة.المكون("عجلة")  → مكون باسم معين
      سيارة.المكون.طول      → عدد المكونات
    """
    def __init__(self, model):
        super().__init__(model.components.values())
        self.model = model

    # ── الاستدعاء بالاسم: سيارة.المكون("عجلة") ──────────────────────────
    def __call__(self, name):
        return self.model._get_component(name)

    @property
    def طول(self):
        return len(self)

    def __str__(self):
        names = list(self.model.components.keys())
        return str(names).replace("'", '"')

    def __repr__(self):
        return self.__str__()


class SubComponentAccessor(list):
    """
    يُستخدم على FBXComponent نفسه للوصول لمكوناته الفرعية (إذا وُجدت).
    يدعم: الاستدعاء بالاسم، الفهرسة، والتكرار.
    """
    def __init__(self, component):
        sub_comps = list(getattr(component, '_sub_components', {}).values())
        super().__init__(sub_comps)
        self._comp = component

    def __call__(self, name):
        sub = getattr(self._comp, '_sub_components', {})
        return sub.get(name, None)

    @property
    def طول(self):
        return len(self)

    def __str__(self):
        names = list(getattr(self._comp, '_sub_components', {}).keys())
        return str(names).replace("'", '"') if names else "[]"

    def __repr__(self):
        return self.__str__()

class FBXModel:
    # الخصائص التي تنتشر تلقائياً لجميع المكونات الداخلية
    _PROPAGATED_PROPS = {'الموقع', 'الدوران', 'المقياس', 'اللون', 'الخامة', 'جاذبية', 'صدام', 'تصادم'}
    
    def __init__(self, engine, filename):
        self.الاسم = ""
        self.الموقع = Vector3(0, 0, 0)
        self.الدوران = Vector3(0, 0, 0)
        self.المقياس = Vector3(1, 1, 1)
        self.اللون = Color(1,1,1)
        self.الخامة = None
        self.تصادم = False
        self.جاذبية = 0
        self.صدام = 0
        self.engine = engine
        self._velocity = Vector3(0, 0, 0)
        
        self.filename = filename
        self.scene = None
        self.components = {}
        
        if HAS_PYASSIMP:
            try:
                self.scene = assimp_py.import_file(filename, assimp_py.Process_Triangulate)
                
                # حساب AABB المحلي الضيق من جميع vertices في الملف
                all_verts = []
                for m in self.scene.meshes:
                    obj_mesh = assimp_to_objmesh(m)
                    all_verts.extend(obj_mesh.vertices)
                    comp = FBXComponent(m.name, obj_mesh, parent=self)
                    self.components[m.name] = comp
                    self.engine.objects.append(comp)
                
                # تخزين حدود AABB المحلية الفعلية من الشبكة
                mn, mx = _compute_mesh_local_aabb(all_verts)
                self._local_min = Vector3(mn[0], mn[1], mn[2])
                self._local_max = Vector3(mx[0], mx[1], mx[2])
                
            except Exception as e:
                print(f"حدث خطأ أثناء تحميل FBX ({filename}): {e}")
                self.scene = None
        else:
            print(f"لا يمكن تحميل FBX ({filename}): مكتبة assimp_py غير متوفرة أو غير صالحة.")
            
        self.المكون = ComponentAccessor(self)

    def __setattr__(self, name, value):
        super().__setattr__(name, value)
        # بث الخاصية لجميع المكونات إذا كانت خاصية تنتشر
        if name in FBXModel._PROPAGATED_PROPS:
            comps = self.__dict__.get('components', {})
            for comp in comps.values():
                object.__setattr__(comp, name, value)
            
    def _get_component(self, اسم_المكون):
        if not self.scene:
            print(f"لا يمكن استخراج المكون '{اسم_المكون}' لعدم توفر بيانات FBX صحيحة.")
            from model_loader import OBJMesh
            comp = FBXComponent(اسم_المكون, OBJMesh(), parent=self)
            self.engine.objects.append(comp)
            return comp
            
        if اسم_المكون in self.components:
            return self.components[اسم_المكون]
        else:
            print(f"لم يتم العثور على المكون '{اسم_المكون}' أو لا يحتوي على مجسم (Mesh).")
            from model_loader import OBJMesh
            comp = FBXComponent(اسم_المكون, OBJMesh(), parent=self)
            self.engine.objects.append(comp)
            return comp


class Square2D:
    def __init__(self):
        self.الاسم = ""
        self.الموقع = Vector3(0, 0, -5)
        self.الدوران = Vector3(0, 0, 0)
        self.المقياس = Vector3(1, 1, 1)
        self.اللون = Color(1,1,1)
        self.الخامة = None
        self.الصورة = ""   # مسار الصورة للشكل 2D
        self.تصادم = False
        self.جاذبية = 0
        self.صدام = False
        self._velocity = Vector3(0, 0, 0)
    def __repr__(self): return f"Square2D(Pos={self.الموقع})"

class Circle2D:
    def __init__(self):
        self.الاسم = ""
        self.الموقع = Vector3(0, 0, -5)
        self.الدوران = Vector3(0, 0, 0)
        self.المقياس = Vector3(1, 1, 1)
        self.اللون = Color(1,1,1)
        self.الخامة = None
        self.الصورة = ""   # مسار الصورة للشكل 2D
        self.تصادم = False
        self.جاذبية = 0
        self.صدام = False
        self._velocity = Vector3(0, 0, 0)
    def __repr__(self): return f"Circle2D(Pos={self.الموقع})"

class Triangle2D:
    def __init__(self):
        self.الاسم = ""
        self.الموقع = Vector3(0, 0, -5)
        self.الدوران = Vector3(0, 0, 0)
        self.المقياس = Vector3(1, 1, 1)
        self.اللون = Color(1,1,1)
        self.الخامة = None
        self.الصورة = ""   # مسار الصورة للشكل 2D
        self.تصادم = False
        self.جاذبية = 0
        self.صدام = False
        self._velocity = Vector3(0, 0, 0)
    def __repr__(self): return f"Triangle2D(Pos={self.الموقع})"

class Custom2D:
    def __init__(self, filename):
        self.الاسم = ""
        self.الموقع = Vector3(0, 0, -5)
        self.الدوران = Vector3(0, 0, 0)
        self.المقياس = Vector3(1, 1, 1)
        self.اللون = Color(1,1,1)
        self.الخامة = filename
        self.تصادم = False
        self.جاذبية = 0
        self.صدام = False
        self._velocity = Vector3(0, 0, 0)
        self.texture_id = None
    def __repr__(self): return f"Custom2D(Pos={self.الموقع})"

class Sphere:
    def __init__(self):
        self.الاسم = ""
        self.الموقع = Vector3(0, 0, -5)
        self.الدوران = Vector3(0, 0, 0)
        self.المقياس = Vector3(1, 1, 1)
        self.اللون = Color(1,1,1)
        self.الخامة = Material()
        self.تصادم = False
        self.جاذبية = 0
        self.صدام = False
        self._velocity = Vector3(0, 0, 0)
    def __repr__(self): return f"Sphere(Pos={self.الموقع})"

class Plane:
    def __init__(self):
        self.الاسم = ""
        self.الموقع = Vector3(0, 0, -5)
        self.الدوران = Vector3(0, 0, 0)
        self.المقياس = Vector3(1, 1, 1)
        self.اللون = Color(1,1,1)
        self.الخامة = Material()
        self.تصادم = False
        self.جاذبية = 0
        self.صدام = False
        self._velocity = Vector3(0, 0, 0)
    def __repr__(self): return f"Plane(Pos={self.الموقع})"

class Terrain:
    def __init__(self, filename):
        self.الاسم = ""
        self.الموقع = Vector3(0, 0, -5)
        self.الدوران = Vector3(0, 0, 0)
        self.المقياس = Vector3(1, 1, 1)
        self.اللون = Color(1,1,1)
        self.الخامة = Material()
        self.تصادم = False
        self.جاذبية = 0
        self.صدام = False
        self._velocity = Vector3(0, 0, 0)
        self.grid_size = 2
        self.heightmap = [0.0, 0.0, 0.0, 0.0]
        self.filepath = filename
        
        if filename:
            try:
                import terrain
                import sys, os
                script_dir = os.path.dirname(os.path.abspath(sys.argv[1])) if len(sys.argv) > 1 else ""
                full_path = os.path.join(script_dir, filename) if script_dir else filename
                sx, sz, gs, hm = terrain.load_terrain_data(full_path)
                self.grid_size = gs
                self.heightmap = hm
                self.المقياس = Vector3(sx, 1.0, sz)
            except Exception as e:
                print("Error loading terrain in game:", e)
                
    def __repr__(self): return f"Terrain(Pos={self.الموقع})"

class Pyramid:
    def __init__(self):
        self.الاسم = ""
        self.الموقع = Vector3(0, 0, -5)
        self.الدوران = Vector3(0, 0, 0)
        self.المقياس = Vector3(1, 1, 1)
        self.اللون = Color(1,1,1)
        self.الخامة = Material()
        self.تصادم = False
        self.جاذبية = 0
        self.صدام = False
        self._velocity = Vector3(0, 0, 0)
    def __repr__(self): return f"Pyramid(Pos={self.الموقع})"

class Cylinder:
    def __init__(self):
        self.الاسم = ""
        self.الموقع = Vector3(0, 0, -5)
        self.الدوران = Vector3(0, 0, 0)
        self.المقياس = Vector3(1, 1, 1)
        self.اللون = Color(1,1,1)
        self.الخامة = Material()
        self.تصادم = False
        self.جاذبية = 0
        self.صدام = False
        self._velocity = Vector3(0, 0, 0)
    def __repr__(self): return f"Cylinder(Pos={self.الموقع})"

class Capsule:
    def __init__(self):
        self.الاسم = ""
        self.الموقع = Vector3(0, 0, -5)
        self.الدوران = Vector3(0, 0, 0)
        self.المقياس = Vector3(1, 1, 1)
        self.اللون = Color(1,1,1)
        self.الخامة = Material()
        self.تصادم = False
        self.جاذبية = 0
        self.صدام = False
        self._velocity = Vector3(0, 0, 0)
    def __repr__(self): return f"Capsule(Pos={self.الموقع})"

class Light:

    def __init__(self):

        # النوع: ضوء_نقطي | ضوء_موجه | ضوء_بقعي
        self.النوع = "ضوء_نقطي"

        # الموقع — يُستخدم في الضوء النقطي والبقعي
        self.الموقع = Vector3(5, 5, 5)

        # الاتجاه — يُستخدم في الضوء الموجه والبقعي
        self.الاتجاه = Vector3(0, -1, 0)

        self.اللون = Color(1, 1, 1)
        self.الصورة = ""
        self.الشدة = 1.0

        # خصائص الضوء البقعي
        self.زاوية_البقعة = 30.0    # زاوية المخروط بالدرجات (1-90)
        self.حدة_البقعة = 64.0     # حدة الحواف (0-128)

        # التضاؤل — لتحديد مدى تأثير المسافة على الضوء النقطي/البقعي
        self.التضاؤل_الثابت = 1.0
        self.التضاؤل_الخطي = 0.05
        self.التضاؤل_التربيعي = 0.01

class Sound:
    def __init__(self, filename):
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            self.sound = pygame.mixer.Sound(filename)
        except Exception as e:
            print(f"تعذر تحميل الصوت {filename}: {e}")
            self.sound = None

    def تشغيل(self):
        if self.sound:
            self.sound.play()

    def إيقاف(self):
        if self.sound:
            self.sound.stop()


class GraphicsEngine:

    def __init__(self):

        self.objects = []
        self.objects_2d = []
        self.lights = []
        self.running = False

        self.camera = Camera()
        self.camera.engine = self

        # إعدادات Ambient Occlusion
        self.ao_baker    = AOBaker(num_samples=32, max_distance=6.0, strength=0.75)
        self.ao_enabled  = True   # يمكن تعطيله بـ engine.ao_enabled = False

        # كائن الماوس — يُربط بالمتغير 'ماوس' في المفسّر
        self.mouse = Mouse()

        # كائن لوحة المفاتيح — يُربط بالمتغير 'كيبورد' في المفسّر
        self.keyboard = Keyboard()

        # إعدادات السماء (Skybox)
        self.sky_color = None
        self.sky_texture = None
        self.sky_cubemap = None
        self.shadows = True
        self.is_rendering_shadow = False
        
        # محرك الفيزياء
        self.physics_engine = PhysicsEngine()
        
        try:
            from tonemapping import Tonemapper
            self.tonemapper = None # Tonemapper(800, 600)  (Disabled temporarily)
        except Exception as e:
            print("Tonemapping Error:", e)
            self.tonemapper = None
            
        self.time = TimeInfo()
        self.canvas = None

    def create_canvas(self):
        self.canvas = Canvas()
        return self.canvas

    def create_light(self):
        new_light = Light()
        if not hasattr(self, 'lights'):
            self.lights = []
        self.lights.append(new_light)
        return new_light

    def create_sound(self, filename):
        return Sound(filename)

    def صنع_سماء_cubemap(self, right, left, top, bottom, front, back):
        return CubeMapSky(right, left, top, bottom, front, back)

    def set_sky(self, texture_or_color):
        if isinstance(texture_or_color, Color):
            self.sky_color = texture_or_color
            self.sky_texture = None
            self.sky_cubemap = None
        elif isinstance(texture_or_color, CubeMapSky):
            self.sky_cubemap = texture_or_color
            self.sky_texture = None
            self.sky_color = None
        else:
            self.sky_texture = texture_or_color
            self.sky_color = None
            self.sky_cubemap = None

    def _bind_tex(self, obj):
        tex_id = obj.الخامة.base if isinstance(obj.الخامة, Material) else getattr(obj, "الخامة", None)
        if isinstance(tex_id, str):
            try:
                import textures
                new_id = textures.load_texture(tex_id)
                if isinstance(obj.الخامة, Material):
                    obj.الخامة.base = new_id
                else:
                    obj.الخامة = new_id
                tex_id = new_id
            except Exception as e:
                print(f"Error loading texture {tex_id}: {e}")
        
        if tex_id is not None and not isinstance(tex_id, str) and tex_id != -1:
            glEnable(GL_TEXTURE_2D)
            glBindTexture(GL_TEXTURE_2D, tex_id)
            
            from OpenGL.GL import glMatrixMode, GL_TEXTURE, GL_MODELVIEW, glLoadIdentity, glTranslatef, glScalef
            glMatrixMode(GL_TEXTURE)
            glLoadIdentity()
            
            sx, sy = 1.0, 1.0
            ox, oy = 0.0, 0.0
            mat = getattr(obj, 'الخامة', None)
            if isinstance(mat, dict):
                try:
                    sx = float(mat.get('scale_x', 1.0))
                    sy = float(mat.get('scale_y', 1.0))
                except: pass
            else:
                if hasattr(mat, 'scale'):
                    sx = float(mat.scale.x)
                    sy = float(mat.scale.y)
                
            glTranslatef(ox, oy, 0.0)
            glScalef(sx, sy, 1.0)
            glMatrixMode(GL_MODELVIEW)
            
            return True
        else:
            glDisable(GL_TEXTURE_2D)
            return False



    def _apply_material(self, obj, base_r, base_g, base_b):
        has_tex = self._bind_tex(obj)
        if has_tex:
            base_r, base_g, base_b = 1.0, 1.0, 1.0
            
        from OpenGL.GL import glMaterialfv, GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE, GL_SPECULAR, glMaterialf, GL_SHININESS
        from OpenGL.GL import glMaterialfv, GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE, GL_SPECULAR, glMaterialf, GL_SHININESS
        glMaterialfv(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE, (base_r, base_g, base_b, 1.0))
        
        metallic = 0.0
        roughness = 0.5
        if hasattr(obj, 'الخامة'):
            mat = obj.الخامة
            # Can be dict in editor or Material instance in game
            if isinstance(mat, dict):
                try:
                    metallic = float(mat.get('metallic', 0.0))
                    roughness = float(mat.get('roughness', 0.5))
                except: pass
            else:
                if getattr(mat, 'metallic', None) is not None:
                    try: metallic = float(mat.metallic)
                    except: pass
                if getattr(mat, 'roughness', None) is not None:
                    try: roughness = float(mat.roughness)
                    except: pass
                    
        spec = metallic
        glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR, (spec, spec, spec, 1.0))
        
        shininess = max(0.0, min(128.0, (1.0 - roughness) * 128.0))
        glMaterialf(GL_FRONT_AND_BACK, GL_SHININESS, shininess)
        return has_tex

    def draw_custom(self, model):
        if not model.mesh:
            return

        if model.display_list is None:
            model.display_list = glGenLists(1)
            glNewList(model.display_list, GL_COMPILE)
            
            glBegin(GL_TRIANGLES)
            for face in model.mesh.faces:
                # face is (face_v, face_t, face_n)
                for vertex_idx, tex_idx, norm_idx in zip(face[0], face[1], face[2]):
                    if norm_idx is not None and norm_idx > 0:
                        nx, ny, nz = model.mesh.normals[norm_idx - 1]
                        glNormal3f(nx, ny, nz)
                    if tex_idx is not None and tex_idx > 0:
                        u, v = model.mesh.texcoords[tex_idx - 1]
                        glTexCoord2f(u, v)
                    vx, vy, vz = model.mesh.vertices[vertex_idx - 1]
                    glVertex3f(vx, vy, vz)
            glEnd()
            glEndList()

        if getattr(model, "texture_id", None) is None and getattr(model, "الخامة", None):
            try:
                import textures
                model.texture_id = textures.load_texture(model.الخامة)
            except:
                model.texture_id = -1
        
        if getattr(model, "texture_id", -1) != -1 and model.texture_id is not None:
            glEnable(GL_TEXTURE_2D)
            glBindTexture(GL_TEXTURE_2D, model.texture_id)
            glColor4f(model.اللون.r, model.اللون.g, model.اللون.b, 1.0)
        else:
            glDisable(GL_TEXTURE_2D)
            glColor3f(model.اللون.r, model.اللون.g, model.اللون.b)

        glCallList(model.display_list)

    def create_window(self, title, width, height):
        pygame.init()

        import os, sys
        self.flags = DOUBLEBUF | OPENGL
        self._is_external_window = os.environ.get("KH_USER_WINDOW") == "1"
        
        pygame.display.gl_set_attribute(pygame.GL_STENCIL_SIZE, 8)
        if os.environ.get("KH_EMBEDDED") == "1" and not self._is_external_window:
            from pygame.locals import NOFRAME, RESIZABLE
            self.flags |= NOFRAME | RESIZABLE

        pygame.display.set_mode(
            (width, height),
            self.flags
        )

        pygame.display.set_caption(title)

        if os.environ.get("KH_EMBEDDED") == "1":
            hwnd = pygame.display.get_wm_info()["window"]
            if self._is_external_window:
                # User explicitly called نافذة() - run as external floating window
                # Restore default window style (show title bar, border)
                import ctypes
                GWL_STYLE = -16
                WS_OVERLAPPEDWINDOW = 0x00CF0000
                ctypes.windll.user32.SetWindowLongW(hwnd, GWL_STYLE, WS_OVERLAPPEDWINDOW)
                SWP_FRAMECHANGED = 0x0020
                SWP_NOZORDER = 0x0004
                SWP_NOSIZE = 0x0001
                SWP_NOMOVE = 0x0002
                ctypes.windll.user32.SetWindowPos(hwnd, 0, 0, 0, 0, 0,
                    SWP_FRAMECHANGED | SWP_NOZORDER | SWP_NOSIZE | SWP_NOMOVE)
                ctypes.windll.user32.ShowWindow(hwnd, 5)  # SW_SHOW
                print(f"__KH_EXTERNAL__:{hwnd}:{width}:{height}")
            else:
                # Default window - embed inside IDE
                print(f"__KH_HWND__:{hwnd}:{width}:{height}")
            sys.stdout.flush()


        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(60, width / height, 0.1, 1000)

        glMatrixMode(GL_MODELVIEW)
        
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_NORMALIZE)

        glShadeModel(GL_SMOOTH)

        glEnable(GL_COLOR_MATERIAL)
        glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)

        glTexEnvi(
            GL_TEXTURE_ENV,
            GL_TEXTURE_ENV_MODE,
            GL_MODULATE
        )

        # لون الخلفية
        #glClearColor(0.2, 0.2, 0.25, 1.0)

        # =======================
        # Lighting
        # =======================
        """
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)

        # إضاءة محيطية بسيطة
        glLightModelfv(
            GL_LIGHT_MODEL_AMBIENT,
            (0.2, 0.2, 0.2, 1.0)
        )

        # مكان الضوء
        glLightfv(
            GL_LIGHT0,
            GL_POSITION,
            (5.0, 5.0, 5.0, 1.0)
        )

        # لون الضوء
        glLightfv(
            GL_LIGHT0,
            GL_DIFFUSE,
            (1.0, 1.0, 1.0, 1.0)
        )

        glLightfv(GL_LIGHT0, GL_SPECULAR, (0.0, 0.0, 0.0, 1.0))

        # خصائص المادة
        glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR, (0.0, 0.0, 0.0, 1.0))

        glMaterialf(
            GL_FRONT_AND_BACK,
            GL_SHININESS,
            64.0
        )
        """
        glEnable(GL_COLOR_MATERIAL)
        glColorMaterial(
            GL_FRONT_AND_BACK,
            GL_AMBIENT_AND_DIFFUSE
        )

        glShadeModel(GL_SMOOTH)

        # الخامات تتأثر بالإضاءة
        glTexEnvi(
            GL_TEXTURE_ENV,
            GL_TEXTURE_ENV_MODE,
            GL_MODULATE
        )

        # تفعيل وضع الماوس النسبي (يخفي المؤشر ويحجز الماوس داخل النافذة)
        pygame.mouse.set_visible(False)
        pygame.event.set_grab(True)

    

    def create_cube(self, position, rotation, color):

        if color is None:
            color = Color(1, 1, 1)   # أبيض افتراضي

        cube = Cube()

        cube.الموقع = position
        cube.الدوران = rotation
        cube.اللون = color

        self.objects.append(cube)

        return cube

    def create_sphere(self, position, rotation, color):
        if color is None: color = Color(1, 1, 1)
        sphere = Sphere()
        sphere.الموقع = position
        sphere.الدوران = rotation
        sphere.اللون = color
        self.objects.append(sphere)
        return sphere

    def create_plane(self, position, rotation, color):
        if color is None: color = Color(1, 1, 1)
        plane = Plane()
        plane.الموقع = position
        plane.الدوران = rotation
        plane.اللون = color
        self.objects.append(plane)
        return plane

    def create_terrain(self, filename):
        terrain = Terrain(filename)
        self.objects.append(terrain)
        return terrain

    def create_pyramid(self, position, rotation, color):
        if color is None: color = Color(1, 1, 1)
        pyramid = Pyramid()
        pyramid.الموقع = position
        pyramid.الدوران = rotation
        pyramid.اللون = color
        self.objects.append(pyramid)
        return pyramid

    def create_cylinder(self, position, rotation, color):
        if color is None: color = Color(1, 1, 1)
        cylinder = Cylinder()
        cylinder.الموقع = position
        cylinder.الدوران = rotation
        cylinder.اللون = color
        self.objects.append(cylinder)
        return cylinder

    def create_capsule(self, position, rotation, color):
        if color is None: color = Color(1, 1, 1)
        capsule = Capsule()
        capsule.الموقع = position
        capsule.الدوران = rotation
        capsule.اللون = color
        self.objects.append(capsule)
        return capsule

    def create_custom(self, filename):
        obj = CustomModel(filename)
        self.objects.append(obj)
        return obj

    def create_fbx(self, filename):
        obj = FBXModel(self, filename)
        return obj

    def create_square_2d(self):
        obj = Square2D()
        self.objects_2d.append(obj)
        return obj

    def create_circle_2d(self):
        obj = Circle2D()
        self.objects_2d.append(obj)
        return obj

    def create_triangle_2d(self):
        obj = Triangle2D()
        self.objects_2d.append(obj)
        return obj

    def create_custom_2d(self, filename):
        obj = Custom2D(filename)
        self.objects_2d.append(obj)
        return obj

    def draw_cube(self, cube):

        if getattr(self, "is_rendering_shadow", False):
            glBegin(GL_QUADS)
            glVertex3f(-1, -1,  1); glVertex3f( 1, -1,  1); glVertex3f( 1,  1,  1); glVertex3f(-1,  1,  1)
            glVertex3f(-1, -1, -1); glVertex3f(-1,  1, -1); glVertex3f( 1,  1, -1); glVertex3f( 1, -1, -1)
            glVertex3f(-1, -1, -1); glVertex3f(-1, -1,  1); glVertex3f(-1,  1,  1); glVertex3f(-1,  1, -1)
            glVertex3f( 1, -1, -1); glVertex3f( 1,  1, -1); glVertex3f( 1,  1,  1); glVertex3f( 1, -1,  1)
            glVertex3f(-1,  1, -1); glVertex3f(-1,  1,  1); glVertex3f( 1,  1,  1); glVertex3f( 1,  1, -1)
            glVertex3f(-1, -1, -1); glVertex3f( 1, -1, -1); glVertex3f( 1, -1,  1); glVertex3f(-1, -1,  1)
            glEnd()
            return

        # قراءة معاملات AO (إذا لم تُحسب بعد، استخدم 1.0 لكل الأوجه)
        ao = getattr(cube, 'ao_factors', [1.0] * 6)

        base_r = cube.اللون.r
        base_g = cube.اللون.g
        base_b = cube.اللون.b

        has_tex = self._apply_material(cube, base_r, base_g, base_b)
        
        # Override material to force a VERY strong specular reflection on the Cube
        from OpenGL.GL import glMaterialfv, glMaterialf, GL_FRONT_AND_BACK, GL_SPECULAR, GL_SHININESS
        glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR, (1.0, 1.0, 1.0, 1.0))
        glMaterialf(GL_FRONT_AND_BACK, GL_SHININESS, 64.0)

        if has_tex:
            base_r, base_g, base_b = 1.0, 1.0, 1.0

        if not hasattr(self, '_cube_faces'):
            self._cube_faces = []
            GRID = 100
            faces_data = [
                ( (0,0,1),  (-1,-1,1), (1,-1,1), (1,1,1), (-1,1,1) ),
                ( (0,0,-1), (1,-1,-1), (-1,-1,-1), (-1,1,-1), (1,1,-1) ),
                ( (-1,0,0), (-1,-1,1), (-1,-1,-1), (-1,1,-1), (-1,1,1) ),
                ( (1,0,0),  (1,-1,-1), (1,-1,1), (1,1,1), (1,1,-1) ),
                ( (0,1,0),  (-1,1,1), (1,1,1), (1,1,-1), (-1,1,-1) ),
                ( (0,-1,0), (-1,-1,-1), (1,-1,-1), (1,-1,1), (-1,-1,1) )
            ]
            for norm, p1, p2, p3, p4 in faces_data:
                dl = glGenLists(1)
                glNewList(dl, GL_COMPILE)
                glBegin(GL_QUADS)
                for y in range(GRID):
                    for x in range(GRID):
                        tx0, ty0 = x / GRID, y / GRID
                        tx1, ty1 = (x + 1) / GRID, (y + 1) / GRID
                        
                        def get_pt(u, v):
                            px = p1[0]*(1-u)*(1-v) + p2[0]*u*(1-v) + p3[0]*u*v + p4[0]*(1-u)*v
                            py = p1[1]*(1-u)*(1-v) + p2[1]*u*(1-v) + p3[1]*u*v + p4[1]*(1-u)*v
                            pz = p1[2]*(1-u)*(1-v) + p2[2]*u*(1-v) + p3[2]*u*v + p4[2]*(1-u)*v
                            return px, py, pz
                            
                        def get_norm(px, py, pz):
                            # Blend flat normal with vertex position for fake curvature (bevel)
                            # This allows flat faces to catch specular highlights like curved objects
                            nx = norm[0] + px * 0.25
                            ny = norm[1] + py * 0.25
                            nz = norm[2] + pz * 0.25
                            L = (nx*nx + ny*ny + nz*nz)**0.5
                            if L == 0: return norm
                            return (nx/L, ny/L, nz/L)

                        px0, py0, pz0 = get_pt(tx0, ty0)
                        glNormal3f(*get_norm(px0, py0, pz0))
                        glTexCoord2f(tx0, ty0); glVertex3f(px0, py0, pz0)
                        
                        px1, py1, pz1 = get_pt(tx1, ty0)
                        glNormal3f(*get_norm(px1, py1, pz1))
                        glTexCoord2f(tx1, ty0); glVertex3f(px1, py1, pz1)
                        
                        px2, py2, pz2 = get_pt(tx1, ty1)
                        glNormal3f(*get_norm(px2, py2, pz2))
                        glTexCoord2f(tx1, ty1); glVertex3f(px2, py2, pz2)
                        
                        px3, py3, pz3 = get_pt(tx0, ty1)
                        glNormal3f(*get_norm(px3, py3, pz3))
                        glTexCoord2f(tx0, ty1); glVertex3f(px3, py3, pz3)
                glEnd()
                glEndList()
                self._cube_faces.append(dl)

        for i in range(6):
            f = ao[i]
            if f < 0.01: f = 1.0  # Fallback for corrupted/unbaked AO
            glColor3f(base_r * f, base_g * f, base_b * f)
            glCallList(self._cube_faces[i])

        glDisable(GL_TEXTURE_2D)

    def draw_sphere(self, sphere):
        if getattr(self, "is_rendering_shadow", False):
            quadric = gluNewQuadric(); gluSphere(quadric, 1.0, 64, 64); gluDeleteQuadric(quadric)
            return
        base_r = sphere.اللون.r
        base_g = sphere.اللون.g
        base_b = sphere.اللون.b

        has_tex = self._apply_material(sphere, base_r, base_g, base_b)
        if has_tex:
            base_r, base_g, base_b = 1.0, 1.0, 1.0

        glColor3f(base_r, base_g, base_b)
        
        quadric = gluNewQuadric()
        gluQuadricNormals(quadric, GLU_SMOOTH)
        gluQuadricTexture(quadric, GL_TRUE)
        gluSphere(quadric, 1.0, 64, 64)
        gluDeleteQuadric(quadric)
        glDisable(GL_TEXTURE_2D)

    def draw_plane(self, plane):
        if getattr(self, "is_rendering_shadow", False):
            glBegin(GL_QUADS); glVertex3f(-1, 0, -1); glVertex3f(-1, 0,  1); glVertex3f( 1, 0,  1); glVertex3f( 1, 0, -1); glEnd()
            return
        base_r = plane.اللون.r
        base_g = plane.اللون.g
        base_b = plane.اللون.b

        has_tex = self._apply_material(plane, base_r, base_g, base_b)
        if has_tex:
            base_r, base_g, base_b = 1.0, 1.0, 1.0

        glColor3f(base_r, base_g, base_b)
        
        if not hasattr(plane, 'display_list'):
            plane.display_list = glGenLists(1)
            glNewList(plane.display_list, GL_COMPILE)
            glBegin(GL_TRIANGLES)
            glNormal3f(0, 1, 0)
            GRID = 200
            for z in range(GRID):
                for x in range(GRID):
                    x0 = -1.0 + (x / GRID) * 2.0
                    x1 = -1.0 + ((x + 1) / GRID) * 2.0
                    z0 = -1.0 + (z / GRID) * 2.0
                    z1 = -1.0 + ((z + 1) / GRID) * 2.0
                    
                    u0 = x / GRID
                    u1 = (x + 1) / GRID
                    v0 = z / GRID
                    v1 = (z + 1) / GRID
                    
                    if (x + z) % 2 == 0:
                        glTexCoord2f(u0, v0); glVertex3f(x0, 0, z0)
                        glTexCoord2f(u0, v1); glVertex3f(x0, 0, z1)
                        glTexCoord2f(u1, v1); glVertex3f(x1, 0, z1)
                        
                        glTexCoord2f(u0, v0); glVertex3f(x0, 0, z0)
                        glTexCoord2f(u1, v1); glVertex3f(x1, 0, z1)
                        glTexCoord2f(u1, v0); glVertex3f(x1, 0, z0)
                    else:
                        glTexCoord2f(u0, v0); glVertex3f(x0, 0, z0)
                        glTexCoord2f(u0, v1); glVertex3f(x0, 0, z1)
                        glTexCoord2f(u1, v0); glVertex3f(x1, 0, z0)
                        
                        glTexCoord2f(u1, v0); glVertex3f(x1, 0, z0)
                        glTexCoord2f(u0, v1); glVertex3f(x0, 0, z1)
                        glTexCoord2f(u1, v1); glVertex3f(x1, 0, z1)
            glEnd()
            glEndList()
            
        self._bind_tex(plane)
        glPushMatrix()
        glTranslatef(plane.الموقع.x, plane.الموقع.y, plane.الموقع.z)
        glRotatef(plane.الدوران.x, 1, 0, 0)
        glRotatef(plane.الدوران.y, 0, 1, 0)
        glRotatef(plane.الدوران.z, 0, 0, 1)
        glScalef(plane.المقياس.x, plane.المقياس.y, plane.المقياس.z)
        glCallList(plane.display_list)
        glPopMatrix()
        glDisable(GL_TEXTURE_2D)

    def draw_terrain(self, terrain):
        has_tex = self._bind_tex(terrain)
        self._apply_material(terrain, terrain.اللون.r, terrain.اللون.g, terrain.اللون.b)
        if has_tex:
            from OpenGL.GL import glColor3f
            glColor3f(1.0, 1.0, 1.0)
        else:
            from OpenGL.GL import glColor3f
            glColor3f(terrain.اللون.r, terrain.اللون.g, terrain.اللون.b)
        glPushMatrix()
        glTranslatef(terrain.الموقع.x, terrain.الموقع.y, terrain.الموقع.z)
        glRotatef(terrain.الدوران.x, 1, 0, 0)
        glRotatef(terrain.الدوران.y, 0, 1, 0)
        glRotatef(terrain.الدوران.z, 0, 0, 1)
        glScalef(terrain.المقياس.x, terrain.المقياس.y, terrain.المقياس.z)
        
        gs = terrain.grid_size
        hm = terrain.heightmap
        if len(hm) >= gs * gs and gs > 1:
            if not hasattr(terrain, 'display_list'):
                import builtins
                if hasattr(builtins, 'print'):
                    print(f"TERRAIN DEBUG: Compiling terrain '{terrain.filepath}' with gs={gs}, max_h={max(hm) if hm else 0}, min_h={min(hm) if hm else 0}")
                terrain.display_list = glGenLists(1)
                glNewList(terrain.display_list, GL_COMPILE)
                step = 2.0 / (gs - 1)
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
                        
                        glNormal3f(0, 1, 0)
                        
                        glTexCoord2f(x/gs, z/gs); glVertex3f(x0, y00, z0)
                        glTexCoord2f((x+1)/gs, z/gs); glVertex3f(x1, y10, z0)
                        glTexCoord2f(x/gs, (z+1)/gs); glVertex3f(x0, y01, z1)
                        
                        glTexCoord2f((x+1)/gs, z/gs); glVertex3f(x1, y10, z0)
                        glTexCoord2f((x+1)/gs, (z+1)/gs); glVertex3f(x1, y11, z1)
                        glTexCoord2f(x/gs, (z+1)/gs); glVertex3f(x0, y01, z1)
                glEnd()
                glEndList()
            glCallList(terrain.display_list)
        else:
            s = 1.0
            glBegin(GL_QUADS)
            glNormal3f(0, 1, 0)
            glTexCoord2f(0, 0); glVertex3f(-s, 0, -s)
            glTexCoord2f(1, 0); glVertex3f( s, 0, -s)
            glTexCoord2f(1, 1); glVertex3f( s, 0,  s)
            glTexCoord2f(0, 1); glVertex3f(-s, 0,  s)
            glEnd()
        glPopMatrix()
        glDisable(GL_TEXTURE_2D)

    def draw_pyramid(self, pyramid):
        if getattr(self, "is_rendering_shadow", False):
            glBegin(GL_QUADS); glVertex3f(-1, -1, -1); glVertex3f( 1, -1, -1); glVertex3f( 1, -1,  1); glVertex3f(-1, -1,  1); glEnd()
            glBegin(GL_TRIANGLES)
            glVertex3f(0, 1, 0); glVertex3f(-1, -1, 1); glVertex3f(1, -1, 1)
            glVertex3f(0, 1, 0); glVertex3f(1, -1, 1); glVertex3f(1, -1, -1)
            glVertex3f(0, 1, 0); glVertex3f(1, -1, -1); glVertex3f(-1, -1, -1)
            glVertex3f(0, 1, 0); glVertex3f(-1, -1, -1); glVertex3f(-1, -1, 1)
            glEnd()
            return
        base_r = pyramid.اللون.r
        base_g = pyramid.اللون.g
        base_b = pyramid.اللون.b

        has_tex = self._apply_material(pyramid, base_r, base_g, base_b)
        if has_tex:
            base_r, base_g, base_b = 1.0, 1.0, 1.0

        glColor3f(base_r, base_g, base_b)
        
        if not hasattr(self, '_pyramid_dl'):
            self._pyramid_dl = glGenLists(1)
            glNewList(self._pyramid_dl, GL_COMPILE)
            GRID = 100
            
            # Base (Quad)
            glBegin(GL_QUADS)
            glNormal3f(0, -1, 0)
            p1, p2, p3, p4 = (-1, -1, -1), (1, -1, -1), (1, -1, 1), (-1, -1, 1)
            for y in range(GRID):
                for x in range(GRID):
                    tx0, ty0 = x / GRID, y / GRID
                    tx1, ty1 = (x + 1) / GRID, (y + 1) / GRID
                    def get_pt(u, v):
                        px = p1[0]*(1-u)*(1-v) + p2[0]*u*(1-v) + p3[0]*u*v + p4[0]*(1-u)*v
                        py = p1[1]*(1-u)*(1-v) + p2[1]*u*(1-v) + p3[1]*u*v + p4[1]*(1-u)*v
                        pz = p1[2]*(1-u)*(1-v) + p2[2]*u*(1-v) + p3[2]*u*v + p4[2]*(1-u)*v
                        return px, py, pz
                    glTexCoord2f(tx0, ty0); glVertex3f(*get_pt(tx0, ty0))
                    glTexCoord2f(tx1, ty0); glVertex3f(*get_pt(tx1, ty0))
                    glTexCoord2f(tx1, ty1); glVertex3f(*get_pt(tx1, ty1))
                    glTexCoord2f(tx0, ty1); glVertex3f(*get_pt(tx0, ty1))
            glEnd()
            
            # Sides (Triangles)
            sides = [
                ((0, 0.5, 1), (-1, -1, 1), (1, -1, 1), (0, 1, 0)),
                ((1, 0.5, 0), (1, -1, 1), (1, -1, -1), (0, 1, 0)),
                ((0, 0.5, -1), (1, -1, -1), (-1, -1, -1), (0, 1, 0)),
                ((-1, 0.5, 0), (-1, -1, -1), (-1, -1, 1), (0, 1, 0))
            ]
            glBegin(GL_QUADS)
            for norm, sp1, sp2, sp3 in sides:
                glNormal3f(*norm)
                for y in range(GRID):
                    for x in range(GRID):
                        tx0, ty0 = x / GRID, y / GRID
                        tx1, ty1 = (x + 1) / GRID, (y + 1) / GRID
                        def get_tri(u, v):
                            px = sp1[0]*(1-u)*(1-v) + sp2[0]*u*(1-v) + sp3[0]*v
                            py = sp1[1]*(1-u)*(1-v) + sp2[1]*u*(1-v) + sp3[1]*v
                            pz = sp1[2]*(1-u)*(1-v) + sp2[2]*u*(1-v) + sp3[2]*v
                            return px, py, pz
                        glTexCoord2f(tx0, ty0); glVertex3f(*get_tri(tx0, ty0))
                        glTexCoord2f(tx1, ty0); glVertex3f(*get_tri(tx1, ty0))
                        glTexCoord2f(tx1, ty1); glVertex3f(*get_tri(tx1, ty1))
                        glTexCoord2f(tx0, ty1); glVertex3f(*get_tri(tx0, ty1))
            glEnd()
            glEndList()
            
        glCallList(self._pyramid_dl)
        glDisable(GL_TEXTURE_2D)

    def draw_cylinder(self, cylinder):
        if getattr(self, "is_rendering_shadow", False):
            glPushMatrix(); glRotatef(-90, 1, 0, 0); glTranslatef(0, 0, -1)
            quadric = gluNewQuadric(); gluCylinder(quadric, 1.0, 1.0, 2.0, 64, 64)
            glPushMatrix(); gluDisk(quadric, 0.0, 1.0, 32, 1); glPopMatrix()
            glTranslatef(0, 0, 2.0); gluDisk(quadric, 0.0, 1.0, 32, 1); gluDeleteQuadric(quadric); glPopMatrix()
            return
        base_r = cylinder.اللون.r
        base_g = cylinder.اللون.g
        base_b = cylinder.اللون.b

        has_tex = self._apply_material(cylinder, base_r, base_g, base_b)
        if has_tex:
            base_r, base_g, base_b = 1.0, 1.0, 1.0

        glColor3f(base_r, base_g, base_b)
        
        glPushMatrix()
        glRotatef(-90, 1, 0, 0)
        glTranslatef(0, 0, -1)
        quadric = gluNewQuadric()
        gluQuadricNormals(quadric, GLU_SMOOTH)
        gluQuadricTexture(quadric, GL_TRUE)
        
        gluCylinder(quadric, 1.0, 1.0, 2.0, 64, 64)
        
        glPushMatrix()
        gluQuadricOrientation(quadric, GLU_INSIDE)
        gluDisk(quadric, 0.0, 1.0, 32, 1)
        glPopMatrix()
        
        glTranslatef(0, 0, 2.0)
        gluQuadricOrientation(quadric, GLU_OUTSIDE)
        gluDisk(quadric, 0.0, 1.0, 32, 1)
        
        gluDeleteQuadric(quadric)
        glPopMatrix()
        glDisable(GL_TEXTURE_2D)

    def draw_capsule(self, capsule):
        if getattr(self, "is_rendering_shadow", False):
            glPushMatrix(); glRotatef(-90, 1, 0, 0); glTranslatef(0, 0, -1)
            quadric = gluNewQuadric(); gluSphere(quadric, 1.0, 64, 64); gluCylinder(quadric, 1.0, 1.0, 2.0, 64, 64)
            glTranslatef(0, 0, 2.0); gluSphere(quadric, 1.0, 64, 64); gluDeleteQuadric(quadric); glPopMatrix()
            return
        base_r = capsule.اللون.r
        base_g = capsule.اللون.g
        base_b = capsule.اللون.b

        has_tex = self._apply_material(capsule, base_r, base_g, base_b)
        if has_tex:
            base_r, base_g, base_b = 1.0, 1.0, 1.0

        glColor3f(base_r, base_g, base_b)
        
        glPushMatrix()
        glRotatef(-90, 1, 0, 0)
        glTranslatef(0, 0, -1)
        quadric = gluNewQuadric()
        gluQuadricNormals(quadric, GLU_SMOOTH)
        gluQuadricTexture(quadric, GL_TRUE)
        
        gluSphere(quadric, 1.0, 64, 64)
        gluCylinder(quadric, 1.0, 1.0, 2.0, 64, 64)
        glTranslatef(0, 0, 2.0)
        gluSphere(quadric, 1.0, 64, 64)
        
        gluDeleteQuadric(quadric)
        glPopMatrix()
        glDisable(GL_TEXTURE_2D)

    def draw_custom(self, model):
        if getattr(self, "is_rendering_shadow", False):
            if model.display_list is not None:
                glCallList(model.display_list)
            return
        if not model.mesh:
            return
            
        if model.display_list is None:
            model.display_list = glGenLists(1)
            glNewList(model.display_list, GL_COMPILE)
            
            mesh = model.mesh
            for f_v, f_t, f_n in mesh.faces:
                if len(f_v) == 3:
                    glBegin(GL_TRIANGLES)
                elif len(f_v) == 4:
                    glBegin(GL_QUADS)
                else:
                    glBegin(GL_POLYGON)
                    
                for i in range(len(f_v)):
                    if f_n[i] != -1 and f_n[i] < len(mesh.normals):
                        glNormal3fv(mesh.normals[f_n[i]])
                    if f_t[i] != -1 and f_t[i] < len(mesh.texcoords):
                        glTexCoord2fv(mesh.texcoords[f_t[i]])
                    if f_v[i] != -1 and f_v[i] < len(mesh.vertices):
                        glVertex3fv(mesh.vertices[f_v[i]])
                    
                glEnd()
            glEndList()

        base_r = model.اللون.r
        base_g = model.اللون.g
        base_b = model.اللون.b

        if getattr(model, "texture_id", None) is None and getattr(model, "الخامة", None):
            try:
                import textures
                model.texture_id = textures.load_texture(model.الخامة)
            except:
                model.texture_id = -1

        if getattr(model, "texture_id", -1) != -1 and getattr(model, "texture_id", None) is not None:
            glEnable(GL_TEXTURE_2D)
            glBindTexture(GL_TEXTURE_2D, model.texture_id)
        else:
            glDisable(GL_TEXTURE_2D)

        from OpenGL.GL import glMaterialfv, GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE, GL_SPECULAR, glMaterialf, GL_SHININESS
        glMaterialfv(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE, (base_r, base_g, base_b, 1.0))
        glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR, (0.0, 0.0, 0.0, 1.0))
        glMaterialf(GL_FRONT_AND_BACK, GL_SHININESS, 64.0)

        glColor3f(base_r, base_g, base_b)
        
        glCallList(model.display_list)
            
        glDisable(GL_TEXTURE_2D)

    
    def check_collisions(self):
        # Reset collisions
        for obj in self.objects_2d:
            obj.تصادم = False
        self.camera.تصادم = False
        for obj in self.objects:
            obj.تصادم = False
            
        for i in range(len(self.objects_2d)):
            for j in range(i+1, len(self.objects_2d)):
                obj1 = self.objects_2d[i]
                obj2 = self.objects_2d[j]
                
                t1 = type(obj1).__name__
                t2 = type(obj2).__name__
                
                # AABB for obj1
                if t1 in ('Square2D', 'Custom2D', 'Triangle2D', 'Circle2D'):
                    w1, h1 = obj1.المقياس.x, obj1.المقياس.y
                    x1, y1 = obj1.الموقع.x - w1/2, obj1.الموقع.y - h1/2
                else:
                    continue
                    
                # AABB for obj2
                if t2 in ('Square2D', 'Custom2D', 'Triangle2D', 'Circle2D'):
                    w2, h2 = obj2.المقياس.x, obj2.المقياس.y
                    x2, y2 = obj2.الموقع.x - w2/2, obj2.الموقع.y - h2/2
                else:
                    continue
                    
                if x1 < x2 + w2 and x1 + w1 > x2 and y1 < y2 + h2 and y1 + h1 > y2:
                    obj1.تصادم = True
                    obj2.تصادم = True

        # Check collisions for 3D objects
        objects_for_physics = self.objects.copy()
        if getattr(self.camera, 'صدام', False) in (1, True, 'مفعل') or getattr(self.camera, 'جاذبية', False) in (1, True, 'مفعل'):
            objects_for_physics.append(self.camera)
            
        for i in range(len(objects_for_physics)):
            for j in range(i+1, len(objects_for_physics)):
                obj1 = objects_for_physics[i]
                obj2 = objects_for_physics[j]
                
                b1 = self.physics_engine._get_aabb_3d(obj1)
                b2 = self.physics_engine._get_aabb_3d(obj2)
                
                if self.physics_engine._check_overlap(b1, b2):
                    obj1.تصادم = True
                    obj2.تصادم = True

    def run(self, per_frame=None):

        self.running = True
        if self.ao_enabled and len(self.objects) > 0:
            self.ao_baker.bake(self.objects)
        elif len(self.objects) > 0:
            for obj in self.objects:
                obj.ao_factors = [1.0] * 6

        clock = pygame.time.Clock()
        dt_ms = 16

        while self.running:
            delta_time = dt_ms / 1000.0
            self.time._delta = delta_time

            import os
            if os.environ.get("KH_EMBEDDED") == "1" and not getattr(self, '_is_external_window', False):
                import ctypes
                from ctypes.wintypes import RECT
                hwnd = pygame.display.get_wm_info()["window"]
                rect = RECT()
                ctypes.windll.user32.GetClientRect(hwnd, ctypes.byref(rect))
                cw = rect.right - rect.left
                ch = rect.bottom - rect.top
                if cw > 0 and ch > 0 and (cw != getattr(self, '_current_w', 0) or ch != getattr(self, '_current_h', 0)):
                    self._current_w = cw
                    self._current_h = ch
                    from OpenGL.GL import glViewport, glMatrixMode, GL_PROJECTION, glLoadIdentity, GL_MODELVIEW
                    from OpenGL.GLU import gluPerspective
                    glViewport(0, 0, cw, ch)
                    glMatrixMode(GL_PROJECTION)
                    glLoadIdentity()
                    gluPerspective(60, cw / ch, 0.1, 1000)
                    glMatrixMode(GL_MODELVIEW)

            # ── إعادة ضبط القيم التي تتغير كل إطار ──
            self.mouse.scroll = 0.0
            self.mouse.حركة_أفقية = 0.0
            self.mouse.حركة_عمودية = 0.0

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.VIDEORESIZE:
                    width, height = event.w, event.h
                    if height == 0: height = 1
                    import os
                    if not os.environ.get("KH_EMBEDDED"):
                        pygame.display.set_mode((width, height), getattr(self, "flags", DOUBLEBUF | OPENGL))
                    
                    self._current_w = width
                    self._current_h = height
                    
                    glViewport(0, 0, width, height)
                    glMatrixMode(GL_PROJECTION)
                    glLoadIdentity()
                    gluPerspective(60, width / height, 0.1, 1000)
                    glMatrixMode(GL_MODELVIEW)

                # حركة المؤشر
                elif event.type == pygame.MOUSEMOTION:
                    pass # تم إيقاف تحديث الموقع المطلق بناءً على طلب المستخدم ليصبح للاتجاه فقط

                # ضغط زر
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        self.mouse.ضغط_يسار = True
                    elif event.button == 3:
                        self.mouse.ضغط_يمين = True

                # رفع زر
                elif event.type == pygame.MOUSEBUTTONUP:
                    if event.button == 1:
                        self.mouse.ضغط_يسار = False
                    elif event.button == 3:
                        self.mouse.ضغط_يمين = False

                # عجلة التمرير
                elif event.type == pygame.MOUSEWHEEL:
                    self.mouse.scroll = float(event.y)

            # ── تحديث لوحة المفاتيح كل إطار ──
            self.keyboard.update()

            # ── تحديث الحركة النسبية للماوس مع الحساسية ──
            dx, dy = pygame.mouse.get_rel()
            sens = self.mouse.حساسية
            self.mouse.حركة_أفقية = dx * sens
            self.mouse.حركة_عمودية = dy * sens
            
            # أفقي وعمودي (-1, 0, 1) مع انتقال ناعم (Smooth)
            target_x = 1.0 if dx > 0 else (-1.0 if dx < 0 else 0.0)
            target_y = 1.0 if dy < 0 else (-1.0 if dy > 0 else 0.0)
            
            smooth_factor = 0.5
            self.mouse.أفقي += (target_x - self.mouse.أفقي) * smooth_factor
            self.mouse.افقي = self.mouse.أفقي
            self.mouse.عمودي += (target_y - self.mouse.عمودي) * smooth_factor

            # ── تحديث الفيزياء ──
            objects_for_physics = self.objects.copy()
            if getattr(self.camera, 'صدام', False) in (1, True, 'مفعل') or getattr(self.camera, 'جاذبية', False) in (1, True, 'مفعل'):
                objects_for_physics.append(self.camera)
            self.physics_engine.update_physics(objects_for_physics, self.objects_2d, delta_time)

            # ── تنفيذ كود كل_فريم من .kh ──
            self.check_collisions()
            if per_frame is not None:
                per_frame()

            self.render_scene()

            dt_ms = clock.tick(60)

        pygame.quit()
    def draw_aabb(self, aabb):
        from OpenGL.GL import (
            glBegin, glEnd, GL_LINES, glVertex3f, glColor3f,
            glDisable, glEnable, GL_LIGHTING, GL_TEXTURE_2D,
            glPushAttrib, glPopAttrib, GL_ENABLE_BIT, glLineWidth
        )
        if not aabb: return
        
        glPushAttrib(GL_ENABLE_BIT)
        glDisable(GL_LIGHTING)
        glDisable(GL_TEXTURE_2D)
        
        glColor3f(1.0, 0.0, 0.0) # أحمر للحدود
        glLineWidth(2.0)
        
        mx, My, mz = aabb['min_x'], aabb['min_y'], aabb['min_z']
        Mx, MY, Mz = aabb['max_x'], aabb['max_y'], aabb['max_z']
        
        glBegin(GL_LINES)
        # قاعدة سفلية
        glVertex3f(mx, My, mz); glVertex3f(Mx, My, mz)
        glVertex3f(Mx, My, mz); glVertex3f(Mx, My, Mz)
        glVertex3f(Mx, My, Mz); glVertex3f(mx, My, Mz)
        glVertex3f(mx, My, Mz); glVertex3f(mx, My, mz)
        
        # قاعدة علوية
        glVertex3f(mx, MY, mz); glVertex3f(Mx, MY, mz)
        glVertex3f(Mx, MY, mz); glVertex3f(Mx, MY, Mz)
        glVertex3f(Mx, MY, Mz); glVertex3f(mx, MY, Mz)
        glVertex3f(mx, MY, Mz); glVertex3f(mx, MY, mz)
        
        # حواف عمودية
        glVertex3f(mx, My, mz); glVertex3f(mx, MY, mz)
        glVertex3f(Mx, My, mz); glVertex3f(Mx, MY, mz)
        glVertex3f(Mx, My, Mz); glVertex3f(Mx, MY, Mz)
        glVertex3f(mx, My, Mz); glVertex3f(mx, MY, Mz)
        glEnd()
        glPopAttrib()

    def get_current_size(self):
        if hasattr(self, "_current_w") and hasattr(self, "_current_h"):
            return self._current_w, self._current_h
        import pygame
        surf = pygame.display.get_surface()
        if surf:
            w, h = surf.get_size()
            self._current_w, self._current_h = w, h
            return w, h
        import os
        return int(os.environ.get("KH_WIDTH", 800)), int(os.environ.get("KH_HEIGHT", 600))

    def render_scene(self):
        from OpenGL.GL import glClearColor, glClear, GL_COLOR_BUFFER_BIT, GL_DEPTH_BUFFER_BIT, GL_STENCIL_BUFFER_BIT, glMatrixMode, GL_MODELVIEW, glLoadIdentity, glPushMatrix, glPushAttrib, GL_ENABLE_BIT, glDisable, GL_DEPTH_TEST, GL_LIGHTING, glEnable, GL_TEXTURE_2D, glColor3f, glBindTexture, glRotatef, glPopMatrix, glPopAttrib, glLightfv, GL_LIGHT0, GL_POSITION, GL_DIFFUSE, GL_SPECULAR, GL_AMBIENT, GL_SPOT_CUTOFF, GL_SPOT_DIRECTION, GL_SPOT_EXPONENT, GL_CONSTANT_ATTENUATION, GL_LINEAR_ATTENUATION, GL_QUADRATIC_ATTENUATION, GL_LIGHT_MODEL_AMBIENT, glLightModelfv, glLightf, glScalef, glTranslatef, glBegin, glEnd, GL_QUADS, GL_POLYGON, GL_TRIANGLES, glVertex2f, glColor4f, glTexCoord2f, GL_PROJECTION, glOrtho, glBlendFunc, GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA, GL_STENCIL_TEST, glStencilFunc, GL_ALWAYS, glStencilOp, GL_KEEP, GL_REPLACE, GL_EQUAL, GL_INCR, glMultMatrixf, glDeleteTextures, glGenTextures, glTexParameteri, GL_TEXTURE_MIN_FILTER, GL_TEXTURE_MAG_FILTER, GL_LINEAR, GL_RGBA, GL_UNSIGNED_BYTE, glTexImage2D, GL_TRUE, GL_COLOR_MATERIAL, glColorMaterial, GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE
        from OpenGL.GLU import gluLookAt, gluNewQuadric, gluQuadricNormals, GLU_SMOOTH, gluQuadricTexture, gluQuadricOrientation, GLU_INSIDE, gluSphere, gluDeleteQuadric
        import pygame
        if self.sky_color:
            glClearColor(self.sky_color.r, self.sky_color.g, self.sky_color.b, 1.0)
        else:
            glClearColor(0.1, 0.1, 0.15, 1.0)

        from OpenGL.GL import glShadeModel, GL_SMOOTH
        glShadeModel(GL_SMOOTH)
        w, h = self.get_current_size()
        
        if hasattr(self, 'tonemapper') and self.tonemapper:
            self.tonemapper.update_size(w, h)
            self.tonemapper.bind()
            
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT | GL_STENCIL_BUFFER_BIT)
        
        if h == 0: h = 1
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        from OpenGL.GLU import gluPerspective
        gluPerspective(self.camera.زاوية_الرؤية, w / h, 0.1, 1000)

        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

        # الكاميرا
        import math
        pitch = math.radians(self.camera.الدوران.x)
        yaw = math.radians(self.camera.الدوران.y)
        
        dx = math.sin(yaw) * math.cos(pitch)
        dy = -math.sin(pitch)
        dz = -math.cos(yaw) * math.cos(pitch)
        
        target_x = self.camera.الموقع.x + dx
        target_y = self.camera.الموقع.y + dy
        target_z = self.camera.الموقع.z + dz

        gluLookAt(
            self.camera.الموقع.x, self.camera.الموقع.y, self.camera.الموقع.z,
            target_x, target_y, target_z,
            0, 1, 0
        )

        # رسم السماء
        if getattr(self, "sky_cubemap", None) is not None:
            sky = self.sky_cubemap
            if sky.textures is None:
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
                
                # جعل السماء تتبع الكاميرا دائماً حتى لا نخرج منها
                glTranslatef(self.camera.الموقع.x, self.camera.الموقع.y, self.camera.الموقع.z)
                
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

        elif getattr(self, "sky_texture", None) is not None:
            glPushMatrix()
            glPushAttrib(GL_ENABLE_BIT)
            glDisable(GL_DEPTH_TEST)
            glDisable(GL_LIGHTING)
            glEnable(GL_TEXTURE_2D)
            glColor3f(1.0, 1.0, 1.0)
            glBindTexture(GL_TEXTURE_2D, self.sky_texture)
            
            quadric = gluNewQuadric()
            gluQuadricNormals(quadric, GLU_SMOOTH)
            gluQuadricTexture(quadric, GL_TRUE)
            gluQuadricOrientation(quadric, GLU_INSIDE)
            
            glRotatef(-90, 1, 0, 0)
            gluSphere(quadric, 100.0, 32, 32)
            
            gluDeleteQuadric(quadric)
            glPopAttrib()
            glPopMatrix()

        # ==========================
        # تحديث الإضاءة
        # ==========================

        if hasattr(self, 'lights') and len(self.lights) > 0:
            glEnable(GL_LIGHTING)
            glEnable(GL_COLOR_MATERIAL)
            glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
            glLightModelfv(GL_LIGHT_MODEL_AMBIENT, (0.05, 0.05, 0.05, 1.0))
            from OpenGL.GL import glLightModeli, GL_LIGHT_MODEL_LOCAL_VIEWER, GL_TRUE
            glLightModeli(GL_LIGHT_MODEL_LOCAL_VIEWER, GL_TRUE)
            
            for idx, light in enumerate(self.lights[:8]):
                gl_light = GL_LIGHT0 + idx
                glEnable(gl_light)
                
                i = light.الشدة
                
                glLightfv(gl_light, GL_DIFFUSE, (light.اللون.r * i, light.اللون.g * i, light.اللون.b * i, 1.0))
                
                if light.النوع == 'ضوء_موجه':
                    # Directional lights should provide strong global illumination to all faces
                    amb = 1.4
                    spec_mult = 8.0  # Double reflection intensity
                else:
                    amb = 0.05
                    spec_mult = 1.0
                    
                glLightfv(gl_light, GL_SPECULAR, (light.اللون.r * i * spec_mult, light.اللون.g * i * spec_mult, light.اللون.b * i * spec_mult, 1.0))
                glLightfv(gl_light, GL_AMBIENT, (light.اللون.r * amb, light.اللون.g * amb, light.اللون.b * amb, 1.0))
                
                if light.النوع == 'ضوء_نقطي':
                    glLightfv(gl_light, GL_POSITION, (light.الموقع.x, light.الموقع.y, light.الموقع.z, 1.0))
                    glLightf(gl_light, GL_SPOT_CUTOFF, 180.0)
                    glLightf(gl_light, GL_CONSTANT_ATTENUATION,  light.التضاؤل_الثابت)
                    glLightf(gl_light, GL_LINEAR_ATTENUATION,    light.التضاؤل_الخطي)
                    glLightf(gl_light, GL_QUADRATIC_ATTENUATION, light.التضاؤل_التربيعي)
                elif light.النوع == 'ضوء_موجه':
                    glLightfv(gl_light, GL_POSITION, (-light.الاتجاه.x, -light.الاتجاه.y, -light.الاتجاه.z, 0.0))
                elif light.النوع == 'ضوء_بقعي':
                    glLightfv(gl_light, GL_POSITION, (light.الموقع.x, light.الموقع.y, light.الموقع.z, 1.0))
                    dir_x, dir_y, dir_z = light.الاتجاه.x, light.الاتجاه.y, light.الاتجاه.z
                    length = (dir_x**2 + dir_y**2 + dir_z**2)**0.5
                    if length > 0.0001:
                        dir_x, dir_y, dir_z = dir_x/length, dir_y/length, dir_z/length
                    glLightfv(gl_light, GL_SPOT_DIRECTION, (dir_x, dir_y, dir_z))
                    cutoff = max(1.0, min(90.0, light.زاوية_البقعة))
                    glLightf(gl_light, GL_SPOT_CUTOFF, cutoff)
                    exponent = max(0.0, min(128.0, light.حدة_البقعة))
                    glLightf(gl_light, GL_SPOT_EXPONENT, exponent)
                    glLightf(gl_light, GL_CONSTANT_ATTENUATION,  light.التضاؤل_الثابت)
                    glLightf(gl_light, GL_LINEAR_ATTENUATION,    light.التضاؤل_الخطي)
                    glLightf(gl_light, GL_QUADRATIC_ATTENUATION, light.التضاؤل_التربيعي)
            
            for idx in range(len(self.lights), 8):
                glDisable(GL_LIGHT0 + idx)
        else:
            for idx in range(1, 8):
                glDisable(GL_LIGHT0 + idx)
            glEnable(GL_LIGHTING)
            glEnable(GL_COLOR_MATERIAL)
            glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
            glLightModelfv(GL_LIGHT_MODEL_AMBIENT, (0.05, 0.05, 0.05, 1.0))
            
            # ضوء خافت افتراضي
            glEnable(GL_LIGHT0)
            glLightfv(GL_LIGHT0, GL_POSITION, (-0.5, -1.0, -0.5, 0.0))
            glLightfv(GL_LIGHT0, GL_DIFFUSE, (0.6, 0.6, 0.6, 1.0))
            glLightfv(GL_LIGHT0, GL_SPECULAR, (0.8, 0.8, 0.8, 1.0))
            glLightfv(GL_LIGHT0, GL_AMBIENT, (0.05, 0.05, 0.05, 1.0))

            from OpenGL.GL import glLightModeli, GL_LIGHT_MODEL_COLOR_CONTROL, GL_SEPARATE_SPECULAR_COLOR
            glLightModeli(GL_LIGHT_MODEL_COLOR_CONTROL, GL_SEPARATE_SPECULAR_COLOR)

        # ==========================
        # رسم المجسمات
        # ==========================

        def render_obj(o):
            glPushMatrix()
            if hasattr(o, 'parent') and o.parent:
                glTranslatef(o.parent.الموقع.x, o.parent.الموقع.y, o.parent.الموقع.z)
                glRotatef(o.parent.الدوران.x, 1, 0, 0)
                glRotatef(o.parent.الدوران.y, 0, 1, 0)
                glRotatef(o.parent.الدوران.z, 0, 0, 1)
                glScalef(o.parent.المقياس.x, o.parent.المقياس.y, o.parent.المقياس.z)
                
            glTranslatef(o.الموقع.x, o.الموقع.y, o.الموقع.z)
            glRotatef(o.الدوران.x, 1, 0, 0)
            glRotatef(o.الدوران.y, 0, 1, 0)
            glRotatef(o.الدوران.z, 0, 0, 1)
            glScalef(o.المقياس.x, o.المقياس.y, o.المقياس.z)
            
            if type(o).__name__ == "Cube": self.draw_cube(o)
            elif type(o).__name__ == "Sphere": self.draw_sphere(o)
            elif type(o).__name__ == "Plane": self.draw_plane(o)
            elif type(o).__name__ == "Terrain": self.draw_terrain(o)
            elif type(o).__name__ == "Pyramid": self.draw_pyramid(o)
            elif type(o).__name__ == "Cylinder": self.draw_cylinder(o)
            elif type(o).__name__ == "Capsule": self.draw_capsule(o)
            elif type(o).__name__ == "CustomModel": self.draw_custom(o)
            elif type(o).__name__ in ("Square2D", "Custom2D"):
                has_tex = getattr(o, "texture_id", -1) != -1 and o.texture_id is not None
                if has_tex:
                    glEnable(GL_TEXTURE_2D)
                    glBindTexture(GL_TEXTURE_2D, o.texture_id)
                    glColor4f(o.اللون.r, o.اللون.g, o.اللون.b, 1.0)
                else:
                    glDisable(GL_TEXTURE_2D)
                    glColor3f(o.اللون.r, o.اللون.g, o.اللون.b)
                    
                glNormal3f(0, 0, 1)
                sw, sh = o.المقياس.x, o.المقياس.y
                glBegin(GL_QUADS)
                if has_tex:
                    glTexCoord2f(0, 0); glVertex3f(-sw/2, -sh/2, 0)
                    glTexCoord2f(1, 0); glVertex3f(sw/2, -sh/2, 0)
                    glTexCoord2f(1, 1); glVertex3f(sw/2, sh/2, 0)
                    glTexCoord2f(0, 1); glVertex3f(-sw/2, sh/2, 0)
                else:
                    glVertex3f(-sw/2, -sh/2, 0); glVertex3f(sw/2, -sh/2, 0)
                    glVertex3f(sw/2, sh/2, 0); glVertex3f(-sw/2, sh/2, 0)
                glEnd()
            elif type(o).__name__ == "Circle2D":
                has_tex = getattr(o, "texture_id", -1) != -1 and o.texture_id is not None
                if has_tex:
                    glEnable(GL_TEXTURE_2D)
                    glBindTexture(GL_TEXTURE_2D, o.texture_id)
                    glColor4f(o.اللون.r, o.اللون.g, o.اللون.b, 1.0)
                else:
                    glDisable(GL_TEXTURE_2D)
                    glColor3f(o.اللون.r, o.اللون.g, o.اللون.b)
                    
                glNormal3f(0, 0, 1)
                r = o.المقياس.x
                glBegin(GL_POLYGON)
                import math
                for i in range(36):
                    theta = i * 10 * 3.14159 / 180
                    cx, cy = math.cos(theta), math.sin(theta)
                    if has_tex: glTexCoord2f(cx * 0.5 + 0.5, cy * 0.5 + 0.5)
                    glVertex3f(r * cx, r * cy, 0)
                glEnd()
            elif type(o).__name__ == "Triangle2D":
                has_tex = getattr(o, "texture_id", -1) != -1 and o.texture_id is not None
                if has_tex:
                    glEnable(GL_TEXTURE_2D)
                    glBindTexture(GL_TEXTURE_2D, o.texture_id)
                    glColor4f(o.اللون.r, o.اللون.g, o.اللون.b, 1.0)
                else:
                    glDisable(GL_TEXTURE_2D)
                    glColor3f(o.اللون.r, o.اللون.g, o.اللون.b)
                    
                glNormal3f(0, 0, 1)
                bw, bh = o.المقياس.x, o.المقياس.y
                glBegin(GL_TRIANGLES)
                if has_tex: glTexCoord2f(0.5, 0.0)
                glVertex3f(0, bh/2, 0)
                if has_tex: glTexCoord2f(0.0, 1.0)
                glVertex3f(-bw/2, -bh/2, 0)
                if has_tex: glTexCoord2f(1.0, 1.0)
                glVertex3f(bw/2, -bh/2, 0)
                glEnd()
            
            glPopMatrix()

        if getattr(self, "shadows", False) and hasattr(self, "lights") and len(self.lights) > 0:
            world_2d = [o for o in self.objects_2d if not getattr(o, 'مساحة_الشاشة', True)]
            all_3d_objs = self.objects + world_2d
            floors = [o for o in all_3d_objs if type(o).__name__ == "Plane"]
            others = [o for o in all_3d_objs if type(o).__name__ != "Plane"]
            
            if floors:
                # 1. رسم الأرضيات وكتابة 1 في الاستنسل
                glEnable(GL_STENCIL_TEST)
                glStencilFunc(GL_ALWAYS, 1, 0xFF)
                glStencilOp(GL_KEEP, GL_KEEP, GL_REPLACE)
                
                for f in floors:
                    render_obj(f)
                    
                # 2. رسم الظلال (فقط الأماكن التي فيها الأرضية)
                glStencilFunc(GL_EQUAL, 1, 0xFF)
                glStencilOp(GL_KEEP, GL_KEEP, GL_INCR)
                
                glDisable(GL_LIGHTING)
                glDisable(GL_DEPTH_TEST)
                glDisable(GL_TEXTURE_2D)
                glEnable(GL_BLEND)
                glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
                glColor4f(0.0, 0.0, 0.0, 0.6)
                
                self.is_rendering_shadow = True
                
                floor = floors[0]
                first_light = self.lights[0]
                l = first_light.الموقع
                light_w = 0.0 if first_light.النوع == "ضوء_موجه" else 1.0
                fy = floor.الموقع.y + 0.001
                
                dot_ln = l.y - light_w * fy
                s_mat = [
                    dot_ln, 0, 0, 0,
                    -l.x, -light_w*fy, -l.z, -light_w,
                    0, 0, dot_ln, 0,
                    l.x*fy, l.y*fy, l.z*fy, l.y
                ]
                
                glPushMatrix()
                glMultMatrixf(s_mat)
                
                for obj in others:
                    render_obj(obj)
                    
                glPopMatrix()
                
                self.is_rendering_shadow = False
                
                glEnable(GL_LIGHTING)
                glEnable(GL_DEPTH_TEST)
                glDisable(GL_BLEND)
                glDisable(GL_STENCIL_TEST)
                
                # 3. رسم باقي المجسمات بشكل عادي
                for obj in others:
                    render_obj(obj)
            else:
                for obj in all_3d_objs:
                    render_obj(obj)
        else:
            world_2d = [o for o in self.objects_2d if not getattr(o, 'مساحة_الشاشة', True)]
            all_3d_objs = self.objects + world_2d
            for obj in all_3d_objs:
                render_obj(obj)

        # ==========================
        # رسم حدود التصادم (AABB)
        # ==========================
        for obj in self.objects + self.objects_2d:
            if getattr(obj, 'رؤية_صدام', False):
                aabb = self.physics_engine._get_aabb_3d(obj)
                self.draw_aabb(aabb)

        # ==========================
        # رسم واجهة المستخدم 2D (HUD)
        # ==========================
        screen_2d = [o for o in self.objects_2d if getattr(o, 'مساحة_الشاشة', True)]
        if screen_2d:
            glDisable(GL_DEPTH_TEST)
            glDisable(GL_LIGHTING)
            
            glMatrixMode(GL_PROJECTION)
            glPushMatrix()
            glLoadIdentity()
            w, h = self.get_current_size()
            glOrtho(0, w, h, 0, -1000, 1000)
            
            glMatrixMode(GL_MODELVIEW)
            glPushMatrix()
            glLoadIdentity()
            
            glEnable(GL_BLEND)
            glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
            
            for obj in screen_2d:
                # ابحث عن مسار الصورة
                tex_path = getattr(obj, "الصورة", "") or getattr(obj, "الخامة", "")
                
                # أعد التحميل إذا تغير المسار
                prev_path = getattr(obj, "_tex_path", None)
                if tex_path != prev_path:
                    obj._tex_loaded = False
                    obj._tex_path = tex_path
                    obj.texture_id = None
                
                # حمّل الـ texture مرة واحدة فقط
                if tex_path and not getattr(obj, "_tex_loaded", False):
                    try:
                        import textures
                        tid = textures.load_texture(tex_path)
                        obj.texture_id = tid
                    except Exception as e:
                        print(f"[خطأ تحميل صورة 2D]: {e}")
                        obj.texture_id = None
                    obj._tex_loaded = True
                
                tex_id = getattr(obj, "texture_id", None)
                has_tex = tex_id is not None and tex_id not in (0, -1)
                
                if has_tex:
                    glEnable(GL_TEXTURE_2D)
                    glBindTexture(GL_TEXTURE_2D, tex_id)
                    glColor4f(obj.اللون.r, obj.اللون.g, obj.اللون.b, 1.0)
                else:
                    glDisable(GL_TEXTURE_2D)
                    glColor3f(obj.اللون.r, obj.اللون.g, obj.اللون.b)
                    
                glPushMatrix()
                
                # قراءة زاوية الدوران كمتجه3 أو كرقم (للتوافق مع 2D القديم)
                if isinstance(obj.الدوران, (int, float)):
                    rot_x, rot_y, rot_z = 0, 0, obj.الدوران
                else:
                    rot_x, rot_y, rot_z = obj.الدوران.x, obj.الدوران.y, obj.الدوران.z
                    
                if type(obj).__name__ in ("Square2D", "Custom2D"):
                    x, y, z = obj.الموقع.x, obj.الموقع.y, obj.الموقع.z
                    sw, sh = obj.المقياس.x, obj.المقياس.y
                    
                    glTranslatef(x, y, z)
                    glRotatef(rot_x, 1, 0, 0)
                    glRotatef(rot_y, 0, 1, 0)
                    glRotatef(rot_z, 0, 0, 1)

                    # رسم المربع ممركزاً
                    glBegin(GL_QUADS)
                    if has_tex:
                        glTexCoord2f(0, 0); glVertex3f(-sw/2, -sh/2, 0)
                        glTexCoord2f(1, 0); glVertex3f(sw/2, -sh/2, 0)
                        glTexCoord2f(1, 1); glVertex3f(sw/2, sh/2, 0)
                        glTexCoord2f(0, 1); glVertex3f(-sw/2, sh/2, 0)
                    else:
                        glVertex3f(-sw/2, -sh/2, 0)
                        glVertex3f(sw/2, -sh/2, 0)
                        glVertex3f(sw/2, sh/2, 0)
                        glVertex3f(-sw/2, sh/2, 0)
                    glEnd()
                elif type(obj).__name__ == "Circle2D":
                    x, y, z = obj.الموقع.x, obj.الموقع.y, obj.الموقع.z
                    r = obj.المقياس.x  # نستخدم x كنصف قطر
                    
                    glTranslatef(x, y, z)
                    glRotatef(rot_x, 1, 0, 0)
                    glRotatef(rot_y, 0, 1, 0)
                    glRotatef(rot_z, 0, 0, 1)

                    glBegin(GL_POLYGON)
                    import math
                    for i in range(36):
                        theta = i * 10 * 3.14159 / 180
                        cx, cy = math.cos(theta), math.sin(theta)
                        if has_tex: glTexCoord2f(cx * 0.5 + 0.5, cy * 0.5 + 0.5)
                        glVertex3f(r * cx, r * cy, 0)
                    glEnd()
                elif type(obj).__name__ == "Triangle2D":
                    x, y, z = obj.الموقع.x, obj.الموقع.y, obj.الموقع.z
                    bw, bh = obj.المقياس.x, obj.المقياس.y

                    glTranslatef(x, y, z)
                    glRotatef(rot_x, 1, 0, 0)
                    glRotatef(rot_y, 0, 1, 0)
                    glRotatef(rot_z, 0, 0, 1)

                    glBegin(GL_TRIANGLES)
                    if has_tex: glTexCoord2f(0.5, 0.0)
                    glVertex3f(0, bh/2, 0)
                    if has_tex: glTexCoord2f(0.0, 1.0)
                    glVertex3f(-bw/2, -bh/2, 0)
                    if has_tex: glTexCoord2f(1.0, 1.0)
                    glVertex3f(bw/2, -bh/2, 0)
                    glEnd()
                glPopMatrix()
            
            glMatrixMode(GL_PROJECTION)
            glPopMatrix()
            glMatrixMode(GL_MODELVIEW)
            glPopMatrix()
            
            glEnable(GL_DEPTH_TEST)

        if hasattr(self, 'tonemapper') and self.tonemapper:
            self.tonemapper.unbind_and_draw()

        # ==========================
        # رسم واجهة المستخدم UI Canvas
        # ==========================
        if self.canvas and self.canvas.elements:
            glDisable(GL_DEPTH_TEST)
            glDisable(GL_LIGHTING)
            
            glMatrixMode(GL_PROJECTION)
            glPushMatrix()
            glLoadIdentity()
            
            w, h = self.get_current_size()
            glOrtho(0, w, h, 0, -1, 1)
            
            glMatrixMode(GL_MODELVIEW)
            glPushMatrix()
            glLoadIdentity()
            
            glEnable(GL_BLEND)
            glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
            
            cw, ch = w, h
            cx, cy = 0, 0
            if not getattr(self.canvas, 'كامل_الشاشة', False):
                if hasattr(self.canvas, 'المقياس'):
                    cw = self.canvas.المقياس.x
                    ch = self.canvas.المقياس.y
                if hasattr(self.canvas, 'الموقع'):
                    cx = self.canvas.الموقع.x
                    cy = self.canvas.الموقع.y
                    
            # Draw Canvas Background
            if hasattr(self.canvas, 'لون_الخلفية') and self.canvas.لون_الخلفية:
                alpha = getattr(self.canvas, 'شفافية_الخلفية', 0.0)
                if alpha > 0:
                    glDisable(GL_TEXTURE_2D)
                    glColor4f(self.canvas.لون_الخلفية.r, self.canvas.لون_الخلفية.g, self.canvas.لون_الخلفية.b, alpha)
                    glBegin(GL_QUADS)
                    glVertex2f(cx, cy)
                    glVertex2f(cx + cw, cy)
                    glVertex2f(cx + cw, cy + ch)
                    glVertex2f(cx, cy + ch)
                    glEnd()
                
            mx, my = pygame.mouse.get_pos()
            
            for el in self.canvas.elements:
                text_str = el.النص
                if HAS_ARABIC:
                    try:
                        reshaped = arabic_reshaper.reshape(text_str)
                        text_str = get_display(reshaped)
                    except:
                        pass
                    
                if el.texture_id is None or el._last_text != text_str or \
                   el._last_color != (el.لون_النص.r, el.لون_النص.g, el.لون_النص.b) or \
                   el._last_size != el.حجم_الخط or getattr(el, '_last_font_name', None) != el.اسم_الخط:
                   
                    if el.texture_id is not None:
                        glDeleteTextures([el.texture_id])
                        
                    pygame.font.init()
                    font = None
                    
                    if el.اسم_الخط.lower().endswith(".ttf"):
                        try:
                            font = pygame.font.Font(el.اسم_الخط, el.حجم_الخط)
                        except:
                            pass
                    
                    if font is None:
                        # Try the user's font first, then fallback to common Arabic fonts
                        fonts_to_try = [el.اسم_الخط, "tahoma", "segoeui", "arial", "timesnewroman"]
                        for f in fonts_to_try:
                            font_path = pygame.font.match_font(f)
                            if font_path:
                                try:
                                    font = pygame.font.Font(font_path, el.حجم_الخط)
                                    break
                                except:
                                    pass
                    
                    if font is None:
                        font = pygame.font.Font(None, el.حجم_الخط)
                        
                    r, g, b = int(el.لون_النص.r * 255), int(el.لون_النص.g * 255), int(el.لون_النص.b * 255)
                    text_surface = font.render(text_str, True, (r, g, b))
                    
                    el.width = text_surface.get_width()
                    el.height = text_surface.get_height()
                    
                    text_data = pygame.image.tostring(text_surface, "RGBA", True)
                    
                    el.texture_id = glGenTextures(1)
                    glBindTexture(GL_TEXTURE_2D, el.texture_id)
                    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
                    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
                    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, el.width, el.height, 0, GL_RGBA, GL_UNSIGNED_BYTE, text_data)
                    
                    el._last_text = text_str
                    el._last_color = (el.لون_النص.r, el.لون_النص.g, el.لون_النص.b)
                    el._last_size = el.حجم_الخط
                    el._last_font_name = el.اسم_الخط

                total_w = el.width
                total_h = el.height
                if type(el).__name__ == "UIButton":
                    total_w = el.المقياس.x if el.المقياس.x > 0 else el.width + 20
                    total_h = el.المقياس.y if el.المقياس.y > 0 else el.height + 20

                px = el.ازاحة.x
                py = el.ازاحة.y
                
                if el.افقي == "وسط":
                    px += cw / 2 - total_w / 2
                elif el.افقي == "يسار":
                    px += 0
                elif el.افقي == "يمين":
                    px += cw - total_w
                    
                if el.عمودي == "وسط":
                    py += ch / 2 - total_h / 2
                elif el.عمودي == "فوق":
                    py += 0
                elif el.عمودي == "تحت":
                    py += ch - total_h
                
                px += cx
                py += cy
                
                if type(el).__name__ == "UIButton":
                    is_hover = px <= mx <= px + total_w and py <= my <= py + total_h
                    el._hover = is_hover
                    el.مضغوط = is_hover and self.mouse.ضغط_يسار
                    
                    if getattr(el, "الخامة", None) and getattr(el, "texture_id_bg", None) is None:
                        try:
                            import textures
                            el.texture_id_bg = textures.load_texture(el.الخامة)
                        except:
                            el.texture_id_bg = -1
                            
                    if getattr(el, "texture_id_bg", -1) != -1 and el.texture_id_bg is not None:
                        glEnable(GL_TEXTURE_2D)
                        glBindTexture(GL_TEXTURE_2D, el.texture_id_bg)
                        if is_hover:
                            glColor4f(0.8, 0.8, 0.8, 1.0)
                        else:
                            glColor4f(1.0, 1.0, 1.0, 1.0)
                    else:
                        glDisable(GL_TEXTURE_2D)
                        br, bg, bb = el.لون_الخلفية.r, el.لون_الخلفية.g, el.لون_الخلفية.b
                        if is_hover:
                            br, bg, bb = min(1.0, br*1.2), min(1.0, bg*1.2), min(1.0, bb*1.2)
                        glColor4f(br, bg, bb, getattr(el, 'شفافية_الخلفية', 1.0))
                        
                    glBegin(GL_QUADS)
                    if getattr(el, "texture_id_bg", -1) != -1 and el.texture_id_bg is not None:
                        glTexCoord2f(0, 1); glVertex2f(px, py)
                        glTexCoord2f(1, 1); glVertex2f(px + total_w, py)
                        glTexCoord2f(1, 0); glVertex2f(px + total_w, py + total_h)
                        glTexCoord2f(0, 0); glVertex2f(px, py + total_h)
                    else:
                        glVertex2f(px, py)
                        glVertex2f(px + total_w, py)
                        glVertex2f(px + total_w, py + total_h)
                        glVertex2f(px, py + total_h)
                    glEnd()
                    
                    text_x = px + (total_w / 2) - (el.width / 2)
                    text_y = py + (total_h / 2) - (el.height / 2)
                else:
                    text_x = px
                    text_y = py
                    
                    if hasattr(el, 'لون_الخلفية') and getattr(el, 'شفافية_الخلفية', 0.0) > 0:
                        glDisable(GL_TEXTURE_2D)
                        glColor4f(el.لون_الخلفية.r, el.لون_الخلفية.g, el.لون_الخلفية.b, getattr(el, 'شفافية_الخلفية', 1.0))
                        glBegin(GL_QUADS)
                        glVertex2f(px, py)
                        glVertex2f(px + total_w, py)
                        glVertex2f(px + total_w, py + total_h)
                        glVertex2f(px, py + total_h)
                        glEnd()

                glEnable(GL_TEXTURE_2D)
                glBindTexture(GL_TEXTURE_2D, el.texture_id)
                glColor4f(1.0, 1.0, 1.0, 1.0)
                
                glBegin(GL_QUADS)
                glTexCoord2f(0, 1); glVertex2f(text_x, text_y)
                glTexCoord2f(1, 1); glVertex2f(text_x + el.width, text_y)
                glTexCoord2f(1, 0); glVertex2f(text_x + el.width, text_y + el.height)
                glTexCoord2f(0, 0); glVertex2f(text_x, text_y + el.height)
                glEnd()
                
                glDisable(GL_TEXTURE_2D)
            
            glPopMatrix()
            glMatrixMode(GL_PROJECTION)
            glPopMatrix()
            glMatrixMode(GL_MODELVIEW)
            glEnable(GL_DEPTH_TEST)

        if not getattr(self, 'is_editor_preview', False):
            pygame.display.flip()
