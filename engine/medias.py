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

try:
    os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "hide"
    import pygame
except ImportError:
    raise ImportError("AudioPlayer requires pygame. install it first.")


class Player(object):
    """
    音频播放工具类，用于异步播放本地音频文件。
    """

    @staticmethod
    async def audio_player(audio_file: str, *_, **__) -> None:
        """
        异步播放指定的音频文件（支持常见音频格式）。

        使用 pygame 的音频引擎进行加载与播放。函数在播放期间会阻塞，直到播放结束。
        适用于需要在异步流程中播放提示音或语音反馈的场景。

        Parameters
        ----------
        audio_file : str
            音频文件的路径，支持 `.mp3`, `.wav`, `.ogg` 等格式。
        """
        pygame.mixer.init()
        pygame.mixer.music.load(audio_file)
        pygame.mixer.music.set_volume(1.0)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            await asyncio.sleep(0.1)


if __name__ == '__main__':
    pass
