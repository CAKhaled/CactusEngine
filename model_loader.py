import os

class OBJMesh:
    def __init__(self):
        self.vertices = []
        self.normals = []
        self.texcoords = []
        self.faces = []

def load_obj(filename):
    if not os.path.exists(filename):
        raise Exception(f"File not found: {filename}")
        
    mesh = OBJMesh()
    
    with open(filename, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line.startswith('#') or not line:
                continue
                
            parts = line.split()
            if not parts:
                continue
                
            if parts[0] == 'v':
                mesh.vertices.append(tuple(map(float, parts[1:4])))
            elif parts[0] == 'vn':
                mesh.normals.append(tuple(map(float, parts[1:4])))
            elif parts[0] == 'vt':
                mesh.texcoords.append(tuple(map(float, parts[1:3])))
            elif parts[0] == 'f':
                face_v = []
                face_t = []
                face_n = []
                for p in parts[1:]:
                    vals = p.split('/')
                    # Negative indices in OBJ refer to the end of the list, 
                    # but typically tools export positive indices. Let's support basic positive.
                    if vals[0]:
                        v = int(vals[0])
                        v = v - 1 if v > 0 else len(mesh.vertices) + v
                        face_v.append(v)
                    else:
                        face_v.append(-1)
                        
                    if len(vals) > 1 and vals[1]:
                        t = int(vals[1])
                        t = t - 1 if t > 0 else len(mesh.texcoords) + t
                        face_t.append(t)
                    else:
                        face_t.append(-1)
                        
                    if len(vals) > 2 and vals[2]:
                        n = int(vals[2])
                        n = n - 1 if n > 0 else len(mesh.normals) + n
                        face_n.append(n)
                    else:
                        face_n.append(-1)
                mesh.faces.append((face_v, face_t, face_n))
                
    return mesh
