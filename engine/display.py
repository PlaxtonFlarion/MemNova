import os
import time
from memnova import const
from engine.tackle import Grapher


loading_frames = [
    """[bold #39FFE4]     ~~~         ~~~        ~~~        ~~~
   /     \\     /     \\    /     \\    /     \\
  | (• •) |---| (• •) |--| (• •) |--| (• •) |
   \\_v__/_     \\__v__/    \\__v__/    \\__v__/
     |||         |||        |||        |||
     ===         ===        ===        ===    """,
    """[bold #00FF9F]     ~~~        ~~~         ~~~        ~~~
  /     \\    /     \\     /     \\    /     \\
 | (• •) |--| (• •) |---| (• •) |--| (• •) |
  \\__v__/    \\_v__/_     \\__v__/    \\__v__/
     |||         |||        |||        |||
     ===         ===        ===        ===    """,
    """[bold #99FFCC]     ~~~        ~~~        ~~~         ~~~
  /     \\    /     \\    /     \\     /     \\
 | (• •) |--| (• •) |--| (• •) |---| (• •) |
  \\__v__/    \\__v__/    \\_v__/_     \\__v__/
     |||         |||        |||        |||
     ===         ===        ===        ===    """
]

banner = r"""[bold #00D7AF] __  __                     _     
|  \/  | ___ _ __ ___  _ __(_)_  __
| |\/| |/ _ \ '_ ` _ \| '__| \ \/ /
| |  | |  __/ | | | | | |  | |>  < 
|_|  |_|\___|_| |_| |_|_|  |_/_/\_\
"""


class Display(object):

    @staticmethod
    def clear():
        os.system('cls' if os.name == 'nt' else 'clear')

    @staticmethod
    def show_logo():
        Grapher.console.print(banner)

    @staticmethod
    def show_license():
        Grapher.console.print(const.APP_DECLARE)

    @staticmethod
    def show_animate():
        Display.clear()
        for _ in range(3):
            for frame in loading_frames:
                Display.clear()
                Grapher.console.print(frame)
                time.sleep(0.2)
        Grapher.console.print(
            f"[bold #00FF87]{{ {const.APP_DESC} Wave Linking... Aligning... Done. }}"
        )
        Grapher.console.print(
            f"[bold #00FF87]{{ {const.APP_DESC} Core Initialized. }}\n"
        )


if __name__ == "__main__":
    pass
