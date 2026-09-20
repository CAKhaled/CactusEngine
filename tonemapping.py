from OpenGL.GL import *
from OpenGL.GL.framebufferobjects import *
from OpenGL.GL.shaders import compileProgram, compileShader
import pygame

class Tonemapper:
    """
    نظام بسيط للـ Tonemapping باستخدام FBO (Framebuffer Object) و Shader.
    يقوم بالتقاط المشهد ثم رسمه مع تطبيق تأثير Tonemapping (Reinhard).
    """
    def __init__(self, width, height, exposure=1.0):
        self.width = width
        self.height = height
        self.exposure = exposure
        self.enabled = True
        self._gl_initialized = False
        self.fbo = 0
        self.texture = 0
        self.rbo = 0
        self.shader = None

    def _init_gl(self):
        try:
            if not bool(glGenFramebuffers):
                print("FBOs not supported!")
                self.enabled = False
                return
        except:
            pass

        self._gl_initialized = True
        
        # إنشاء FBO
        self.fbo = glGenFramebuffers(1)
        glBindFramebuffer(GL_FRAMEBUFFER, self.fbo)
        
        # إنشاء Texture للتصيير
        self.texture = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, self.texture)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, self.width, self.height, 0, GL_RGB, GL_UNSIGNED_BYTE, None)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, self.texture, 0)
        
        # إنشاء Renderbuffer للعمق (Depth) و (Stencil)
        self.rbo = glGenRenderbuffers(1)
        glBindRenderbuffer(GL_RENDERBUFFER, self.rbo)
        glRenderbufferStorage(GL_RENDERBUFFER, GL_DEPTH24_STENCIL8, self.width, self.height)
        glFramebufferRenderbuffer(GL_FRAMEBUFFER, GL_DEPTH_STENCIL_ATTACHMENT, GL_RENDERBUFFER, self.rbo)
        
        if glCheckFramebufferStatus(GL_FRAMEBUFFER) != GL_FRAMEBUFFER_COMPLETE:
            print("ERROR: Framebuffer is not complete!")
        glBindFramebuffer(GL_FRAMEBUFFER, 0)
        
        # إنشاء Shader
        vertex_src = """
        void main() {
            gl_TexCoord[0] = gl_MultiTexCoord0;
            gl_Position = gl_ModelViewProjectionMatrix * gl_Vertex;
        }
        """
        
        fragment_src = """
        uniform sampler2D screenTexture;
        uniform float exposure;
        
        void main() {
            vec3 hdrColor = texture2D(screenTexture, gl_TexCoord[0].st).rgb;
            
            // Exposure tone mapping
            vec3 mapped = vec3(1.0) - exp(-hdrColor * exposure);
            
            // Gamma correction
            mapped = pow(mapped, vec3(1.0 / 2.2));
            
            gl_FragColor = vec4(mapped, 1.0);
        }
        """
        
        try:
            self.shader = compileProgram(
                compileShader(vertex_src, GL_VERTEX_SHADER),
                compileShader(fragment_src, GL_FRAGMENT_SHADER)
            )
        except Exception as e:
            print("Tonemapping Shader Error:", e)
            self.shader = None

    def update_size(self, width, height):
        if self.width == width and self.height == height:
            return
        if width <= 0 or height <= 0:
            return
            
        self.width = width
        self.height = height
        
        if not self._gl_initialized:
            self._init_gl()
            return
            
        glBindTexture(GL_TEXTURE_2D, self.texture)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, width, height, 0, GL_RGB, GL_UNSIGNED_BYTE, None)
        
        glBindRenderbuffer(GL_RENDERBUFFER, self.rbo)
        glRenderbufferStorage(GL_RENDERBUFFER, GL_DEPTH24_STENCIL8, width, height)

    def bind(self):
        if not self._gl_initialized:
            self._init_gl()
            
        if self.enabled and self._gl_initialized:
            glBindFramebuffer(GL_FRAMEBUFFER, self.fbo)

    def unbind_and_draw(self):
        if not self.enabled or not self._gl_initialized:
            return
            
        glBindFramebuffer(GL_FRAMEBUFFER, 0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        
        if self.shader:
            glUseProgram(self.shader)
            loc = glGetUniformLocation(self.shader, "exposure")
            if loc != -1:
                glUniform1f(loc, self.exposure)
        
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()
        
        glPushAttrib(GL_ENABLE_BIT)
        glDisable(GL_DEPTH_TEST)
        glDisable(GL_LIGHTING)
        glEnable(GL_TEXTURE_2D)
        
        glBindTexture(GL_TEXTURE_2D, self.texture)
        glColor3f(1.0, 1.0, 1.0)
        
        glBegin(GL_QUADS)
        glTexCoord2f(0, 0); glVertex2f(-1, -1)
        glTexCoord2f(1, 0); glVertex2f(1, -1)
        glTexCoord2f(1, 1); glVertex2f(1, 1)
        glTexCoord2f(0, 1); glVertex2f(-1, 1)
        glEnd()
        
        glPopAttrib()
        
        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        
        if self.shader:
            glUseProgram(0)
