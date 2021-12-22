from abc import ABC, abstractmethod

import usb.core
import usb.util


class owonPDS(ABC):
    __OWON_VENDOR_ID = 0x5345
    __OWON_SCOPE_PRODUCT_ID = 0x1234
    _READ_ENDPOINT = 0x81
    _WRITE_ENDPOINT = 0x03

    def __init__(self):
        self.dev = None

    def findDevice(self) -> bool:
        self.dev = usb.core.find(idVendor=0x5345, idProduct=0x1234)
        return self.connected()

    def connected(self) -> bool:
        return self.dev != None


class pds6062(owonPDS):
    _WRITE_ENDPOINT = 0x01
