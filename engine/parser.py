import argparse
from engine import const


class Parser(object):

    @staticmethod
    def parse_cmd() -> "argparse.Namespace":
        parser = argparse.ArgumentParser(
            const.NAME, usage=None, description=f"Command Line Arguments {const.DESC}"
        )

        return parser.parse_args()


if __name__ == '__main__':
    pass
