"""Check every ZIP entry, including Fusion's Zstandard method93, without importing CAD."""
import binascii,ctypes,ctypes.util,struct,zipfile,zlib
from pathlib import Path

def verify(path):
 library=ctypes.util.find_library('zstd');assert library,'libzstd is required for Fusion ZIP method93';zstd=ctypes.CDLL(library);zstd.ZSTD_decompress.argtypes=[ctypes.c_void_p,ctypes.c_size_t,ctypes.c_void_p,ctypes.c_size_t];zstd.ZSTD_decompress.restype=ctypes.c_size_t;zstd.ZSTD_isError.argtypes=[ctypes.c_size_t];zstd.ZSTD_isError.restype=ctypes.c_uint
 entries=0;total=0;methods=set()
 with zipfile.ZipFile(path)as archive,Path(path).open('rb')as stream:
  for info in archive.infolist():
   assert not(info.flag_bits&1),'Encrypted archive entry';stream.seek(info.header_offset);header=stream.read(30);assert header[:4]==b'PK\x03\x04';name_length,extra_length=struct.unpack_from('<HH',header,26);stream.seek(name_length+extra_length,1);compressed=stream.read(info.compress_size);assert len(compressed)==info.compress_size
   if info.compress_type==0:data=compressed
   elif info.compress_type==8:data=zlib.decompress(compressed,-15)
   elif info.compress_type==93:
    output=ctypes.create_string_buffer(info.file_size);source=ctypes.create_string_buffer(compressed);size=zstd.ZSTD_decompress(output,info.file_size,source,len(compressed));assert not zstd.ZSTD_isError(size)and size==info.file_size,(info.filename,size);data=output.raw[:size]
   else:raise ValueError(('Unsupported archive compression',info.compress_type))
   assert len(data)==info.file_size and binascii.crc32(data)&0xffffffff==info.CRC,info.filename
   entries+=1;total+=len(data);methods.add(info.compress_type)
 return {'passed':True,'entries':entries,'uncompressed_bytes':total,'zip_compression_methods':sorted(methods),'checker':'ZIP central-directory sizes and CRC32 for every entry; libzstd for method93. This verifies archive integrity, not independent CAD reconstruction.'}
