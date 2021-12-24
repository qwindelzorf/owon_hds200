#! /usr/bin/env/python3

from owonHDS import owonHDS
import sys
from hexdump import hexdump


def main() -> int:
    scope = owonHDS()
    scope.find_device()
    if not scope.dev:
        print("No device found")
        return -1

    cmd = ":DATa:WAVe:SCReen:CH1?"
    resp = scope.scpi_command(cmd)

    # with open("out.bin", "wb") as binfile:
    #     binfile.write(data)

    return 0


if __name__ == "__main__":
    sys.exit(main())
