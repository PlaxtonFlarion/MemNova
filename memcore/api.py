#      _          _
#     / \   _ __ (_)
#    / _ \ | '_ \| |
#   / ___ \| |_) | |
#  /_/   \_\ .__/|_|
#          |_|
#
# ==== Notes: License ====
# Copyright (c) 2024  Memrix :: 记忆星核
# This file is licensed under the Memrix :: 记忆星核 License. See the LICENSE.md file for more details.

import os
import re
import typing
from loguru import logger
from engine.channel import (
    Channel, Messenger
)
from memcore import authorize
from memnova import const


class Api(object):
    """
    Api

    通用异步接口适配器类，封装各类与远程服务交互的静态方法，包括数据获取、
    文件生成、命令配置加载等逻辑，适用于微服务通信、TTS 服务、自动化平台等场景。

    当前支持的服务包括语音格式元信息拉取、语音合成任务、业务用例命令获取等。
    所有接口方法均通过异步方式与后端 API 通信，支持 JSON 响应解析及异常处理。

    Notes
    -----
    - 提供统一的参数打包与请求流程，封装远程接口调用的细节。
    - 支持动态参数拼接、异常捕获、数据缓存与文件写入。
    - 可根据实际业务场景扩展其他静态方法，如上传日志、获取配置、拉取资源等。
    """

    background: list = []

    @staticmethod
    async def ask_request_get(
        url: str, key: typing.Optional[str] = None, *_, **kwargs
    ) -> dict:
        """
        通用异步 GET 请求方法。

        构造带参数的异步 GET 请求，自动附带默认参数并发送到指定 URL。支持从响应中提取指定字段，
        用于统一的业务数据获取流程，如模板信息、配置元数据等。

        Parameters
        ----------
        url : str
            请求的目标接口地址。

        key : str, optional
            可选的响应字段键名，若提供则返回对应字段的内容，否则返回整个响应字典。

        *_
            保留参数，未使用。

        **kwargs
            追加到请求参数中的动态键值对，用于拼接请求 query 参数。

        Returns
        -------
        dict
            远程服务返回的 JSON 数据（或提取后的字段值）。
        """
        params = Channel.make_params() | kwargs
        async with Messenger() as messenger:
            resp = await messenger.poke("GET", url, params=params)
            return resp.json()[key] if key else resp.json()

    @staticmethod
    async def formatting() -> typing.Optional[dict]:
        """
        获取远程 TTS 服务的可用状态及支持的音频格式列表。

        Returns
        -------
        dict or None
            {
                "enabled": bool,       # 服务可用状态
                "formats": list[str],  # 支持的音频格式列表
                ...                    # 其他元信息
            }
            若服务不可用或请求异常，则返回 None。
        """
        try:
            sign_data = await Api.ask_request_get(const.SPEECH_META_URL)
            auth_info = authorize.verify_signature(sign_data)
        except Exception as e:
            return logger.debug(e)

        return auth_info.get("mode", {})

    @staticmethod
    async def profession(case: str) -> dict:
        """
        根据指定用例名从业务接口获取命令列表。

        通过异步请求远程业务系统，加载指定 case 的命令配置数据。

        Parameters
        ----------
        case : str
            用例名称，用于作为参数查询业务命令配置。

        Returns
        -------
        dict
            返回包含命令配置的字典组成结构。
        """
        params = Channel.make_params() | {"case": case}
        async with Messenger() as messenger:
            resp = await messenger.poke("GET", const.BUSINESS_CASE_URL, params=params)
            return resp.json()

    @staticmethod
    async def fetch_template_file(url: str, template_name: str) -> str:
        """
        异步获取远程模板文件内容。

        本方法通过指定的 URL 与模板名称组合构建请求参数，
        并使用 Messenger 客户端发起 GET 请求，获取模板内容。

        Parameters
        ----------
        url : str
            远程请求的基础地址（如模板服务接口地址）。

        template_name : str
            模板文件名称，用于作为查询参数 "page" 的值。

        Returns
        -------
        str
            请求返回的模板文件内容字符串。
        """
        params = Channel.make_params() | {"page": template_name}
        async with Messenger() as messenger:
            resp = await messenger.poke("GET", url, params=params)
            return resp.text

    @staticmethod
    async def synthesize(speak: str, allowed_extra: list) -> tuple[str, bytes]:
        """
        合成文本语音并返回文件名及二进制内容。

        Parameters
        ----------
        speak : str
            待合成的文本内容。可带有扩展名（如 "你好.mp3"），如无扩展名，则自动添加默认扩展名。

        allowed_extra : list of str
            支持的音频文件扩展名列表，例如 ["mp3", "wav"]，用于判定输出格式。

        Returns
        -------
        tuple of (str, bytes)
            - 文件名（已去除非法字符和自动拼接扩展名），如 "你好.mp3"
            - 合成后音频文件的二进制内容
        """
        allowed_ext = {ext.lower().lstrip(".") for ext in allowed_extra}
        logger.debug(f"Allowed ext -> {allowed_ext}")

        stem, waver = os.path.splitext((speak or "").strip())
        waver = waver.lower().lstrip(".")
        if waver not in allowed_ext or not waver:
            waver = (next(iter(allowed_ext)) if allowed_ext else const.WAVERS)

        # 文件名去除非法字符
        final_speak = re.sub(r"[^a-zA-Z0-9\u4e00-\u9fff]+", "", stem)

        # 构建 payload
        payload = {"speak": final_speak, "waver": waver} | Channel.make_params()
        logger.debug(f"Remote synthesize: {payload}")

        try:
            async with Messenger() as messenger:
                resp = await messenger.poke("POST", const.SPEECH_VOICE_URL, json=payload)
                logger.debug(f"Download url: {(download_url := resp.json()['url'])}")

                resp = await messenger.poke("GET", download_url)

        except Exception as e:
            logger.debug(e)

        return final_speak + "." + waver, resp.content

    @staticmethod
    async def remote_config() -> typing.Optional[dict]:
        """
        获取远程配置中心的全局配置数据。
        """
        try:
            sign_data = await Api.ask_request_get(const.GLOBAL_CF_URL)
            auth_info = authorize.verify_signature(sign_data)
        except Exception as e:
            return logger.debug(e)

        return auth_info.get("configuration", {})

    @staticmethod
    async def online_template_meta() -> typing.Optional[dict]:
        """
        获取模版元信息。
        """
        try:
            sign_data = await Api.ask_request_get(const.TEMPLATE_META_URL)
            auth_info = authorize.verify_signature(sign_data)
        except Exception as e:
            return logger.debug(e)

        return auth_info.get("template", {})

    @staticmethod
    async def online_toolkit_meta(platform: str) -> typing.Optional[dict]:
        """
        获取工具元信息。
        """
        try:
            sign_data = await Api.ask_request_get(const.TOOLKIT_META_URL, platform=platform)
            auth_info = authorize.verify_signature(sign_data)
        except Exception as e:
            return logger.debug(e)

        return auth_info.get("toolkit", {})


if __name__ == '__main__':
    pass
