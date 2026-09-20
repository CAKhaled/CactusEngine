"""
mouse.py
=========
كائن الماوس — يُستخدَم في لغة .kh للوصول إلى حالة الماوس.

الخصائص المتاحة في كود .kh:
  ماوس.x            → موقع X بالبكسل (float)
  ماوس.y            → موقع Y بالبكسل (float)
  ماوس.scroll       → عجلة التمرير (float، تُعاد للصفر كل إطار)
  ماوس.ضغط_يسار    → زر الماوس الأيسر مضغوط؟ (True/False)
  ماوس.ضغط_يمين    → زر الماوس الأيمن مضغوط؟ (True/False)
"""


import pygame

class Mouse:

    def __init__(self):

        # موقع المؤشر بالبكسل (مطلق)
        self.أفقي = 0.0
        self.عمودي = 0.0

        # اسماء بديلة بدون همزة (للمرونة)
        self.افقي = 0.0

        # الحركة النسبية لهذا الإطار (تُعاد للصفر كل إطار)
        self.حركة_أفقية = 0.0   # delta X × حساسية
        self.حركة_عمودية = 0.0   # delta Y × حساسية

        # مضاعف الحساسية — يمكن تغييره من كود .kh
        self.حساسية = 0.3

        # عجلة التمرير — تُضبط كل حدث، وتُعاد للصفر كل إطار تلقائياً
        self.scroll = 0.0

        # أزرار الماوس
        self.ضغط_يسار = False
        self.ضغط_يمين = False
        self._معلق = False

    @property
    def معلق(self):
        return 1 if self._معلق else 0

    @معلق.setter
    def معلق(self, value):
        val = bool(value)
        self._معلق = val
        try:
            pygame.event.set_grab(val)
            pygame.mouse.set_visible(not val)
        except:
            pass

    def __repr__(self):
        return (
            f"ماوس("
            f"أفقي={self.أفقي:.1f}, عمودي={self.عمودي:.1f}, "
            f"حركة_أفقية={self.حركة_أفقية:.3f}, حركة_عمودية={self.حركة_عمودية:.3f}, "
            f"scroll={self.scroll:.1f}, "
            f"يسار={self.ضغط_يسار}, يمين={self.ضغط_يمين})"
        )
