from typing import List, Optional
from hexdump import hexdump

import usb.core
import usb.util


class owonHDS:
    __OWON_VENDOR_ID = 0x5345
    __OWON_SCOPE_PRODUCT_ID = 0x1234
    __DEFAULT_INTERFACE = 0x00
    __DEFAULT_CONFIGURATION = 0x01
    _READ_ENDPOINT = 0x81
    _WRITE_ENDPOINT = 0x01

    def __init__(self):
        self.dev: Optional[usb.core.Device] = None

    def _config_device(self) -> Optional[usb.core.Configuration]:
        cfg = None
        if self.dev:
            try:
                cfg = self.dev.get_active_configuration()
            except usb.core.USBError:
                pass

            if cfg is None or cfg.bConfigurationValue != self.__DEFAULT_CONFIGURATION:
                self.dev.set_configuration(self.__DEFAULT_CONFIGURATION)
                cfg = self.dev.get_active_configuration()
        return cfg

    def scpi_command(self, cmd: str) -> str:
        cmd = cmd.upper()
        if not self.dev:
            return ""
        cfg = self._config_device()
        if not cfg:
            return ""

        termination = "\r\n"
        if not cmd.endswith(termination):
            cmd += termination

        self.dev.reset()
        usb.util.claim_interface(self.dev, self.__DEFAULT_INTERFACE)

        self.dev.clear_halt(self._WRITE_ENDPOINT)
        if self.dev.write(self._WRITE_ENDPOINT, cmd) != len(cmd):
            return ""
        self.dev.clear_halt(self._WRITE_ENDPOINT)

        response: str = ""
        block = usb.util.create_buffer(16 * 1024)
        total_bytes: int = 0

        self.dev.clear_halt(self._READ_ENDPOINT)

        while True:
            read_bytes = 0
            try:
                read_bytes = self.dev.read(self._READ_ENDPOINT, block, 100)
                total_bytes += read_bytes

                response += f"<{read_bytes} bytes>\n"
                response += hexdump(block[:read_bytes], "return")
                response += "\n"

            except usb.core.USBTimeoutError:
                # This is the expected exit path from the loop
                break
            except usb.core.USBError as err:
                if err.errno == 75:  # overflow
                    response += f"<{read_bytes} bytes with overflow>\n"
                    continue
                raise err  # re-throw
        self.dev.clear_halt(self._READ_ENDPOINT)

        response += f"\n<{total_bytes} total bytes>"
        return response

    def find_device(self) -> bool:
        self.dev = usb.core.find(idVendor=self.__OWON_VENDOR_ID, idProduct=self.__OWON_SCOPE_PRODUCT_ID)
        if self.dev:
            self.dev.reset()
            return True
        return False
