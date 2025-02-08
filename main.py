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

            print(init())

        case 'catfile':
            if len(args) < 3:
                print("command requires two arguments\nusage: lit catfile <type> <hash>")
                return

            print(catfile(args[1:]))

        case 'hashobject':
            if len(args) < 2:
                print("command requires one argument\nusage: lit hashobject <filename>")
                return
            elif len(args) > 3:
                print("too many arguments for command `lit hashobject`")
                return

            print(hashobject(args[1:]))

        case 'writetree':
            print(writetree(args[1:]))

        case 'lstree':
            if len(args) != 2:
                print("command requires one argument\nusage: lit lstree <hash>")
                return

            print(*lstree(args[1:]))

        case other:
            print(f"unrecognized command {other}")

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
    return type, size, content

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

    return "initialized a repository\ncurrent branch is main"

def catfile(args):
    recognizedflags = ["-p"]
    flags, args = parseargs(args)
    # TODO: add support for other object types
    if not set(flags).issubset(recognizedflags):
        print("unrecognized flag\nusage: lit catfile [-p | <type>] <hash>")
        return

    if len(args) < 1:
        print("too little arguments\nusage: lit catfile [-p | <type>] <hash>")
        return
    elif 2 < len(args):
        print("too many arguments\nusage: lit catfile [-p | <type>] <hash>")
        return


    type = args[0] if len(args) == 2 else None
    hash = args[-1] if len(args) == 2 else args[-1]

    if len(hash) != 40:
        print(f"invalid hash {hash}\nusage: lit catfile [-p | <type>] <hash>")
        return

    if flags:
        if len(args) != 1:
            print("too many arguments\nusage: lit catfile [-p | <type>] <hash>")
            return
        if '-p' in flags:
            try:
                with open(f".lit/objects/{hash[0:2]}/{hash[2:]}", "rb") as file:
                    conttype, size, content = decompfile(file.read())
                    return content.decode().strip()
            except FileNotFoundError:
                print(f"object {hash} not found")
                return

    elif type:
        try:
            with open(f".lit/objects/{hash[0:2]}/{hash[2:]}", "rb") as file:
                conttype, size, content = decompfile(file.read())
                if conttype != type:
                    print(f"object {hash} is not a blob")
                    return
                return content.decode().strip()
        except FileNotFoundError:
            print(f"object {hash} not found")
            return

    else:
        try:
            with open(f".lit/objects/{hash[0:2]}/{hash[2:]}", "rb") as file:
                conttype, size, content = decompfile(file.read())
                return content.strip()
        except FileNotFoundError:
            print(f"object {hash} not found")
            return

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

    return hash

def lstree(args):
    flags, args = parseargs(args)

    hash = args[0].strip()
    res = []

    if len(hash) != 40:
        print(f"hash shoould be 40 characters long but input is {len(hash)} characters only\nusage: lit lstree <hash>")
        return []

    try:
        with open(f".lit/objects/{hash[:2]}/{hash[2:]}", "rb") as file:
            type, size, content = decompfile(file.read())
            content = content.decode()
            if type != "tree":
                print(f"object {hash} is not a tree")
                return []

            if "--name-only" in flags:
                while content:
                    header, content = content.split("\x00", maxsplit=1)
                    _, name = header.split(' ', maxsplit=1)
                    content = content[40:]
                    res.append(name)

            else:
                while content:
                    mode, content = content.split(" ", maxsplit=1)

                    #TODO: find some way to fix this
                    print(content)
                    name, content = content.split("\x00", maxsplit=1)

                    shahash = content[:40]
                    content = content[40:]

                    print(f"mode: {mode}\nname: {name}\nhash: {shahash}")
                    res.append(f"{mode} {name} {shahash}")

    except FileNotFoundError:
        print(f"tree {hash} not found")
    # return res

def writetree(args):
    flags, args = parseargs(args)
    path = args[0] if args else "./"

    if os.path.isfile(path):
        return hashfile(path)

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
            ithash = hashfile(fullpath)
            s += f"100644 {item}\x00{ithash}".encode()
        else:
            subtreehash = writetree([fullpath])
            s += f"40000 {item}\x00{subtreehash}".encode()

    s = f"tree {len(s)}\x00{s}".encode()
    hash = hashlib.sha1(s).hexdigest()

    os.makedirs(f".lit/objects/{hash[:2]}", exist_ok=True)
    with open(f".lit/objects/{hash[:2]}/{hash[2:]}", "wb") as file:
        file.write(zlib.compress(s))

    return hash

if __name__ == "__main__":
    main()
