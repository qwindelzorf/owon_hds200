#! /usr/bin/env/python3

from owonHDS import owonHDS
import sys
import json


def main() -> int:
    scope = owonHDS()
    scope.find_device()
    if not scope.dev:
        print("No device found")
        return -1

    for channel in scope.enabled_channels():
        channel_data = scope.get_data(channel)

        with open(f"out_{channel}.bin", "wb") as binfile:
            binfile.write(channel_data)
        with open(f"out_{channel}.csv", "w") as csvfile:
            for sample in channel_data:
                csvfile.write(f"{sample}\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
