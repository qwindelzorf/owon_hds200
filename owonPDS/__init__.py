from abc import ABC, abstractmethod
from array import array
from typing import List, Optional
from hexdump import hexdump

import usb.core
import usb.util


class owonPDS(ABC):
    __OWON_VENDOR_ID = 0x5345
    __OWON_SCOPE_PRODUCT_ID = 0x1234
    __DEFAULT_INTERFACE = 0x00
    __DEFAULT_CONFIGURATION = 0x01
    _READ_ENDPOINT = 0x81
    _WRITE_ENDPOINT = 0x03

    def __init__(self):
        self.dev: Optional[usb.core.Device] = None

    def _configDevice(self) -> Optional[usb.core.Configuration]:
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
        if not self.dev:
            return ""
        cfg = self._configDevice()
        if not cfg:
            return ""

        self.dev.reset()
        usb.util.claim_interface(self.dev, self.__DEFAULT_INTERFACE)

        self.dev.clear_halt(self._WRITE_ENDPOINT)
        if self.dev.write(self._WRITE_ENDPOINT, cmd) != len(cmd):
            return ""
        self.dev.clear_halt(self._WRITE_ENDPOINT)

        response: str = ""
        block = usb.util.create_buffer(2048)
        total_bytes = 0

        self.dev.clear_halt(self._READ_ENDPOINT)

        while True:
            try:
                read_bytes = self.dev.read(self._READ_ENDPOINT, block, 10)
                total_bytes += read_bytes

                try:
                    response += block.tobytes().decode("ascii")
                except UnicodeDecodeError:
                    print(f"{read_bytes} undecodable bytes:")
                    hexdump(block[:read_bytes])
                    print("\n")
                    response += f"<{read_bytes} bytes>"
                    pass

            except usb.core.USBTimeoutError:
                break
        self.dev.clear_halt(self._READ_ENDPOINT)

        return response.split("\0")[-1]

    def findDevice(self) -> bool:
        self.dev = usb.core.find(idVendor=self.__OWON_VENDOR_ID, idProduct=self.__OWON_SCOPE_PRODUCT_ID)
        if self.dev:
            self.dev.reset()
            return True
        return False

    def connected(self) -> bool:
        return self.dev != None


class pds6062(owonPDS):
    _WRITE_ENDPOINT = 0x01
