#! /usr/bin/env/python3

from colorama.ansi import Fore
from prompt_toolkit.shortcuts.prompt import PromptSession
from owonPDS import pds6062
import sys

from prompt_toolkit import prompt
from prompt_toolkit.history import FileHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.styles import Style


def main() -> int:
    scope = pds6062()
    scope.findDevice()
    if not scope.connected():
        print("No device found")
        return -1

    print("Device found\n\n")

    while True:

        try:
            cmd = prompt(
                [("class:caret", ">")],
                style=Style.from_dict({"caret": "#ff0066", "": "#00ff66"}),
                history=FileHistory("history.txt"),
                auto_suggest=AutoSuggestFromHistory(),
            )
        except KeyboardInterrupt:
            break
        else:
            if cmd:
                resp = scope.scpi_command(cmd)
                print(f"{resp}\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
