import bpy
import bmesh
import os
import math

bl_info = {
    "name" : "BlurImportExport",
    "author" : "TimberStalker",
    "description" : "",
    "blender" : (3, 0, 0),
    "version" : (0, 0, 1),
    "category" : "Import-Export"
}

from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty, BoolProperty, EnumProperty
from bpy.types import MeshVertex, Operator


import numpy as np
class Reader:
    def __init__(self, filepath):
        with open(filepath, 'rb') as file:
            self.data = file.read()
            self.pointer = 0
    def position(self):    
        return hex(self.pointer)
    def pos(self) -> int:    
        return self.pointer
    
    def read(self, amount) -> bytes:
        end = self.pointer+amount
        temp = self.data[self.pointer:end]
        self.pointer = end
        return temp
    
    def read_byte(self) -> int:
        #"""Read an integer from the file and advance the pointer 4 bytes"""
        return int.from_bytes(self.read(1), "little")
    
    def read_int(self, sign="True") -> int:
        #"""Read an integer from the file and advance the pointer 4 bytes"""
        return int.from_bytes(self.read(4), "little", signed=sign)

    def read_short(self) -> int:
        #"""Read a short from the file and advance the pointer 2 bytes"""
        return int(np.frombuffer(self.read(2), np.short))

    def read_float(self) -> float:
        #"""Read a float from the file and advance the pointer 4 bytes"""
        return float(np.frombuffer(self.read(4), np.float32))

    def read_half(self) -> float:
        #"""Read a half from the file and advance the pointer 2 bytes"""
        return float(np.frombuffer(self.read(2), np.float16))

    def read_string(self, len = 0, clip = 0) -> str:
        #"""Read a string from the file and advance the pointer [stringLength] bytes. 
        #If no string length is given, the function will first read an integer describing the length and then read the string"""
        
        if len == 0:
            len = self.read_int()
            
        bytes = self.read(len-clip)
        if clip > 0:
            self.advance(clip)
        return bytes.decode('utf-8')
    
    def read_cstring(self) -> str:
        bytes = bytearray()
        byte = self.read_byte()
        while(byte != 0):
            bytes.append(byte)
            byte = self.read_byte()
        
        return bytes.decode('utf-8')
        
    def read_matrix(self):
        scalex = self.read_float() #1
        
        shear1 = self.read_float() #1
        shear2 = self.read_float() #1
        shear3 = self.read_float() #1
        
        scaley = self.read_float() #1
        
        shear4 = self.read_float() #1
        shear5 = self.read_float() #1
        shear6 = self.read_float() #1
        
        scalez = self.read_float() #1
        
        rotationx = math.atan2(shear6, scaley)
        rotationy = math.atan2(-shear5, math.sqrt(shear6**2 + scaley**2))
        rotationz = math.atan2(shear3, scalex)
        
        positionx = self.read_float()
        positiony = self.read_float()
        positionz = self.read_float()
        
        return {'position':[positionx, positionz, positiony], 'scale':[scalex, scalez, scaley], 'rotation':[rotationx, rotationz, rotationy]}
    

    def advance(self,amount = 4):
        #"""Advance the pointer [amount] of bytes or 4 if no amount is given"""
        self.pointer += amount
            
    def advance_to(self,findVal):
        #"""Advance the pointer untill the next readable value matches [findVal]"""
        while self.read_int() != findVal:
            self.advance(-3)
        self.advance(-4)
        
def to_hex(inString) -> str:
    return format(inString, 'x')








#---------------------------------------------------------------------------------------------------
#---------------------------------------------------------------------------------------------------
#---------------------------------------------------------------------------------------------------
#---------------------------------------------------------------------------------------------------
#---------------------------------------------------------------------------------------------------
def import_cpmodel(self, context, filepath, swap_faces):
    
    model = read_cpmodel_data(self, filepath)
    
    create_model_from_data(model, swap_faces)
    
    for object in bpy.data.objects:
        if not object.parent == None:
            object.matrix_parent_inverse = object.parent.matrix_world.inverted()
        
    return {'FINISHED'}
    
def read_cpmodel_data(self, filepath):
    
    reader = Reader(filepath)
    
    model = {}
    
    r_pos = reader.pos
    r_int = reader.read_int
    r_string = reader.read_string
    r_cstring = reader.read_cstring
    r_float = reader.read_float
    r_short = reader.read_short
    r_byte = reader.read_byte
    r_half = reader.read_half
    r_matrix = reader.read_matrix
    r_ad = reader.advance
    
    def r_bb():
        return ({'x':r_float(), 'z':r_float(), 'y':r_float()}, {'x':r_float(), 'z':r_float(), 'y':r_float()})
    def r_sec(len, clip):
        sections.append({'title':r_string(len, clip), 'start':r_pos()-len, 'length':r_int(), 'end':r_int()})
    def print_sec(sec):
        print('{0}: 0x{1} [0x{2}]'.format(sec['title'], to_hex(sec['start']), to_hex(sec['length'])))
    def bb_toString(bbox):
        return '({:.2f}, {:.2f}, {:.2f}), ({:.2f}, {:.2f}, {:.2f})'.format(bbox[0]['x'], bbox[0]['y'], bbox[0]['z'], bbox[1]['x'], bbox[1]['y'], bbox[1]['z'])
    
    def readSubModel(names):
        matrix = r_matrix()
        bbox = r_bb()
        
        name_index = r_int()
        name = names[name_index]
        
        model_index = r_int()
        child_element_count = r_int()
        hierarchy_index = r_int()
        ued4 = r_int()
        ued5 = r_int()
        ued6 = r_int()
        
        submodel = {}
        submodel['matrix'] = matrix
        submodel['name'] = name
        submodel['bounding_box'] = bbox
        submodel['model_index'] = model_index
        submodel['element_count'] = child_element_count
        submodel['hierarchy_index'] = hierarchy_index
        
        print('|{0} ({1})'.format(name, i))
        print('|\tPosition :' + str(matrix['position']))
        print('|\tRotation :' + str(matrix['rotation']))
        print('|\tScale :' + str(matrix['scale']))
        print('|\tBounding Box :' + bb_toString(bbox))
        print('|\tChild Count :' + str(child_element_count))
        print('|\tUnknown :' + str((ued4, ued5, ued6)))
        print('|')
        return submodel
        
    def readElement(names, elements):
        model_index = r_int()
         
        matrix = r_matrix()
        bbox = r_bb()
         
        name_index = r_int()
        name = names[name_index]
        
        
        element_index = r_int()
        parent_index = r_int()
        ued3 = r_int()
        ued4 = r_int()
        ued5 = r_int()
        ued6_0 = r_short()
        ued6_1 = r_short()
        
        element = {}
        element['matrix'] = matrix
        element['bounding_box'] = bbox
        element['name'] = name
        if parent_index >= 0:
            element['parent'] = parent_index
        models[model_index][element_index] = element
        
        print('|{0} ({1})'.format(name, i))
        print('|\tPosition :' + str(matrix['position']))
        print('|\tRotation :' + str(matrix['rotation']))
        print('|\tScale :' + str(matrix['scale']))
        print('|\tBounding Box :' + bb_toString(bbox))
        sayParent = ""
        if 'parent' in element and not elements[parent_index] == 0:
            sayParent = elements[parent_index]['name']
        print('|\tParent :({0}) {1}'.format(parent_index, sayParent))
        print('|\tModel Parent :{0}-{1}'.format(model_index, element_index))
        print('|\tUnknown :' + str((ued3, ued4, ued5)))
        print('|\tUnknown2 :' + str((ued6_0, ued6_1)))
        print('|')
        return element
        
    def readTexture():
        name = r_string()
        tu1 = r_int()
        
        r_ad() #52410000
        r_ad() #52410000
        r_ad() #02000000
        
        name2 = r_string()
        r_ad()
        
        tu2 = r_int()
        tu3 = r_int()
        tu4 = r_int()
        tu5 = r_int()
        tu6 = r_int()
        tu7 = r_int()
        tu8 = r_int()
        tu9 = r_int()
        tu10 = r_int()
        tu11 = r_int()
        tu12 = r_int()
        
        length = r_int()
        height = r_int()
        width = r_int()
        
        tu13 = r_int()
        
        mipmaps = r_int()
        dxt = r_int()
        
        tu14 = r_int()
        tu15 = r_int()
        
        pitch = int((width * 1024 + 7)/8)
        print('|({0}) {1}'.format(i, name))
        print('|\t'+to_hex(dxt))
        print('|\tData {0}x{1} M:{2} P:{3} [0x{4}]'.format(width, height, mipmaps, pitch, length))
        print('|\tUnknown1 :0x{0}'.format(to_hex(tu1)))
        print('|\tUnknown2.1 :{0} {1} {2} {3} {4}'.format(tu2, tu3, tu4, tu5, tu6))
        print('|\tUnknown2.2 :{0} {1} {2} {3} {4}'.format(tu7, tu8, tu9, tu10, tu11))
        print('|\tUnknown3 :0x{0}'.format(to_hex(tu12)))
        print('|\tUnknown4 :{0}'.format(tu13))
        print('|\tUnknown4 :{0} {1}'.format(tu14, tu15))
        print('|')
        
        tex_data = reader.read(length - 0x1c)
        
        texture = {}
        texture['name'] = name
        texture['name2'] = name2
        texture['dxt'] = dxt
        texture['width'] = width
        texture['height'] = height
        texture['length'] = length
        texture['mipmaps'] = mipmaps
        texture['pitch'] = pitch
        texture['data'] = tex_data
        return texture
    
    def readVertex(t):
        if  t == 6:
            x = r_float()
            y = r_float()
            z = r_float()
            return (x, z, y, 0)
        elif t == 8:
            x = r_half()
            y = r_half()
            return (x, y, 0, 0)
        elif t == 9:
            x = r_half()
            y = r_half()
            z = r_half()
            w = r_half()
            return (x, z, y, w)
        elif t == 0xA:
            x = r_byte()
            y = r_byte()
            z = r_byte()
            w = r_byte()
            return (x, y, z, w)
        elif t == 0xB:
            x = r_byte()/255.0
            y = r_byte()/255.0
            z = r_byte()/255.0
            w = r_byte()/255.0
            return (x, y, z, w)
            
    def renderListNode_Cull():
        pass
    def renderListNode_Common():
        pass
    
    sections = []
    
    sections.append((r_string(4), 0, 0)) #..CP
    
    r_sec(8, 3) #Model
    
    r_sec(8, 2) #Header
    r_ad()
    
    r_sec(8, 2) #MdlDat
    
    r_sec(8, 2) #Header
    r_ad()
    
    
    models = [0] * r_int()
    elements = [0] * r_int()
    r_ad()
    model_bb = r_bb()
    
    r_sec(8, 2) #5
    
    nameOffsets = []
    for i in range(r_int() + 1):
        nameOffsets.append(r_int())
    
    print_sec(sections[-1])
    names = [r_cstring() for i in range(1, len(nameOffsets))]
    
    [print('|({1})  {0}'.format(name, i)) for (i,name) in enumerate(names)]
    
    model['names'] = names
    
    r_sec(8, 2) #Models
    
    print_sec(sections[-1])
    for i in range(len(models)):
        models[i] = readSubModel(names)
    
    model['models'] = models
    
    r_sec(8, 1) #Elements
    print()
    print_sec(sections[-1])
    for i in range(len(elements)):
        elements[i] = readElement(names, elements)
    
    model['elements'] = elements
    r_sec(8, 2) #8 Constr
    print_sec(sections[-1])
    
    r_sec(8, 2) #9 Render
    print_sec(sections[-1])
    
    r_sec(8, 2) #10 Render
    print_sec(sections[-1])
    
    r_sec(8, 2) #11 Header
    print_sec(sections[-1])
    r_ad()
    
    r_sec(8, 3) #12 Scene
    print_sec(sections[-1])
    
    r_ad() #ARCH
    r_ad(8) #01000000 00000000
    
    r_ad() #ARCH
    r_ad(8) #00000000 01000000
    
    r_ad(12)  # 52410100 52410000 02000000
    
    r_ad(8) #52410000 00000000
    r_ad(8) #52410000 #52410200
    r_ad(8) #52410000 #00000000
    
    r_ad() #52410000
    
    print('\nARCH Data 0x' + to_hex(r_pos()))
    arch_dats = [0] * r_int()
    for i in range(len(arch_dats)):
        ad1 = r_int()
        ad2 = r_int()
        arch_dats[i] = (ad1, ad2)
        print('|\t ' + str(arch_dats[i]))
    
    
    r_ad(0xc) #FFFFFFFFFFFF
    r_ad(8) #00000000 52410000
    r_ad(0x20) #Unknown
    r_ad(8) #52410000 Unknown
    r_ad() #52410000
    
    ff_Count = r_int()
    r_ad(ff_Count+4)
    
    r_ad(8) #52410000 00000000
    
    r_ad(8) #52410000 00000000
    
    r_ad() #52410000
    
    print('\nVertex Definitions 0x'+to_hex(r_pos()))
    vert_definitions = [0] * r_int()
    for i in range(len(vert_definitions)):
        r_ad()
        
        data = [0] * r_int()
        print('|Definition ({0})'.format(i))
        for j in range(len(data)):
            r_ad()
            type_prefix = r_short()
            offset = r_short()
            data_type = r_int()
            r_ad()
            channel = r_int()
            sub_channel = r_byte()
            
            print('|\t{0}\t{1}-{2}\t{3}-{4}'.format(to_hex(data_type), type_prefix, offset, channel, sub_channel))
            definition = {}
            definition['prefix'] = type_prefix
            definition['offset'] = offset
            definition['type'] = data_type
            definition['channel'] = channel
            definition['sub_channel'] = sub_channel
            data[j] = definition
        vert_definitions[i] = data
    
    model['vert_definitions'] = vert_definitions
    
    r_ad()
    print('\nFX Files 0x'+to_hex(r_pos()))
    fx_files = [0] * r_int()
    for i in range(len(fx_files)):
        r_ad()
        r_ad()
        file_name = r_string()
        
        print('|({0}) {1}'.format(i, file_name))
        
        fx_files[i] = file_name
    
    model['fx_files'] = fx_files
    r_ad()
    r_ad() #52410000
    r_ad() #52410000
    r_ad() #02000000
    
    print('\nTextures 0x' + to_hex(r_pos()))
    textures = [0] * r_int()
    
    for i in range(len(textures)):
        textures[i] = readTexture()
        
    model['textures'] = textures
    
    r_ad(8) #52410000 52410300
    r_ad(8) #52410000 00000000
    r_ad(8) #52410000 00000000
    r_ad(8) #52410000 00000000
    r_ad(8) #52410000 00000000
    r_ad(8) #52410000 00000000
    r_ad() #01000000
    
    r_ad() #52410000
    r_ad(7) #03000000 000002
    r_ad() #52410000
    r_ad() #52410000
    r_ad(8) #52410000 00000000
    r_ad(8) #00000000 00000000

    uvsd1 = r_int()
    r_ad() #52410000
    r_ad() #52410000
    r_ad(8) #02000000 0A000000
    r_ad() #52410000
    r_ad() #52410000
    r_ad(8) #02000000 00000000
    r_ad() #52410000
    
    print('\nVert Streams 0x'+to_hex(r_pos()))
    vertex_streams = [0] * r_int()
    
    for i in range(len(vertex_streams)):
        r_ad(1) #02
        r_ad() #52410100
        r_ad() #52410000
        
        byte_length = r_int()
        
        r_ad()
        print('|Vert Stream ({0})'.format(i))
        print('|\tDefinitions:')
        vert_stream_definitions = [0] * r_int()
        for j in range(len(vert_stream_definitions)):
            r_ad()
            data_type = r_int()
            unknown_vert_stream_data = r_int()
            channel = r_int()
            sub_channel = r_int()
            
            definition = {}
            definition['type'] = data_type
            definition['unknown'] = unknown_vert_stream_data
            definition['channel'] = channel
            definition['sub_channel'] = sub_channel
            vert_stream_definitions[j] = definition
            
            print('|\t\t{0}\t{1}\t{2}-{3}'.format(to_hex(data_type), unknown_vert_stream_data, channel, sub_channel))
        
        r_ad()
        vert_data_offsets = [r_short() for j in range(r_int())]
        
        vertex_count = r_int()
        r_ad()
        vertex_stream_length = r_int()
        r_ad()
        r_ad(vertex_stream_length)
        if i == len(vertex_streams) - 1:
            reader.advance_to(0x4152)
        else:
            reader.advance_to(0x1415202)
        
        r_ad(-vertex_stream_length)
        
        start = r_pos()
        
        verticies = []
        for j in range(vertex_count):
            
            vertex = []
            
            for definition in vert_stream_definitions:
                t = definition['type']
                vertex.append(readVertex(t))
                
            verticies.append(vertex)
            
        print('|\tData :0x{0} [0x{1}]'.format(to_hex(start), to_hex(vertex_stream_length)))
        print('|\tCount :{0}'.format(vertex_count))
        print('|\tBytes :{0}'.format(byte_length))
        print('|')
        
        stream = {}
        stream['verticies'] = verticies
        stream['bytes'] = byte_length
        stream['count'] = vertex_count
        stream['length'] = vertex_stream_length
        stream['start'] = start
        stream['definition'] = vert_stream_definitions
        vertex_streams[i] = stream
    
    model['vertex_streams'] = vertex_streams
    r_ad()
    print('\nFace Streams 0x' + to_hex(r_pos()))
    face_streams = [0] * r_int()
    
    for i in range(len(face_streams)):
        r_ad(1) #02
        r_ad() #52410100
        
        face_count = r_int()
        
        r_ad() #00000000
        r_ad() #52410000
        
        face_stream_length = r_int()
        
        r_ad() #10000000
        
        r_ad(face_stream_length)
        
        if i == len(face_streams) - 1:
            reader.advance_to(0x4152)
        else:
            reader.advance_to(0x1415202)
        
        r_ad(-face_stream_length)
        start = r_pos()
        
        faces = [r_short() for j in range(face_count)]
        
        print('|\tFace Stream ({0})'.format(i))
        print('|\tStart :0x{0}'.format(to_hex(start)))
        print('|\tLength :0x{0}'.format(to_hex(face_stream_length)))
        print('|\tCount :{0}'.format(face_count))
        print('|')
        
        stream = {}
        stream['faces'] = faces
        stream['start'] = start
        stream['length'] = face_stream_length
        stream['count'] = face_count
        face_streams[i] = stream
    
    r_ad() #52410000
    
    model['face_streams'] = face_streams
    
    print('\nRendering Data 0x' + to_hex(r_pos()))
    rendering_data = [0] * r_int()
    print('\nLen ' + str(len(rendering_data)))
    for i in  range(len(rendering_data)):
        r_ad(1) #03
        node_name = r_string()
        
        if(node_name == "RenderingData::CullNode"):
            pass
        elif(node_name == "RenderingData::RenderListNode_Common"):
            pass
        
        common = r_int() #52410200
        if common == 0x4152:
            r_ad(0x58)
            ff_count = r_int()
            r_ad(ff_count + 4)
            break
        
        r_ad() #52410000
        modelName = r_string()
        r_ad() #52410000
        udat = [(r_int(), r_int()) for j in range(r_int())]
        
        urd1 = r_int()
        urd2 = r_int()
        urd3 = r_int()
        urd4 = r_int()
        
        r_ad()
        
        bbox = r_bb()
        urdf1 = r_float()
        urdf2 = r_float()
        
        r_ad()
        
        urd5 = r_int()
        
        r_ad()
        
        print('|Rendering Data ({0}) {1}'.format(i, node_name))
        print('|\tCommon :0x{0}'.format(common))
        print('|\tModel :{0}'.format(modelName))
        print('|\tUnknown1 :{0}'.format(udat))
        print('|\tUnknown2 :{0} {1} {2} {3}'.format(urd1, urd2, urd3, urd4))
        print('|\tBounding Box :' + bb_toString(bbox))
        print('|\tUnknown3 :{0} {1}'.format(urdf1, urdf2))
        print('|\tUnknown4 :{0}'.format(urd5))
        print('|')
        
        ff_count = r_int()
        r_ad(ff_count+4)
        r_ad() #52410000
        r_ad() #00000000
        r_ad() #52410000
        r_ad() #00000000
    
    model['rendering_data'] = rendering_data
    
    r_ad() #52410000
    r_ad() #00000000
    r_ad() #52410000
    r_ad() #00000000
    r_ad() #52410000
    r_ad() #52410000
    
    print('\nShaders 0x' + to_hex(r_pos()))
    shaders = [0] * r_int()
    print(len(shaders))
    
    for i in range(len(shaders)):
        r_ad()
        name_length = r_int()
        if name_length == 0:
            r_ad()
            urdv1 = (r_int(), r_int(), r_int())
            r_ad()
            urdv2 = (r_int(), r_int(), r_int())
            continue
        fx_name = r_string(name_length)
        r_ad()
        
        print('|Shader ({0}) {1}'.format(i, fx_name))
        parameters = [{}] * r_int()
        
        print('|\tParams:')
        for param in parameters:
            r_ad()
            param_name = r_string()
            param_values = [r_int(), r_int()]
        
            print('|\t\t {0}:{1}'.format(param_name, param_values))    
            param['name'] = param_name
            param['values'] = param_values
        
        extra_params = [r_int() for j in range(2)]
        r_ad()
        
        other_params = [r_short() for j in range(r_int() + 1)]
        print('|\tExtra Params :{0}'.format(extra_params))
        print('|\tOther Params :{0}'.format(other_params))
        print('|')
        r_ad(6)
    
    model['shaders'] = shaders
    
    r_ad()
    r_ad()
    
    r_ad()
    
    print('\nMeshes 0x' + to_hex(r_pos()))
    meshes = [0] * r_int()
    for i in range(len(meshes)):
        r_ad()
        material_index = r_int()
        definition_index = r_int()
        face_type = r_int()
        face_stream_index = r_int()
        object_index = r_short()
        mud2 = r_short()
        
        r_ad()
        mud3 = r_int()
        mud4 = r_int()
        
        r_ad()
        mud5 = r_int()
        mud6 = r_int()
        
        r_ad() #52410000
        r_ad() #01000000
        r_ad() #05000000
        r_ad() #00000000
        r_ad() #00000000
        r_ad() #01000000
        r_ad() #00000000
        
        r_ad() #52410000
        
        mesh_data_1 = [0] * r_int()
        for j in range(len(mesh_data_1)):
            r_ad() #52410000
            data = {}
            data['face_offset'] = r_int()
            data['face_count'] = r_int()
            data['vert_offset'] = r_int()
            data['vert_count'] = r_int()
            mesh_data_1[j] = data
            
        r_ad() #52410000
        
        mesh_data_2 = [0] * r_int()
        for j in range(len(mesh_data_2)):
            r_ad() #52410000
            data = {}
            data['u1'] = r_int()
            data['u2'] = r_int()
            data['vOffset'] = r_int()
            data['u4'] = r_int()
            
            r_ad()
            data['u5'] = r_int()
            data['u6'] = r_int()
            mesh_data_2[j] = data
        
        mesh = {}
        mesh['definition'] = definition_index
        mesh['face_type'] = face_type
        mesh['face_stream_index'] = face_stream_index
        mesh['object_index'] = object_index
        mesh['data1'] = mesh_data_1
        mesh['data2'] = mesh_data_2
        mesh['material_index'] = material_index
        mesh['index'] = i
        meshes[i] = mesh
        
        print('|Mesh {0}'.format(i))
        print('|\tMaterial :({0}) {1}'.format(material_index, fx_files[material_index]))
        print('|\tDefinition :({0}) {1}'.format(definition_index, ''.join([to_hex(definition['type']) for definition in vert_definitions[definition_index]])))
        print('|\tFace Type :{0} (Triangle|TStrip)'.format(face_type))
        print('|\tFace Stream :{0}'.format(face_stream_index))
        print('|\tObject :({0}) {1}'.format(object_index, elements[object_index]['name']))
        print('|\tUnknown2 :{0}'.format(mud2))
        print('|\tUnknown3 :{0} {1}'.format(mud3, mud4))
        print('|\tUnknown4 :{0} {1}'.format(mud5, mud6))
        print('|\tData1 :')
        [print('|\t\tFaces :({0})-({1}) Verts :({2})-({3})'.format(dats['face_offset'], dats['face_count'], dats['vert_offset'], dats['vert_count'])) for dats in mesh_data_1]
        print('|\tData2 :')
        [print('|\t\tUnknown1 :({0})-({1}) Verts :({2})-({3}) Unknown :({4})-({5})'.format(dats['u1'], dats['u2'], dats['vOffset'], dats['u4'], dats['u5'], dats['u6'])) for dats in mesh_data_2]
        print('|')
    
    model['meshes'] = meshes
    
    #bpy.context.scene['last_model'] = model
    
    return model


def create_model_from_data(model, swap_faces):
    
    directory = bpy.path.abspath("//")
    saved = directory != ''
    if not saved:
        self.report({'WARNING'}, "The blend file is not saved. Textures will not be downloaded.")
    elif not os.path.exists(directory+"textures"):
        os.makedirs(directory+"textures")
    
    textures = []
    for tx in model['textures']:
        if saved:    
            with open(directory+"textures\\"+tx['name']+".dds", 'wb') as textureFile:
            
                def write(value, len = 4):
                    textureFile.write(value.to_bytes(len, byteorder='little'))
                
                textureFile.write(b'DDS ')                  #Magic Header
                write(0x7c)                                 #Header Size
                write(0xa1007)                              #dw Flags 0xa1007
                write(tx['width'])                             #Height
                write(tx['height'])                            #Width
                write(tx['pitch'])                                #Pitch
                write(0x0)                                  #Depth
                write(tx['mipmaps'])                          #MipMapCount
                write(0x0, 44)                              #dwReserved1[11]
            
                #pixel format
            
                write(0x20)                                 #Pixel Format Size
                write(0x4)                                  #Pixel Format Flags
                write(tx['dxt'])                               #DXT[1?]
                write(0x0)                                  #Red Bit Mask
                write(0x0)                                  #Blue Bit Mask
                write(0x0)                                  #Green Bit Mask
                write(0x0)                                  #Alpha Bit Mask
            
                #Back to regular Header
            
                write(0x0)                                  #Caps
                write(0x401008)                             #Caps2
            
                write(0x0)                                  #Unused Caps3
                write(0x0)                                  #Unused Caps4
                write(0x0)                                  #Unused Reserved2
            
                write(0x0)                                  #I have no idea
            
                textureFile.write(tx['data']) #textureData
            
            tex = bpy.ops.image.open(filepath=directory+"textures\\"+tx['name']+".dds")
            textures.append(tex)
    
    materials = []
    for fx_name in model['fx_files']:
        fx = fx_name.split('.')[0]
        mat = bpy.data.materials.get(fx)
        if(mat is None):
            mat = bpy.data.materials.new(fx)
        materials.append(mat)
    
    defined_vertex_streams = {}
    
    for vs in model['vertex_streams']:
        vs_vert_definition = ''.join([to_hex(definition['type']) for definition in vs['definition']])
        defined_vertex_streams[vs_vert_definition] = vs
    
    objects = [None] * len(model['elements'])
    
    for mesh in model['meshes']:
        definition = [item for item in model['vert_definitions'][mesh['definition']] if item['prefix'] == 0]
        
        string_definition = ''.join([to_hex(item['type']) for item in definition])
        vert_stream = defined_vertex_streams[string_definition]
        
        if swap_faces == True: 
            face_stream = model['face_streams'][1-mesh['face_stream_index']]
        else:
            face_stream = model['face_streams'][mesh['face_stream_index']]    
        
        
        if objects[mesh['object_index']] == None:
            objects[mesh['object_index']] = {'bm':bmesh.new(), 'materials':[]}
        
        object = objects[mesh['object_index']]
        bm = object['bm']
        
        vertex_colors = []
        if len(definition) > 2:
            for i in range(len(definition) - 2):
                fc = bm.verts.layers.float_color.get('Vert_Data_' + str(i), None)
                if fc == None:
                    fc = bm.verts.layers.float_color.new('Vert_Data_' + str(i))
                
                vertex_colors.append(fc)
            
        fc = bm.verts.layers.float_color.verify()
        
        verts = []
        
        vert_offset = mesh['data1'][0]['vert_offset']
        vert_start = int(mesh['data2'][0]['vOffset']/vert_stream['bytes']) + vert_offset
        vert_count = mesh['data1'][0]['vert_count']
        vert_end = vert_start + vert_count
        
        for vertex_data in vert_stream['verticies'][vert_start:vert_end]:
            
            vert = bm.verts.new(vertex_data[0][0:3])
            if(len(vertex_data) > 1):
                vert.normal = vertex_data[1][0:3]
            for i,fc in enumerate(vertex_colors):
                vert[fc] = vertex_data[i+2]
            
            verts.append(vert)


        faces = []
        
        face_start = mesh['data1'][0]['face_offset']
        face_count = mesh['data1'][0]['face_count'] 
        
        
        face_end = face_start + face_count 
        
        stream_faces = face_stream['faces']
        
        desired_material = materials[mesh["material_index"]]
        if not desired_material in object['materials']:
            object['materials'].append(desired_material)
            material_index = len(object['materials']) - 1
        else:
            material_index = object['materials'].index(desired_material)
        
        uv_1 = bm.loops.layers.uv.get('UV1', None)
        if uv_1 == None:
            uv_1 = bm.loops.layers.uv.new('UV1')
        
        uv_2 = bm.loops.layers.uv.get('UV2', None)
        if uv_2 == None:
            uv_2 = bm.loops.layers.uv.new('UV2')
        
        def create_face(v1, v2, v3):
            try:
                new_face = bm.faces.new([v1, v2, v3])
                new_face.material_index = material_index
            
                if len(vertex_colors) > 0:  
                    for loop in new_face.loops:
                        uv = loop.vert[vertex_colors[0]]
                        loop[uv_1].uv[0] = uv[0]
                        loop[uv_1].uv[1] = 1-uv[2]
                        loop[uv_2].uv[0] = uv[1]
                        loop[uv_2].uv[1] = 1-uv[3]
            
                faces.append(new_face)
            except:
                print("Duplicate face:")
                #print("|\tMeshDefinition: {0}".format(string_definition))
                #print("|\tMeshIndex: {0}".format(meshes.index(mesh)))
                #print("|\tVertStream: {0}".format(vertex_streams.index(vert_stream)))
                #print("|\tFaceStream: {0}".format(face_streams.index(face_stream)))
                #print("|\tV1: {0}".format(v1.co))
                #print("|\tV2: {0}".format(v2.co))
                #print("|\tV3: {0}".format(v3.co))
                
        if mesh['face_type'] == 0:
            for i in range(face_start, face_end, 3):
                i1 = stream_faces[i] - vert_offset
                i2 = stream_faces[i+1] - vert_offset
                i3 = stream_faces[i+2] - vert_offset
                
                create_face(verts[i1], verts[i2], verts[i3])
        if mesh['face_type'] == 1:
            for i in range(face_start, face_end - 2):
                i1 = stream_faces[i] - vert_offset
                i2 = stream_faces[i+1] - vert_offset
                i3 = stream_faces[i+2] - vert_offset
                
                if i1 == i2 or i2 == i3 or i3 == i1:
                    continue
                if (i-face_start)%2 == 1:
                    create_face(verts[i1], verts[i2], verts[i3])
                else:
                    create_face(verts[i1], verts[i3], verts[i2])
                
    
    linked_objects = []
    for i, object in enumerate(objects):
        element = model['elements'][i]
        
        if not object == None:
            bm = object['bm']
            
            object_mesh = bpy.data.meshes.new(element['name'])
            
            bm.to_mesh(object_mesh)
            object_mesh.update()
            
            linked_object = bpy.data.objects.new(element['name'], object_mesh)
            [linked_object.data.materials.append(mat) for mat in object['materials']]
            bm.free()
        else:
            linked_object = bpy.data.objects.new(element['name'], None)
            linked_object.empty_display_size = 0.2
            linked_object.empty_display_type = 'SPHERE'
        
        linked_object.location = element['matrix']['position']
        
        if 'parent' in element:
            linked_object.parent = linked_objects[element['parent']]
            linked_object.matrix_parent_inverse = linked_object.parent.matrix_world.inverted()
        
        bpy.context.collection.objects.link(linked_object)
        linked_objects.append(linked_object)

#---------------------------------------------------------------------------------------------------
#---------------------------------------------------------------------------------------------------
#---------------------------------------------------------------------------------------------------
#---------------------------------------------------------------------------------------------------
#---------------------------------------------------------------------------------------------------

class ImportCPModelData(Operator, ImportHelper):
    """This appears in the tooltip of the operator and in the generated docs"""
    bl_idname = "import_cpmodel.data"
    bl_label = "Import CPModel"

    # ImportHelper mixin class uses this
    filename_ext = ".model"

    filter_glob: StringProperty(
        default="*.model",
        options={'HIDDEN'},
        maxlen=255,  # Max internal buffer length, longer would be clamped.
    )

    swap_faces: BoolProperty(
        name="Swap Faces",
        description="Some models have faces stored strangely. If the import doesent work the first time, try this.",
        default=False,
    )

    def execute(self, context):
        return import_cpmodel(self, context, self.filepath, self.swap_faces)

def menu_func_import(self, context):
    self.layout.operator(ImportCPModelData.bl_idname, text="Import CPModel (.model)")


def register():
    bpy.utils.register_class(ImportCPModelData)
    #bpy.types.TOPBAR_MT_file_import.append(menu_func_import)


def unregister():
    bpy.utils.unregister_class(ImportCPModelData)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)

if __name__ == "__main__":
    register()
    bpy.ops.import_cpmodel.data('INVOKE_DEFAULT')
