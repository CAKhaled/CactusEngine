import os
import pygame
from OpenGL.GL import *
from OpenGL.GLU import *
from PIL import Image

pygame.init()
pygame.display.set_mode((800, 600), pygame.OPENGL | pygame.DOUBLEBUF)

from graphics import GraphicsEngine, Square2D
from math_types import Vector3, Color

o = Square2D()
o.الموقع = Vector3(400, 300, 0)
o.المقياس = Vector3(100, 100, 0)
o.الدوران = Vector3(0, 0, 0)
o.اللون = Color(1.0, 0.0, 0.0)
o.texture_id = -1
o.مساحة_الشاشة = True

ge = GraphicsEngine()
ge.objects_2d.append(o)
ge.render_scene()
pygame.display.flip()

data = glReadPixels(0, 0, 800, 600, GL_RGB, GL_UNSIGNED_BYTE)
img = Image.frombytes('RGB', (800, 600), data)
img = img.transpose(Image.FLIP_TOP_BOTTOM)
img.save('test_output.png')
pygame.quit()
