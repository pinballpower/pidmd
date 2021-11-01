'''
Parser for VNI files
Derived from https://github.com/freezy/dmd-extensions/
'''

import struct
import logging

from tools.io import readByte, readInt16, readString, readUInt16, readUInt32
from tools.data import reverseBytes

class VNIException(Exception):
    
    def __init__(self, msg):
        super().__init__(msg)
        
        
class Color():
    
    def __init__(self):
        self.r=0
        self.g=0
        self.b=0
        pass
    
    def readFromFile(self, file):
        self.r, self.g, self.b = struct.unpack("BBB",file.read(3));
        
    def __str__(self):
        return("%02x%02x%02x".format(self.r,self.g,self.b))

class VNI(object):
    '''
    reads VNI files
    see also https://github.com/freezy/dmd-extensions/tree/master/LibDmd/Converter/Colorize
    '''

    def __init__(self, filename):
        self.filename=filename
        self.nunAnimations=0
        self.version=0
        self.read_vni()
        
        
    def read_vni(self):
        self.file = open(self.filename, "rb")
        
        header = readString(self.file,4)
        if header != "VPIN":
            raise VNIException("VNI %s: Not a valid VNI file", self.filename)
        

        self.version = readInt16(self.file)
        self.numAnimations = readInt16(self.file)
        logging.debug("VNI %s: version %s, %s animations",self.filename, self.version, self.numAnimations)
        
        if self.version >= 2:
            logging.debug("VNI %s: Skipping %s bytes of animation indexes.", self.filename, self.numAnimations * 4);
            self.file.read(self.numAnimations * 4)
            
        try: 
            done=False
            while not done:
                animation=VNIAnimation(self)
        except Exception:
            pass
        
    def __str__(self):
        return("VNI v{} with {} animations".format(self.version, self.numAnimations))
   
   
class VNIAnimationPlane:
    
    def __init__(self, vni, planesize, marker):
        self.marker = marker
        self.plane=reverseBytes(vni.file.read(planesize))
        
    
class VNIAnimationFrame():
    
    def __init__(self, vni):
        self.planeSize = readInt16(vni.file)
        self.delay=readUInt16(vni.file)
        self.mask = None
        self.planes = []
        
        if vni.version >= 4:
            self.hash=readUInt32(vni.file)
            
            bitlength = readByte(vni.file)
            
            if vni.version < 3:
                raise VNIException("Version < 3 not yet supported")
                self.readPlanes(bitlength, self.planeSize, vni);
            
            else:
                compressed = readByte(vni.file)
                
                if not compressed:
                    self.readPlanes(bitlength, self.planeSize, vni);
                else:
                    raise VNIException("compressed planes not yet supported")
                
                
    def readPlanes(self, bitlength, planeSize, vni):
        for _i in range(0,bitlength):
            marker = readByte(vni.file)
            if marker == 0x6d:
                # TODO: reverse
                self.mask = vni.file.read(planeSize)
                logging.debug("VNI %s: animation, got mask ",vni.filename)
            else:
                self.planes.append(VNIAnimationPlane(vni, planeSize, marker))
                logging.debug("VNI %s: animation, got plane ",vni.filename)
 
    
class VNIAnimation():
    
    def __init__(self, vni):
        
        self.transitionFrom = 0
        
        namelen = readInt16(vni.file)
        if namelen > 0:
            self.name=readString(vni.file, namelen)
        else:
            self.name="<undef>"
            
        logging.debug("VNI %s: animation %s: ", vni.filename, self.name)
        
        self.cycles = readInt16(vni.file);
        self.hold = readInt16(vni.file);
        self.clockFrom = readInt16(vni.file);
        self.clockSmall = readByte(vni.file);
        self.clockInFront = readByte(vni.file);
        self.clockOffsetX = readInt16(vni.file);
        self.clockOffsetY = readInt16(vni.file);
        self.refreshDelay = readInt16(vni.file);
        self.type = readByte(vni.file);
        self.fsk= readByte(vni.file);

        self.numFrames=readInt16(vni.file);
        if self.numFrames < 0:
            self.numFrames += 65536
        logging.debug("VNI %s: animation %s, %s frames ", vni.filename, self.name, self.numFrames)
        
        if vni.version >= 2:                 
            self.paletteIndex = readInt16(vni.file)
            numColors = readInt16(vni.file)
            self.aniColors = []
            for _i in range(0, numColors):
                color=Color()
                color.readFromFile(vni.file)
                self.aniColors.append(color)
            logging.debug("VNI %s: animation %s, %s colors ", vni.filename, self.name, len(self.aniColors))
            
        
        if vni.version >= 3:
            self.EditMode = readByte(vni.file)
        else:
            self.editMode=0
        
        if vni.version >= 4:
            self.width = readInt16(vni.file);
            self.height = readInt16(vni.file);
            logging.debug("VNI %s: animation %s, %sx%s ", vni.filename, self.name, self.width, self.height)
        else:
            self.width=None
            self.height=None
            
            
        if vni.version >= 5:
            self.numMasks = readInt16(vni.file)
            self.masks=[]
            for _i in range(0,self.numMasks):
                _locked = readByte(vni.file) # Not yet used yet
                size = readInt16(vni.file)
                self.masks.append(vni.file.read(size))
            logging.debug("VNI %s: animation %s, %s masks", vni.filename, self.name, len(self.masks))
                
                
        if vni.version >= 6:
            self.linkedAnimation = readByte(vni.file);
            length = readInt16(vni.file)
            self.aniName = readString(vni.file, length)
            self.starFrame = readUInt32(vni.file)
            
            
        self.frames = [];
        self.animationduration = 0;
        for i in range(0, self.numFrames):
            frame = VNIAnimationFrame(vni)
            self.frames.append(frame)
            if (frame.mask is not None) and (self.transitionFrom == 0):
                self.transitionFrom = i
                self.animationduration += frame.delay
            
            
    def __str__(self):
        return self.name

    
        
        