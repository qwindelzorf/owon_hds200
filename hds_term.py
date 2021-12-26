#! /usr/bin/env/python3

from typing import Dict, Iterable

from owonHDS import owonHDS
from hexdump import hexdump
import sys

from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.completion import WordCompleter, NestedCompleter
from prompt_toolkit.history import FileHistory
from prompt_toolkit.lexers import PygmentsLexer
from prompt_toolkit.shortcuts import input_dialog
from prompt_toolkit.shortcuts.prompt import PromptSession
from prompt_toolkit.styles import Style
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.validation import Validator, ValidationError
from prompt_toolkit.completion import CompleteEvent, Completer, Completion
from prompt_toolkit.document import Document
from prompt_toolkit.completion.nested import NestedDict

from pygments.lexer import RegexLexer
from pygments.token import Generic, Text


class ScpiLexer(RegexLexer):
    name = "SCPI"
    aliases = ["scpi"]

    tokens = {
        "root": [
            (r":[^: ?]+", Generic.Inserted),
            (r".*\n", Text),
        ]
    }


class ScpiCompleter(NestedCompleter):
    """Exactly the same as NestedCompleter, but using ':' as the separator, rather than ' '"""

    def __repr__(self) -> str:
        return "ScpiCompleter(%r, ignore_case=%r)" % (self.options, self.ignore_case)

    def get_completions(self, document: Document, complete_event: CompleteEvent) -> Iterable[Completion]:
        separator = ":"

        # Split document.
        text = document.text_before_cursor.lstrip(separator)
        stripped_len = len(document.text_before_cursor) - len(text)

        # If there is a ":", check for the first term, and use a subcompleter.
        if separator in text:
            first_term = text.split(separator)[0]
            completer = self.options.get(first_term)

            # If we have a sub completer, use this for the completions.
            if completer is not None:
                remaining_text = text[len(first_term) :].lstrip(separator)
                move_cursor = len(text) - len(remaining_text) + stripped_len

                new_document = Document(
                    remaining_text,
                    cursor_position=document.cursor_position - move_cursor,
                )

                for c in completer.get_completions(new_document, complete_event):
                    yield c

        # No space in the input: behave exactly like `WordCompleter`.
        else:
            completer = WordCompleter(list(self.options.keys()), ignore_case=self.ignore_case)
            for c in completer.get_completions(document, complete_event):
                yield c


class ScpiValidator(Validator):
    """Validate that a message is a valid SCPI command

    Only works on full commands, not "on the fly"
    """

    def validate(self, document: Document) -> None:
        import re

        text = document.text
        m = re.search(r"([:\*]\w+)+(\?| \w+)", text)
        if not m:
            raise ValidationError(cursor_position=len(text), message="Invalid SCPI command")


def main() -> int:
    prompt_style = Style.from_dict(
        {
            "caret": "#ff0066",  # the prompt indicator
            "completion-menu.completion": "bg:#008888 #ffffff",
            "completion-menu.completion.current": "bg:#00aaaa #000000",
            "": "#00ff66",  # user input
        }
    )

    cmd_completer = WordCompleter(["exit", "quit", "save", "dump"])
    scpi_completer = ScpiCompleter.from_nested_dict(
        {
            "ACQuire": {"MODe", "DEPMem"},
            "CH1": {"DISPlay", "COUPling", "PROBe", "SCALe", "OFFSet"},
            "CH2": {"DISPlay", "COUPling", "PROBe", "SCALe", "OFFSet"},
            "DATa": {
                "WAVe": {
                    "SCReen": {
                        "CH": {"1", "2"},
                        "HEAD": None,
                        "BMP": None,  # undocumented - dump screen as bmp
                    },
                    "DEPMEM": {"ALL"},  # undocumented - dump screen as bin
                }
            },
            "HORizontal": {"SCALe", "OFFSet"},
            "TRIGger": {
                "STATus": None,
                "SINGle": {
                    "SOURce": None,
                    "COUPling": None,
                    "EDGe": {"LEVel"},
                    "SLOPe": None,
                    "SWEep": None,
                },
            },
            "MEASurement": {
                "DISPlay": None,
                "CH1": {"MAX", "MIN", "PKPK", "VAMP", "AVERage", "PERiod", "FREQuency"},
                "CH2": {"MAX", "MIN", "PKPK", "VAMP", "AVERage", "PERiod", "FREQuency"},
            },
            "CHANnel": None,
            "FUNCtion": {
                "FREQuency",
                "PERiod",
                "AMPLitude",
                "OFFset",
                "HIGHt",
                "LOW",
                "SYMMetry",
                "WIDTh",
                "DTYCycle",
                "LOAD",
            },
        }
    )

    kb = KeyBindings()

    @kb.add("tab")
    def _(event):
        "Initialize autocompletion, or select the next completion."
        buff = event.app.current_buffer
        if buff.complete_state:
            buff.complete_next()
        else:
            buff.start_completion(select_first=False)

    session: PromptSession = PromptSession(
        style=prompt_style,
        history=FileHistory("term_history.txt"),
        auto_suggest=AutoSuggestFromHistory(),
        complete_while_typing=True,
        completer=scpi_completer,
        lexer=PygmentsLexer(ScpiLexer),
        complete_in_thread=True,
        key_bindings=kb,
        # validator=ScpiValidator(),
        # validate_while_typing=False,
    )

    scope = owonHDS()
    scope.find_device()
    if not scope.dev:
        print("No device found")
        return -1
    else:
        id = scope.device_id()
        if id:
            print(f"Device {id.manufacturer} {id.model} found at port {scope.dev.port_number}:{scope.dev.address}\n\n")
        else:
            print("Device founc, but could not identify.")
            return -2

    response: bytes = b""
    while True:
        try:
            cmd = session.prompt([("class:caret", ">")])
        except KeyboardInterrupt:  # ctrl+c
            break
        except EOFError:  # ctrl+d
            break

        if not cmd:
            continue

        cmd_parts = cmd.split()
        if not cmd_parts[0]:
            continue

        elif cmd_parts[0] == "exit" or cmd_parts[0] == "quit":
            # breaking out of the loop is the "normal" exit path
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
                with open(filename, "wb") as out_file:
                    out_file.write(response)
            except OSError as err:
                print(f"Invalid path: {err.strerror}")
                continue
            print(f"Last response saved to {filename}")

        elif cmd_parts[0] == "help":
            print("- help:   Show this help message")
            print("- save:   Save the most recent response from the scope to a file.")
            print("- exit:   Quit the program")
            print("- ctrl+c: Quit the program")
            pass

        else:
            try:
                ScpiValidator().validate(Document(cmd))
                response = scope.scpi_command(cmd)
                out = hexdump(response, "return")
                out += f"\n<{len(response)} bytes>"
                print(f"{out}")
            except ValidationError:
                print(f'Invalid command. Not SCPI or keyword. type "help" for valid commands.')

    return 0


if __name__ == "__main__":
    sys.exit(main())
