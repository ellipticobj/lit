import sys
import os
import zlib
import hashlib
import shutil
from utils import hashfile, decompfile, parseargs

# TODO: make a better argument parser

# hints
CATFILEHINT = "usage: lit catfile [-p | <type>] <hash>"
INITHINT = "usage: lit init"
HASHOBJECTHINT = "usage: lit hashobject [-w] <path>"
LSTREEHINT = "usage: lit lstree [--name-only] <hash>"
WRITETREEHINT = "usage: lit writetree"

def main():
    args = sys.argv[1:]

    if not args:
        print("usage: lit <command> [<args>]")
        return

    match args[0]:
        case 'init':
            if len(args) > 3:
                print(f"too many arguments\n{INITHINT}")
                return

            print(init())

        case 'catfile':
            print(catfile(args[1:]))

        case 'hashobject':
            print(hashobject(args[1:]))

        case 'writetree':
            print(writetree(args[1:]))

        case 'lstree':
            res = lstree(args[1:])

            if not isinstance(res, list):
                print(res)
                return
            elif isinstance(res, list):
                for item in res:
                    print(item)

        case other:
            print(f"unrecognized command {other}")

def init():
    if os.path.exists(f"{os.getcwd()}/.lit"):
        print("this directory is already a lit repository. \nare you sure you want to continue? (y/n) ", end="")
        resp = input().strip().lower()

        if resp == 'y':
            shutil.rmtree(f"{os.getcwd()}/.lit")
            print("deleted existing lit repository")
        elif resp == 'n':
            return
        else:
            print("n")
            return

    os.makedirs(f"{os.getcwd()}/.lit/objects")
    os.makedirs(f"{os.getcwd()}/.lit/refs")

    with open(f"{os.getcwd()}/.lit/HEAD", "w") as file:
        file.write("ref: refs/heads/main\n")

    return "initialized a repository\ncurrent branch is main"

def catfile(args):
    if len(args) < 2:
        return f"command requires two arguments\n{CATFILEHINT}"

    recognizedflags = ["-p"]
    flags, args = parseargs(args)

    if not set(flags).issubset(recognizedflags):
        return f"unrecognized flag\n{CATFILEHINT}"

    if len(args) < 1:
        return f"too little arguments\n{CATFILEHINT}"
    elif 2 < len(args):
        return f"too many arguments\n{CATFILEHINT}"

    objtype = args[0] if len(args) == 3 else "blob"
    hash = args[-1] if len(args) == 2 else args[-1]

    if objtype not in ["blob", "tree", "commit"]:
        return f"unrecognized type {objtype}\n{CATFILEHINT}"

    if len(hash) != 40:
        return f"invalid hash {hash}\n{CATFILEHINT}"

    if flags:
        if len(args) != 1:
            return f"too many arguments\n{CATFILEHINT}"

        if '-p' in flags:
            # TODO: add pretty print
            try:
                _, _, content = decompfile(f"{os.getcwd()}/.lit/objects/{hash[0:2]}/{hash[2:]}")
                return content.decode().strip()
            except FileNotFoundError:
                return f"object {hash} not found"
        else:
            return f"unrecognized flag\n{CATFILEHINT}"

    elif objtype:
        try:
            conttype, _, content = decompfile(f"{os.getcwd()}/.lit/objects/{hash[0:2]}/{hash[2:]}")
            if conttype != objtype:
                return f"object {hash} is not a blob"
            return content.decode().strip()
        except FileNotFoundError:
            return f"object {hash} not found"

    else:
        try:
            _, _, content = decompfile(f"{os.getcwd()}/.lit/objects/{hash[0:2]}/{hash[2:]}")
            return content.decode().strip()
        except FileNotFoundError:
            return f"object {hash} not found"

def hashobject(args):
    if len(args) < 1:
        return f"command requires one argument\n{HASHOBJECTHINT}"
    elif len(args) > 2:
        return f"too many arguments\n{HASHOBJECTHINT}"

    flags, args = parseargs(args)
    type = 'blob'
    filename = args[0]

    try:
        filesize = os.path.getsize(filename)
    except FileNotFoundError:
        return f"file {filename} not found"

    if "-w" in flags:
        hash = hashfile(f"{os.getcwd()}/{filename}", filesize, write=True, type=type)
    else:
        hash = hashfile(f"{os.getcwd()}/{filename}", filesize, write=False, type=type)

    return hash

def lstree(args):
    if len(args) < 1:
        return f"too little arguments\n{LSTREEHINT}"

    if len(args) > 2:
        return f"too many arguments\n{LSTREEHINT}"

    flags, args = parseargs(args)

    hash = args[0].strip()
    res = []

    if len(hash) != 40:
        return f"hash shoould be 40 characters long but input is {len(hash)} characters only\n{LSTREEHINT}"

    try:
        type, size, content = decompfile(f"{os.getcwd()}/.lit/objects/{hash[:2]}/{hash[2:]}")
        content = content
        if type.decode() != "tree":
            return f"object {hash} is not a tree"

        if "--name-only" in flags:
            while content:
                header, content = content.split(b"\x00", maxsplit=1)
                _, name = header.decode().split(' ', maxsplit=1)
                content = content[40:]
                res.append(name)

        else:
            while content:
                mode, content = content.split(b" ", maxsplit=1)

                name, content = content.split(b"\x00", maxsplit=1)

                shahash = content[:40]
                content = content[40:]

                res.append(f"{mode.decode()} {name.decode()} {shahash.hex()}")

    except FileNotFoundError:
        return f"tree {hash} not found"
    return res

def writetree(args):
    if len(args) > 1:
        print("too many arguments\n{WRITETREEHINT}")
        return

    flags, args = parseargs(args)
    path = f"{args[0]}" if args else "./"

    if os.path.isfile(path):
        return hashfile(path)

    contents = sorted(
        os.listdir(path),
        key=lambda x: x if os.path.isfile(os.path.join(path, x)) else f"{x}/"
    )
    s = b""

    for item in contents:
        if item in [".lit"]:
            continue

        fullpath = os.path.join(path, item)

        if os.path.isfile(fullpath):
            itemhash = hashfile(fullpath)
            s += f"100644 {item}\x00{itemhash}".encode()
        else:
            subtreehash = writetree([fullpath])
            s += f"40000 {item}\x00{subtreehash}".encode()

    s = f"tree {len(s)}\x00".encode() + s
    hash = hashlib.sha1(s).hexdigest()

    os.makedirs(f"{os.getcwd()}/.lit/objects/{hash[:2]}", exist_ok=True)
    with open(f"{os.getcwd()}/.lit/objects/{hash[:2]}/{hash[2:]}", "wb") as file:
        file.write(zlib.compress(s))

    return hash

if __name__ == "__main__":
    main()
