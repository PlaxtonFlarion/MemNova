#   __  __          _ _
#  |  \/  | ___  __| (_) __ _ ___
#  | |\/| |/ _ \/ _` | |/ _` / __|
#  | |  | |  __/ (_| | | (_| \__ \
#  |_|  |_|\___|\__,_|_|\__,_|___/
#
# ==== Notes: License ====
# Copyright (c) 2024  Memrix :: 记忆星核
# This file is licensed under the Memrix :: 记忆星核 License. See the LICENSE.md file for more details.

import os
import asyncio
from pathlib import Path
from loguru import logger
from memcore.api import Api
from memnova import const

try:
    os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "hide"
    import pygame
except ImportError:
    raise ImportError("AudioPlayer requires pygame. install it first.")


class Player(object):
    """
    音频播放工具类，用于异步播放本地音频文件。
    """

    def __init__(self, opera_place: str, allowed_extra: list):
        self.opera_place = opera_place
        self.allowed_extra = allowed_extra

    async def audio_player(self, audio_file: str, *_, **__) -> None:
        """
        异步播放指定的音频文件（支持常见音频格式）。

        使用 pygame 的音频引擎进行加载与播放。函数在播放期间会阻塞，直到播放结束。
        适用于需要在异步流程中播放提示音或语音反馈的场景。

        Parameters
        ----------
        audio_file : str
            音频文件的路径，支持 `.mp3`, `.wav`, `.ogg` 等格式。
        """
        if (speech := Path(audio_file)).is_file():
            speech_file = audio_file
        else:
            speech_file = await Api.synthesize(
                speech.stem, speech.suffix or const.WAVERS, self.opera_place, self.allowed_extra
            )

        pygame.mixer.init()
        pygame.mixer.music.load(speech_file)
        pygame.mixer.music.set_volume(1.0)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            await asyncio.sleep(0.1)


if __name__ == '__main__':
    pass
