def parse16(array, offset):
    return (array[offset + 1] << 8) + array[offset]

def parse32(array, offset):
    return (parse16(array, offset + 2) << 16) + parse16(array, offset)

def pack16(data):
    return [data & 255, data >> 8]

def pack32(data):
    return pack16(data & 0xffff) + pack16(data >> 16)