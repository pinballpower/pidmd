'''
Copyright (c) 2019 Pinball Power

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
'''

import struct
import logging

def readByte(file):
    res, = struct.unpack("B",file.read(1));
    return res

def readInt16(file):
    res, = struct.unpack(">h",file.read(2));
    return res

def readUInt16(file):
    res, = struct.unpack(">H",file.read(2));
    return res

def readUInt32(file):
    res, = struct.unpack(">I",file.read(4));
    return res

def readString(file, length):
    return file.read(length).decode("UTF-8")

def reverseByte(b):
    res = ((b & 0x01) << 7) | ((b & 0x02) << 6) | ((b & 0x04) << 5) | ((b & 0x08) << 4) | \
          ((b & 0x10) << 3) | ((b & 0x20) << 2) | ((b & 0x40) << 1) | ((b & 0x80) << 1) 
    return res

def reverseBytes(b):
    return bytearray(b).reverse()

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
 
    
class VNIAnimation(object):
    
    def __init__(self, vni):
        
        namelen = readInt16(vni.file)
        if namelen > 0:
            self.name=readString(vni.file, namelen)
        else:
            self.name="<undefined>"
            
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
        for _i in range(0, self.numFrames):
            frame = VNIAnimationFrame(vni)
            self.frames.append(frame)
            self.animationduration += frame.delay
#                 if (Frames[i].Mask != null && TransitionFrom == 0) {
#                     TransitionFrom = i;
#                 }
#                 AnimationDuration += Frames[i].Delay;
#             }
            
            
    def __str__(self):
        return self.name

    





# 
#             Logger.Debug("VNI[{3}] Reading {0} frame{1} for animation \"{2}\"...", numFrames, numFrames == 1 ? "" : "s", Name, reader.BaseStream.Position);
#             Frames = new AnimationFrame[numFrames];
#             AnimationDuration = 0;
#             for (var i = 0; i < numFrames; i++) {
#                 Frames[i] = new VniAnimationFrame(reader, fileVersion, AnimationDuration);
#                 if (Frames[i].Mask != null && TransitionFrom == 0) {
#                     TransitionFrom = i;
#                 }
#                 AnimationDuration += Frames[i].Delay;
#             }
#         }
# 
    
        
        