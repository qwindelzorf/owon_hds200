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

    cmd = ":DATa:WAVe:SCReen:HEAD?"
    head = json.loads(scope.scpi_command(cmd).decode("utf-8"))

    for channel in head["CHANNEL"]:
        channel_name = channel["NAME"]
        channel_enabled = channel["DISPLAY"] == "ON"
        if channel_enabled:
            cmd = f":DATa:WAVe:SCReen:{channel_name}?"
            channel_data = scope.scpi_command(cmd)

            with open(f"out_{channel_name}.bin", "wb") as binfile:
                binfile.write(channel_data)
            with open(f"out_{channel_name}.csv", "w") as csvfile:
                for sample in channel_data:
                    csvfile.write(f"{sample}\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
