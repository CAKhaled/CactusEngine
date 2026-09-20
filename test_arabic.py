import pygame
import os
from graphics import GraphicsEngine, Canvas
import time

pygame.init()
pygame.display.set_mode((800, 600), pygame.OPENGL | pygame.DOUBLEBUF)

engine = GraphicsEngine()
engine.canvas = Canvas()
btn = engine.canvas.اضافة_زر("مرحباً بالعالم")
btn.الموقع = type('obj', (object,), {'x': 100, 'y': 100})() # fake Vector2
btn.ازاحة = type('obj', (object,), {'x': 100, 'y': 100})()

engine.render_scene()
pygame.display.flip()

# Save screen
size = pygame.display.get_window_size()
import OpenGL.GL as gl
pixels = gl.glReadPixels(0, 0, size[0], size[1], gl.GL_RGB, gl.GL_UNSIGNED_BYTE)
surface = pygame.image.fromstring(pixels, size, 'RGB')
surface = pygame.transform.flip(surface, False, True)
pygame.image.save(surface, 'arabic_test.png')
print("Saved arabic_test.png")
pygame.quit()
