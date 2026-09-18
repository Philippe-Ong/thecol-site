"""Render the existing Hibiscus bottle with studio lighting in Blender.

Run Blender in background with the source .blend and --python this file.
Pass -- --final for the full-resolution, packed production scene.
Working files are kept in .render-work; the original model is never overwritten.
"""
import sys
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / '.render-work'
WORK.mkdir(exist_ok=True)
FINAL = '--final' in sys.argv
GPU = '--gpu' in sys.argv
s = bpy.context.scene


def enum_set(owner, key, value):
    allowed = [i.identifier for i in owner.bl_rna.properties[key].enum_items]
    if value not in allowed:
        raise ValueError(f'{key}: {value} not in {allowed}')
    setattr(owner, key, value)


def shader(material, node_type):
    return next(n for n in bpy.data.materials[material].node_tree.nodes if n.type == node_type)


# The source contains both glass and liquid surfaces, and the original label UVs.
shader('Externe', 'BSDF_GLASS').inputs['Roughness'].default_value = 0.025
shader('Externe', 'BSDF_GLASS').inputs['IOR'].default_value = 1.46
liquid = shader('Interne', 'BSDF_PRINCIPLED')
liquid.inputs['Base Color'].default_value = (0.95, 0.25, 0.075, 1)
liquid.inputs['Roughness'].default_value = 0.015
absorption = shader('Interne', 'VOLUME_ABSORPTION')
absorption.inputs['Color'].default_value = (0.80, 0.045, 0.012, 1)
absorption.inputs['Density'].default_value = 1
cap = shader('Bouchon', 'BSDF_PRINCIPLED')
cap.inputs['Base Color'].default_value = (0.012, 0.014, 0.012, 1)
cap.inputs['Metallic'].default_value = 0.75
cap.inputs['Roughness'].default_value = 0.24
cap.inputs['Coat Weight'].default_value = 0.25
for name in ['Material', 'Material.001', 'Material.002']:
    paper = shader(name, 'BSDF_PRINCIPLED')
    paper.inputs['Roughness'].default_value = 0.58
    paper.inputs['Specular IOR Level'].default_value = 0.24

center = Vector((0.3058793, -0.4097538, 0.0017))
front = Vector((0.284, 0.959, 0)).normalized()
right = Vector((front.y, -front.x, 0))
up = Vector((0, 0, 1))
camera = s.camera
enum_set(camera.data, 'type', 'ORTHO')
camera.data.ortho_scale = 0.215
camera.location = center + front * 0.9 + up * 0.024
camera.rotation_euler = (center - camera.location).to_track_quat('-Z', 'Y').to_euler()
camera.data.dof.use_dof = False

for obj in s.objects:
    if obj.type == 'LIGHT':
        obj.hide_render = True


def softbox(name, x, y, z, power, width, height):
    light = bpy.data.lights.new(name, 'AREA')
    enum_set(light, 'shape', 'RECTANGLE')
    light.energy = power
    light.size = width
    light.size_y = height
    obj = bpy.data.objects.new(name, light)
    s.collection.objects.link(obj)
    obj.location = center + right * x + front * y + up * z
    obj.rotation_euler = (center - obj.location).to_track_quat('-Z', 'Y').to_euler()


softbox('Studio key', -0.22, 0.13, 0.09, 3, 0.065, 0.28)
softbox('Studio fill', 0.23, 0.12, 0.025, 1.5, 0.075, 0.25)
softbox('Studio rim', 0.13, -0.16, 0.04, 3, 0.06, 0.24)
softbox('Studio top', -0.04, 0.015, 0.28, 2, 0.18, 0.18)
world_bg = next(n for n in s.world.node_tree.nodes if n.type == 'BACKGROUND')
world_bg.inputs['Strength'].default_value = 0.65

try:
    s.render.engine = 'CYCLES'
except TypeError as exc:
    raise RuntimeError('Cycles required for glass refraction') from exc
enum_set(s.cycles, 'device', 'CPU')
if GPU:
    prefs = bpy.context.preferences.addons['cycles'].preferences
    backends = [item[0] for item in prefs.get_device_types(bpy.context)]
    if 'OPTIX' not in backends:
        raise RuntimeError('OptiX is unavailable; omit --gpu to render on CPU')
    prefs.compute_device_type = 'OPTIX'
    prefs.get_devices()
    selected = [device for device in prefs.devices if device.type == 'OPTIX']
    if not selected:
        raise RuntimeError('No OptiX GPU found; omit --gpu to render on CPU')
    for device in prefs.devices:
        device.use = device.type == 'OPTIX'
    enum_set(s.cycles, 'device', 'GPU')
    print('Rendering with', [device.name for device in selected], flush=True)
s.cycles.samples = 256 if FINAL else 48
s.cycles.use_denoising = True
s.cycles.max_bounces = 16
s.cycles.transmission_bounces = 12
s.cycles.transparent_max_bounces = 12
s.cycles.film_transparent_glass = False
s.cycles.adaptive_threshold = 0.01 if FINAL else 0.04
s.render.resolution_x = 600 if FINAL else 300
s.render.resolution_y = 1400 if FINAL else 700
s.render.resolution_percentage = 100
s.render.film_transparent = True
s.render.use_border = False
enum_set(s.render.image_settings, 'file_format', 'PNG')
enum_set(s.render.image_settings, 'color_mode', 'RGBA')
filename = 'hibiscus-final-gpu.png' if FINAL and GPU else 'hibiscus-final.png' if FINAL else 'hibiscus-preview.png'
s.render.filepath = str(WORK / filename)
s.view_settings.exposure = 0.0

# Pack only images that exist; unused reference planes may point to missing files.
if FINAL:
    for image in bpy.data.images:
        if image.filepath and Path(bpy.path.abspath(image.filepath)).is_file():
            image.pack()
    bpy.ops.wm.save_as_mainfile(filepath=str(WORK / 'hibiscus-studio.blend'))
bpy.ops.render.render(write_still=True)
print('THECOL_RENDER_COMPLETE', s.render.filepath, flush=True)
