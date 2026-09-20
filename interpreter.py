from graphics import GraphicsEngine, CubeMapSky
from graphics import Cube
from math_types import Vector2, Vector3, Color
from textures import load_texture
import random
import time
import math

class KhMath:
    def __init__(self, time_obj):
        self._time = time_obj
        
    def lerp(self, a, b, t):
        if not isinstance(a, (int, float)) or not isinstance(b, (int, float)):
            raise Exception("رياضيات.lerp: القيم يجب أن تكون أرقام")
        t = max(0.0, min(1.0, float(t)))
        return a + (b - a) * t

    def sin(self, x):
        if not isinstance(x, (int, float)):
            raise Exception("رياضيات.sin: القيم يجب أن تكون أرقام")
        return math.sin(x)

    def cos(self, x):
        if not isinstance(x, (int, float)):
            raise Exception("رياضيات.cos: القيم يجب أن تكون أرقام")
        return math.cos(x)

    def abs(self, x):
        if not isinstance(x, (int, float)):
            raise Exception("رياضيات.abs: القيم يجب أن تكون أرقام")
        return abs(x)

    def log(self, x, base=math.e):
        if not isinstance(x, (int, float)):
            raise Exception("رياضيات.log: القيم يجب أن تكون أرقام")
        if x <= 0:
            raise Exception("رياضيات.log: القيمة يجب أن تكون أكبر من الصفر")
        return math.log(x, base)

    def pow(self, x, y):
        if not isinstance(x, (int, float)) or not isinstance(y, (int, float)):
            raise Exception("رياضيات.pow: القيم يجب أن تكون أرقام")
        return math.pow(x, y)

    def حركة_سلسة(self, current, target, duration):
        if not isinstance(current, (int, float)) or not isinstance(target, (int, float)) or not isinstance(duration, (int, float)):
            raise Exception("رياضيات.حركة_سلسة: القيم يجب أن تكون أرقام")
        dt = self._time.دلتا()
        if duration <= 0:
            return target
        t = dt / duration
        t = max(0.0, min(1.0, float(t)))
        return current + (target - current) * t

class BreakLoop(Exception):
    pass

class ReturnException(Exception):
    def __init__(self, value):
        self.value = value

class KhObject:
    def __init__(self, class_name, interpreter):
        self._class_name = class_name
        self._interpreter = interpreter
        self.خصائص = {}
        self.دوال = {}
    
    def __getattr__(self, name):
        if name in self.خصائص:
            return self.خصائص[name]
        if name in self.دوال:
            def bound_method(*args):
                old_vars = self._interpreter.variables.copy()
                
                func = self.دوال[name]
                # Filter out 'هذا' from expected args so user can optionally include it in def
                expected_args = [a for a in func["args"] if a != "هذا"]
                
                for i, arg_name in enumerate(expected_args):
                    if i < len(args):
                        self._interpreter.variables[arg_name] = args[i]
                    elif arg_name in self._interpreter.variables:
                        del self._interpreter.variables[arg_name]
                        
                self._interpreter.variables['هذا'] = self
                
                ret_val = None
                try:
                    self._interpreter.execute_blocks(func["body"])
                except ReturnException as e:
                    ret_val = e.value
                finally:
                    self._interpreter.variables = old_vars
                    
                return ret_val
            return bound_method
        raise AttributeError(f"الخاصية أو الدالة '{name}' غير موجودة في الكائن")

    def __setattr__(self, name, value):
        if name in ("_class_name", "_interpreter", "خصائص", "دوال"):
            super().__setattr__(name, value)
        else:
            self.خصائص[name] = value

class Interpreter:
    def __init__(self):
        self.variables = {}
        self.functions = {}
        self.classes = {}
        self.graphics = GraphicsEngine()
        self.has_window = False
        self.variables['محرك'] = self.graphics

        # تعريف 'ماوس' كمتغير جاهز مسبقاً — يشير لكائن الماوس في المحرك
        self.variables['ماوس'] = self.graphics.mouse

        # تعريف 'كيبورد' كمتغير جاهز مسبقاً — يشير لكائن لوحة المفاتيح
        self.variables['كيبورد'] = self.graphics.keyboard

        # تعريف الكاميرا لتسهيل التحكم فيها
        self.variables['الكاميرا'] = self.graphics.camera
        
        # تعريف الوقت
        self.variables['وقت'] = self.graphics.time

        # تعريف متجه3 للوصول إلى خصائصه (مثل متجه3.الأمام)
        self.variables['متجه3'] = Vector3
        
        # تعريف متجه2
        self.variables['متجه2'] = Vector2
        
        # دالة الرياضيات
        self.variables['رياضيات'] = KhMath(self.graphics.time)
        
        # كلمة فارغ
        self.variables['فارغ'] = None

    def _split_args(self, text):
        args = []
        current = []
        depth_paren = 0
        depth_bracket = 0
        depth_brace = 0
        in_string = False
        string_char = ''
        
        for char in text:
            if in_string:
                current.append(char)
                if char == string_char:
                    in_string = False
            else:
                if char in ('"', "'"):
                    in_string = True
                    string_char = char
                    current.append(char)
                elif char == '(':
                    depth_paren += 1
                elif char == ')':
                    depth_paren -= 1
                elif char == '[':
                    depth_bracket += 1
                elif char == ']':
                    depth_bracket -= 1
                elif char == '{':
                    depth_brace += 1
                elif char == '}':
                    depth_brace -= 1
                elif char == ',' and depth_paren == 0 and depth_bracket == 0 and depth_brace == 0:
                    args.append("".join(current).strip())
                    current = []
                    continue
                
                if not (char in ('"', "'") and in_string): # Only append if it wasn't already appended
                    current.append(char)
        
        if current:
            args.append("".join(current).strip())
        return [a for a in args if a]

    def _split_expr(self, text):
        tokens = []
        current = ""
        in_string = False
        string_char = ""
        depth_paren = 0
        depth_bracket = 0
        depth_brace = 0
        
        i = 0
        while i < len(text):
            char = text[i]
            
            if in_string:
                current += char
                if char == string_char:
                    in_string = False
                    if depth_paren == 0 and depth_bracket == 0 and depth_brace == 0:
                        tokens.append(current)
                        current = ""
            else:
                if char in ('"', "'"):
                    if depth_paren == 0 and depth_bracket == 0 and depth_brace == 0:
                        if current.strip():
                            tokens.append(current.strip())
                        current = char
                    else:
                        current += char
                    in_string = True
                    string_char = char
                elif char == '(':
                    depth_paren += 1
                    current += char
                elif char == ')':
                    depth_paren -= 1
                    current += char
                elif char == '[':
                    depth_bracket += 1
                    current += char
                elif char == ']':
                    depth_bracket -= 1
                    current += char
                elif char == '{':
                    depth_brace += 1
                    current += char
                elif char == '}':
                    depth_brace -= 1
                    current += char
                elif depth_paren == 0 and depth_bracket == 0 and depth_brace == 0:
                    if char in ('+', '*', '/', '-'):
                        if char == '-':
                            if not tokens and not current.strip():
                                current += char
                                i += 1
                                continue
                            if tokens and tokens[-1] in ('+', '-', '*', '/', '==', '!=', '>', '<', '>=', '<=') and not current.strip():
                                current += char
                                i += 1
                                continue
                        
                        if current.strip():
                            tokens.append(current.strip())
                        tokens.append(char)
                        current = ""
                    elif char.isspace():
                        if current.strip():
                            tokens.append(current.strip())
                            current = ""
                    else:
                        current += char
                else:
                    current += char
            i += 1
            
        if current.strip():
            tokens.append(current.strip())
            
        return tokens

    def _get_obj_and_key(self, path):
        path = path.strip()
        
        depth_paren = 0
        depth_bracket = 0
        depth_brace = 0
        in_string = False
        string_char = ''
        
        first_accessor_idx = -1
        
        i = 0
        while i < len(path):
            char = path[i]
            if in_string:
                if char == string_char:
                    in_string = False
            else:
                if char in ('"', "'"):
                    in_string = True
                    string_char = char
                elif char == '(': depth_paren += 1
                elif char == ')': depth_paren -= 1
                elif char == '{': depth_brace += 1
                elif char == '}': depth_brace -= 1
                elif char == '[':
                    if depth_paren == 0 and depth_bracket == 0 and depth_brace == 0:
                        first_accessor_idx = i
                        break
                    depth_bracket += 1
                elif char == ']':
                    depth_bracket -= 1
                elif char == '.':
                    if depth_paren == 0 and depth_bracket == 0 and depth_brace == 0:
                        first_accessor_idx = i
                        break
            i += 1
            
        if first_accessor_idx == -1:
            return self.variables, path, False
            
        base_expr = path[:first_accessor_idx].strip()
        if not base_expr:
            raise Exception(f"تعبير غير صالح: {path}")
            
        try:
            obj = self.evaluate(base_expr)
        except Exception as e:
            if base_expr in self.variables:
                obj = self.variables[base_expr]
            else:
                raise Exception(f"المتغير أو التعبير '{base_expr}' غير موجود أو به خطأ: {e}")
        
        prev_obj = obj
        last_key = None
        is_index = False
        
        i = first_accessor_idx
        while i < len(path):
            if path[i] == '.':
                i += 1
                prop_name = ""
                while i < len(path) and path[i] not in ('.', '['):
                    prop_name += path[i]
                    i += 1
                
                prev_obj = obj
                last_key = prop_name.strip()
                is_index = False
                
                if i < len(path):
                    if prev_obj is None:
                        raise Exception(f"لا يمكن الوصول للخاصية '{last_key}' لأن المتغير فارغ!")
                    if isinstance(obj, list) and last_key == "طول":
                        obj = len(obj)
                    else:
                        if last_key == "الصورة" and not hasattr(prev_obj, "الصورة"): last_key = "filepath"
                        if not hasattr(prev_obj, last_key) and last_key == "filepath": setattr(prev_obj, "filepath", "")
                        
                        if last_key == "الخامة":
                            from graphics import Material
                            curr_val = getattr(prev_obj, last_key, None)
                            if not isinstance(curr_val, Material):
                                new_mat = Material()
                                if curr_val != "":
                                    new_mat.base = curr_val
                                setattr(prev_obj, last_key, new_mat)
                                
                        obj = getattr(prev_obj, last_key)
                    
            elif path[i] == '[':
                depth = 1
                start_idx = i + 1
                i += 1
                while i < len(path) and depth > 0:
                    if path[i] == '[': depth += 1
                    elif path[i] == ']': depth -= 1
                    i += 1
                
                idx_expr = path[start_idx:i-1]
                idx_val = self.evaluate(idx_expr)
                
                prev_obj = obj
                if isinstance(prev_obj, list):
                    last_key = int(idx_val)
                else:
                    last_key = idx_val
                is_index = True
                
                if i < len(path):
                    obj = prev_obj[last_key]
            else:
                i += 1
                
        return prev_obj, last_key, is_index

    def _find_op_outside_parens(self, text, ops):
        depth_paren = 0
        depth_bracket = 0
        depth_brace = 0
        in_string = False
        string_char = ''
        
        i = 0
        while i < len(text):
            char = text[i]
            if in_string:
                if char == string_char:
                    in_string = False
            else:
                if char in ('"', "'"):
                    in_string = True
                    string_char = char
                elif char == '(': depth_paren += 1
                elif char == ')': depth_paren -= 1
                elif char == '[': depth_bracket += 1
                elif char == ']': depth_bracket -= 1
                elif char == '{': depth_brace += 1
                elif char == '}': depth_brace -= 1
                elif depth_paren == 0 and depth_bracket == 0 and depth_brace == 0:
                    for op in ops:
                        if text[i:i+len(op)] == op:
                            return i
            i += 1
        return -1

    def get_value(self, value):
        value = value.strip()

        # نص مقتبس بعلامات اقتباس مزدوجة أو مفردة
        if (value.startswith('"') and value.endswith('"')) or \
           (value.startswith("'") and value.endswith("'")):
            return value[1:-1]
            
        if value == "مفعل":
            return True
        if value == "مقفل":
            return False

        # عدد صحيح
        if value.lstrip("-").isdigit():
            return int(value)

        # عدد عشري
        try:
            if "." in value:
                return float(value)
        except ValueError:
            pass

        if value.startswith("-"):
            rest = value[1:].strip()
            if rest:
                try:
                    # If this succeeds without an error, return its negative
                    return -self.get_value(rest)
                except Exception:
                    pass

        # الوصول إلى خصائص الكائن أو عناصر المصفوفة
        if "." in value or "[" in value:
            prev_obj, last_key, is_index = self._get_obj_and_key(value)
            if is_index:
                return prev_obj[last_key]
            elif prev_obj is self.variables:
                return prev_obj[last_key]
            else:
                if prev_obj is None:
                    raise Exception(f"لا يمكن الوصول للخاصية '{last_key}' لأن المتغير فارغ!")
                if isinstance(prev_obj, list) and last_key == "طول":
                    return len(prev_obj)
                if last_key == "الصورة" and not hasattr(prev_obj, "الصورة"): last_key = "filepath"
                if not hasattr(prev_obj, last_key) and last_key == "filepath": setattr(prev_obj, "filepath", "")
                if not hasattr(prev_obj, last_key):
                    raise Exception(f"الخاصية '{last_key}' غير موجودة")
                return getattr(prev_obj, last_key)

        if value in self.variables:
            return self.variables[value]

        raise Exception(f"المتغير '{value}' غير موجود")

    def evaluate(self, expr):
        expr = expr.strip()
        
        if not expr:
            raise Exception("تعبير غير صالح (تأكد من عدم وجود أخطاء إملائية مثل كتابة == مرتين)")

        # أولاً، إذا كان التعبير بالكامل عبارة عن نص مقتبس، نقوم بإرجاعه مباشرة
        # لتجنب تقسيمه بالخطأ عبر المعاملات الشرطية أو المسافات
        if (expr.startswith('"') and expr.endswith('"')) or \
           (expr.startswith("'") and expr.endswith("'")):
            # التأكد من أنه ليس أكثر من نص واحد (مثل "أ" + "ب")
            temp_tokens = self._split_expr(expr)
            if len(temp_tokens) == 1:
                return expr[1:-1]

        if expr.startswith("[") and expr.endswith("]"):
            inner = expr[1:-1].strip()
            if not inner:
                return []
            return [self.evaluate(part) for part in self._split_args(inner)]

        if expr.startswith("{") and expr.endswith("}"):
            inner = expr[1:-1].strip()
            if not inner:
                return {}
            parts = self._split_args(inner)
            d = {}
            if any(":" in p for p in parts):
                for p in parts:
                    if ":" in p:
                        k, v = p.split(":", 1)
                        d[self.evaluate(k)] = self.evaluate(v)
            else:
                for i in range(0, len(parts), 2):
                    if i + 1 < len(parts):
                        k = self.evaluate(parts[i])
                        v = self.evaluate(parts[i+1])
                        d[k] = v
            return d



        # التحقق من وجود معاملات شرطية لتقييمها
        for op in ["==", "!=", ">=", "<=", ">", "<", " او ", " أو ", " و "]:
            if self._find_op_outside_parens(expr, [op]) != -1:
                return self.evaluate_condition(expr)

        if expr == "صنع_واجهة()":
            return self.graphics.create_canvas()

        if expr == "صنع_مكعب()":
            return self.graphics.create_cube(Vector3(0, 0, 0), Vector3(0, 0, 0), Color(1, 1, 1))

        if expr == "صنع_كرة()":
            return self.graphics.create_sphere(Vector3(0, 0, 0), Vector3(0, 0, 0), Color(1, 1, 1))

        if expr == "صنع_سطح()":
            return self.graphics.create_plane(Vector3(0, 0, 0), Vector3(0, 0, 0), Color(1, 1, 1))

        if expr.startswith("صنع_تضاريس(") and expr.endswith(")"):
            filename = expr[len("صنع_تضاريس("):-1].strip()
            if filename.startswith('"') and filename.endswith('"') or filename.startswith("'") and filename.endswith("'"):
                filename = filename[1:-1]
            return self.graphics.create_terrain(filename)

        if expr == "صنع_هرم()":
            return self.graphics.create_pyramid(Vector3(0, 0, 0), Vector3(0, 0, 0), Color(1, 1, 1))

        if expr == "صنع_اسطوانة()":
            return self.graphics.create_cylinder(Vector3(0, 0, 0), Vector3(0, 0, 0), Color(1, 1, 1))

        if expr == "صنع_كبسولة()":
            return self.graphics.create_capsule(Vector3(0, 0, 0), Vector3(0, 0, 0), Color(1, 1, 1))

        if expr.startswith("صنع_مخصص(") and expr.endswith(")"):
            filename = expr[len("صنع_مخصص("):-1].strip()
            if filename.startswith('"') and filename.endswith('"') or filename.startswith("'") and filename.endswith("'"):
                filename = filename[1:-1]
            return self.graphics.create_custom(filename)

        lower_expr = expr.lower()
        if lower_expr.startswith("صنع_fbx(") and expr.endswith(")"):
            filename = expr[len("صنع_fbx("):-1].strip()
            if filename.startswith('"') and filename.endswith('"') or filename.startswith("'") and filename.endswith("'"):
                filename = filename[1:-1]
            return self.graphics.create_fbx(filename)

        if expr == "صنع_مربع2D()":
            return self.graphics.create_square_2d()

        if expr == "صنع_دائرة2D()":
            return self.graphics.create_circle_2d()

        if expr == "صنع_مثلث2D()":
            return self.graphics.create_triangle_2d()

        if expr.startswith("صنع_مخصص2D(") and expr.endswith(")"):
            filename = expr[len("صنع_مخصص2D("):-1].strip()
            if filename.startswith('"') and filename.endswith('"') or filename.startswith("'") and filename.endswith("'"):
                filename = filename[1:-1]
            return self.graphics.create_custom_2d(filename)

        if expr.startswith("نافذة(") and expr.endswith(")"):
            self.has_window = True
            import os
            os.environ["KH_USER_WINDOW"] = "1"
            content = expr[6:-1]
            values = [v.strip() for v in self._split_args(content)]
            title = values[0].strip('"')
            width = int(values[1])
            height = int(values[2])
            self.graphics.create_window(title, width, height)
            return None

        if expr == "صنع_ضوء()":
            return self.graphics.create_light()
            
        if expr.startswith("حجم(") and expr.endswith(")"):
            content = expr[4:-1].strip()
            val = self.evaluate(content)
            if isinstance(val, (list, str)):
                return int(len(val))
            raise Exception(f"دالة 'حجم' تتوقع مصفوفة أو نص، تم إعطاء: {type(val).__name__}")
            
        if expr.startswith("رؤية_صدام(") and expr.endswith(")"):
            content = expr[10:-1].strip()
            obj = self.evaluate(content)
            if obj is not None:
                setattr(obj, 'رؤية_صدام', True)
                if hasattr(obj, 'components'):
                    for comp in obj.components.values():
                        setattr(comp, 'رؤية_صدام', True)
            return None

        if expr.startswith("تحميل_خامة(") and expr.endswith(")"):
            filename = expr[len("تحميل_خامة("):-1].strip()
            if filename.startswith('"') and filename.endswith('"'):
                filename = filename[1:-1]
            return load_texture(filename)

        if expr.startswith("تحميل_صورة(") and expr.endswith(")"):
            filename = expr[len("تحميل_صورة("):-1].strip()
            if filename.startswith('"') and filename.endswith('"'):
                filename = filename[1:-1]
            elif filename.startswith("'") and filename.endswith("'"):
                filename = filename[1:-1]
            return filename  # يرجع المسار مباشرة للأشكال 2D

        if expr.startswith("صنع_صوت(") and expr.endswith(")"):
            filename = expr[len("صنع_صوت("):-1].strip()
            if (filename.startswith('"') and filename.endswith('"')) or (filename.startswith("'") and filename.endswith("'")):
                filename = filename[1:-1]
            return self.graphics.create_sound(filename)

        if expr.startswith("مؤقت(") and expr.endswith(")"):
            content = expr[len("مؤقت("):-1].strip()
            seconds = float(self.evaluate(content))
            
            if getattr(self, "has_window", False):
                import pygame
                start_ticks = pygame.time.get_ticks()
                target_ticks = seconds * 1000
                clock = pygame.time.Clock()
                while (pygame.time.get_ticks() - start_ticks) < target_ticks:
                    pygame.event.pump()
                    if hasattr(self.graphics, "render_scene"):
                        self.graphics.render_scene()
                        pygame.display.flip()
                    clock.tick(60)
            else:
                import threading
                threading.Event().wait(seconds)
            return None

        if expr.startswith("عشوائي(") and expr.endswith(")"):
            content = expr[len("عشوائي("):-1].strip()
            values = [v.strip() for v in self._split_args(content)]
            if len(values) != 2:
                raise Exception("عشوائي تحتاج إلى قيمتين: الحد الأدنى والحد الأعلى")
            min_val = float(self.evaluate(values[0]))
            max_val = float(self.evaluate(values[1]))
            return random.uniform(min_val, max_val)

        if expr.startswith("نوع(") and expr.endswith(")"):
            content = expr[4:-1].strip()
            val = self.evaluate(content)
            
            if isinstance(val, bool):
                return "منطقي"
            elif isinstance(val, int):
                return "رقم صحيح"
            elif isinstance(val, float):
                return "رقم عشري"
            elif isinstance(val, str):
                return "نص"
            elif isinstance(val, list):
                return "مصفوفة"
            elif isinstance(val, dict):
                return "قاموس"
            else:
                return type(val).__name__

        if expr.startswith("صنع_سماء_cubemap(") or expr.startswith("صنع_سماء_مكعبة("):
            start_len = len("صنع_سماء_cubemap(") if expr.startswith("صنع_سماء_cubemap(") else len("صنع_سماء_مكعبة(")
            content = expr[start_len:-1].strip()
            values = [v.strip() for v in self._split_args(content)]
            if len(values) != 6:
                raise Exception("صنع_سماء_مكعبة تحتاج إلى 6 مسارات للصور")
            
            paths = []
            for v in values:
                p = self.evaluate(v)
                if isinstance(p, str): paths.append(p)
                else: raise Exception("يجب أن تكون مسارات الصور نصوصاً")
                
            cubemap = self.graphics.صنع_سماء_cubemap(*paths)
            self.graphics.set_sky(cubemap)
            return cubemap

        if expr.startswith("صنع_سماء(") and expr.endswith(")"):
            arg = expr[len("صنع_سماء("):-1].strip()
            
            # If it's a string, it's a texture path
            if arg.startswith('"') and arg.endswith('"'):
                filename = arg[1:-1]
                tex = load_texture(filename)
                self.graphics.set_sky(tex)
                return tex
            else:
                val = self.evaluate(arg)
                if isinstance(val, Color) or isinstance(val, CubeMapSky):
                    self.graphics.set_sky(val)
                return val

        if expr.startswith("لون(") and expr.endswith(")"):
            content = expr[4:-1]
            values = [v.strip() for v in self._split_args(content)]

            if len(values) != 3:
                raise Exception("اللون يحتاج إلى 3 قيم (R, G, B)")
            r = float(self.evaluate(values[0]))
            g = float(self.evaluate(values[1]))
            b = float(self.evaluate(values[2]))
            
            # إذا كانت القيم من 0 إلى 255 نحولها إلى 0-1
            if r > 1 or g > 1 or b > 1:
                r /= 255.0
                g /= 255.0
                b /= 255.0

            return Color(r, g, b)

        # دعم استدعاء الدوال الخاصة بالكائنات: obj.method(arg1, arg2) أو دوال المستخدم
        if "(" in expr and expr.endswith(")"):
            # التأكد من أنه ليس تعبيراً رياضياً ينتهي بقوس أو يحتوي أكثر من استدعاء
            _temp_tokens = self._split_expr(expr)
            if len(_temp_tokens) == 1:
                method_idx = expr.find("(")
                call_part = expr[:method_idx]
                if "." in call_part:
                    obj_name, method_name = call_part.rsplit(".", 1)
                    obj = self.evaluate(obj_name.strip())
                    args_content = expr[method_idx+1:-1].strip()
                    if args_content:
                        args = [self.evaluate(a.strip()) for a in self._split_args(args_content)]
                    else:
                        args = []
                    method_name = method_name.strip()
                    
                    if isinstance(obj, list):
                        if method_name == "ضف":
                            obj.append(*args)
                            return None
                        elif method_name == "احذف":
                            obj.remove(*args)
                            return None
                        elif method_name == "احذف_فهرس":
                            return obj.pop(*args)
                    
                    method = getattr(obj, method_name)
                    return method(*args)
                else:
                    func_name = call_part.strip()
                    if func_name in self.functions:
                        func = self.functions[func_name]
                        args_content = expr[method_idx+1:-1].strip()
                        if args_content:
                            passed_args = [self.evaluate(a.strip()) for a in self._split_args(args_content)]
                        else:
                            passed_args = []
                        
                        old_vars = {}
                        for i, arg_name in enumerate(func["args"]):
                            if arg_name in self.variables:
                                old_vars[arg_name] = self.variables[arg_name]
                            if i < len(passed_args):
                                self.variables[arg_name] = passed_args[i]
                                
                        try:
                            self.execute_blocks(func["body"])
                            ret_val = None
                        except ReturnException as e:
                            ret_val = e.value
                        
                        for arg_name in func["args"]:
                            if arg_name in old_vars:
                                self.variables[arg_name] = old_vars[arg_name]
                            else:
                                if arg_name in self.variables:
                                    del self.variables[arg_name]
                        
                        return ret_val
                    elif func_name in getattr(self, "classes", {}):
                        cls_def = self.classes[func_name]
                        obj = KhObject(func_name, self)
                        for block in cls_def["body"]:
                            if block["type"] == "block" and block["header"].startswith("دالة "):
                                signature = block["header"][4:-1].strip()
                                if "(" in signature and signature.endswith(")"):
                                    name_part, args_part = signature.split("(", 1)
                                    m_name = name_part.strip()
                                    args_str = args_part[:-1].strip()
                                    m_args = [a.strip() for a in args_str.split(",")] if args_str else []
                                    obj.دوال[m_name] = {
                                        "args": m_args,
                                        "body": block["body"]
                                    }
                        if "بناء" in obj.دوال or "البناء" in obj.دوال:
                            constructor_name = "بناء" if "بناء" in obj.دوال else "البناء"
                            args_content = expr[method_idx+1:-1].strip()
                            if args_content:
                                passed_args = [self.evaluate(a.strip()) for a in self._split_args(args_content)]
                            else:
                                passed_args = []
                            getattr(obj, constructor_name)(*passed_args)
                        return obj

        # =========================
        # متجه2
        # =========================
        if expr.startswith("متجه2(") and expr.endswith(")"):
            content = expr[6:-1]
            values = [v.strip() for v in self._split_args(content)]

            if len(values) != 2:
                raise Exception("متجه2 يحتاج قيمتين")

            x = self.evaluate(values[0])
            y = self.evaluate(values[1])
            return Vector2(x, y)

        # =========================
        # متجه3
        # =========================
        if expr.startswith("متجه3(") and expr.endswith(")"):
            content = expr[6:-1]
            values = [v.strip() for v in self._split_args(content)]

            if len(values) != 3:
                raise Exception("متجه3 يحتاج ثلاث قيم")

            x = self.evaluate(values[0])
            y = self.evaluate(values[1])
            z = self.evaluate(values[2])
            return Vector3(x, y, z)

        tokens = self._split_expr(expr)

        if len(tokens) == 1:
            t = tokens[0].strip()
            if t.startswith("(") and t.endswith(")"):
                depth = 0
                is_enclosing = True
                for j, char in enumerate(t):
                    if char == '(': depth += 1
                    elif char == ')': depth -= 1
                    if depth == 0 and j < len(t) - 1:
                        is_enclosing = False
                        break
                if is_enclosing:
                    return self.evaluate(t[1:-1])
            return self.get_value(t)

        if len(tokens) >= 3 and len(tokens) % 2 != 0:
            result = self.evaluate(tokens[0])
            for i in range(1, len(tokens), 2):
                op = tokens[i]
                next_val = self.evaluate(tokens[i+1])

                if op == "+":
                    if isinstance(result, str) or isinstance(next_val, str):
                        def to_str(v):
                            if v is True: return "مفعل"
                            if v is False: return "مقفل"
                            if isinstance(v, float) and v.is_integer(): return str(int(v))
                            return str(v)
                        result = to_str(result) + to_str(next_val)
                    else:
                        result = result + next_val
                else:
                    def to_num(v):
                        if isinstance(v, str):
                            try:
                                return float(v)
                            except ValueError:
                                return v
                        return v
                    
                    r_val = to_num(result)
                    n_val = to_num(next_val)
                    
                    if op == "-":
                        result = r_val - n_val
                    elif op == "*":
                        result = r_val * n_val
                    elif op == "/":
                        result = r_val / n_val
                    else:
                        raise Exception(f"تعبير غير صالح: {expr}")
            return result

        raise Exception(f"تعبير غير صالح: {expr}")


    # ─────────────────────────────────────────────
    # تنفيذ سطر واحد — مشترك بين setup وكل_فريم
    # ─────────────────────────────────────────────

    def execute_line(self, line, line_number=0):
        """ينفّذ سطراً واحداً من كود .kh"""

        line = line.strip()

        if not line or line.startswith("#"):
            return

        # تعريف متغير
        if line.startswith("ابغا "):
            rest = line[5:]
            if "=" not in rest:
                self.variables[rest.strip()] = 0
            else:
                name, expr = rest.split("=", 1)
                self.variables[name.strip()] = self.evaluate(expr.strip())

        # طباعة
        elif line.startswith("اطبع "):
            expr = line[5:].strip()
            val = self.evaluate(expr)
            try:
                import sys
                if sys.stdout is not None:
                    if isinstance(val, bool):
                        print("مفعل" if val else "مقفل", flush=True)
                    else:
                        print(val, flush=True)
            except Exception:
                pass
            
        # إرجاع قيمة
        elif line.startswith("ارجع "):
            expr = line[5:].strip()
            raise ReturnException(self.evaluate(expr))

        elif line.startswith("صنع_") or line.startswith("تحميل_") or ("=" not in line and "(" in line and line.endswith(")")):
            self.evaluate(line)

        # ── += و -= ──────────────────────────────────────
        elif "+=" in line or "-=" in line:
            op = "+=" if "+=" in line else "-="
            left, right = line.split(op, 1)
            left  = left.strip()
            right = right.strip()

            delta = self.evaluate(right)

            if "." in left or "[" in left:
                prev_obj, last_key, is_index = self._get_obj_and_key(left)
                if is_index:
                    current = prev_obj[last_key]
                    prev_obj[last_key] = current + delta if op == "+=" else current - delta
                elif prev_obj is self.variables:
                    current = prev_obj[last_key]
                    prev_obj[last_key] = current + delta if op == "+=" else current - delta
                else:
                    if last_key == "الصورة" and not hasattr(prev_obj, "الصورة"): last_key = "filepath"
                    if not hasattr(prev_obj, last_key) and last_key == "filepath": setattr(prev_obj, "filepath", "")
                    current = getattr(prev_obj, last_key)
                    setattr(prev_obj, last_key, current + delta if op == "+=" else current - delta)
            else:
                if left not in self.variables:
                    raise Exception(f"المتغير '{left}' غير موجود")
                current = self.variables[left]
                self.variables[left] = current + delta if op == "+=" else current - delta

        # ── تعيين متغير أو خاصية ────────
        elif "=" in line:
            left, right = line.split("=", 1)
            left  = left.strip()
            right = right.strip()
            
            val = self.evaluate(right)
            if "." in left or "[" in left:
                prev_obj, last_key, is_index = self._get_obj_and_key(left)
                if is_index:
                    prev_obj[last_key] = val
                elif prev_obj is self.variables:
                    prev_obj[last_key] = val
                else:
                    if last_key == "الصورة" and not hasattr(prev_obj, "الصورة"): last_key = "filepath"
                    setattr(prev_obj, last_key, val)
            else:
                self.variables[left] = val

        elif line.startswith("نافذة("):
            start = line.find("(")
            end   = line.rfind(")")
            args  = line[start+1:end]
            values = [x.strip() for x in self._split_args(args)]
            if len(values) != 3:
                raise Exception("نافذة تحتاج: عنوان، عرض، ارتفاع")
            title  = values[0].strip('"')
            width  = int(values[1])
            height = int(values[2])
            # Mark that user explicitly called نافذة() - IDE will show as external window
            import os
            os.environ["KH_USER_WINDOW"] = "1"
            self.graphics.create_window(title, width, height)
            self.has_window = True

        elif line == "توقف":
            raise BreakLoop()

        else:
            raise Exception(f"أمر غير معروف في السطر {line_number}: {line}")

    # ─────────────────────────────────────────────
    # تنفيذ كامل الكود (بالشجرة البرمجية الجديدة AST)
    # ─────────────────────────────────────────────

    def evaluate_condition(self, cond_str):
        cond_str = cond_str.strip()
        
        # إزالة الأقواس المحيطة بالتعبير بالكامل إن وجدت
        if cond_str.startswith("(") and cond_str.endswith(")"):
            depth = 0
            is_enclosing = True
            for j, char in enumerate(cond_str):
                if char == '(': depth += 1
                elif char == ')': depth -= 1
                if depth == 0 and j < len(cond_str) - 1:
                    is_enclosing = False
                    break
            if is_enclosing:
                return self.evaluate_condition(cond_str[1:-1])

        # العمليات المنطقية (OR و AND)
        or_idx = self._find_op_outside_parens(cond_str, [" أو ", " او "])
        if or_idx != -1:
            op_str = " أو " if cond_str[or_idx:or_idx+4] == " أو " else " او "
            left = cond_str[:or_idx]
            right = cond_str[or_idx+len(op_str):]
            return self.evaluate_condition(left) or self.evaluate_condition(right)
            
        and_idx = self._find_op_outside_parens(cond_str, [" و "])
        if and_idx != -1:
            left = cond_str[:and_idx]
            right = cond_str[and_idx+3:]
            return self.evaluate_condition(left) and self.evaluate_condition(right)

        for op in ["==", "!=", ">=", "<=", ">", "<"]:
            op_idx = self._find_op_outside_parens(cond_str, [op])
            if op_idx != -1:
                left = cond_str[:op_idx]
                right = cond_str[op_idx+len(op):]
                if op == "==":
                    return self.evaluate(left) == self.evaluate(right)
                elif op == "!=":
                    return self.evaluate(left) != self.evaluate(right)
                elif op == ">=":
                    return float(self.evaluate(left)) >= float(self.evaluate(right))
                elif op == "<=":
                    return float(self.evaluate(left)) <= float(self.evaluate(right))
                elif op == ">":
                    return float(self.evaluate(left)) > float(self.evaluate(right))
                elif op == "<":
                    return float(self.evaluate(left)) < float(self.evaluate(right))
        
        return bool(self.evaluate(cond_str))

    def _preprocess_lines(self, raw_lines):
        processed = []
        
        current_line_num = -1
        current_line_content = ""
        original_indent_str = ""
        
        for line_num, raw_line in raw_lines:
            stripped = raw_line.strip()
            
            if not stripped or stripped.startswith("#"):
                if current_line_content:
                    continue
                else:
                    processed.append((line_num, raw_line))
                    continue
                    
            clean_line = ""
            in_str_local = False
            str_char_local = ""
            for char in raw_line:
                if in_str_local:
                    clean_line += char
                    if char == str_char_local:
                        in_str_local = False
                else:
                    if char in ('"', "'"):
                        in_str_local = True
                        str_char_local = char
                        clean_line += char
                    elif char == '#':
                        break
                    else:
                        clean_line += char
                        
            clean_line = clean_line.rstrip()
            
            if not current_line_content:
                current_line_num = line_num
                indent_len = len(raw_line) - len(raw_line.lstrip())
                original_indent_str = raw_line[:indent_len]
                current_line_content = clean_line.lstrip()
            else:
                current_line_content += " " + clean_line.lstrip()
                
            depth_paren = 0
            depth_bracket = 0
            depth_brace = 0
            in_string = False
            string_char = ""
            for char in current_line_content:
                if in_string:
                    if char == string_char:
                        in_string = False
                else:
                    if char in ('"', "'"):
                        in_string = True
                        string_char = char
                    elif char == '(': depth_paren += 1
                    elif char == ')': depth_paren -= 1
                    elif char == '[': depth_bracket += 1
                    elif char == ']': depth_bracket -= 1
                    elif char == '{': depth_brace += 1
                    elif char == '}': depth_brace -= 1
            
            if depth_paren <= 0 and depth_bracket <= 0 and depth_brace <= 0:
                processed.append((current_line_num, original_indent_str + current_line_content))
                current_line_content = ""
                original_indent_str = ""
                
        if current_line_content:
            processed.append((current_line_num, original_indent_str + current_line_content))
            
        return processed

    def parse_blocks(self, raw_lines, current_indent=0):
        # raw_lines is now a list of (line_num, raw_line_str)
        blocks = []
        i = 0
        expected_indent = None
        
        while i < len(raw_lines):
            line_num, raw_line = raw_lines[i]
            line = raw_line.strip()
            
            if not line or line.startswith("#"):
                i += 1
                continue
                
            indent = len(raw_line) - len(raw_line.lstrip())
            
            if indent < current_indent:
                break
                
            if expected_indent is None:
                expected_indent = indent
            elif indent != expected_indent:
                raise Exception(f"خطأ في المسافات البادئة في السطر {line_num}: متوقع {expected_indent} مسافات ولكن وجد {indent}")
                
            if line.endswith(":"):
                block_lines = []
                j = i + 1
                while j < len(raw_lines):
                    next_line_num, next_raw = raw_lines[j]
                    next_line = next_raw.strip()
                    if not next_line or next_line.startswith("#"):
                        j += 1
                        continue
                    next_indent = len(next_raw) - len(next_raw.lstrip())
                    if next_indent > indent:
                        block_lines.append((next_line_num, next_raw))
                        j += 1
                    else:
                        break
                
                blocks.append({
                    "type": "block",
                    "header": line,
                    "line_number": line_num,
                    "body": self.parse_blocks(block_lines, indent + 1)
                })
                i = j
            else:
                blocks.append({
                    "type": "line",
                    "content": line,
                    "line_number": line_num
                })
                i += 1
        return blocks

    def execute_blocks(self, blocks):
        last_if_result = None
        for block in blocks:
            try:
                if block["type"] == "line":
                    if block["content"] != "تشغيل()":
                        self.execute_line(block["content"], block.get("line_number", 0))
                    last_if_result = None
                elif block["type"] == "block":
                    header = block["header"]
                    if header in ("كل_فريم:", "كل فريم:"):
                        def per_frame_callback():
                            self.execute_blocks(block["body"])
                        self.per_frame_callback = per_frame_callback
                        last_if_result = None
                    elif header.startswith("اذا ") or header.startswith("إذا "):
                        cond_str = header[4:-1].strip()
                        last_if_result = self.evaluate_condition(cond_str)
                        if last_if_result:
                            self.execute_blocks(block["body"])
                    elif header == "غير_ذلك:" or header == "غير ذلك:":
                        if last_if_result is False:
                            self.execute_blocks(block["body"])
                        last_if_result = None
                    elif header == "كرر:":
                        while True:
                            try:
                                # Feature: if the 'كرر:' block contains exactly one 'إذا' block, treat its condition as the loop condition
                                if len(block["body"]) == 1 and block["body"][0]["type"] == "block" and (block["body"][0]["header"].startswith("اذا ") or block["body"][0]["header"].startswith("إذا ")):
                                    cond_str = block["body"][0]["header"][4:-1].strip()
                                    if not self.evaluate_condition(cond_str):
                                        break
                                self.execute_blocks(block["body"])
                            except BreakLoop:
                                break
                    elif header.startswith("دالة "):
                        signature = header[4:-1].strip()
                        if "(" in signature and signature.endswith(")"):
                            name_part, args_part = signature.split("(", 1)
                            name = name_part.strip()
                            args_str = args_part[:-1].strip()
                            args = [a.strip() for a in args_str.split(",")] if args_str else []
                            self.functions[name] = {
                                "args": args,
                                "body": block["body"]
                            }
                        else:
                            raise Exception(f"تعريف دالة غير صالح: {header}")
                    elif header.startswith("كلاس ") or header.startswith("كائن "):
                        name = header[5:-1].strip() if header.startswith("كلاس ") else header[5:-1].strip()
                        if not hasattr(self, "classes"): self.classes = {}
                        self.classes[name] = {
                            "body": block["body"]
                        }
                    else:
                        raise Exception(f"مربع برمجي غير معروف: {header}")
            except Exception as e:
                if not getattr(e, "kh_line", None):
                    e.kh_line = block.get("line_number", 0)
                    e.kh_code = block.get("header") if block["type"] == "block" else block.get("content")
                raise e

    def execute(self, code):
        """
        يُحلِّل الكود ويبني شجرة الأوامر وينفذها.
        """
        self.per_frame_callback = None
        lines = code.splitlines()
        
        # توحيد المسافات البادئة (التابات إلى مسافات)
        enumerated_lines = [(i+1, line.replace("\t", "    ")) for i, line in enumerate(lines)]
        
        preprocessed_lines = self._preprocess_lines(enumerated_lines)
        
        blocks = self.parse_blocks(preprocessed_lines, 0)
        self.execute_blocks(blocks)
        
        # If the user didn't create a window, create a default one
        if not getattr(self, "has_window", False):
            self.graphics.create_window("FPS Camera", 910, 650)
            self.has_window = True
            
        # ── تشغيل تلقائي في نهاية الملف إذا تم إنشاء نافذة ──
        if getattr(self, "has_window", False):
            self.graphics.run(per_frame=self.per_frame_callback)


        if expr.startswith("تعيين_حجم_الخامة(") and expr.endswith(")"):
            args_str = expr[len("تعيين_حجم_الخامة("):-1].strip()
            args = self._split_args(args_str)
            if len(args) >= 3:
                obj_name = self.evaluate(args[0])
                if isinstance(obj_name, str): obj = self.variables.get(obj_name, None)
                else: obj = obj_name
                if obj and hasattr(obj, 'الخامة'):
                    if not isinstance(obj.الخامة, dict) and not hasattr(obj.الخامة, 'scale_x'):
                        from graphics import Material
                        obj.الخامة = Material()
                        
                    val_x = self.evaluate(args[1])
                    val_y = self.evaluate(args[2])
                    if isinstance(obj.الخامة, dict):
                        obj.الخامة['scale_x'] = val_x
                        obj.الخامة['scale_y'] = val_y
                    else:
                        obj.الخامة.scale_x = val_x
                        obj.الخامة.scale_y = val_y
            return None

        if expr.startswith("تعيين_معدنية_الخامة(") and expr.endswith(")"):
            args_str = expr[len("تعيين_معدنية_الخامة("):-1].strip()
            args = self._split_args(args_str)
            if len(args) >= 2:
                obj_name = self.evaluate(args[0])
                if isinstance(obj_name, str): obj = self.variables.get(obj_name, None)
                else: obj = obj_name
                if obj and hasattr(obj, 'الخامة'):
                    if not isinstance(obj.الخامة, dict) and not hasattr(obj.الخامة, 'metallic'):
                        from graphics import Material
                        obj.الخامة = Material()
                    val = self.evaluate(args[1])
                    if isinstance(obj.الخامة, dict):
                        obj.الخامة['metallic'] = val
                    else:
                        obj.الخامة.metallic = val
            return None

        if expr.startswith("تعيين_خشونة_الخامة(") and expr.endswith(")"):
            args_str = expr[len("تعيين_خشونة_الخامة("):-1].strip()
            args = self._split_args(args_str)
            if len(args) >= 2:
                obj_name = self.evaluate(args[0])
                if isinstance(obj_name, str): obj = self.variables.get(obj_name, None)
                else: obj = obj_name
                if obj and hasattr(obj, 'الخامة'):
                    if not isinstance(obj.الخامة, dict) and not hasattr(obj.الخامة, 'roughness'):
                        from graphics import Material
                        obj.الخامة = Material()
                    val = self.evaluate(args[1])
                    if isinstance(obj.الخامة, dict):
                        obj.الخامة['roughness'] = val
                    else:
                        obj.الخامة.roughness = val
            return None
