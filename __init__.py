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

def read_cpmodel_data(self, context, filepath, use_some_setting):
    directory = bpy.path.abspath("//")
    saved = directory != ''
    if not saved:
        self.report({'WARNING'}, "The blend file is not saved. Textures will not be downloaded.")
    elif not os.path.exists(directory+"textures"):
        os.makedirs(directory+"textures")
    
    reader = Reader(filepath)
    
    #..CP
    reader.advance() 
    
    # Model...
    reader.read_string(8)
    fileEnd = reader.read_int()
    reader.advance(4)

    # Header..
    reader.read_string(8) 
    headerSize = reader.read_int()
    reader.advance(8)
    
    # MdlDat..
    reader.read_string(8) 
    modelDataEnd = reader.read_int()
    reader.advance(4)

    # Header..
    reader.read_string(8) 
    modelDataHeaderEnd = reader.read_int()
    reader.advance(8)

    print('Model Data')
    print('|File End: '+to_hex(fileEnd))
    print('|Header Size: '+to_hex(fileEnd))
    print('|Model End: '+to_hex(modelDataEnd))
    print('|Model Header End: '+to_hex(modelDataHeaderEnd))
    print()
    
    modelCount = reader.read_int()
    elementCount = reader.read_int()
    reader.advance(4)
    reader.advance(0x18) # Unknown Data
    
    print('Models: '+str(modelCount))
    print('Elements: '+str(elementCount))
    print()
    
    reader.read_string(8) # StrTab..
    unknown = reader.read_int()
    reader.advance(4)
    

    stringTableCount = reader.read_int()
    nameOffsets = []
    for i in range(0, stringTableCount + 1):
        nameOffsets.append(reader.read_int())
        #int[] nameOffsets = Enumerable.Range(0, stringTableCount + 1).Select(_ => reader.read_int()).ToArray()

    print('Names')
        
    stringTable = []
    for i in range(0, stringTableCount):
        name = reader.read_string(nameOffsets[i + 1] - nameOffsets[i] - 1)
        reader.advance(1)
        stringTable.append(name)
        print('|('+str(i)+')\t'+name)

    reader.read_string(8) # Models..
    modelsEnd = reader.read_int()
    reader.advance()
    
    print()
    print("Models")
    for i in range(0, modelCount):
        
        matrix = reader.read_matrix()
        
        #unknownList = reader.read(24) # unknown Data Possibly id
        ued1 = reader.read_float()
        ued2 = reader.read_float()
        ued3 = reader.read_float()
        ued4 = reader.read_float()
        ued5 = reader.read_float()
        ued6 = reader.read_float()
        
        nameIndex = reader.read_int()
        
        ued14 = reader.read_int()
        ued15 = reader.read_int()
        ued16 = reader.read_int()
        ued17 = reader.read_int()
        ued18 = reader.read_int()
        ued19 = reader.read_int()
        
        name = stringTable[nameIndex]
        
        modelObject = bpy.data.objects.new("Model {0}".format(name), None)
    
        modelObject.empty_display_size = 0.1
        modelObject.empty_display_type = 'SPHERE'
        
        modelObject.location = matrix['position']
        modelObject.rotation_euler = matrix['rotation']
        modelObject.scale = matrix['scale']
        
        print("|" + name + "({0})".format(str(i)))
        print("|\tPos :" + str(matrix['position']))
        print("|\tRot :" + str(matrix['rotation']))
        print("|\tScale :" + str(matrix['scale']))
        print("|\tUnknown1.0 :" + str((ued1, ued2, ued3)))
        print("|\tUnknown1.5 :" + str((ued4, ued5, ued6)))
        print("|\tUnknown2 :" + str((ued14, ued15, ued16, ued17, ued18, ued19)))
        print("|")   
        bpy.context.collection.objects.link(modelObject)
    #reader.advance(modelsEnd-12)

    reader.read_string(8) # Element.
    elementEnd = reader.read_int()
    
    object_dats = []
    print()
    print("Elements")
    for i in range(0, elementCount):
        reader.read_int()
        reader.advance() #00000000
        
        matrix = reader.read_matrix()
        
        #unknownList = reader.read(24) # unknown Data Possibly id
        ued1 = reader.read_float()
        ued2 = reader.read_float()
        ued3 = reader.read_float()
        ued4 = reader.read_float()
        ued5 = reader.read_float()
        ued6 = reader.read_float()
        
        nameIndex = reader.read_int()
        
        ued14 = reader.read_int()
        parentIndex = reader.read_int()
        ued16 = reader.read_int()
        ued17 = reader.read_int()
        ued18 = reader.read_int()
        
        objectName = stringTable[nameIndex]
        
        object_dats.append({'name':objectName,'matrix':matrix})
        
        print("|" + objectName + "({0})".format(str(i)))
        print("|\tPos :" + str(matrix['position']))
        print("|\tRot :" + str(matrix['rotation']))
        print("|\tScale :" + str(matrix['scale']))
        print("|\tUnknown1.0 :" + str((ued1, ued2, ued3)))
        print("|\tUnknown1.5 :" + str((ued4, ued5, ued6)))
        print("|\tUnknown2 :" + str((ued14, parentIndex, ued16, ued17, ued18)))
        print("|") 
    
    reader.advance() #FFFFFFFF
    
    print("Constr "+str(reader.position()));
    reader.read_string(8) # Constr..
    reader.advance() # Constr Header Size
    reader.advance()

    print("Render "+str(reader.position()));
    reader.read_string(8) # Render..
    urd1 = reader.read_int() # Unknown
    reader.advance()

    print("Render "+str(reader.position()));
    reader.read_string(8) # Render..
    urd1 = reader.read_int() # Unknown
    
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

    meshGroupDefinitionsCount = reader.read_int()
    print(meshGroupDefinitionsCount)
    meshGroupDefinitions = []
    
    print()
    print("Mesh Definitions")
    for i in range(meshGroupDefinitionsCount):
        print("|Defintion " + str(i))
        reader.advance() #52410000
        definitionLength = reader.read_int()
        meshDefinition = ""
        data = []
        for j in range(definitionLength):
            reader.advance() #52410000
            uvd1 = reader.read_short()
            uvd2 = reader.read_short()
            vertDataType = reader.read_int()
            if uvd1 != 3:
                meshDefinition += to_hex(vertDataType)
                
            reader.advance() #00000000
            uvd3 = reader.read_int()
            uvd4 = reader.read_byte() # unknownVertData3
            
            print("|\t{2} {0}-{1}\t{3}-{4}".format(uvd1, uvd2, to_hex(vertDataType), uvd3, uvd4))
            
            data.append({'type':vertDataType, '1':uvd1, '2':uvd2, '3':uvd3, '4':uvd4})
        print("|\tFull : " + meshDefinition)
        print()
        meshGroupDefinitions.append(meshDefinition)

    reader.read_int() #52410000
    fxNamesCount = reader.read_int()
    for i in range(fxNamesCount):
        reader.advance() #52410000
        reader.advance() #52410000
        fxName = reader.read_string()

    unknown1 = reader.read_int()
    reader.advance() #52410000
    reader.advance() #52410000
    reader.advance() #02000000

    textureCount = reader.read_int()
    textures = []
    print("Textures")
    for i in range(0, textureCount):
        pos = reader.position()
        texName = reader.read_string()
        print("|{0} ({1})".format(texName, i))
        print('|\tPosition : ' + str(pos))
        
        tu1 = reader.read_int()
        reader.advance() #52410000
        reader.advance() #52410000
        reader.advance() #02000000
        texName2 = reader.read_string()
        reader.advance() #52410100
        tu2 = reader.read_int() #00000000
        tu3 = reader.read_int()
        tu4 = reader.read_int()
        
        tu5 = reader.read_int() #01000000
        tu6 = reader.read_int()
        tu7 = reader.read_int()
        
        tu8 = reader.read_int() #00000000
        tu9 = reader.read_int()
        tu10 = reader.read_int()
        tu11 = reader.read_int()
        
        tu13 = reader.read_int()
        
        texLength = reader.read_int()
        texHeight = reader.read_int()
        texWidth = reader.read_int()
        tu14 = reader.read_int()
        mipmapCount = reader.read_int()
        dxtVer = reader.read_int()
        tu15 = reader.read_int()
        tu16 = reader.read_int()
        
        print('|\tDXT' + str(dxtVer))
        print('|\tTex Dat : ' + str((texLength, texHeight, texWidth, mipmapCount)))
        print('|\tUnknown1 : ' + str((to_hex(tu1), tu2, tu3, tu4)))
        print('|\tUnknown2 : ' + str((tu5, tu6, tu7)))
        print('|\tUnknown3 : ' + str((tu8, tu9, tu10, tu11)))
        print('|\tTexUnknown : ' + str((tu14, tu15, tu16)))
        
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
                write(mipmapCount)                          #MipMapCount
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
            
            tex = bpy.ops.image.open(filepath=directory+"textures\\"+texName+".dds")
            textures.append(tex)

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
    print("\n")
    vertStreams = {}
    
    for i in range(0, meshGroupCount):
        print("Vert Stream " + str(i))
        reader.advance(1) #02
        reader.advance() #52410100
        reader.advance() #52410000
        vertexBytes = reader.read_int()
        print("|\tBytes Length : "+ str(vertexBytes))
        
        reader.advance() #52410000

        vertDataLength = reader.read_int()
        meshDefinition = ""
        meshTypes = []
        for j in range(0, vertDataLength):
            reader.read_int() #52410000
            vertDataType = reader.read_int()
            reader.read_int() #00000000
            unknownVertData1 = reader.read_int()
            unknownVertData2 = reader.read_int()
            meshDefinition += to_hex(vertDataType)
            meshTypes.append({'type':vertDataType,'data1':unknownVertData1,'data2':unknownVertData2})
        
        print('|\tMesh Definition : ' + meshDefinition)
        
        reader.advance() #52410000
        vertDataSplits = reader.read_int()
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
        
        vertStart = reader.pos()
        print("|\tVerts Start : 0x"+to_hex(vertStart))
        print("|\tVerts Count : "+to_hex(vertexCount))
        for j in range(0, vertexCount):
            #vertSplitLength = 0
            vertData = []
            
            for k in range(0, vertDataLength):
                type = meshTypes[k]['type']
                if  type == 6:
                    x = reader.read_float()
                    y = reader.read_float()
                    z = reader.read_float()
                    vertData.append((x, y, z))
                elif type == 8:
                    x = reader.read_half()
                    y = reader.read_half()
                    vertData.append((x, y))
                elif type == 9:
                    x = reader.read_half()
                    y = reader.read_half()
                    z = reader.read_half()
                    w = reader.read_half()
                    vertData.append((x, y, z, w))
                elif type == 0xA:
                    x = reader.read_byte()
                    y = reader.read_byte()
                    z = reader.read_byte()
                    w = reader.read_byte()
                    vertData.append((x, y, z, w))
                elif type == 0xB:
                    x = reader.read_byte()/255.0
                    y = reader.read_byte()/255.0
                    z = reader.read_byte()/255.0
                    w = reader.read_byte()/255.0
                    vertData.append((x, y, z, w))
            
            verticies.append(vertData)
            
        vertStreams[meshDefinition] = {'len':vertexBytes, 'verts':verticies, 'data':meshTypes, 'start':vertStart}
        print("\n")
        
    print("read mesh groups")
    reader.advance() #52410000
    faceStreamCount = reader.read_int()
    faceStreams = []
    print("\n")
    for i in range(0, faceStreamCount):
        print('Face Stream '+ str(i))
        reader.advance(1) #02
        reader.advance() #52410100
        faceCount = reader.read_int()
        print('|\tFace Count : '+str(faceCount))
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
        faceStart = reader.pos()
        print('|\tFace Start : 0x' + to_hex(faceStart))
        faces = []
        for j in range(0, faceCount):
            faces.append(reader.read_short())
            
        faceStreams.append({'faces':faces, 'start':faceStart})
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
        print('Mesh ' + str(i))
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
        group = vertStreams[definition]
        offset = meshData1[k][2]
        vertStart = int(meshData2[0][2]/group['len']) + offset
        vertCount = meshData1[k][3]
        vertEnd = vertStart + vertCount
        
        faceStart = meshData1[k][0]
        faceEnd = faceStart + meshData1[k][1]
        
        #print('|\tDefinition : ' + definition)
        #print('|\tVert Start : 0x' + to_hex(group['start'] + vertStart * group['len']))
        #print('|\tVert Count : ' + str(vertCount))
        #print('|\tFace Start : 0x' + to_hex(faceStreams[faceStreamIndex]['start'] + faceStart * 2))
        #print('|\tFace Count : ' + str(meshData1[k][1]))
        #print('|\tVert Pos Type : ' + str(len(group['verts'][0][0])))
        #print('|\tVert Data Length : ' + str(group['len']))
        
        if meshObjectIndex not in objectGroups:
            objectGroups[meshObjectIndex] = bmesh.new()
        
        bm = objectGroups[meshObjectIndex]
        vertdata = group['data']
        
        vs = group['verts']
        
        verts = []
        uvs = []
        weights = None
        colors = []
        
        for j in range(2, len(vertdata)):
            dat = vertdata[j]
            if dat['type'] == 0xa:
                weights = []
            elif not vertdata[j-1]['type'] == 0xa:
                uvs.append([])
                
        
        identity_layer = bm.verts.layers.int.verify()
        
        
        uv_type = group['data'][2]['type']
        print((faceStart, faceEnd-faceStart))
        for l in range(vertStart,vertEnd):
            vertDat = vs[l]
            pos = vertDat[0]
            normal = vertDat[1]
            uv = vertDat[2]
            
            vert = bm.verts.new((pos[0], pos[2], pos[1]))
            vert.normal = (normal[0], normal[2], normal[1])
            vert[identity_layer] = i
            
            verts.append(vert)
            
            if uv_type == 9:
                uvs.append((uv[0], uv[1], uv[2], uv[3]))
            elif uv_type == 8:
                uvs.append((uv[0], uv[1]))
            
            for id in range(2, len(vertdata)):
                dat = vertdata[id]
                  
                
            if len(vertDat) > 3:
                col = vertDat[3]
                if len(col) == 1:
                    colors.append((col[0], 0, 0, 0))
                elif len(col) == 2:
                    colors.append((col[0], col[1], 0, 0))
                elif len(col) == 3:
                    colors.append((col[0], col[1], col[2], 0))
                elif len(col) == 4:
                    colors.append((col[0], col[1], col[2], col[3]))
                    
        
        faces = []
        if faceType == 0:
            for j in range(faceStart, faceEnd, 3):
                i1 = faceStreams[faceStreamIndex]['faces'][j] - offset
                i2 = faceStreams[faceStreamIndex]['faces'][j+1] - offset
                i3 = faceStreams[faceStreamIndex]['faces'][j+2] - offset
                try:
                    faces.append(bm.faces.new((verts[i1], verts[i3], verts[i2])))
                except:
                    print("failed face")
        elif faceType == 1:
            for j in range(faceStart, faceEnd-2):
                i1 = faceStreams[faceStreamIndex]['faces'][j] - offset
                i2 = faceStreams[faceStreamIndex]['faces'][j+1] - offset
                i3 = faceStreams[faceStreamIndex]['faces'][j+2] - offset
                try:
                    if i1 == i2 or i2 == i3 or i3 == i1:
                        continue
                    if (j-faceStart)%2 == 1:
                        faces.append(bm.faces.new((verts[i1], verts[i2], verts[i3])))
                    else:
                        faces.append(bm.faces.new((verts[i1], verts[i3], verts[i2])))
                except:
                    print("failed face")
        
        bm.verts.ensure_lookup_table()
        bm.faces.ensure_lookup_table()
        
        
        if uv_type == 8 or uv_type == 9:
            uv_layer_1 = bm.loops.layers.uv.get('UV1', None)
            if uv_layer_1 == None:
                uv_layer_1 = bm.loops.layers.uv.new('UV1')
                
        if uv_type == 9:
            uv_layer_2 = bm.loops.layers.uv.get('UV2', None)
            if uv_layer_2 == None:
                uv_layer_2 = bm.loops.layers.uv.new('UV2')
                
            
        color_layer = bm.loops.layers.color.verify()
        
        for face in faces:
            for t, loop in enumerate(face.loops):
                vertIndex = verts.index(loop.vert)
                
                if uv_type == 8 or uv_type == 9:
                    uv = uvs[vertIndex]
                    
                    #loop[uv_layer_1].uv[0] = uv[0]
                    #loop[uv_layer_1].uv[1] = 1-uv[1]
                
                if uv_type == 9:
                    uv = uvs[vertIndex]
                    
                    #loop[uv_layer_2].uv[0] = uv[2]
                    #loop[uv_layer_2].uv[1] = 1-uv[3]
                    
                if len(vs[l]) > 3:
                    color = colors[vertIndex]
                    loop[color_layer] = color
        
    # would normally load the data here
    for objectIndex in range(0, len(object_dats)):
        dat = object_dats[objectIndex]
        object = None
        
        if objectIndex in objectGroups:
            bm = objectGroups[objectIndex]
                    
            objectMesh = bpy.data.meshes.new(dat['name'])
            
            bm.to_mesh(objectMesh)
            objectMesh.update()
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
