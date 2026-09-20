import sys
sys.path.append('.')
from interpreter import Interpreter

interp = Interpreter()
interp.execute('''
ابغا قائمة = [1, 2, 3]
اطبع (قائمة)[0]
ابغا كائن = { "خاصية": 42 }
اطبع ((كائن)).خاصية
(قائمة)[1] = 99
اطبع قائمة[1]
''')
