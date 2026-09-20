import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from interpreter import Interpreter
interp = Interpreter()

try:
    print('TEST 1:', interp.evaluate('"النقاط" " النقاط"'))
except Exception as e:
    print('TEST 1 ERROR:', e)

try:
    print('TEST 2:', interp.evaluate('"النقاط" + " 10"'))
except Exception as e:
    print('TEST 2 ERROR:', e)
