import bpy
import bmesh
import os
import math

bl_info = {
    "name" : "BlurImportExport",
    "author" : "TimberStalker",
    "description" : "",
    "blender" : (2, 80, 0),
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
    
    def read(self, amount) -> bytes:
        end = self.pointer+amount
        temp = self.data[self.pointer:end]
        self.pointer = end
        return temp

    def read_int(self) -> int:
        #"""Read an integer from the file and advance the pointer 4 bytes"""
        return int.from_bytes(self.read(4), "little")

    def read_short(self) -> int:
        #"""Read a short from the file and advance the pointer 2 bytes"""
        return int(np.frombuffer(self.read(2), np.short))

    def read_float(self) -> float:
        #"""Read a float from the file and advance the pointer 4 bytes"""
        return float(np.frombuffer(self.read(4), np.float32))

    def read_half(self) -> float:
        #"""Read a half from the file and advance the pointer 2 bytes"""
        return float(np.frombuffer(self.read(2), np.float16))

    def read_string(self, stringLength = 0) -> str:
        #"""Read a string from the file and advance the pointer [stringLength] bytes. 
        #If no string length is given, the function will first read an integer describing the length and then read the string"""
        if stringLength == 0:
            return self.read(self.read_int()).decode('utf-8')
        else:
            return self.read(stringLength).decode('utf-8')
        
    def read_matrix(self):
        scalex = self.read_float() #1
        
        shear1 = self.read_float() #1
        shear2 = self.read_float() #1
        shear3 = self.read_float() #1
        
        scalez = self.read_float() #1
        
        shear4 = self.read_float() #1
        shear5 = self.read_float() #1
        shear6 = self.read_float() #1
        
        scaley = self.read_float() #1
        
        rotationx = math.atan2(shear6, scaley)
        rotationz = math.atan2(-shear5, math.sqrt(shear6**2 + scaley**2))
        rotationy = math.atan2(shear3, scalex)
        
        positionx = self.read_float()
        positionz = self.read_float()
        positiony = self.read_float()
        
        return {'position':[positionx, positiony, positionz], 'scale':[scalex, scaley, scalez], 'rotation':[rotationx, rotationy, rotationz]}
    

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

def read_cpmodel_data(self, context, filepath, use_some_setting):
    directory = bpy.path.abspath("//")
    saved = directory != ''
    if not saved:
        self.report({'WARNING'}, "The blend file is not saved. Textures will not be downloaded.")
    elif not os.path.exists(directory+"textures"):
        os.makedirs(directory+"textures")
    
    reader = Reader(filepath)
    
    reader.advance() #..CP
    reader.read_string(8) # Model...
    
    fileEnd = reader.read_int()
    reader.advance(4)

    reader.read_string(8) # Header..
    headerSize = reader.read_int()
    reader.advance(8)

    reader.read_string(8) # MdlDat..
    modelDataEnd = reader.read_int()
    reader.advance(4)

    reader.read_string(8) # Header..
    modelDataHeaderEnd = reader.read_int()
    reader.advance(8)

    modelCount = reader.read_int()
    elementCount = reader.read_int()
    reader.advance(4)
    reader.advance(0x18) # Unknown Data
    
    reader.read_string(8) # StrTab..
    unknown = reader.read_int()
    reader.advance(4)

    stringTableCount = reader.read_int()
    nameOffsets = []
    for i in range(0, stringTableCount + 1):
        nameOffsets.append(reader.read_int())
        #int[] nameOffsets = Enumerable.Range(0, stringTableCount + 1).Select(_ => reader.read_int()).ToArray()
    
    stringTable = []
    for i in range(0, stringTableCount):
        name = reader.read_string(nameOffsets[i + 1] - nameOffsets[i] - 1)
        reader.advance(1)
        stringTable.append(name)
        print(str(i)+' '+name)

    reader.read_string(8) # Models..
    modelsEnd = reader.read_int()
    reader.advance()
    
    for i in range(0, modelCount):
        
        matrix = reader.read_matrix()
        
        unknownList = reader.read(24) # unknown Data Possibly id
        
        nameIndex = reader.read_int()
        
        unknownElementData14 = reader.read_int()
        unknownElementData15 = reader.read_int()
        unknownElementData16 = reader.read_int()
        unknownElementData17 = reader.read_int()
        unknownElementData18 = reader.read_int()
        unknownElementData19 = reader.read_int()
        
        name = stringTable[nameIndex]
        
        print(i)
        print(matrix['position'])
        print(matrix['rotation'])
        print(matrix['scale'])
        
        print(unknownList)
        
        print("{0} {1} {2} {3} {4} {5}".format(unknownElementData14, unknownElementData15, unknownElementData16, unknownElementData17, unknownElementData18, unknownElementData19))
        
        print('\n')
        
        modelObject = bpy.data.objects.new("Model {0}".format(name), None)
    
        modelObject.empty_display_size = 0.1
        modelObject.empty_display_type = 'SPHERE'
        
        modelObject.location = matrix['position']
        modelObject.rotation_euler = matrix['rotation']
        modelObject.scale = matrix['scale']
        
        bpy.context.collection.objects.link(modelObject)
    #reader.advance(modelsEnd-12)

    reader.read_string(8) # Element.
    elementEnd = reader.read_int()
    
    object_dats = []
    for i in range(0, elementCount):
        reader.read_int()
        reader.advance() #00000000
        
        matrix = reader.read_matrix()
        
        unknownList = reader.read(24) # unknown Data Possibly id
        
        nameIndex = reader.read_int()
        
        unknownElementData14 = reader.read_int()
        unknownElementData15 = reader.read_int()
        unknownElementData16 = reader.read_int()
        unknownElementData17 = reader.read_int()
        unknownElementData18 = reader.read_int()
        
        objectName = stringTable[nameIndex]
        
        print(i)
        print(objectName)
        
        print(matrix['position'])
        print(matrix['rotation'])
        print(matrix['scale'])
        
        print(unknownList)
        
        print("{0} {1} {2} {3} {4}".format(unknownElementData14, unknownElementData15, unknownElementData16, unknownElementData17, unknownElementData18))
        
        print('\n')
        
        object_dats.append({'name':objectName,'matrix':matrix})
    
    reader.advance() #FFFFFFFF
    
    print("Constr "+str(reader.position()));
    reader.read_string(8) # Constr..
    reader.advance() # Constr Header Size
    reader.advance()

    print("Render "+str(reader.position()));
    reader.read_string(8) # Render..
    reader.advance() # Unknown
    reader.advance()

    print("Render "+str(reader.position()));
    reader.read_string(8) # Render..
    reader.advance() # Unknown
    reader.advance()

    print("Header "+str(reader.position()));
    reader.read_string(8) # Header..
    reader.read_int() # Header Size
    reader.advance(8)
    
    reader.read_string(8) # Scene...
    sceneEnd = reader.read_int()
    reader.advance()
    reader.read_string(4) # ARCH
    reader.advance(8) # 01000000 00000000

    reader.read_string(4) # ARCH
    reader.advance() # 00000000 01000000
    unknownArch = reader.read_int()
    
    reader.advance() # 52410100
    reader.advance() # 52410000
    reader.advance() # 02000000
    
    reader.advance() #52410000
    reader.advance() #00000000
    
    reader.advance() #52410000
    reader.advance() #52410200
    
    reader.advance() #52410000
    reader.advance() #00000000
    
    reader.advance() #52410000

    unknownCount = reader.read_int()
    for i in range(0, unknownCount):
        reader.advance(8)

    reader.advance(0xc) #FFFFFFFFFFFF
    reader.advance(8) #00000000 52410000
    reader.advance(0x20) #Unknown
    reader.advance(8) #52410000 Unknown
    reader.advance() #52410000

    ff_Count = reader.read_int()
    reader.advance(ff_Count+4)
    
    reader.advance() #52410000
    reader.advance() #00000000
    
    reader.advance() #52410000
    reader.read_int() #00000000
    
    reader.advance() #52410000

    print("Count "+str(reader.position()));
    meshGroupDevinitionsCount = reader.read_int()
    print(meshGroupDevinitionsCount)
    meshGroupDefinitions = []
    for i in range(0, meshGroupDevinitionsCount):
        reader.advance() #52410000
        definitionLength = reader.read_int()
        meshDefinition = ""
        for j in range(0, definitionLength):
            reader.advance() #52410000
            unknownVertData1 = reader.read_short()
            unknownVertData2 = reader.read_short()
            vertDataType = reader.read_int()
            if unknownVertData1 != 3:
                meshDefinition += to_hex(vertDataType)
            
            reader.advance() #00000000
            
            unknownVertData3 = reader.read_int()
            reader.advance(1) # unknownVertData3
        print(meshDefinition)
        meshGroupDefinitions.append(meshDefinition)

    reader.read_int() #52410000
    fxNamesCount = reader.read_int()
    for i in range(0, fxNamesCount):
        reader.advance() #52410000
        reader.advance() #52410000
        fxName = reader.read_string()

    unknown1 = reader.read_int()
    reader.advance() #52410000
    reader.advance() #52410000
    reader.advance() #02000000

    textureCount = reader.read_int()
    print("texture count :" + str(textureCount))
    for i in range(0, textureCount):
        texName = reader.read_string()
            
        texUnknown = reader.read_int()
        reader.advance() #52410000
        reader.advance() #52410000
        reader.advance() #02000000
        texName2 = reader.read_string()
        reader.advance() #52410100
        texUnknown2 = reader.read_int() #00000000
        texUnknown3 = reader.read_int()
        texUnknown4 = reader.read_int()
        
        texUnknown5 = reader.read_int() #01000000
        texUnknown6 = reader.read_int()
        texUnknown7 = reader.read_int()
        
        texUnknown8 = reader.read_int() #00000000
        texUnknown9 = reader.read_int()
        texUnknown10 = reader.read_int()
        texUnknown11 = reader.read_int()
        
        texUnknown13 = reader.read_int()
        #reader.advance(0x2c)
        texLength = reader.read_int()
        texHeight = reader.read_int()
        texWidth = reader.read_int()
        texUnknown14 = reader.read_int()
        mipmapCount = reader.read_int()
        dxtVer = reader.read_int()
        texUnknown15 = reader.read_int()
        texUnknown16 = reader.read_int()
        #reader.advance(texLength - 0x1c)
        
        pitch = int((texWidth * 1024 + 7)/8)
        
        if saved:                
            with open(directory+"textures\\"+texName+".dds", 'wb') as textureFile:
            
                def write(value, len = 4):
                    textureFile.write(value.to_bytes(len, byteorder='little'))
                
                textureFile.write(b'DDS ')                  #Magic Header
                write(0x7c)                                 #Header Size
                write(0xa1007)                              #dw Flags 0xa1007
                write(texWidth)                             #Height
                write(texHeight)                            #Width
                write(pitch)                                #Pitch
                write(0x0)                                  #Depth
                write(0x9)                          #MipMapCount
                write(0x0, 44)                              #dwReserved1[11]
            
                #pixel format
            
                write(0x20)                                 #Pixel Format Size
                write(0x4)                                  #Pixel Format Flags
                write(dxtVer)                               #DXT[1?]
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
            
                textureFile.write(reader.read(texLength - 0x1c)) #textureData
            
            bpy.ops.image.open(filepath=directory+"textures\\"+texName+".dds")

    reader.advance(8) #52410000 52410300
    reader.advance(8) #52410000 00000000
    reader.advance(8) #52410000 00000000
    reader.advance(8) #52410000 00000000
    reader.advance(8) #52410000 00000000
    reader.advance(8) #52410000 00000000
    reader.advance() #01000000
    
    reader.advance() #52410000
    reader.advance(7) #03000000 000002
    reader.advance() #52410000
    reader.advance() #52410000
    reader.advance(8) #52410000 00000000
    reader.advance(8) #00000000 00000000

    unknownMeshData1 = reader.read_int()
    reader.advance() #52410000
    reader.advance() #52410000
    reader.advance(8) #02000000 0A000000
    reader.advance() #52410000
    reader.advance() #52410000
    reader.advance(8) #02000000 00000000
    reader.advance() #52410000

    meshGroupCount = reader.read_int()
    print("mesh groups count :" + str(meshGroupCount))
    meshGroups = {}
    for i in range(0, meshGroupCount):
        reader.advance(1) #02
        reader.advance() #52410100
        reader.advance() #52410000
        vertexBytes = reader.read_int()
        reader.advance() #52410000

        vertDataLength = reader.read_int()
        meshDefinition = ""
        for j in range(0, vertDataLength):
            reader.read_int() #52410000
            vertDataType = reader.read_int()
            reader.read_int() #00000000
            unknownVertData1 = reader.read_int()
            unknownVertData2 = reader.read_int()
            meshDefinition += to_hex(vertDataType)
        
        reader.advance() #52410000
        vertDataSplits = reader.read_int() #This is always the same as vertDataLength
        #reader.advance(vertDataSplits * 2) #This is important. I just cant read shorts in .Net 5
        print(vertDataSplits)
        vertDataLengths = []
        for j in range(0, vertDataSplits):
            vertDataLengths.append(reader.read_short())

        vertexCount = reader.read_int()
        reader.advance() #52410000
        vertexLength = reader.read_int()
        reader.advance() #10000000
        reader.advance(vertexLength)

        if i == meshGroupCount - 1:
            reader.advance_to(0x4152)
        else:
            reader.advance_to(0x1415202)

        verticies = []
        reader.advance(-vertexLength)

        for j in range(0, vertexCount):
            vertSplitLength = 0
            vertData = []
            
            if vertDataSplits > 1:
                vertSplitLength = vertDataLengths[1]
            else:
                vertSplitLength = vertexBytes
                
            if vertSplitLength == 12:
                x = reader.read_float()
                y = reader.read_float()
                z = reader.read_float()
                verticies.append((x, z, y))
                reader.advance(vertexBytes-12)
            else:
                x = reader.read_half()
                y = reader.read_half()
                z = reader.read_half()
                verticies.append((x, z, y))
                reader.advance(vertexBytes-6)

        #vertexStartPoint = reader.Offset - vertexLength
        meshGroups[meshDefinition] = (vertexBytes, verticies)
        
    print("read mesh groups")
    reader.advance() #52410000
    faceStreamCount = reader.read_int()
    print("face stream count :" + str(faceStreamCount))
    faceStreams = []
    print("\n")
    for i in range(0, faceStreamCount):
        reader.advance(1) #02
        reader.advance() #52410100
        faceCount = reader.read_int()
        reader.advance() #00000000
        reader.advance() #52410000
        faceBytesLength = reader.read_int()
        reader.advance() #10000000
        reader.advance(faceBytesLength)
        if i == faceStreamCount - 1:
            reader.advance_to(0x4152)
        else:
            reader.advance_to(0x1415202)
        
        reader.advance(-faceBytesLength)
        faces = []
        for j in range(0, faceCount):
            faces.append(reader.read_short())
            
        faceStreams.append(faces)
        #reader += faceBytesLength
    print("read faces")
    reader.advance() #52410000
    renderingDataCount = reader.read_int()
    print("rendering data count :" + str(renderingDataCount))
    for i in range(0, renderingDataCount):
        reader.advance(1) #03
        cullNodeName = reader.read_string()
        common = reader.read_int() #52410200
        if(common == 0x4152):
            reader.advance(0x58)
            ff_count1 = reader.read_int()
            reader.advance(ff_count1 + 4)
            break
        
        reader.advance() #52410000
        modelName = reader.read_string()
        reader.advance() #52410000
        unknownCount2 = reader.read_int()
        for j in range(0, unknownCount2):
            unknownRenderData1 = reader.read_int()
            unknownRenderData2 = reader.read_int()
        
        reader.advance() #FFFFFFFF
        reader.advance(0x3c)

        ff_count = reader.read_int()
        reader.advance(ff_count+4)
        reader.advance() #52410000
        reader.advance() #00000000
        reader.advance() #52410000
        reader.advance() #00000000
    print("read rendering data")
    reader.advance() #52410000
    reader.advance() #00000000
    reader.advance() #52410000
    reader.advance() #00000000
    reader.advance() #52410000
    unknownCount3 = reader.read_int() #52410000
    reader.advance_to(0x14152)
    reader.advance(-4)
    meshCount = reader.read_int()
    print(str(meshCount)+" meshes")
    
    #mainCollection = bpy.data.collections.new(filepath.split('\\')[-1].split('.')[0])
    parentObject = bpy.data.objects.new(filepath.split('\\')[-1].split('.')[0], None)
    
    parentObject.empty_display_size = 2
    parentObject.empty_display_type = 'PLAIN_AXES'
    
    bpy.context.collection.objects.link(parentObject)
    
    objectGroups = {}
    for i in range(0, meshCount):
        reader.advance() # 52410100
        meshUnknown1 = reader.read_int()
        meshIndex = reader.read_int()
        faceType = reader.read_int()
        faceStreamIndex = reader.read_int()
        meshObjectIndex = reader.read_short()
        meshUnknown5 = reader.read_short()
        reader.advance() #52410000
        meshUnknown6 = reader.read_int()
        meshUnknown7 = reader.read_int()
        reader.advance() #52410000
        meshUnknown8 = reader.read_int()
        meshUnknown9 = reader.read_int()
        reader.advance() #52410000
        reader.advance() #01000000
        reader.advance() #05000000
        reader.advance() #00000000
        reader.advance() #00000000
        reader.advance() #01000000
        reader.advance() #00000000
        reader.advance() #52410000
        meshData1Count = reader.read_int()
        
        meshData1 = []
        for j in range(0, meshData1Count):
            reader.advance() #52410000
            faceOffset = reader.read_int()
            faceCount = reader.read_int()
            extraVertOffset = reader.read_int()
            vertexCount = reader.read_int()

            meshData1.append((faceOffset, faceCount, extraVertOffset, vertexCount))
        reader.advance() #52410000
        meshData2Count = reader.read_int()
        meshData2 = []
        for j in range(0, meshData2Count):
            reader.advance() #52410000
            unknownMeshDat1 = reader.read_int()
            unknownMeshDat2 = reader.read_int()
            vertexOffset = reader.read_int()
            unknownMeshDat4 = reader.read_int()
            reader.advance() #52410000
            unknownMeshDat5 = reader.read_int()
            unknownMeshDat6 = reader.read_int()
            meshData2.append((unknownMeshDat1, unknownMeshDat2, vertexOffset, unknownMeshDat4))
        
        k = 0
        
        definition = meshGroupDefinitions[meshIndex]
        group = meshGroups[definition]
        offset = meshData1[k][2]
        vertStart = int(meshData2[0][2]/group[0]) + offset
        vertCount = meshData1[k][3]
        vertEnd = vertStart + vertCount
        
        faceStart = meshData1[k][0]
        faceEnd = faceStart + meshData1[k][1]
        
        
        faces = []
        if faceType == 0:
            for j in range(faceStart, faceEnd, 3):
                index1 = faceStreams[faceStreamIndex][j] - offset
                index2 = faceStreams[faceStreamIndex][j+1] - offset
                index3 = faceStreams[faceStreamIndex][j+2] - offset
                
                faces.append((index1, index3, index2))
                
        elif faceType == 1:
            for j in range(faceStart, faceEnd-2):
                index1 = faceStreams[faceStreamIndex][j] - offset
                index2 = faceStreams[faceStreamIndex][j+1] - offset
                index3 = faceStreams[faceStreamIndex][j+2] - offset
            
                if index1 == index2 or index2 == index3 or index3 == index1:
                    continue
                if (j-faceStart)%2 == 1:
                    faces.append((index1, index2, index3))
                else:
                    faces.append((index1, index3, index2))
                
        meshPart = bpy.data.meshes.new('temp')
        #print(faces)
        meshPart.from_pydata(group[1][vertStart:vertEnd], [], faces)
        if meshPart.validate():
            meshPart.update()
        
        if meshObjectIndex not in objectGroups:
            objectGroups[meshObjectIndex] = bmesh.new()
            
        objectGroups[meshObjectIndex].from_mesh(meshPart)
        bpy.data.meshes.remove(meshPart)
        
    # would normally load the data here
    for objectIndex in range(0, len(object_dats)):
        dat = object_dats[objectIndex]
        object = None
        if objectIndex in objectGroups:
            objectMesh = bpy.data.meshes.new(dat['name'])
            bmesh.ops.remove_doubles(objectGroups[objectIndex], verts=objectGroups[objectIndex].verts, dist=0.0001)
        
            objectGroups[objectIndex].to_mesh(objectMesh)
            object = bpy.data.objects.new(dat['name'], objectMesh)
        else:
            object = bpy.data.objects.new(dat['name'], None)
            object.empty_display_size = 0.2
            object.empty_display_type = 'CUBE'
            
        object.location = dat['matrix']['position']
        
        object.parent = parentObject
        
        bpy.context.collection.objects.link(object)
    return {'FINISHED'}

class ImportSomeData(Operator, ImportHelper):
    """This appears in the tooltip of the operator and in the generated docs"""
    bl_idname = "import_test.some_data"
    bl_label = "Import Some Data"

    # ImportHelper mixin class uses this
    filename_ext = ".model"

    filter_glob: StringProperty(
        default="*.model",
        options={'HIDDEN'},
        maxlen=255,  # Max internal buffer length, longer would be clamped.
    )

    # List of operator properties, the attributes will be assigned
    # to the class instance from the operator settings before calling.
    use_setting: BoolProperty(
        name="Example Boolean",
        description="Example Tooltip",
        default=True,
    )

    type: EnumProperty(
        name="Example Enum",
        description="Choose between two items",
        items=(
            ('OPT_A', "First Option", "Description one"),
            ('OPT_B', "Second Option", "Description two"),
        ),
        default='OPT_A',
    )

    def execute(self, context):
        return read_cpmodel_data(self, context, self.filepath, self.use_setting)

def menu_func_import(self, context):
    self.layout.operator(ImportSomeData.bl_idname, text="Import CPModel (.model)")


def register():
    bpy.utils.register_class(ImportSomeData)
    #bpy.types.TOPBAR_MT_file_import.append(menu_func_import)


def unregister():
    bpy.utils.unregister_class(ImportSomeData)
    #bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)

if __name__ == "__main__":
    register()

    # test call
    bpy.ops.import_test.some_data('INVOKE_DEFAULT')