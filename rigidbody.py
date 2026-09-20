import math
from math_types import Vector2, Vector3


# ─────────────────────────────────────────────────────────────────────────────
# تحويل نقطة محلية → عالمية (نفس ترتيب OpenGL)
# ─────────────────────────────────────────────────────────────────────────────
def _apply_transform(x, y, z, px, py, pz, prx, pry, prz, psx, psy, psz):
    x *= psx;  y *= psy;  z *= psz
    rz = math.radians(prz)
    x, y = x*math.cos(rz) - y*math.sin(rz), x*math.sin(rz) + y*math.cos(rz)
    ry = math.radians(pry)
    x, z = x*math.cos(ry) + z*math.sin(ry), -x*math.sin(ry) + z*math.cos(ry)
    rx = math.radians(prx)
    y, z = y*math.cos(rx) - z*math.sin(rx),  y*math.sin(rx) + z*math.cos(rx)
    return x + px, y + py, z + pz


# ─────────────────────────────────────────────────────────────────────────────
# حساب Convex Hull مبسّط عند التحميل (مرة واحدة فقط)
# ─────────────────────────────────────────────────────────────────────────────

# 26 اتجاه يغطي كل أوجه/حواف/زوايا مكعب الوحدة
_HULL_DIRS = []
for _sx in (-1, 0, 1):
    for _sy in (-1, 0, 1):
        for _sz in (-1, 0, 1):
            if _sx == 0 and _sy == 0 and _sz == 0:
                continue
            _n = math.sqrt(_sx*_sx + _sy*_sy + _sz*_sz)
            _HULL_DIRS.append((_sx/_n, _sy/_n, _sz/_n))


def compute_convex_hull_approx(vertices):
    """
    يُعيد ~26 نقطة تمثّل "Support Points" للـ mesh في 26 اتجاهاً.
    هذه النقاط كافية لتعريف الـ Convex Hull التقريبي.
    """
    if not vertices:
        return []
    hull = set()
    for dx, dy, dz in _HULL_DIRS:
        best_dot = -float('inf')
        best_idx = 0
        for i, (vx, vy, vz) in enumerate(vertices):
            d = vx*dx + vy*dy + vz*dz
            if d > best_dot:
                best_dot = d
                best_idx = i
        hull.add(best_idx)
    return [vertices[i] for i in hull]


# ─────────────────────────────────────────────────────────────────────────────
# Convex Mesh Collider - يستخدم Hull المبسّط + Cache
# ─────────────────────────────────────────────────────────────────────────────
class MeshCollider:

    @staticmethod
    def get_world_hull(fbx_component):
        """
        يُعيد Hull Vertices في الفضاء العالمي.
        يستخدم Cache: يُعيد النتيجة المخزّنة إذا لم يتغير الـ Transform.
        """
        comp = fbx_component
        p = comp.parent
        if p is None:
            return []

        px, py, pz    = p.الموقع.x,  p.الموقع.y,  p.الموقع.z
        prx, pry, prz = p.الدوران.x, p.الدوران.y, p.الدوران.z
        psx = p.المقياس.x if hasattr(p, 'المقياس') else 1.0
        psy = p.المقياس.y if hasattr(p, 'المقياس') else 1.0
        psz = p.المقياس.z if hasattr(p, 'المقياس') else 1.0

        # ── Cache: تحقق إذا لم يتغير الـ Transform ──
        transform_key = (round(px,4), round(py,4), round(pz,4),
                         round(prx,2), round(pry,2), round(prz,2),
                         round(psx,4), round(psy,4), round(psz,4))

        cached_key  = getattr(comp, '_hull_cache_key',  None)
        cached_hull = getattr(comp, '_hull_cache_world', None)

        if cached_key == transform_key and cached_hull is not None:
            return cached_hull

        # ── احسب Hull المحلي مرة واحدة عند التحميل ──
        local_hull = getattr(p, '_local_hull', None)
        if local_hull is None:
            mesh = getattr(comp, 'mesh', None)
            if mesh and hasattr(mesh, 'vertices') and mesh.vertices:
                local_hull = compute_convex_hull_approx(mesh.vertices)
            else:
                local_hull = []
            p._local_hull = local_hull

        # ── حوّل Hull للفضاء العالمي ──
        world_hull = [
            _apply_transform(lx, ly, lz, px, py, pz, prx, pry, prz, psx, psy, psz)
            for (lx, ly, lz) in local_hull
        ]

        comp._hull_cache_key   = transform_key
        comp._hull_cache_world = world_hull
        return world_hull

    @staticmethod
    def get_world_aabb(fbx_component):
        """AABB من Hull الفعلي — دقيق وسريع."""
        hull = MeshCollider.get_world_hull(fbx_component)
        if not hull:
            return None
        xs = [v[0] for v in hull]
        ys = [v[1] for v in hull]
        zs = [v[2] for v in hull]
        return {
            'min_x': min(xs), 'max_x': max(xs),
            'min_y': min(ys), 'max_y': max(ys),
            'min_z': min(zs), 'max_z': max(zs),
        }

    @staticmethod
    def get_min_y(fbx_component):
        """أدنى نقطة Y في الـ Hull في الفضاء العالمي."""
        hull = MeshCollider.get_world_hull(fbx_component)
        if not hull:
            return None
        return min(v[1] for v in hull)


# ─────────────────────────────────────────────────────────────────────────────
# محرك الفيزياء
# ─────────────────────────────────────────────────────────────────────────────
class PhysicsEngine:
    def __init__(self):
        self.gravity_3d          = -9.81
        self.terminal_velocity_3d = -50.0
        self.gravity_2d           =  9.81 * 50
        self.terminal_velocity_2d =  1000.0

    # ─── AABB 3D ─────────────────────────────────────────────────────────────
    def _get_aabb_3d(self, obj):
        sx, sy, sz = 1.0, 1.0, 1.0
        if hasattr(obj, 'المقياس'):
            sx, sy, sz = obj.المقياس.x, obj.المقياس.y, obj.المقياس.z
        px, py, pz = obj.الموقع.x, obj.الموقع.y, obj.الموقع.z
        t = type(obj).__name__

        if t == 'FBXComponent' and hasattr(obj, 'parent') and obj.parent:
            p = obj.parent
            custom_box    = getattr(p, 'صندوق_صدام', None)
            custom_center = getattr(p, 'مركز_صدام',  None)

            if custom_box is not None:
                # صندوق مخصص من المستخدم
                ppx, ppy, ppz     = p.الموقع.x, p.الموقع.y, p.الموقع.z
                prx2, pry2, prz2  = p.الدوران.x, p.الدوران.y, p.الدوران.z
                psx2 = p.المقياس.x if hasattr(p,'المقياس') else 1.0
                psy2 = p.المقياس.y if hasattr(p,'المقياس') else 1.0
                psz2 = p.المقياس.z if hasattr(p,'المقياس') else 1.0
                hx, hy, hz = custom_box.x/2, custom_box.y/2, custom_box.z/2
                cx = custom_center.x if custom_center else 0
                cy = custom_center.y if custom_center else 0
                cz = custom_center.z if custom_center else 0
                corners = [
                    (-hx+cx, -hy+cy, -hz+cz), ( hx+cx, -hy+cy, -hz+cz),
                    (-hx+cx,  hy+cy, -hz+cz), ( hx+cx,  hy+cy, -hz+cz),
                    (-hx+cx, -hy+cy,  hz+cz), ( hx+cx, -hy+cy,  hz+cz),
                    (-hx+cx,  hy+cy,  hz+cz), ( hx+cx,  hy+cy,  hz+cz),
                ]
                pts = [_apply_transform(*c, ppx,ppy,ppz,prx2,pry2,prz2,psx2,psy2,psz2)
                       for c in corners]
                return {
                    'min_x': min(pt[0] for pt in pts), 'max_x': max(pt[0] for pt in pts),
                    'min_y': min(pt[1] for pt in pts), 'max_y': max(pt[1] for pt in pts),
                    'min_z': min(pt[2] for pt in pts), 'max_z': max(pt[2] for pt in pts),
                }

            # Convex Mesh Collider (Hull مبسّط بـ Cache)
            aabb = MeshCollider.get_world_aabb(obj)
            if aabb:
                return aabb

            # Fallback
            ppx2, ppy2, ppz2 = p.الموقع.x, p.الموقع.y, p.الموقع.z
            pss = p.المقياس.x if hasattr(p,'المقياس') else 1.0
            return {'min_x': ppx2-pss,'max_x': ppx2+pss,
                    'min_y': ppy2-pss,'max_y': ppy2+pss,
                    'min_z': ppz2-pss,'max_z': ppz2+pss}

        if t == 'Plane':
            return {'min_x': px-sx, 'max_x': px+sx,
                    'min_y': py-sy*8,'max_y': py+0.05,
                    'min_z': pz-sz,  'max_z': pz+sz}
        if t in ('Sphere', 'Pyramid', 'Cylinder', 'Cube', 'CustomModel'):
            return {'min_x': px-sx,'max_x': px+sx,
                    'min_y': py-sy,'max_y': py+sy,
                    'min_z': pz-sz,'max_z': pz+sz}
        if t in ('Square2D', 'Custom2D'):
            return {'min_x': px-sx/2,'max_x': px+sx/2,
                    'min_y': py-sy/2,'max_y': py+sy/2,
                    'min_z': pz-0.01,'max_z': pz+0.01}
        if t == 'Circle2D':
            return {'min_x': px-sx,'max_x': px+sx,
                    'min_y': py-sx,'max_y': py+sx,
                    'min_z': pz-0.01,'max_z': pz+0.01}
        if t == 'Triangle2D':
            return {'min_x': px-sx/2,'max_x': px+sx/2,
                    'min_y': py-sy/2,'max_y': py+sy/2,
                    'min_z': pz-0.01,'max_z': pz+0.01}
        if t == 'Capsule':
            return {'min_x': px-sx,'max_x': px+sx,
                    'min_y': py-sy*2,'max_y': py+sy*2,
                    'min_z': pz-sz,'max_z': pz+sz}
        return {'min_x': px-sx,'max_x': px+sx,
                'min_y': py-sy,'max_y': py+sy,
                'min_z': pz-sz,'max_z': pz+sz}

    # ─── AABB 2D ─────────────────────────────────────────────────────────────
    def _get_aabb_2d(self, obj):
        t = type(obj).__name__
        px, py = obj.الموقع.x, obj.الموقع.y
        if t in ('Square2D', 'Custom2D'):
            w, h = obj.المقياس.x, obj.المقياس.y
            return {'min_x': px - w/2, 'max_x': px + w/2, 'min_y': py - h/2, 'max_y': py + h/2}
        elif t == 'Circle2D':
            r = obj.نصف_القطر if hasattr(obj, 'نصف_القطر') else obj.المقياس.x
            return {'min_x': px-r,'max_x': px+r,'min_y': py-r,'max_y': py+r}
        elif t == 'Triangle2D':
            w = obj.القاعدة if hasattr(obj, 'القاعدة') else obj.المقياس.x
            h = obj.الارتفاع if hasattr(obj, 'الارتفاع') else obj.المقياس.y
            return {'min_x': px-w/2,'max_x': px+w/2,'min_y': py-h/2,'max_y': py+h/2}
        return {'min_x': px,'max_x': px,'min_y': py,'max_y': py}

    def _check_overlap(self, b1, b2):
        if 'min_z' in b1:
            return (b1['min_x'] <= b2['max_x'] and b1['max_x'] >= b2['min_x'] and
                    b1['min_y'] <= b2['max_y'] and b1['max_y'] >= b2['min_y'] and
                    b1['min_z'] <= b2['max_z'] and b1['max_z'] >= b2['min_z'])
        return (b1['min_x'] <= b2['max_x'] and b1['max_x'] >= b2['min_x'] and
                b1['min_y'] <= b2['max_y'] and b1['max_y'] >= b2['min_y'])

    # ─── حل التصادم 3D ───────────────────────────────────────────────────────
    def _get_fbx_parent(self, obj):
        if type(obj).__name__ == 'FBXComponent' and hasattr(obj,'parent') and obj.parent:
            return obj.parent
        return None

    def _resolve_collision_3d(self, obj1, obj2, box1, box2):
        # حرّك FBXModel الأب دائماً (ليس FBXComponent)
        move1 = self._get_fbx_parent(obj1) or obj1
        move2 = self._get_fbx_parent(obj2) or obj2

        overlap_y1 = box1['max_y'] - box2['min_y']
        overlap_y2 = box2['max_y'] - box1['min_y']
        overlap_x1 = box1['max_x'] - box2['min_x']
        overlap_x2 = box2['max_x'] - box1['min_x']
        overlap_z1 = box1['max_z'] - box2['min_z']
        overlap_z2 = box2['max_z'] - box1['min_z']

        overlaps = [
            (overlap_y1,'y',-1),(overlap_y2,'y',1),
            (overlap_x1,'x',-1),(overlap_x2,'x',1),
            (overlap_z1,'z',-1),(overlap_z2,'z',1),
        ]
        valid = [o for o in overlaps if o[0] > 0]
        if not valid: return

        amount, axis, direction = min(valid, key=lambda x: x[0])
        amount += 1e-4

        m1 = getattr(obj1,'جاذبية',False) in (1,True,'مفعل')
        m2 = getattr(obj2,'جاذبية',False) in (1,True,'مفعل')
        is_cam1 = getattr(obj1,'الاسم','') == 'الكاميرا'
        is_cam2 = getattr(obj2,'الاسم','') == 'الكاميرا'

        def push(target, vel_src, sign):
            if axis == 'y':
                target.الموقع.y += amount * direction * sign
                vel_src._velocity.y = 0
            elif axis == 'x':
                target.الموقع.x += amount * direction * sign
                vel_src._velocity.x *= 0.5
            elif axis == 'z':
                target.الموقع.z += amount * direction * sign
                vel_src._velocity.z *= 0.5

        if m1 and m2:
            push(move1, obj1,  1)
            push(move2, obj2, -1)
        elif not m1 and not m2:
            t = move1 if (is_cam1 and not is_cam2) else (move2 if (is_cam2 and not is_cam1) else move1)
            v = obj1 if t is move1 else obj2
            push(t, v, 1 if t is move1 else -1)
        elif m1:
            push(move1, obj1, 1)
        else:
            push(move2, obj2, -1)

    def _resolve_collision_2d(self, obj1, obj2, box1, box2):
        overlaps = [
            (box1['max_y']-box2['min_y'],'y',-1),
            (box2['max_y']-box1['min_y'],'y', 1),
            (box1['max_x']-box2['min_x'],'x',-1),
            (box2['max_x']-box1['min_x'],'x', 1),
        ]
        valid = [o for o in overlaps if o[0] > 0]
        if not valid: return
        amount, axis, direction = min(valid, key=lambda x: x[0])
        amount += 1e-4
        m1 = getattr(obj1,'جاذبية',False) in (1,True,'مفعل')
        m2 = getattr(obj2,'جاذبية',False) in (1,True,'مفعل')
        target, sign = (obj1,1) if m1 and not m2 else ((obj2,-1) if m2 else (obj1,1))
        if axis == 'y':
            target.الموقع.y += amount * direction * sign; target._velocity.y = 0
        else:
            target.الموقع.x += amount * direction * sign; target._velocity.x = 0

    # ─── حلقة الفيزياء الرئيسية ───────────────────────────────────────────────
    def update_physics(self, objects_3d, objects_2d, delta_time):
        NUM_SUBSTEPS = 4
        sub_dt   = min(delta_time, 0.05) / NUM_SUBSTEPS
        solid_3d = [o for o in objects_3d if getattr(o,'صدام',False) in (1,True,'مفعل')]

        for _ in range(NUM_SUBSTEPS):
            # جاذبية
            for obj in objects_3d:
                if getattr(obj,'جاذبية',False) in (1,True,'مفعل'):
                    obj._velocity.y += self.gravity_3d * sub_dt
                    if obj._velocity.y < self.terminal_velocity_3d:
                        obj._velocity.y = self.terminal_velocity_3d
                    move_target = self._get_fbx_parent(obj) or obj
                    move_target.الموقع.y += obj._velocity.y * sub_dt

            # حل التصادمات
            for i in range(len(solid_3d)):
                for j in range(i+1, len(solid_3d)):
                    o1, o2 = solid_3d[i], solid_3d[j]
                    b1 = self._get_aabb_3d(o1)
                    b2 = self._get_aabb_3d(o2)
                    if b1 and b2 and self._check_overlap(b1, b2):
                        self._resolve_collision_3d(o1, o2, b1, b2)

        # 2D
        for obj in objects_2d:
            if getattr(obj,'جاذبية',False) in (1,True,'مفعل'):
                obj._velocity.y += self.gravity_2d * delta_time
                if obj._velocity.y > self.terminal_velocity_2d:
                    obj._velocity.y = self.terminal_velocity_2d
                obj.الموقع.y += obj._velocity.y * delta_time

        solid_2d = [o for o in objects_2d if getattr(o,'صدام',False) in (1,True,'مفعل')]
        for i in range(len(solid_2d)):
            for j in range(i+1, len(solid_2d)):
                o1, o2 = solid_2d[i], solid_2d[j]
                b1, b2 = self._get_aabb_2d(o1), self._get_aabb_2d(o2)
                if self._check_overlap(b1, b2):
                    self._resolve_collision_2d(o1, o2, b1, b2)

    # ─── Raycast ─────────────────────────────────────────────────────────────
    def _raycast(self, origin, direction, objects, max_distance):
        closest_obj  = None
        closest_dist = max_distance
        for obj in objects:
            try:
                aabb = self._get_aabb_3d(obj)
            except:
                continue
            if not aabb: continue
            tmin, tmax, hit = -float('inf'), float('inf'), True
            for axis in ['x','y','z']:
                mv = aabb[f'min_{axis}']; Mv = aabb[f'max_{axis}']
                ov = getattr(origin, axis); dv = getattr(direction, axis)
                if abs(dv) < 1e-6:
                    if ov < mv or ov > Mv: hit = False; break
                else:
                    t1 = (mv-ov)/dv; t2 = (Mv-ov)/dv
                    if t1 > t2: t1, t2 = t2, t1
                    tmin = max(tmin, t1); tmax = min(tmax, t2)
                    if tmin > tmax: hit = False; break
            if hit and 0 < tmin < closest_dist:
                closest_dist = tmin; closest_obj = obj
        return closest_obj
