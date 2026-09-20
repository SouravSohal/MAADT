import bpy
import math
import os

# Clear existing objects
bpy.ops.wm.read_factory_settings(use_empty=True)

# Helper function to create materials
def create_material(name, color, emissive=False):
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs['Base Color'].default_value = color
    if emissive:
        bsdf.inputs['Emission Color'].default_value = color
        bsdf.inputs['Emission Strength'].default_value = 2.0
    return mat

mat_body = create_material("Mat_Body", (0.8, 0.8, 0.8, 1))
mat_engine = create_material("Mat_Engine", (0.1, 0.1, 0.8, 1), emissive=True) # Starts blue-ish
mat_prop = create_material("Mat_Prop", (0.1, 0.1, 0.1, 1))

# 1. Fuselage
bpy.ops.mesh.primitive_cylinder_add(radius=0.5, depth=4, location=(0, 0, 0))
fuselage = bpy.context.active_object
fuselage.name = "Fuselage"
fuselage.rotation_euler[1] = math.pi / 2  # Rotate along Y axis
fuselage.data.materials.append(mat_body)

# 2. Wings
bpy.ops.mesh.primitive_cube_add(size=1, location=(0.5, 0, 0.2))
wings = bpy.context.active_object
wings.name = "Wings"
wings.scale = (0.5, 6, 0.05) # Long wingspan
wings.data.materials.append(mat_body)
wings.parent = fuselage

# 3. V-Tail
bpy.ops.mesh.primitive_cube_add(size=1, location=(-1.8, 0.5, 0.3))
tail_l = bpy.context.active_object
tail_l.name = "Tail_L"
tail_l.scale = (0.4, 1.2, 0.05)
tail_l.rotation_euler[0] = math.pi / 4 # Angle up
tail_l.data.materials.append(mat_body)
tail_l.parent = fuselage

bpy.ops.mesh.primitive_cube_add(size=1, location=(-1.8, -0.5, 0.3))
tail_r = bpy.context.active_object
tail_r.name = "Tail_R"
tail_r.scale = (0.4, 1.2, 0.05)
tail_r.rotation_euler[0] = -math.pi / 4 # Angle up
tail_r.data.materials.append(mat_body)
tail_r.parent = fuselage

# 4. Engine Block
bpy.ops.mesh.primitive_cylinder_add(radius=0.45, depth=0.6, location=(-2.0, 0, 0))
engine = bpy.context.active_object
engine.name = "Engine_Block"
engine.rotation_euler[1] = math.pi / 2
engine.data.materials.append(mat_engine)
engine.parent = fuselage

# 5. Propeller
bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=0.2, location=(-2.4, 0, 0))
prop_hub = bpy.context.active_object
prop_hub.name = "Propeller"
prop_hub.rotation_euler[1] = math.pi / 2
prop_hub.data.materials.append(mat_prop)

# Blades
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0))
blade = bpy.context.active_object
blade.name = "Blade"
blade.scale = (0.05, 1.8, 0.1)
blade.parent = prop_hub
blade.data.materials.append(mat_prop)

# Ensure Propeller isn't parented to engine so we can rotate it independently in Three.js easily, 
# or parent it to fuselage
prop_hub.parent = fuselage

# Export to GLB
export_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../frontend/public/uav_model.glb'))
os.makedirs(os.path.dirname(export_path), exist_ok=True)

bpy.ops.export_scene.gltf(
    filepath=export_path,
    export_format='GLB',
    use_selection=False,
    export_apply=True
)

print(f"Successfully exported UAV model to {export_path}")
