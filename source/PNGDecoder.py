import struct
import zlib
import matplotlib.pyplot as plt
import numpy as np
__png_signature = b'\x89PNG\r\n\x1a\n'
__path = 'basn6a08.png'
__dog_path = 'dog.png'


class PNGData:
    pixels = []
    width = 0
    height = 0
    


 
def decode(path):
    """
    decodes a png.
    :param p1: the path to the png
    :return: returns a PNGData which contains it's pixels , width and height
    """
    f = open(path, 'rb')
    acutal_png_signature = f.read(len(__png_signature))
    if acutal_png_signature != __png_signature:
        print("invalid")
        return
    chunks = []
    while True:
        chunk = __read_chunk(f)
        chunks.append(chunk)
        if chunk[0] == b'IEND':
            break
    IHDR_data = __read_IHDR_data(chunks[0])
    pixels = __process_IDAT_chunks(chunks, IHDR_data)
    png_data = PNGData()
    png_data.pixels = pixels
    png_data.width = IHDR_data[0]
    png_data.height = IHDR_data[1]
    return png_data


def __process_IDAT_chunks(chunks, IHDR_data):
    full_data = b''.join(data for type, data in chunks if type == b'IDAT')

    decompressed_IDAT = zlib.decompress(full_data)
    recon = []
    bytes_per_pixel = 4
    stride = IHDR_data[0] * bytes_per_pixel
    i = 0
    for r in range(IHDR_data[1]):
        filter_type = decompressed_IDAT[i]
        i += 1
        for c in range(stride):
            filt_x = decompressed_IDAT[i]
            i += 1
            if filter_type == 0:
                recon_x = filt_x
            elif filter_type == 1:
                recon_x = filt_x + __recon_a(r, c, recon, stride, bytes_per_pixel)
            elif filter_type == 2:
                recon_x = filt_x + __recon_b(r, c, recon, stride)
            elif filter_type == 3:
                recon_x = filt_x + (__recon_a(r, c, recon, stride, bytes_per_pixel) +
                                    __recon_b(r, c, recon, stride)) // 2
            elif filter_type == 4:
                recon_x = filt_x + __paeth_predictor(__recon_a(r, c, recon, stride, bytes_per_pixel),
                                                  __recon_b(r, c, recon, stride),
                                                  __recon_c(r,c,recon,stride,bytes_per_pixel))
            else:
                print('Unknown filter type')
            recon.append(recon_x & 0xff) 
            
    return recon

def __read_IHDR_data(IHDR_chunk):
    data_section = IHDR_chunk[1]
    width = struct.unpack('>I', data_section[0:4])[0]
    height = struct.unpack('>I', data_section[4:8])[0]
    bit_depth = data_section[8]
    color_type = data_section[9]
    compression_method = data_section[10]
    filter_method = data_section[11]
    interlace_method = data_section[12]
    if bit_depth != 8:
        print('we only support a bit depth of 8')
        exit(-1)
    if color_type != 6:
        print('we only support truecolor with alpha')
        exit(-1)
    if compression_method != 0:
        print('Invalid compression method')
        exit(-1)
    if filter_method != 0:
        print('invalid filter method')
        exit(-1)
    if interlace_method != 0:
        print('we only support no interlacing')

    return (width, height)


def __read_chunk(file):

    chunk_length = struct.unpack('>I', file.read(4))[0]
    chunk_type = struct.unpack('>4s', file.read(4))[0]
    chunk_data = file.read(chunk_length)
    expected_crc32 = struct.unpack('>I', file.read(4))
    actual_crc32 = zlib.crc32(chunk_data,
                              zlib.crc32(struct.pack('>4s', chunk_type)))
    if actual_crc32 != expected_crc32[0]:
        print('chunk checksum failed')
        return
    return (chunk_type, chunk_data)


def __paeth_predictor(a, b, c):
    p = a + b - c
    pa = abs(p - a)
    pb = abs(p - b)
    pc = abs(p - c)
    if pa <= pb and pa <= pc:
        Pr = a
    elif pb <= pc:
        Pr = b
    else:
        Pr = c
    return Pr


def __recon_a(r, c, recon, stride, bytes_per_pixel):
    return recon[r * stride + c - bytes_per_pixel] if c >= bytes_per_pixel else 0


def __recon_b(r, c, recon, stride):
    return recon[(r-1) * stride + c] if r > 0 else 0


def __recon_c(r, c, recon,  stride, bytes_per_pixel):
    return recon[(r-1) * stride + c - bytes_per_pixel] if r > 0 and c >= bytes_per_pixel else 0


if __name__ == '__main__':
    my_png_data = decode(__dog_path)
    plt.imshow(np.array(my_png_data.pixels).reshape((my_png_data.height, my_png_data.width, 4)))
    plt.show()
