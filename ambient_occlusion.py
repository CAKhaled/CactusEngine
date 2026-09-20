"""
ambient_occlusion.py
=====================
نظام Ambient Occlusion بسيط للمشاهد ثلاثية الأبعاد.

الطريقة:
  - لكل وجه من أوجه كل مكعب، نرمي أشعة عشوائية في نصف كرة باتجاه النورمال
  - إذا اصطدم شعاع بمكعب آخر → يزيد التظليل
  - معامل AO الناتج يُطبَّق كتعديل على اللون عند الرسم

الاستخدام:
  from ambient_occlusion import AOBaker
  baker = AOBaker(num_samples=32, max_distance=4.0)
  baker.bake(objects)        # يُحسب مرة واحدة قبل حلقة الرندر
"""

import math
import random


# ─────────────────────────────────────────
# مساعدات الحساب
# ─────────────────────────────────────────

def _dot(a, b):
    return a[0]*b[0] + a[1]*b[1] + a[2]*b[2]

def _cross(a, b):
    return (
        a[1]*b[2] - a[2]*b[1],
        a[2]*b[0] - a[0]*b[2],
        a[0]*b[1] - a[1]*b[0],
    )

def _normalize(v):
    length = math.sqrt(v[0]**2 + v[1]**2 + v[2]**2)
    if length < 1e-8:
        return (0.0, 1.0, 0.0)
    return (v[0]/length, v[1]/length, v[2]/length)


# ─────────────────────────────────────────
# تقاطع شعاع مع AABB
# ─────────────────────────────────────────

def _ray_hits_aabb(origin, direction, box_min, box_max, max_dist):
    """
    اختبار تقاطع شعاع (slab method) مع صندوق محيطي.
    يُعيد True إذا تقاطع الشعاع في المسافة (0, max_dist).
    """
    t_min = 0.0001  # تجنّب التقاطع الذاتي
    t_max = max_dist

    for i in range(3):
        orig_i = origin[i]
        dir_i  = direction[i]
        bmin_i = box_min[i]
        bmax_i = box_max[i]

        if abs(dir_i) < 1e-9:
            # الشعاع موازٍ لهذا المحور
            if orig_i < bmin_i or orig_i > bmax_i:
                return False
        else:
            t1 = (bmin_i - orig_i) / dir_i
            t2 = (bmax_i - orig_i) / dir_i
            if t1 > t2:
                t1, t2 = t2, t1
            t_min = max(t_min, t1)
            t_max = min(t_max, t2)
            if t_min > t_max:
                return False

    return True


# ─────────────────────────────────────────
# توليد عيّنات نصف كرة
# ─────────────────────────────────────────

def _build_tangent_frame(normal):
    """يبني إطار (tangent, bitangent, normal) لتحويل العيّنات."""
    n = _normalize(normal)
    up = (1.0, 0.0, 0.0) if abs(n[1]) > 0.9 else (0.0, 1.0, 0.0)
    t = _normalize(_cross(n, up))
    b = _cross(n, t)
    return t, b, n


def _hemisphere_samples(normal, num_samples):
    """
    يولّد عيّنات موزّعة بتوزيع جيب التمام (cosine-weighted)
    في نصف الكرة باتجاه normal.
    """
    t, b, n = _build_tangent_frame(normal)
    samples = []

    for _ in range(num_samples):
        # Cosine-weighted hemisphere sampling
        r1 = random.random()
        r2 = random.random()

        sin_theta = math.sqrt(r1)
        cos_theta = math.sqrt(1.0 - r1)
        phi       = 2.0 * math.pi * r2

        # إحداثيات في الإطار المحلي
        sx = sin_theta * math.cos(phi)
        sy = sin_theta * math.sin(phi)
        sz = cos_theta

        # تحويل إلى الإطار العالمي
        wx = sx * t[0] + sy * b[0] + sz * n[0]
        wy = sx * t[1] + sy * b[1] + sz * n[1]
        wz = sx * t[2] + sy * b[2] + sz * n[2]

        samples.append((wx, wy, wz))

    return samples


# ─────────────────────────────────────────
# AOBaker — الكلاس الرئيسي
# ─────────────────────────────────────────

class AOBaker:
    """
    يحسب Ambient Occlusion لكل مكعب في المشهد مرة واحدة قبل الرندر.

    المعاملات:
      num_samples  : عدد الأشعة لكل وجه (أكثر = أدق وأبطأ)
      max_distance : أقصى مسافة يؤثر فيها مكعب على AO مكعب آخر
      strength     : قوة تأثير AO (0.0 = لا تأثير، 1.0 = تأثير كامل)
    """

    # أوجه المكعب: (إزاحة مركز الوجه، اتجاه النورمال)
    FACES = [
        ((0,  0,  1), ( 0,  0,  1)),  # الأمام
        ((0,  0, -1), ( 0,  0, -1)),  # الخلف
        ((-1, 0,  0), (-1,  0,  0)),  # اليسار
        (( 1, 0,  0), ( 1,  0,  0)),  # اليمين
        ((0,  1,  0), ( 0,  1,  0)),  # الأعلى
        ((0, -1,  0), ( 0, -1,  0)),  # الأسفل
    ]

    def __init__(self, num_samples=32, max_distance=4.0, strength=0.7):
        self.num_samples  = num_samples
        self.max_distance = max_distance
        self.strength     = strength

    # ─────────────────────────────────────
    # الحساب الرئيسي
    # ─────────────────────────────────────

    def bake(self, objects):
        """
        يحسب معاملات AO لكل وجه في كل مكعب ويخزّنها في cube.ao_factors.
        cube.ao_factors = قائمة من 6 قيم (0.0 → مظلم تماماً ، 1.0 → لا تظليل)
        الترتيب: [أمام، خلف، يسار، يمين، أعلى، أسفل]
        """
        # بناء قائمة AABB لكل مكعب مرة واحدة
        aabbs = self._build_aabbs(objects)

        for idx, cube in enumerate(objects):
            factors = []

            px = cube.الموقع.x
            py = cube.الموقع.y
            pz = cube.الموقع.z

            for (offset, normal) in self.FACES:
                # مركز الوجه في الإحداثيات العالمية
                face_center = (
                    px + offset[0],
                    py + offset[1],
                    pz + offset[2],
                )

                samples = _hemisphere_samples(normal, self.num_samples)

                hit_count = 0
                for ray_dir in samples:
                    for j, aabb in enumerate(aabbs):
                        if j == idx:
                            continue  # تجاهل المكعب نفسه
                        if _ray_hits_aabb(face_center, ray_dir,
                                          aabb[0], aabb[1],
                                          self.max_distance):
                            hit_count += 1
                            break  # يكفي أول اصطدام لهذا الشعاع

                occlusion = hit_count / self.num_samples   # 0.0 → 1.0
                ao_value  = 1.0 - occlusion * self.strength
                factors.append(max(0.0, min(1.0, ao_value)))

            cube.ao_factors = factors

        print(f"[AO] تم حساب Ambient Occlusion لـ {len(objects)} مجسم "
              f"({self.num_samples} عيّنة لكل وجه)")

    # ─────────────────────────────────────
    # مساعدات
    # ─────────────────────────────────────

    def _build_aabbs(self, objects):
        """يُعيد قائمة من (box_min, box_max) لكل مكعب (حجم 1×1×1 نصف حجم)."""
        aabbs = []
        for cube in objects:
            px = cube.الموقع.x
            py = cube.الموقع.y
            pz = cube.الموقع.z
            sx = cube.المقياس.x
            sy = cube.المقياس.y
            sz = cube.المقياس.z
            aabbs.append((
                (px - sx, py - sy, pz - sz),  # box_min
                (px + sx, py + sy, pz + sz),  # box_max
            ))
        return aabbs
