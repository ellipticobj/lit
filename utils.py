import zlib
import hashlib

def parseargs(args):
    flags = []
    kwargs = []

    for arg in args:
        if arg.startswith('-'):
            flags.append(arg)
        else:
            kwargs.append(arg)

    return flags, kwargs

def hashfile(path, filesize=None, write=False, type="blob"):
    with open(path, "rb") as file:
        content = file.read()
        filesize = len(content) if not filesize else filesize
        unhashed = f"{type} {str(filesize)}\x00".encode() + content

    hash = hashlib.sha1(unhashed).hexdigest()

    if write:
        os.makedirs(f".lit/objects/{hash[:2]}", exist_ok=True)
        with open(f".lit/objects/{hash[:2]}/{hash[2:]}", "wb") as file:
            file.write(zlib.compress(unhashed))

    return hash

def decompfile(path):
    with open(path, "rb") as file:
        compressed = file.read()
    decompressed = zlib.decompress(compressed)
    header, content = decompressed.split(b'\x00', 1)
    type, size = header.split(b" ")
    return type, size, content
