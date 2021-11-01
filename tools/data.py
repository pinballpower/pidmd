'''
'''

def reverseByte(b):
    res = ((b & 0x01) << 7) | ((b & 0x02) << 6) | ((b & 0x04) << 5) | ((b & 0x08) << 4) | \
          ((b & 0x10) << 3) | ((b & 0x20) << 2) | ((b & 0x40) << 1) | ((b & 0x80) << 1) 
    return res

def reverseBytes(b):
    return bytearray(b).reverse()