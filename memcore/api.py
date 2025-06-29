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

import re
import json
import typing
import asyncio
from pathlib import Path
from loguru import logger
from engine.channel import (
    Channel, Messenger
)
from engine.tinker import FileAssist
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
    async def formatting() -> typing.Optional[list]:
        """
        获取支持的语音合成格式列表。

        异步从远程服务获取格式信息，若发生异常则返回 None 并记录日志。

        Returns
        -------
        list or None
            成功时返回格式字符串列表，例如 ["mp3", "ogg", "webm"]；
            若请求失败则返回 None。

        Raises
        ------
        Exception
            当远程请求或解析失败时捕获并记录日志，返回 None。
        """
        try:
            sign_data = await Api.ask_request_get(const.SPEECH_META_URL)
            auth_info = authorize.verify_signature(sign_data)
        except Exception as e:
            return logger.debug(e)

        return auth_info.get("formats", [])

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
    async def fetch_template_versions() -> dict:
        """
        从远程服务器拉取模板版本元信息。

        Returns
        -------
        dict
            远程模板名与版本号及其下载链接的映射。
        """
        params = Channel.make_params()
        async with Messenger() as messenger:
            resp = await messenger.poke("GET", const.TEMPLATE_META_URL, params=params)
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
    async def sync_templates(template_dir: "Path") -> None:
        """
        异步同步远程模板文件至本地目录。

        此方法会对比本地与远程的模板版本号，仅下载更新过的模板文件。
        同步完成后，会更新本地的版本信息文件（通常为 versions.json）。

        Parameters
        ----------
        template_dir : Path
            模板文件的本地保存目录，所有模板及其版本信息将写入此目录。

        Raises
        ------
        Exception
            当远程接口不可达、文件写入失败或解析错误等情况发生时，可能抛出异常。
        """
        template_dir.mkdir(parents=True, exist_ok=True)
        versions_file = template_dir / const.X_TEMPLATE_VERSION

        remote_versions = await Api.fetch_template_versions()

        try:
            locals_versions = json.loads(versions_file.read_text()) if versions_file.exists() else {}
        except (FileNotFoundError, json.JSONDecodeError):
            locals_versions = {}

        updated_local_version = locals_versions.copy()

        # 计算需要更新的模板
        if locals_versions:
            download_map = {
                name: info for name, info in remote_versions.items()
                if info["version"] > locals_versions.get(name, {}).get("version", "")
            }
        else:
            download_map = remote_versions

        # 更新本地版本记录
        for k, v in download_map.items():
            updated_local_version[k] = {"version": v["version"]}

        # 并发拉取模板内容
        download_list = await asyncio.gather(
            *(Api.fetch_template_file(v["url"], k) for k, v in download_map.items())
        )

        # 并发写入模板文件
        await asyncio.gather(
            *(FileAssist.describe_text(template_dir / k, content)
              for content, (k, _) in zip(download_list, download_map.items()))
        )

        # 写入版本信息文件
        await FileAssist.dump_json(versions_file, updated_local_version)

    @staticmethod
    async def synthesize(speak: str, waver: str, src_opera_place: str, allowed_extra: list) -> str:
        """
        合成语音音频文件。

        根据指定文本与音频格式生成语音文件，若已存在本地缓存则直接返回路径；
        否则通过远程接口获取下载链接并保存音频至本地。

        Parameters
        ----------
        speak : str
            要合成的语音内容。

        waver : str
            请求的音频格式后缀（如 'mp3'、'wav'）。

        allowed_extra : list
            支持的音频格式列表，仅这些格式会触发远程合成逻辑。

        src_opera_place : str
            本地语音文件根目录（将生成在其下的 VOICES 子目录中）。

        Returns
        -------
        str
            本地语音文件的绝对路径，或拼接后的默认字符串（当 waver 不被允许时）。
        """
        allowed_ext = {ext.lower().lstrip('.') for ext in allowed_extra}
        logger.debug(f"Allowed ext -> {allowed_ext}")

        # 清洗输入
        clean_speak = speak.strip()
        clean_waver = waver.strip().lower().lstrip(".")

        # 检查 speak 中是否包含扩展名
        match = re.search(r"\.([a-zA-Z0-9]{1,6})$", clean_speak)
        speak_ext = match.group(1).lower() if match else ""
        speak_stem = re.sub(r"\.([a-zA-Z0-9]{1,6})$", "", clean_speak)

        # 判断是否为音频请求
        if clean_waver in allowed_ext:
            final_speak = speak_stem
            final_waver = clean_waver
        elif speak_ext in allowed_ext:
            final_speak = speak_stem
            final_waver = speak_ext
        else:
            # 非音频请求，直接拼接返回
            combination = f"{clean_speak}.{clean_waver}" if clean_waver else clean_speak
            logger.debug(f"Non-audio request, combination -> {combination}")
            return combination

        # 构建文件名和本地缓存路径
        audio_name = str(Path(final_speak).with_suffix(f".{final_waver}"))

        if not (voices := Path(src_opera_place) / const.VOICES).exists():
            voices.mkdir(parents=True, exist_ok=True)

        if (audio_file := voices / audio_name).is_file():
            logger.debug(f"Local audio file: {audio_file}")
            return str(audio_file)

        # 构建 payload
        payload = {"speak": final_speak, "waver": final_waver} | Channel.make_params()
        logger.debug(f"Remote synthesize: {payload}")

        try:
            async with Messenger() as messenger:
                resp = await messenger.poke("POST", const.SPEECH_VOICE_URL, json=payload)
                logger.debug(f"Download url: {(download_url := resp.json()['url'])}")

                redis_or_r2_resp = await messenger.poke("GET", download_url)
                audio_file.write_bytes(redis_or_r2_resp.content)

        except Exception as e:
            logger.debug(e)

        return str(audio_file)

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


if __name__ == '__main__':
    pass
