#! /usr/bin/env/python3

from prompt_toolkit.shortcuts.prompt import PromptSession
from owonHDS import owonHDS
import sys

from prompt_toolkit import prompt
from prompt_toolkit.history import FileHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.shortcuts import input_dialog
from prompt_toolkit.styles import Style


def main() -> int:
    scope = owonHDS()
    scope.find_device()
    if not scope.dev:
        print("No device found")
        return -1
    else:
        print(f"Device found at port {scope.dev.port_number}:{scope.dev.address}\n\n")

    prompt_style = Style.from_dict(
        {
            "caret": "#ff0066",  # the prompt indicator
            "": "#00ff66",  # user input
        }
    )

    response = ""
    while True:
        try:
            cmd = prompt(
                message=[("class:caret", ">")],
                style=prompt_style,
                history=FileHistory("term_history.txt"),
                auto_suggest=AutoSuggestFromHistory(),
            )
        except KeyboardInterrupt:
            break

        cmd_parts = cmd.split()

        if not cmd_parts[0]:
            continue

        elif cmd_parts[0] == "exit" or cmd_parts[0] == "quit":
            break

        elif cmd_parts[0] == "dump" or cmd_parts[0] == "save":
            filename = ""
            if len(cmd_parts) != 2:
                filename = input_dialog(title="Save Last Response", text="Please provide a filename:").run()
            else:
                filename = cmd_parts[1]

            if not filename:
                print("Save cancelled")
                continue

            try:
                with open(filename, "w") as out_file:
                    out_file.write(response)
            except OSError as err:
                print(f"Invalid path: {err.strerror}")
                continue
            print(f"Last response saved to {filename}")

        elif cmd_parts[0] == "help":
            print("TODO: Help message goes here")
            pass

        else:
            response = scope.scpi_command(cmd)
            print(f"{response}\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
