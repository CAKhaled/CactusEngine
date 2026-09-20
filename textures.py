from OpenGL.GL import *
import pygame

def load_texture(filename):
    if hasattr(filename, 'base'):
        filename = filename.base
    if not filename:
        return None

    try:
        from OpenGL.GL import glGetString, GL_VERSION
        if not glGetString(GL_VERSION):
            return filename
    except Exception:
        return filename

    surface = pygame.image.load(filename)
    surface = pygame.transform.flip(surface, False, True)

    texture = glGenTextures(1)

    glBindTexture(GL_TEXTURE_2D, texture)

    data = pygame.image.tostring(surface, "RGBA", True)

    glTexImage2D(
        GL_TEXTURE_2D,
        0,
        GL_RGBA,
        surface.get_width(),
        surface.get_height(),
        0,
        GL_RGBA,
        GL_UNSIGNED_BYTE,
        data
    )

    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    # منع ظهور خطوط سوداء عند حواف الصور (مهم جداً للسماء المكعبة)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, 0x2901) # GL_CLAMP_TO_EDGE
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, 0x2901) # GL_CLAMP_TO_EDGE

    glBindTexture(GL_TEXTURE_2D, 0)

    return texture