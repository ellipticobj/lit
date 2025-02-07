import sys
import os
import zlib
import hashlib

def main():
    args = sys.argv[1:]

    if not args:
        # TODO: add instructions
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

        case other:
            print(f"unrecognized command {other}")

def init():
    if os.path.exists(".lit") and os.path.exists(".lit/objects") and os.path.exists(".lit/refs") and os.path.exists(".lit/HEAD"):
        print("this directory is already a lit repository. \nare you sure you want to continue? (y/n) ", end="")
        resp = input()

        if resp.lower() != 'y':
            print("n")
            return

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
    if len(args) > 2:
        print("too many arguments for command `lit catfile`")
        return
    # TODO: add support for other object types
    if args[0] == "blob" or args[0] == "-p":
        # read a blob
        hash = args[1]
        with open(f".lit/objects/{hash[0:2]}/{hash[2:]}", "rb") as file:
            type, size, content = decompfile(file.read())
            print(content)

    else:
        print(f"unrecognized object type {args[1]}\nthis is NOT a full implementation. only blobs are supported for this command.")

def hashobject(args):
    # TODO: implement type declaration
    type = 'blob'

    if args[0] == '-w':
        filename = args[1]
    else:
        filename = args[0]

    try:
        filesize = os.path.getsize(filename)
    except FileNotFoundError:
        print(f"file {filename} not found")
        return

    with open(filename, "r") as file:
        compressed = zlib.compress(f"{type} {filesize}\x00{file.read()}".encode())

    hash = hashlib.sha1(compressed).hexdigest()
    dir, file = hash[:2], hash[2:]

    if not os.path.exists(f".lit/objects/{dir}"):
        os.mkdir(f".lit/objects/{dir}")

    with open(f".lit/objects/{dir}/{file}", "wb") as file:
        file.write(compressed)

    print(hash)

if __name__ == "__main__":
    main()
