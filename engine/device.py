import re


class Device(object):

    def __init__(self, serial: str):
        self.serial = serial

    def __str__(self):
        return f"<Device serial={self.serial}>"

    __repr__ = __str__


if __name__ == '__main__':
    pass
