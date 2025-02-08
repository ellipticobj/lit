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
            if len(args) > 3:
                print("too many arguments for command `lit init`")
                return

            return init()

        case 'catfile':
            if len(args) < 3:
                print("command requires two arguments\nusage: lit catfile <type> <hash>")
                return

            return catfile(args[1:])

        case 'hashobject':
            if len(args) < 2:
                print("command requires one argument\nusage: lit hashobject <filename>")
                return
            elif len(args) > 3:
                print("too many arguments for command `lit hashobject`")
                return

            return hashobject(args[1:])

        case 'writetree':
            return writetree(args[1:])

        case 'lstree':
            if len(args) != 2:
                print("command requires one argument\nusage: lit lstree <hash>")
                return

            return lstree(args[1:])

        case other:
            print(f"unrecognized command {other}")
            return

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
        unhashed = f"{type} {filesize}\x00{content}".encode('utf-8')

    hash = hashlib.sha1(unhashed).hexdigest()

    if write:
        os.makedirs(f".lit/objects/{hash[:2]}", exist_ok=True)
        with open(f".lit/objects/{hash[:2]}/{hash[2:]}", "wb") as file:
            file.write(zlib.compress(unhashed))

    return hash

def decompfile(compressed):
    decompressed = zlib.decompress(compressed)
    header, content = decompressed.split(b'\x00', 1)
    type, size = header.decode().split(" ")
    return type, size, content.decode()

def init():
    if os.path.exists(".lit"):
        print("this directory is already a lit repository. \nare you sure you want to continue? (y/n) ", end="")
        resp = input().strip().lower()

        if resp == 'y':
            shutil.rmtree(".lit")
            print("deleted existing lit repository")
        elif resp == 'n':
            return
        else:
            print("n")
            return

    os.makedirs(".lit/objects")
    os.makedirs(".lit/refs")

    with open(".lit/HEAD", "w") as file:
        file.write("ref: refs/heads/main\n")

    print("initialized a repository")
    print("current branch is named main") # TODO: make some way for users to switch branches
    return "lit init"


def catfile(args):
    flags, args = parseargs(args)

    # TODO: if there are two args, there shouldnt be any flags, and args should be: type, hash
    # else: there should be a flag and they should be: -p, hash

    # TODO: add support for other object types
    if "-p" in flags:
        hash = args[1]
        with open(f".lit/objects/{hash[0:2]}/{hash[2:]}", "rb") as file:
            conttype, size, content = decompfile(file.read())
            print(content.strip())
            return

    elif type == "blob":
        hash = args[1]
        with open(f".lit/objects/{hash[0:2]}/{hash[2:]}", "rb") as file:
            conttype, size, content = decompfile(file.read())
            if conttype != "blob":
                print(f"object {hash} is not a blob")
                return
            print(content.strip())
            return

    else:
        print(f"unrecognized object type {args[1]}\nthis is NOT a full implementation. only blobs are supported for this command.")

def hashobject(args):
    flags, args = parseargs(args)

    type = 'blob'

    filename = args[0]

    try:
        filesize = os.path.getsize(filename)
    except FileNotFoundError:
        print(f"file {filename} not found")
        return

    if "-w" in flags:
        hash = hashfile(filename, filesize, write=True, type=type)
    else:
        hash = hashfile(filename, filesize, write=False, type=type)

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
    path = args[0] if args else "./"

    if os.path.isfile(path):
        return hashfile(path)

    print(os.path.join(path, x))
    contents = sorted(
        os.listdir(path),
        key=lambda x: x if os.path.isfile(os.path.join(path, x)) else f"{x}/"
    )
    s = b""

    for item in contents:
        if item in [".lit", ".git"]:
            continue

        fullpath = os.path.join(path, item)

        if os.path.isfile(fullpath):
            hash = hashfile(fullpath)
            s += f"100644 {item}\x00{hash}".encode()
        else:
            subtreehash = writetree([fullpath])
            s += f"40000 {item}\x00{subtreehash}".encode()

    s = f"tree {len(s)}\x00{s}".encode() + s
    hash = hashlib.sha1(s).hexdigest()

    os.makedirs(f".lit/objects/{hash[:2]}", exist_ok=True)
    with open(f".lit/objects/{hash[:2]}/{hash[2:]}", "wb") as file:
        file.write(zlib.compress(s))

    return hash

if __name__ == "__main__":
    main()
