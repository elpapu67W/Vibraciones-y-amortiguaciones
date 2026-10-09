import bpy
import csv
import math

RUTA= r"C:\Users\alejo\OneDrive\Documents\PITON\respuesta.csv"
FPS = 30
EXAG = 5.0                              


with open(RUTA, newline="") as fh:
    filas = list(csv.DictReader(fh))


bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete()
escena = bpy.context.scene
escena.render.fps = FPS
escena.frame_start = 1
escena.frame_end = len(filas)


def material(nombre, color):
    m = bpy.data.materials.new(nombre)
    m.diffuse_color = color           
    return m


def cubo(nombre, loc, dim, mat):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o = bpy.context.active_object
    o.name = nombre
    o.scale = dim
    o.data.materials.append(mat)
    return o



ROJO = material("fija", (0.82, 0.29, 0.36, 1))
AZUL = material("aislada", (0.18, 0.53, 0.67, 1))
GRIS = material("gris", (0.54, 0.58, 0.63, 1))
NEGRO = material("negro", (0.1, 0.15, 0.2, 1))
CAUCHO = material("caucho", (0.27, 0.3, 0.34, 1))

ESP = 0.04                            
H = 0.40                               
X_F, X_I = -0.75, 0.75                 
Z_MESA = 0.0
Z_BASE_F = ESP                        
Z_BASE_I = 0.12                       
OFF = (-0.25, 0.25)                     


def maqueta(x0, mat, aislada):
    z_base = Z_BASE_I if aislada else Z_BASE_F
    z_techo = z_base + H
    return dict(
        x0=x0, aislada=aislada, z_base=z_base, z_techo=z_techo,
        mesa=cubo("mesa_" + mat.name, (x0, 0, Z_MESA), (0.9, 0.3, ESP), GRIS),
        base=cubo("base_" + mat.name, (x0, 0, z_base), (0.6, 0.2, ESP), mat),
        techo=cubo("techo_" + mat.name, (x0, 0, z_techo), (0.6, 0.2, ESP), mat),
        col=[cubo(f"col{i}_" + mat.name, (x0, 0, 0), (0.02, 0.02, 1), NEGRO) for i in range(2)],
        ais=[cubo(f"ais{i}_" + mat.name, (x0, 0, 0), (0.05, 0.05, 1), CAUCHO) for i in range(2)] if aislada else [],
    )


def poner_barra(o, x1, z1, x2, z2, frame):

    dx, dz = x2 - x1, z2 - z1
    o.location = ((x1 + x2)/2, 0, (z1 + z2)/2)
    o.rotation_euler = (0, math.atan2(dx, dz), 0)
    o.scale[2] = math.hypot(dx, dz)
    o.keyframe_insert("location", frame=frame)
    o.keyframe_insert("rotation_euler", frame=frame)
    o.keyframe_insert("scale", frame=frame)


def animar(m, frame, xg, xb, xs):
    x0 = m["x0"]
    X = lambda x: x0 + EXAG*x
    for nombre, x in (("mesa", xg), ("base", xb), ("techo", xs)):
        m[nombre].location.x = X(x)
        m[nombre].keyframe_insert("location", index=0, frame=frame)
    for i, off in enumerate(OFF):
        poner_barra(m["col"][i], X(xb) + off, m["z_base"] + ESP/2, X(xs) + off, m["z_techo"] - ESP/2, frame)
        if m["aislada"]:
            poner_barra(m["ais"][i], X(xg) + off, Z_MESA + ESP/2, X(xb) + off, m["z_base"] - ESP/2, frame)


mF = maqueta(X_F, ROJO, False)
mI = maqueta(X_I, AZUL, True)

for i, f in enumerate(filas, start=1):
    xg, xb = float(f["xg"]), float(f["xb"])
    animar(mF, i, xg, xg, float(f["xs_f"]))      
    animar(mI, i, xg, xb, float(f["xs_i"]))


bpy.ops.object.camera_add(location=(0, -5, 0.45), rotation=(math.pi/2, 0, 0))
escena.camera = bpy.context.active_object
bpy.ops.object.light_add(type="SUN", location=(2, -3, 4))
bpy.context.active_object.data.energy = 3

try:
    if hasattr(escena.render.image_settings, "media_type"): 
        escena.render.image_settings.media_type = "VIDEO"
    escena.render.image_settings.file_format = "FFMPEG"
    escena.render.ffmpeg.format = "MPEG4"
    escena.render.filepath = "//aislamiento_sismico.mp4"
except Exception as e:
    print("No se pudo configurar la salida de video; elígela a mano en Output Properties:", e)
print(f"Listo: {len(filas)} fotogramas. Pulsa la barra espaciadora para reproducir.")