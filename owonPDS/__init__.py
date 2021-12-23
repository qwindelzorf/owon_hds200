from abc import ABC, abstractmethod
from typing import List, Optional

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

    def _readMemory(self, numBytes: int) -> Optional[bytearray]:
        if not self.connected():
            return None

        cfg = self._configDevice()
        if cfg is None:
            return None

        data = bytearray()

        if self.dev and cfg:
            self.dev.reset()
            usb.util.claim_interface(self.dev, self.__DEFAULT_INTERFACE)

            start_cmd = "STARTBMP"
            self.dev.clear_halt(self._WRITE_ENDPOINT)
            if self.dev.write(self._WRITE_ENDPOINT, start_cmd) != len(start_cmd):
                return None

            self.dev.clear_halt(self._READ_ENDPOINT)
            data = self.dev.read(self._READ_ENDPOINT, numBytes)
        else:
            return None

        return data

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
