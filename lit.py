import sys
import os

class TooManyArguments(Exception):
    def __init__(self, message=""):
        super().__init__(message)

def main():
    args = sys.argv[1:]

    if not args:
        # TODO: add instructions
        return

    match args[0]:
        case 'init':
            if len(args) > 2:
                raise TooManyArguments("too many arguments for command `lit init`")
        case other:
            raise RuntimeError(f"unrecognized command {other}")

def init():
    os.mkdir(".lit")
    os.mkdir(".lit/objects")
    os.mkdir(".lit/refs")

    with open(".lit/HEAD", "w") as file:
        file.write("ref: refs/heads/main\n")

    print("initialized a repository")
    print("current branch is named main") # TODO: make some way for users to switch branches

if __name__ == "__main__":
    main()
