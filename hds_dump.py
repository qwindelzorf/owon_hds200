from owonPDS import pds6062
import sys


def main() -> int:
    scope = pds6062()
    scope.findDevice()
    if not scope.connected():
        print("No device found")
        return -1

    print("Scope found")
    return 0


if __name__ == "__main__":
    sys.exit(main())
