"""Показать запечённую модель в Blender до запуска игры: атлас с готовой текстурой в сцене WB_Bake. name задаётся перед exec."""
import bpy

_sc = bpy.data.scenes["WB_Bake"]
bpy.context.window.scene = _sc
_low = bpy.data.objects[name + "_atlas"]
_hi = bpy.data.objects.get(name + "_hi")
if _hi:
    _hi.hide_viewport = True
    _hi.hide_render = True
_img = bpy.data.images.load(r"C:/Users/Name/projectWARHAMMER/src/main/resources/assets/warpbound/textures/entity/" + name + ".png", check_existing=False)
_img.reload()
_mat = bpy.data.materials.get("WB_view") or bpy.data.materials.new("WB_view")
_mat.use_nodes = True
_nt = _mat.node_tree
_nt.nodes.clear()
_out = _nt.nodes.new("ShaderNodeOutputMaterial")
_em = _nt.nodes.new("ShaderNodeEmission")
_tx = _nt.nodes.new("ShaderNodeTexImage")
_tx.image = _img
_nt.links.new(_tx.outputs[0], _em.inputs[0])
_nt.links.new(_em.outputs[0], _out.inputs[0])
_low.data.materials.clear()
_low.data.materials.append(_mat)
