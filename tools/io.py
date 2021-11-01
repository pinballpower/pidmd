'''
I/O tools
'''

import struct

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


