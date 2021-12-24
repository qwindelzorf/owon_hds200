#! /usr/bin/env/python3

from owonPDS import pds6062
import sys
from hexdump import hexdump


def main() -> int:
    scope = pds6062()
    scope.findDevice()
    if not scope.connected():
        print("No device found")
        return -1

    print("Device found")

    # data = scope._readMemory(32767)
    # if data is None:
    #     print("Unable to read device")
    #     return -2

    # print(f"Read {len(data)} bytes")
    # hexdump(data[0:256])

    # with open("out.bin", "wb") as binfile:
    #     binfile.write(data)

    cmd = ":DATa:WAVe:SCReen:HEAD?"
    resp = scope.scpi_command(cmd)
    print(f"{cmd} -> {resp}")

    cmd = ":DATa:WAVe:SCReen:CH1?"
    resp = scope.scpi_command(cmd)
    print(f"{cmd} -> {resp}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
