bl_info = {
    "name": "groove coaster thing",
    "blender": (3, 0, 0),
    "category": "Object",
}

import bpy
import struct
import os
import math
import mathutils
import pytransform3d
from mathutils import Vector, Matrix
from .stage_types.stage import stage
from bpy.props import (
    BoolProperty,
    FloatProperty,
    StringProperty,
    EnumProperty,
)
from bpy_extras.io_utils import (
    ImportHelper,
    ExportHelper,
    orientation_helper,
    path_reference_mode,
    axis_conversion,
)

def load_tumo(context, filepath):
    tumo_obj = load_tumo_data(filepath)

    me = bpy.data.meshes.new("mesh")
    me.from_pydata(tumo_obj[0], tumo_obj[1], tumo_obj[2])
    me.update()

    new_object = bpy.data.objects.new('new_object', me)

    new_collection = bpy.data.collections.new('new_collection')
    bpy.context.scene.collection.children.link(new_collection)


    new_collection.objects.link(new_object)

#returns tuple with verts, edges, faces
def load_tumo_data(filepath):
    with open(filepath, "rb") as fi:

        fi.read(4) #version, TODO: check if 1
        fi.read(4) #bonecount

        vert_count = struct.unpack(">I", fi.read(4))[0]

        verts = []
        edges = []
        faces = []
        
        for i in range(0, vert_count):
            #verts.append(struct.unpack(">fff", fi.read(12)))
            new_vert = struct.unpack(">fff", fi.read(12)) #ZYX -> XYZ (XZY)
            verts.append((new_vert[2], new_vert[0], new_vert[1]))

        while(True):
            if(struct.unpack("I", fi.read(4))[0] == 0xFFFFFFFF):
                break
            fi.seek(fi.tell() - 3)
        
        fi.read(4) #unk
        face_count = struct.unpack(">I", fi.read(4))[0]

        #raise ValueError(str(face_count))

        for i in range(0, face_count):
            new_face = []
            face_vert_count = struct.unpack(">I", fi.read(4))[0]
            for v in range(0, face_vert_count):
                new_face.append(struct.unpack(">III", fi.read(12))[0])
            faces.append(new_face)

        edge_count = struct.unpack(">I", fi.read(4))[0]
        for i in range(0, edge_count):
            new_edge = struct.unpack(">II", fi.read(8))
            edges.append(list(new_edge))
            
        
        return (verts, edges, faces)

def save_tumo(context, filepath):
    pass


class ImportTUMO(bpy.types.Operator, ImportHelper):
    """load a .tumo file"""
    bl_idname = "import_scene.tumo"
    bl_label = "Import TUMO"

    filename_ext = ".tumo"

    filter_glob: StringProperty(
        default="*.tumo",
        options={'HIDDEN'},
    )

    def execute(self, context):
        #raise ValueError("" + str(self.filepath))
        load_tumo(context, self.filepath)
        return {'FINISHED'}

def ms_to_frame(context, ms):
    #context.scene.render.fps_base? do we need to use this sometimes? idk
    return (float(ms) / float(1000.0)) * float(context.scene.render.fps)

def load_chart(context, filepath):
    model_dir = "/mnt/sde1/games/unp/"

    fi = open(filepath, 'rb')
    st = stage.parse_stream(fi)
    fi.close()
    
    #setup collections etc
    chart_collection = bpy.data.collections.new('chart_collection')
    object_collection = bpy.data.collections.new('object_collection')
    model_collection = bpy.data.collections.new('model_collection')
    model_collection.hide_render = True
    model_collection.hide_viewport = True
    context.scene.collection.children.link(chart_collection)
    chart_collection.children.link(object_collection)
    chart_collection.children.link(model_collection)
    
    #line and "move blob"
    if(True):
        cursor_mesh = bpy.data.meshes.new("cursor_mesh")
        cursor_mesh.from_pydata([[0.0, 0.0, 0.0], [0.0, 0.0, 0.1]], [], [])
        cursor_obj = bpy.data.objects.new("cursor_obj", cursor_mesh)
        cursor_obj.show_wire = True
        cursor_obj.show_name = True
        chart_collection.objects.link(cursor_obj)
        cursor_obj.keyframe_insert(data_path="location", frame=ms_to_frame(context, 0))
        cursor_obj.animation_data.action.fcurves[0].keyframe_points[-1].interpolation = 'LINEAR'
        
        line_verts = []
        for piece in st.trackPieces:
            line_verts.append((piece.Zpos, piece.Xpos, piece.Ypos))
            cursor_obj.location = [piece.Zpos, piece.Xpos, piece.Ypos]
            cursor_obj.keyframe_insert(data_path="location", frame=ms_to_frame(context, piece.timestampMs))
            cursor_obj.animation_data.action.fcurves[0].keyframe_points[-1].interpolation = 'LINEAR'
        line_edges = []
        for i in range(1, len(line_verts)):
            line_edges.append([i-1, i])
    
        line_mesh = bpy.data.meshes.new("line_mesh")
        line_mesh.from_pydata(line_verts, line_edges, line_edges)
        line_mesh.update()
        
        line_obj = bpy.data.objects.new("line_obj", line_mesh)
        line_obj.show_wire = True
        chart_collection.objects.link(line_obj)
    
    #models
    model_names = list(st.objectNames.names)
    for model_name in model_names:
        model_filename = model_name + ".tumo"
        if model_filename in os.listdir(model_dir):
            curr_model = load_tumo_data(os.path.join(model_dir, model_filename))
            
            new_mesh = bpy.data.meshes.new("mesh_" + model_name)
            new_mesh.from_pydata(curr_model[0], curr_model[1], curr_model[2])
            new_mesh.update()
            
            new_obj = bpy.data.objects.new(model_name, new_mesh)
            model_collection.objects.link(new_obj)
            #ret = bpy.ops.object.duplicate({"object": new_obj, "selected_objects": [new_obj]}, linked=True)
            #dup_obj = context.object
    
    #world = bpy.data.worlds['World']
    #world.use_nodes = True
    #bg = world.node_tree.nodes['Background']
    #r = 0
    #g = 0
    #b = 0
    #bg.inputs[0].default_value[:3] = (r, g, b)
    #bg.inputs[1].default_value = 1.0
    
    #objects
    model_nr = 0
    for object in st.objects:
        model_nr += 1
        if(object.model == 0xFFFFFFFF):
            pass #HACK: do something
        
        #make linked duplicate of model
        model_name = model_names[object.model]
        model_obj = model_collection.objects[model_name]
        new_obj = bpy.data.objects.new(model_name + "_" + str(model_nr), model_obj.data.copy())
        
        #add colored material
        mat = bpy.data.materials.new('obj_' + str(model_nr) + "_" + model_name + "_mat")
        mat.diffuse_color = [object.color.get_red(), object.color.get_green(), object.color.get_blue(), object.color.alpha]
        new_obj.data.materials.append(mat)
        
        #setup as wireframe (if option is selected)
        if object.solidBool == True: #inverse, very cool
            new_obj.display_type = 'WIRE'
        
        new_obj.location = [object.Xpos, object.Zpos, object.Ypos]
        new_obj.rotation_euler = [math.radians(360.0 - object.Xrot), math.radians(360.0 - object.Zrot), math.radians(360.0 - object.Yrot)]
        new_obj.scale = [object.Xscale, object.Zscale, object.Yscale]
        new_obj.hide_render = True
        new_obj.hide_viewport = True
        
        new_obj.animation_data_create()
        new_obj.animation_data.action = bpy.data.actions.new(name="obj_"+str(model_nr)+"_action")
        fc_xp = new_obj.animation_data.action.fcurves.new(data_path="location", index=0)
        fc_yp = new_obj.animation_data.action.fcurves.new(data_path="location", index=1)
        fc_zp = new_obj.animation_data.action.fcurves.new(data_path="location", index=2)
        
        fc_xs = new_obj.animation_data.action.fcurves.new(data_path="scale", index=0)
        fc_ys = new_obj.animation_data.action.fcurves.new(data_path="scale", index=1)
        fc_zs = new_obj.animation_data.action.fcurves.new(data_path="scale", index=2)
        
        fc_xr = new_obj.animation_data.action.fcurves.new(data_path="rotation_euler", index=0)
        fc_zr = new_obj.animation_data.action.fcurves.new(data_path="rotation_euler", index=2)
        fc_yr = new_obj.animation_data.action.fcurves.new(data_path="rotation_euler", index=1)
        
        mat.animation_data_create()
        mat.animation_data.action = bpy.data.actions.new(name="mat_"+str(model_nr)+"_action")
        fc_diff_r = mat.animation_data.action.fcurves.new(data_path="diffuse_color", index=0)
        fc_diff_g = mat.animation_data.action.fcurves.new(data_path="diffuse_color", index=1)
        fc_diff_b = mat.animation_data.action.fcurves.new(data_path="diffuse_color", index=2)
        fc_diff_a = mat.animation_data.action.fcurves.new(data_path="diffuse_color", index=3)
        
        mat.keyframe_insert(data_path="diffuse_color", frame=ms_to_frame(context, 0))
        
        new_obj.keyframe_insert(data_path="location", frame=ms_to_frame(context, 0))
        fc_xp.keyframe_points[-1].interpolation = 'CONSTANT'
        fc_yp.keyframe_points[-1].interpolation = 'CONSTANT'
        fc_zp.keyframe_points[-1].interpolation = 'CONSTANT'
        
        new_obj.keyframe_insert(data_path="scale", frame=ms_to_frame(context, 0))
        fc_xs.keyframe_points[-1].interpolation = 'CONSTANT'
        fc_ys.keyframe_points[-1].interpolation = 'CONSTANT'
        fc_zs.keyframe_points[-1].interpolation = 'CONSTANT'
        
        new_obj.keyframe_insert(data_path="rotation_euler", frame=ms_to_frame(context, 0))
        fc_xr.keyframe_points[-1].interpolation = 'LINEAR'
        fc_yr.keyframe_points[-1].interpolation = 'LINEAR'
        fc_zr.keyframe_points[-1].interpolation = 'LINEAR'
        
        new_obj.keyframe_insert(data_path="hide_viewport", frame=ms_to_frame(context, 0))
        new_obj.keyframe_insert(data_path="hide_render", frame=ms_to_frame(context, 0))
        new_obj.keyframe_insert(data_path="display_type", frame=ms_to_frame(context, 0))
        object_collection.objects.link(new_obj)

        for i in range(len(object.movementEntries)):
            m = object.movementEntries[i]
            new_obj.location = [m.Xpos + object.Xpos, m.Zpos + object.Zpos, m.Ypos + object.Ypos]
            
            intmode = 'CONSTANT'
            if m.tweenAwayBool == True:
                intmode = 'LINEAR'
            if m.tweenTowardsBool == True and i != 0: #TODO: check if correctly implemented
                fc_xp.keyframe_points[-1].interpolation = intmode
                fc_yp.keyframe_points[-1].interpolation = intmode
                fc_zp.keyframe_points[-1].interpolation = intmode
            
            new_obj.keyframe_insert(data_path="location", frame=ms_to_frame(context, m.timestampMs))
            fc_xp.keyframe_points[-1].interpolation = intmode
            fc_yp.keyframe_points[-1].interpolation = intmode
            fc_zp.keyframe_points[-1].interpolation = intmode
        
        for i in range(len(object.visibilityEntries)):
            v = object.visibilityEntries[i]
            if(v.visibleBool == True):
                new_obj.hide_render = False
                new_obj.hide_viewport = False
            else:
                new_obj.hide_render = True
                new_obj.hide_viewport = True
            
            new_obj.keyframe_insert(data_path="hide_viewport", frame=ms_to_frame(context, v.timestampMs))
            new_obj.keyframe_insert(data_path="hide_render", frame=ms_to_frame(context, v.timestampMs))
        
        for i in range(len(object.colorChangeEntries)):
            c = object.colorChangeEntries[i]
            #mat = new_obj.data.materials[0]
            mat.diffuse_color[0] = float(c.color.red) / 255.0
            mat.diffuse_color[1] = float(c.color.green) / 255.0
            mat.diffuse_color[2] = float(c.color.blue) / 255.0
            mat.diffuse_color[3] = float(c.color.alpha) / 255.0
            
            intmode = 'CONSTANT'
            if(c.unk5 == True):
                intmode = 'LINEAR'
            mat.keyframe_insert(data_path="diffuse_color", frame=ms_to_frame(context, c.timestampMs))
            fc_diff_r.keyframe_points[-1].interpolation = intmode
            fc_diff_g.keyframe_points[-1].interpolation = intmode
            fc_diff_b.keyframe_points[-1].interpolation = intmode
            fc_diff_a.keyframe_points[-1].interpolation = intmode
        
        for i in range(len(object.scalingEntries)):
            s = object.scalingEntries[i]
            new_obj.scale = [s.Xscale * object.Xscale, s.Zscale * object.Zscale, s.Yscale * object.Yscale]
            
            intmode = 'CONSTANT'
            if s.tweenAwayBool == True:
                intmode = 'LINEAR'
            if s.tweenTowardsBool == True and i != 0: #TODO: check if correctly implemented
                fc_xs.keyframe_points[-1].interpolation = intmode
                fc_ys.keyframe_points[-1].interpolation = intmode
                fc_zs.keyframe_points[-1].interpolation = intmode
            
            new_obj.keyframe_insert(data_path="scale", frame=ms_to_frame(context, s.timestampMs))
            fc_xs.keyframe_points[-1].interpolation = intmode
            fc_ys.keyframe_points[-1].interpolation = intmode
            fc_zs.keyframe_points[-1].interpolation = intmode
            

        for r in object.rotationEntries:
            continue #HACK: just ignore for now, they're pain anyways
            
            intmode = 'LINEAR'
            
            #obmatnew = Matrix.Rotation(r.unk14, 4, 'X') * new_obj.matrix_world
            #new_obj.matrix_world = obmatnew
            #context.view_layer.update()
            
            #rot_local = Vector((math.radians(r.unk14), math.radians(r.unk10), math.radians(r.unk6)))
            #rot_world = new_obj.matrix_world.to_3x3() @ rot_local
            
            #new_obj.matrix_world += rot_world
            #eul = Euler((math.radians(r.unk14), math.radians(r.unk10), math.radians(r.unk6)), 'XYZ')
            
            #new_obj.rotation_euler = [math.radians(360.0 - object.Xrot) % 359.0, math.radians(360.0 - object.Zrot) % 359.0, math.radians(360.0 - object.Yrot) % 359.0]
            #context.view_layer.update()
            #local_rotate(new_obj, eul)
            
            #context.view_layer.update()

            orig = Euler((math.radians(360.0 - object.Xrot), math.radians(360.0 - object.Zrot), math.radians(360.0 - object.Yrot)), 'XYZ').to_quaternion()
            #orig = Euler((math.radians(object.Xrot), math.radians(object.Zrot), math.radians(object.Yrot)), 'XYZ').to_quaternion()
            new = Euler((math.radians(r.unk10), math.radians(r.unk14), math.radians(r.unk6)), 'XYZ').to_quaternion()
            #new = Euler((math.radians(90), math.radians(180), math.radians(45)), 'XYZ').to_quaternion()
            orig.rotate(new)
            new_obj.rotation_euler = orig.to_euler()
            
            #new_obj.rotation_euler.rotate_axis('X', math.radians(r.unk10))
            #new_obj.rotation_euler.rotate_axis('Y', math.radians(r.unk14))
            #new_obj.rotation_euler.rotate_axis('Z', math.radians(r.unk6))
            
            #additional_rot_mat = Euler((r.unk14, r.unk10, r.unk6), 'XYZ').to_matrix().to_4x4()
            #
            #new_obj.rotation_euler = [math.radians(r.unk14 + object.Xrot), math.radians(r.unk10 + object.Zrot), math.radians(r.unk6 + object.Yrot)]
            #new_obj.rotation_euler = [math.radians(360.0 - object.Xrot), math.radians(360.0 - object.Zrot), math.radians(360.0 - object.Yrot)]
            #new_obj.rotation_euler = [math.radians(object.Xrot), math.radians(object.Zrot), math.radians(object.Yrot)]
            #new_obj.matrix_world *= Matrix.Rotation(math.radians(r.unk10), 4, 'Y')
            #context.view_layer.update()            
            #orig_loc, orig_rot, orig_scale = new_obj.matrix_local.decompose()
            #
            #orig_loc_mat = Matrix.Translation(orig_loc)
            #orig_rot_mat = orig_rot.to_matrix().to_4x4()
            #orig_scale_mat = Matrix.Scale(orig_scale[0],4,(1,0,0)) * Matrix.Scale(orig_scale[1],4,(0,1,0)) * Matrix.Scale(orig_scale[2],4,(0,0,1))
            #
            #new_obj.matrix_local = orig_loc_mat * orig_rot_mat * additional_rot_mat * orig_scale_mat
            
            #new_obj.rotation_euler = [math.radians(object.Xrot), math.radians(object.Zrot), math.radians(object.Yrot)]
            #context.view_layer.update()
            #context.view_layer.update()
            new_obj.keyframe_insert(data_path="rotation_euler", frame=ms_to_frame(context, r.timestampMs + object.visibilityEntries[1].timestampMs))
            fc_xr.keyframe_points[-1].interpolation = intmode
            fc_yr.keyframe_points[-1].interpolation = intmode
            fc_zr.keyframe_points[-1].interpolation = intmode
            context.view_layer.update()
            
def local_reset(obj, rotation):
    loc, rot, scale = obj.matrix_world.decompose()
    rotation = rotation.copy()
    if not isinstance(rotation, Matrix):
        obj.matrix_world = rotation.to_matrix().to_4x4()
    else:
        obj.matrix_world = rotation.to_4x4()
    obj.location = loc
    obj.scale = scale

def local_rotate(obj, rotation):
    loc, rot, scale = obj.matrix_world.decompose()
    rotation = rotation.copy()
    rotation.rotate(rot)
    if not isinstance(rotation, Matrix):
        obj.matrix_world = rotation.to_matrix().to_4x4()
    else:
        obj.matrix_world = rotation.to_4x4()
    obj.location = loc
    obj.scale = scale

class ImportChart(bpy.types.Operator, ImportHelper):
    """load a .dat GC chart file"""
    bl_idname = "import_chart.dat"
    bl_label = "Import GC chart"

    filename_ext = ".dat"

    filter_glob: StringProperty(
        default="*.dat",
        options={'HIDDEN'},
    )

    def execute(self, context):
        #raise ValueError("" + str(self.filepath))
        load_chart(context, self.filepath)
        return {'FINISHED'}

def menu_func_tumo_import(self, context):
    self.layout.operator(ImportTUMO.bl_idname, text="TUMO (.tumo)")

def menu_func_chart_import(self, context):
    self.layout.operator(ImportChart.bl_idname, text="GC Chart (.dat)")

def register():
    try:
        unregister()
    except:
        print("noo unregister failed")
    bpy.utils.register_class(ImportTUMO)
    bpy.utils.register_class(ImportChart)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_tumo_import)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_chart_import)

def unregister():
    print("unregistering")
    bpy.utils.unregister_class(ImportTUMO)
    bpy.utils.unregister_class(ImportChart)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_tumo_import)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_chart_import)

if __name__ == "__main__":
    register()
