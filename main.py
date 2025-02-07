import sys
import os
import zlib
import hashlib
import shutil

def main():
    args = sys.argv[1:]

    if not args:
        print("usage: lit <command> [<args>]")
        return

    match args[0]:
        case 'init':
            if len(args) > 2:
                print("too many arguments for command `lit init`")

            return init()

        case 'catfile':
            args = args[1:]
            if len(args) < 2:
                print("command requires two arguments\nusage: lit catfile <type> <hash>")

            return catfile(args)

        case 'hashobject':
            args = args[1:]
            if len(args) < 2:
                print("command requires two arguments\nusage: lit hashobject <filename>")
            elif len(args) > 3:
                print("too many arguments for command `lit hashobject`")

            return hashobject(args)

        case 'writetree':
            args = args[1:]

            return writetree(args)

        case 'lstree':
            args = args[1:]
            if len(args) != 1:
                print("command requires one argument\nusage: lit lstree <hash>")

            return lstree(args)

        case other:
            print(f"unrecognized command {other}")


def parseargs(args):
    flags = []
    kwargs = []

    for arg in args:
        if arg.startswith('-'):
            flags.append(arg)
        elif arg.startswith('--'):
            kwargs.append(arg)

    return flags, kwargs

def hashfile(path, write=False):
    with open(path, "rb") as file:
        unhashed = f"blob {len(file.read())}\x00{file.read()}".encode('utf-8')

    hash = hashlib.sha1(unhashed).hexdigest()

    if write:
        os.makedirs(f".git/objects/{hash[:2]}", exist_ok=True)
        with open(f".lit/objects/{hash[:2]}/{hash[2:]}", "wb") as file:
            file.write(zlib.compress(hash.encode()))

    return hash

def init():
    if os.path.exists(".lit") and os.path.exists(".lit/objects") and os.path.exists(".lit/refs") and os.path.exists(".lit/HEAD"):
        print("this directory is already a lit repository. \nare you sure you want to continue? (y/n) ", end="")
        resp = input()

        if resp.lower() != 'y':
            print("n")
            return
        else:
            shutil.rmtree(".lit")
            print("deleted existing lit repository")

    os.mkdir(".lit")
    os.mkdir(".lit/objects")
    os.mkdir(".lit/refs")

    with open(".lit/HEAD", "w") as file:
        file.write("ref: refs/heads/main\n")

    print("initialized a repository")
    print("current branch is named main") # TODO: make some way for users to switch branches
    return "lit init"

def decompfile(compressed):
    decompressed = zlib.decompress(compressed)
    header, content = decompressed.split(b'\x00', 1)
    type, size = header.decode().split(" ")
    return type, size, content.decode()

def catfile(args):
    flags, args = parseargs(args)

    if len(args) > 2:
        print("too many arguments for command `lit catfile`")
        return

    if len(args) < 2:
        print("command requires two arguments\nusage: lit catfile <type> <hash>")
        return

    type = args[0]
    hash = args[1]

    # TODO: add support for other object types
    if "-p" in flags or type == "blob":
        hash = args[1]
        with open(f".lit/objects/{hash[0:2]}/{hash[2:]}", "rb") as file:
            conttype, size, content = decompfile(file.read())
            print(content)

    else:
        print(f"unrecognized object type {args[1]}\nthis is NOT a full implementation. only blobs are supported for this command.")

def hashobject(args):
    flags, args = parseargs(args)

    type = 'blob'

    filename = args[1]

    try:
        filesize = os.path.getsize(filename)
    except FileNotFoundError:
        print(f"file {filename} not found")
        return

    if "-w" in flags:
        hash = hashfile(filename, write=True)
    else:
        hash = hashfile(filename, write=False)

    print(hash)

def lstree(args):
    flags, args = parseargs(args)
    hash = flags[0]

    if len(flags) != 40:
        print("invalid hash")
        return

    try:
        with open(f".lit/objects/{hash[:2]}/{hash[2:]}", "rb") as file:
            type, size, content = decompfile(file.read())
            if type != "tree":
                print(f"object {hash} is not a tree")
                idx = 0

                if "--name-only" in flags:
                    while idx < len(content):
                        nameend = content.find(b'\x00', idx)
                        name = content[idx:nameend].decode()
                        print(name)
                        idx = nameend + 21
                else:
                    while idx < len(content):
                        modeend = content.find(b' ', idx)
                        mode = content[idx:modeend].decode()

                        nameend = content.find(b'\x00', modeend)
                        name = content[modeend+1:nameend].decode()

                        conthash = content[nameend+1:nameend+21].hex()

                        print(f"{mode} {conthash} {name}")

                        idx = nameend + 21

    except FileNotFoundError:
        print(f"tree {hash} not found")

def writetree(args):
    flags, args = parseargs(args)
    path = args[0] if args else "."

    if os.path.isfile(path):
        return hashfile(path)

    contents = sorted(
        os.listdir(path),
        key=lambda x: x if os.path.isfile(os.path.join(path, x)) else f"{x}/"
    )
    s = b""

    for item in contents:
        if item == ".lit" or item == ".git":
            continue

        fullpath = os.path.join(path, item)

        if os.path.isfile(fullpath):
            s += f"100644 {item}\x00".encode()
        else:
            s += f"40000 {item}\x00".encode()

        hash = int.to_bytes(int(writetree(fullpath), base=16), length=20, byteorder='big')
        s += hash

    s = f"tree {len(s)}\x00{s}".encode()
    hash = hashlib.sha1(s).hexdigest()

    os.makedirs(f".lit/objects/{hash[:2]}", exist_ok=True)
    with open(f".lit/objects/{hash[:2]}/{hash[2:]}", "wb") as file:
        file.write(zlib.compress(s))

    return hash

if __name__ == "__main__":
    main()
