"""
keyboard.py
============
كائن لوحة المفاتيح — يُستخدَم في لغة .kh للوصول إلى حالة الأزرار.

كل خاصية هي boolean:
  True  = المفتاح مضغوط الآن
  False = المفتاح غير مضغوط

الاستخدام في .kh:
  كل_فريم:
    اطبع كيبورد.مسافة
    اطبع كيبورد.w
    اطبع كيبورد.يسار
"""

import pygame


class Keyboard:

    def __init__(self):

        # ── حروف (a → z) ─────────────────────────────
        self.a = False;  self.b = False;  self.c = False
        self.d = False;  self.e = False;  self.f = False
        self.g = False;  self.h = False;  self.i = False
        self.j = False;  self.k = False;  self.l = False
        self.m = False;  self.n = False;  self.o = False
        self.p = False;  self.q = False;  self.r = False
        self.s = False;  self.t = False;  self.u = False
        self.v = False;  self.w = False;  self.x = False
        self.y = False;  self.z = False

        # ── أرقام (0 → 9) ────────────────────────────
        self.r0 = False;  self.r1 = False;  self.r2 = False
        self.r3 = False;  self.r4 = False;  self.r5 = False
        self.r6 = False;  self.r7 = False;  self.r8 = False
        self.r9 = False

        # ── أسهم التوجيه ──────────────────────────────
        self.يسار  = False
        self.يمين  = False
        self.أعلى  = False
        self.اعلى  = False
        self.أسفل  = False
        self.اسفل  = False

        # ── مفاتيح خاصة ──────────────────────────────
        self.مسافة   = False   # Space
        self.دخول    = False   # Enter
        self.هروب    = False   # Escape
        self.حذف     = False   # Backspace
        self.مسح     = False   # Delete
        self.تاب     = False   # Tab
        self.شيفت    = False   # Shift (أيسر أو أيمن)
        self.كنترول  = False   # Ctrl  (أيسر أو أيمن)
        self.ألت     = False   # Alt   (أيسر أو أيمن)
        self.كابس    = False   # Caps Lock
        self.انتر    = False   # alias لـ دخول

        # ── مفاتيح الوظائف F1→F12 ────────────────────
        self.f1  = False;  self.f2  = False;  self.f3  = False
        self.f4  = False;  self.f5  = False;  self.f6  = False
        self.f7  = False;  self.f8  = False;  self.f9  = False
        self.f10 = False;  self.f11 = False;  self.f12 = False

        # ── لوحة الأرقام الجانبية (Numpad) ───────────
        self.num0 = False;  self.num1 = False;  self.num2 = False
        self.num3 = False;  self.num4 = False;  self.num5 = False
        self.num6 = False;  self.num7 = False;  self.num8 = False
        self.num9 = False

        # ── علامات ────────────────────────────────────
        self.نقطة   = False   # .
        self.فاصلة  = False   # ,
        self.سيميكولون = False # ;
        self.مسافة_أمام = False  # /
        self.ناقص   = False   # -
        self.يساوي  = False   # =
        self.قوس_يسار  = False  # [
        self.قوس_يمين  = False  # ]
        self.شرطة_مائلة = False  # \

    # ─────────────────────────────────────────────────
    # التحديث — يُستدعى كل إطار من graphics.py
    # ─────────────────────────────────────────────────

    def update(self):
        """يقرأ حالة لوحة المفاتيح من pygame ويحدّث كل الخصائص."""

        k = pygame.key.get_pressed()

        # حروف
        self.a = bool(k[pygame.K_a]);  self.b = bool(k[pygame.K_b])
        self.c = bool(k[pygame.K_c]);  self.d = bool(k[pygame.K_d])
        self.e = bool(k[pygame.K_e]);  self.f = bool(k[pygame.K_f])
        self.g = bool(k[pygame.K_g]);  self.h = bool(k[pygame.K_h])
        self.i = bool(k[pygame.K_i]);  self.j = bool(k[pygame.K_j])
        self.k = bool(k[pygame.K_k]);  self.l = bool(k[pygame.K_l])
        self.m = bool(k[pygame.K_m]);  self.n = bool(k[pygame.K_n])
        self.o = bool(k[pygame.K_o]);  self.p = bool(k[pygame.K_p])
        self.q = bool(k[pygame.K_q]);  self.r = bool(k[pygame.K_r])
        self.s = bool(k[pygame.K_s]);  self.t = bool(k[pygame.K_t])
        self.u = bool(k[pygame.K_u]);  self.v = bool(k[pygame.K_v])
        self.w = bool(k[pygame.K_w]);  self.x = bool(k[pygame.K_x])
        self.y = bool(k[pygame.K_y]);  self.z = bool(k[pygame.K_z])

        # أرقام الصف العلوي
        self.r0 = bool(k[pygame.K_0]);  self.r1 = bool(k[pygame.K_1])
        self.r2 = bool(k[pygame.K_2]);  self.r3 = bool(k[pygame.K_3])
        self.r4 = bool(k[pygame.K_4]);  self.r5 = bool(k[pygame.K_5])
        self.r6 = bool(k[pygame.K_6]);  self.r7 = bool(k[pygame.K_7])
        self.r8 = bool(k[pygame.K_8]);  self.r9 = bool(k[pygame.K_9])

        # أسهم
        self.يسار = bool(k[pygame.K_LEFT])
        self.يمين = bool(k[pygame.K_RIGHT])
        self.أعلى = bool(k[pygame.K_UP])
        self.اعلى = self.أعلى
        self.أسفل = bool(k[pygame.K_DOWN])
        self.اسفل = self.أسفل

        # مفاتيح خاصة
        self.مسافة  = bool(k[pygame.K_SPACE])
        self.دخول   = bool(k[pygame.K_RETURN])
        self.انتر   = self.دخول
        self.هروب   = bool(k[pygame.K_ESCAPE])
        self.حذف    = bool(k[pygame.K_BACKSPACE])
        self.مسح    = bool(k[pygame.K_DELETE])
        self.تاب    = bool(k[pygame.K_TAB])
        self.شيفت   = bool(k[pygame.K_LSHIFT] or k[pygame.K_RSHIFT])
        self.كنترول = bool(k[pygame.K_LCTRL]  or k[pygame.K_RCTRL])
        self.ألت    = bool(k[pygame.K_LALT]   or k[pygame.K_RALT])
        self.كابس   = bool(k[pygame.K_CAPSLOCK])

        # F1 → F12
        self.f1  = bool(k[pygame.K_F1]);   self.f2  = bool(k[pygame.K_F2])
        self.f3  = bool(k[pygame.K_F3]);   self.f4  = bool(k[pygame.K_F4])
        self.f5  = bool(k[pygame.K_F5]);   self.f6  = bool(k[pygame.K_F6])
        self.f7  = bool(k[pygame.K_F7]);   self.f8  = bool(k[pygame.K_F8])
        self.f9  = bool(k[pygame.K_F9]);   self.f10 = bool(k[pygame.K_F10])
        self.f11 = bool(k[pygame.K_F11]);  self.f12 = bool(k[pygame.K_F12])

        # Numpad
        self.num0 = bool(k[pygame.K_KP0]);  self.num1 = bool(k[pygame.K_KP1])
        self.num2 = bool(k[pygame.K_KP2]);  self.num3 = bool(k[pygame.K_KP3])
        self.num4 = bool(k[pygame.K_KP4]);  self.num5 = bool(k[pygame.K_KP5])
        self.num6 = bool(k[pygame.K_KP6]);  self.num7 = bool(k[pygame.K_KP7])
        self.num8 = bool(k[pygame.K_KP8]);  self.num9 = bool(k[pygame.K_KP9])

        # علامات
        self.نقطة         = bool(k[pygame.K_PERIOD])
        self.فاصلة        = bool(k[pygame.K_COMMA])
        self.سيميكولون    = bool(k[pygame.K_SEMICOLON])
        self.مسافة_أمام   = bool(k[pygame.K_SLASH])
        self.ناقص         = bool(k[pygame.K_MINUS])
        self.يساوي        = bool(k[pygame.K_EQUALS])
        self.قوس_يسار     = bool(k[pygame.K_LEFTBRACKET])
        self.قوس_يمين     = bool(k[pygame.K_RIGHTBRACKET])
        self.شرطة_مائلة   = bool(k[pygame.K_BACKSLASH])

    def __repr__(self):
        pressed = [name for name, val in vars(self).items() if val is True]
        return f"كيبورد(مضغوط={pressed})"
