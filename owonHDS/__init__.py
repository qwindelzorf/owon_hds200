from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

import usb.core
import usb.util


@dataclass
class deviceID:
    manufacturer: str
    model: str
    serial: str
    version: str


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

    def find_device(self) -> bool:
        self.dev = usb.core.find(idVendor=self.__OWON_VENDOR_ID, idProduct=self.__OWON_SCOPE_PRODUCT_ID)
        if self.dev:
            self.dev.reset()
            return True
        return False

    def scpi_command(self, cmd: str) -> bytes:
        if not cmd:
            return b""

        cmd = cmd.upper()
        response_expected: bool = cmd.rstrip().endswith("?")

        # Reference java app has termination, but it doesn't seem to be necessary.
        # termination = "\r\n"
        # if not cmd.endswith(termination):
        #     cmd += termination

        if not self.dev:
            return b""
        cfg = self._config_device()
        if not cfg:
            return b""

        self.dev.reset()
        usb.util.claim_interface(self.dev, self.__DEFAULT_INTERFACE)

        self.dev.clear_halt(self._WRITE_ENDPOINT)
        if self.dev.write(self._WRITE_ENDPOINT, cmd) != len(cmd):
            return b""
        self.dev.clear_halt(self._WRITE_ENDPOINT)

        if not response_expected:
            return b""

        block = usb.util.create_buffer(16 * 1024)
        response: bytes = b""
        total_bytes: int = 0

        while True:
            read_bytes = 0
            try:
                read_bytes = self.dev.read(self._READ_ENDPOINT, block, 100)
                total_bytes += read_bytes
                response += block.tobytes()[0:read_bytes]

            except usb.core.USBTimeoutError:
                # This is the expected exit path from the loop
                break
            except usb.core.USBError as err:
                if err.errno == 75:  # overflow
                    continue
                raise err  # re-throw
        self.dev.clear_halt(self._READ_ENDPOINT)

        trimmed_response = response[response.rfind(0) + 1 :]
        return trimmed_response

    def device_id(self) -> Optional[deviceID]:
        data = self.scpi_command("*IDN?")
        if not data:
            return None

        id = data.decode("ascii").rstrip().split(",")
        if not id:
            return None
        if not len(id) == 4:
            return None

        return deviceID(manufacturer=id[0], model=id[1], serial=id[2], version=id[3])
