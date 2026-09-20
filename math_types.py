class Vector2:
    def __init__(self,x,y):
        self.x=x
        self.y=y
        self.z=0.0

    def __repr__(self):
        return f"متجه2({self.x}, {self.y})"
        
    def __eq__(self, other):
        if isinstance(other, Vector2):
            return self.x == other.x and self.y == other.y
        return False

    def __add__(self, other):
        if isinstance(other, Vector2):
            return Vector2(self.x + other.x, self.y + other.y)
        return Vector2(self.x + other, self.y + other)

    def __sub__(self, other):
        if isinstance(other, Vector2):
            return Vector2(self.x - other.x, self.y - other.y)
        return Vector2(self.x - other, self.y - other)

    def __mul__(self, other):
        if isinstance(other, Vector2):
            return Vector2(self.x * other.x, self.y * other.y)
        return Vector2(self.x * other, self.y * other)

    def __truediv__(self, other):
        if isinstance(other, Vector2):
            return Vector2(self.x / other.x, self.y / other.y)
        return Vector2(self.x / other, self.y / other)

Vector2.الأمام = Vector2(0, -1)
Vector2.اليمين = Vector2(1, 0)

class Vector3:
    def __init__(self,x,y,z):
        self.x=x
        self.y=y
        self.z=z

    def __repr__(self):
        return f"متجه3({self.x}, {self.y}, {self.z})"
        
    def __eq__(self, other):
        if isinstance(other, Vector3):
            return self.x == other.x and self.y == other.y and self.z == other.z
        return False

    def __add__(self, other):
        if isinstance(other, Vector3):
            return Vector3(self.x + other.x, self.y + other.y, self.z + other.z)
        # إذا تم إضافة رقم عادي، نجمع مع المحور Z لأنه الأهم في تدوير 2D (ويمكن إضافة لباقي المحاور)
        return Vector3(self.x + other, self.y + other, self.z + other)

    def __sub__(self, other):
        if isinstance(other, Vector3):
            return Vector3(self.x - other.x, self.y - other.y, self.z - other.z)
        return Vector3(self.x - other, self.y - other, self.z - other)

    def __mul__(self, other):
        if isinstance(other, Vector3):
            return Vector3(self.x * other.x, self.y * other.y, self.z * other.z)
        return Vector3(self.x * other, self.y * other, self.z * other)

    def __truediv__(self, other):
        if isinstance(other, Vector3):
            return Vector3(self.x / other.x, self.y / other.y, self.z / other.z)
        return Vector3(self.x / other, self.y / other, self.z / other)

Vector3.الأمام = Vector3(0, 0, -1)
Vector3.اليمين = Vector3(1, 0, 0)

class TimeInfo:
    def __init__(self):
        self._delta = 0.0
        self._fixed_delta = 0.016
        
    def دلتا(self):
        return self._delta
        
    def دلتا_مصلح(self):
        return self._fixed_delta

class Color:
    def __init__(self, r, g, b):
        self.r = r
        self.g = g
        self.b = b

    def __repr__(self):
        return f"لون({self.r}, {self.g}, {self.b})"
        
    def __eq__(self, other):
        if isinstance(other, Color):
            return self.r == other.r and self.g == other.g and self.b == other.b
        return False