import sys
import os

class TooManyArguments(Exception):
    pass

class NotEnouchArguments(Exception):
    pass

class UnrecognizedCommand(Exception):
    pass

def main():
    args = sys.argv[1:]

    if not args:
        # TODO: add instructions
        return

    match args[0]:
        case 'init':
            if len(args) > 2:
                raise TooManyArguments("too many arguments for command `lit init`")

            if os.path.exists(".lit") and os.path.exists(".lit/objects") and os.path.exists(".lit/refs") and os.path.exists(".lit/HEAD"):
                print("this directory is already a lit repository. \nare you sure you want to continue? (y/n) ", end="")
                resp = input()

                if resp.lower() == 'y':
                    return init()
                else:
                    print("n")
                    return

            return init()

        case 'catfile':
            if len(args) < 2:
                return NotEnouchArguments("not enough arguments for command `lit catfile`")

            return catfile(args[1:])

        case other:
            raise UnrecognizedCommand(f"unrecognized command {other}")

def init():
    os.mkdir(".lit")
    os.mkdir(".lit/objects")
    os.mkdir(".lit/refs")

    with open(".lit/HEAD", "w") as file:
        file.write("ref: refs/heads/main\n")

    print("initialized a repository")
    print("current branch is named main") # TODO: make some way for users to switch branches
    return "lit init"

def catfile(args):
    # TODO: add support for other object types
    if args[1] == "blob":
        if args[2].startswith("-"):
            # TODO: handle flags here
            pass

        hash = args[2]
        try:
            with open(f".lit/objects/{hash[0:1]}/{hash[2:]}", "r") as file:
                print(file.read())
        except:
            raise FileNotFoundError(f"object {hash} not found")

    else:
        return UnrecognizedCommand(f"unrecognized object type {args[1]}\nthis is NOT a full git implementation. currently, only blobs are supported for this command.")

if __name__ == "__main__":
    main()
