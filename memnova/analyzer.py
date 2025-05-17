#      _                _
#     / \   _ __   __ _| |_   _ _______ _ __
#    / _ \ | '_ \ / _` | | | | |_  / _ \ '__|
#   / ___ \| | | | (_| | | |_| |/ /  __/ |
#  /_/   \_\_| |_|\__,_|_|\__, /___\___|_|
#                         |___/
#
# ==== Notes: License ====
# Copyright (c) 2024  Memrix :: 记忆星核
# This file is licensed under the Memrix :: 记忆星核 License. See the LICENSE.md file for more details.

import os
import random
import string
import typing
import asyncio
import aiofiles
import aiosqlite
import numpy as np
from loguru import logger
from datetime import datetime
from bokeh.io import (
    curdoc, output_file
)
from bokeh.plotting import (
    save, figure
)
from bokeh.models import (
    ColumnDataSource, Span, HoverTool,
    DatetimeTickFormatter, BoxAnnotation, Range1d
)
from jinja2 import (
    Environment, FileSystemLoader
)
from engine.tackle import DataBase
from memcore.display import Display
from memnova import const


class Analyzer(object):
    """
    Memrix 分析器类，用于生成内存测试报告，包括统计图表绘制与 HTML 页面渲染。

    该类负责读取采集数据库中的内存数据，提取前台与后台运行阶段的指标曲线，
    通过 Bokeh 绘制可交互图表，并基于 Jinja2 模板渲染完整的 HTML 报告页面。

    适用于批量测试后的数据分析与可视化场景。

    Parameters
    ----------
    db : aiosqlite.Connection
        已连接的异步 SQLite 数据库对象，包含内存采集结果表。

    download : str
        报告输出路径，所有生成的 HTML 图表与页面文件将保存至该目录。

    Attributes
    ----------
    db : aiosqlite.Connection
        采集数据数据库连接对象，供后续查询与分析调用。

    download : str
        报告输出路径，包含图表文件与最终报告 HTML 文件。
    """

    def __init__(self, db: "aiosqlite.Connection", download: str):
        self.db = db
        self.download = download

    async def form_report(self, template: str, *args, **kwargs) -> None:
        """
        渲染最终 HTML 报告页面，并保存至下载目录。

        使用 Jinja2 模板引擎将传入的统计结果、图表路径等数据注入 HTML 模板中。
        输出文件名以 `Inform_时间戳.html` 命名，存放在 `self.download` 指定目录。

        Parameters
        ----------
        template : str
            HTML 模板文件的绝对路径。

        *args :
            位置参数，传递给 Jinja2 模板。

        **kwargs :
            关键字参数，作为模板渲染上下文传入。

        Notes
        -----
        - 模板必须为合法 Jinja2 文件，包含可注入变量。
        - 输出文件编码遵循系统预设常量 `const.ENCODING`。
        - 模板与数据解耦，支持自定义报告样式与结构。
        """
        template_dir, template_file = os.path.dirname(template), os.path.basename(template)
        loader = FileSystemLoader(template_dir)
        environment = Environment(loader=loader)
        template = environment.get_template(template_file)
        html = template.render(*args, **kwargs)

        salt: "typing.Callable" = lambda: "".join(
            random.choices(string.ascii_uppercase + string.digits, k=5)
        )
        html_file = os.path.join(self.download, f"{const.APP_DESC}_Inform_{salt()}.html")

        async with aiofiles.open(html_file, "w", encoding=const.ENCODING) as f:
            await f.write(html)
            logger.info(html_file)

        Display.build_file_tree(html_file)

    async def draw_memory(self, data_dir: str) -> dict[str, str]:
        """
        生成指定数据目录下的前台与后台内存曲线图（HTML 格式），并返回关键统计结果。

        本方法将从数据库中提取对应轮次的数据，分别绘制前台（fg）与后台（bg）曲线图，
        每张图均包含：
        - PSS 曲线
        - 峰值 / 均值标记点与标注线
        - RSS / USS 数据悬浮提示
        - 当前 Activity 与 UID 优先级信息
        - 可隐藏图例、平滑颜色渐变、平均带宽区间标识

        Parameters
        ----------
        data_dir : str
            数据目录标识（即本轮采集数据的标记，用于生成报告路径和图表命名）。

        Returns
        -------
        dict[str, str]
            包含以下键的字典：
            - fg_max / bg_max：PSS 峰值（MB）
            - fg_avg / bg_avg：PSS 均值（MB）
            - fg_loc / bg_loc：图表文件相对路径
            - minor_title：本轮任务的标识标题

        Notes
        -----
        - 图表文件将以 `FG_<data_dir>.html` / `BG_<data_dir>.html` 命名
        - 所有图表使用 Bokeh 绘制，支持交互与动态图例
        - 如果数据缺失或结构异常，将自动跳过绘图并返回空结果
        - 输出路径结构为 `{download}/summary/{data_dir}/`
        """

        async def draw(file_name: str, data_list: list[tuple]) -> dict:
            """
            绘制指定数据列表的内存曲线图（PSS），并保存为交互式 HTML 文件。

            图表使用 Bokeh 构建，展示内存随时间变化的趋势线，并附带峰值、均值标记，
            支持自定义颜色、图例折叠、悬浮提示、横向辅助线等视觉信息。

            Parameters
            ----------
            file_name : str
                图表类型标识（如 "fg" 或 "bg"），用于文件命名与图例标识。

            data_list : list[tuple]
                从数据库中提取的原始内存数据，每项包含：
                (timestamp, rss, pss, uss, opss, activity, adj, foreground)

            Returns
            -------
            dict
                图表渲染后的统计信息字典，包含：
                - {file_name}_max : str
                    当前数据中的 PSS 峰值（单位 MB）
                - {file_name}_avg : str
                    当前数据中的 PSS 平均值（单位 MB）
                - {file_name}_loc : str
                    图表文件的相对路径（用于最终报告整合）

            Notes
            -----
            - 使用 Bokeh 的 HoverTool 提供悬浮提示，包括 PSS、RSS、USS、Activity 和 ADJ 状态
            - 峰值（红）、均值（粉）、最小值（绿）使用散点与辅助线标注
            - 图表输出位置为：`{download}/summary/{data_dir}/FG_*.html 或 BG_*.html`
            - 若数据为空或结构异常将返回空字典，不影响报告主流程
            """
            if not data_list:
                return {}

            try:
                timestamp, rss, pss, uss, opss, activity, adj, foreground = list(zip(*data_list))
            except ValueError:
                return {}

            data = {
                "x": [datetime.strptime(t, "%Y-%m-%d %H:%M:%S") for t in timestamp],
                "y": pss,
                "rss": rss,
                "uss": uss,
                "adj": adj,
                "foreground": foreground,
                "activity": [
                    (act.split("/")[-1] if "/" in act else act) if act else act for act in activity
                ],
            }

            avg_value, max_value, min_value = float(np.mean(pss)), max(pss), min(pss)

            data["colors"] = [
                "#FF4B00" if y == max_value else ("#00FF85" if y == min_value else "#FFBC00") for y in data["y"]
            ]
            data["sizes"] = [
                5 if y == max_value else (5 if y == min_value else 2) for y in data["y"]
            ]

            source = ColumnDataSource(data=data)
            p = figure(
                sizing_mode="stretch_both",
                x_axis_type="datetime",
                title="Memory Usage over Time",
                y_range=Range1d(min_value - 100 if min_value >= 100 else 0, max_value + 150)
            )
            p.line(
                "x", "y",
                source=source, line_width=1, alpha=0.8, color="#FFBC00", legend_label=file_name.upper()
            )

            p.scatter(
                "x", "y",
                source=source, size="sizes", color="colors", hover_fill_color="#DF9911", hover_alpha=0.5
            )

            p.scatter(color="#FF4B00", legend_label=f"峰值: {max_value:.2f} MB")
            p.scatter(color="#F900FF", legend_label=f"均值: {avg_value:.2f} MB")

            # 范围
            mid_box = BoxAnnotation(
                bottom=min_value, top=max_value, fill_alpha=0.1, fill_color="#0072B2"
            )
            p.add_layout(mid_box)

            # 平均线
            avg_line = Span(
                location=avg_value, dimension="width", line_color="#F900FF", line_dash="dotted", line_width=1
            )
            p.add_layout(avg_line)

            # 最大值
            max_line = Span(
                location=max_value, dimension="width", line_color="#FF4B00", line_dash="dotted", line_width=1
            )
            p.add_layout(max_line)

            # 最小值
            min_line = Span(
                location=min_value, dimension="width", line_color="#00FF85", line_dash="dotted", line_width=1
            )
            p.add_layout(min_line)

            # 悬浮提示
            tooltips = """
                <div style="background: linear-gradient(to bottom, #B6FBFF, #83A4D4); padding: 5px 10px;">
                    <div>
                        <span style="font-size: 17px;">PSS:</span>
                        <span style="font-size: 17px; font-weight: bold; color: #4B4B4B;">@y{0.00} MB</span>
                    </div>
                    <div>
                        <span style="font-size: 17px;">RSS:</span>
                        <span style="font-size: 17px; font-weight: bold; color: #4B4B4B;">@rss{0.00} MB</span>
                    </div>
                    <div>
                        <span style="font-size: 17px;">USS:</span>
                        <span style="font-size: 17px; font-weight: bold; color: #4B4B4B;">@uss{0.00} MB</span>
                    </div>

                    <hr style="border: 0; height: 1px; background-image: repeating-linear-gradient(to right, rgba(0,0,0,0.75), rgba(0,0,0,0.75) 1px, rgba(0,0,0,0) 1px, rgba(0,0,0,0) 5px);">

                    <div>
                        <span style="font-size: 17px;">时间轴:</span>
                        <span style="font-size: 17px; font-weight: bold; color: #9400D3;">@x{%H:%M:%S}</span>
                    </div>
                    <div>
                        <span style="font-size: 17px;">优先级:</span>
                        <span style="font-size: 17px; font-weight: bold; color: #483D8B;">@foreground</span>
                    </div>
                    <div>
                        <span style="font-size: 17px;">当前页:</span>
                        <span style="font-size: 17px; font-weight: bold; color: #006400;">@activity</span>
                    </div>
                </div>
            """

            hover = HoverTool(
                tooltips=tooltips, formatters={"@x": "datetime"}
            )
            p.add_tools(hover)

            p.xgrid.grid_line_color = "gray"
            p.ygrid.grid_line_color = "gray"
            p.xgrid.grid_line_alpha = 0.2
            p.ygrid.grid_line_alpha = 0.2

            p.xaxis.axis_label = "时间轴"
            p.yaxis.axis_label = "内存用量 (MB)"
            p.xaxis.major_label_orientation = 30 * np.pi / 180
            p.xaxis.formatter = DatetimeTickFormatter(
                microseconds="%H:%M:%S", milliseconds="%H:%M:%S", seconds="%H:%M:%S",
                minsec="%H:%M:%S", minutes="%Y-%m-%d %H:%M:%S",
                hourmin="%Y-%m-%d %H:%M:%S", hours="%Y-%m-%d %H:%M:%S",
                days="%Y-%m-%d %H:%M:%S", months="%Y-%m-%d %H:%M:%S", years="%Y-%m-%d %H:%M:%S"
            )

            p.legend.location = "top_left"
            p.legend.click_policy = "hide"
            p.legend.border_line_width = 2
            p.legend.border_line_color = "#11D2DF"
            p.legend.border_line_alpha = 0.1
            p.legend.background_fill_color = "#DFC911"
            p.legend.background_fill_alpha = 0.1
            p.background_fill_color = "#ECE9E6"
            p.background_fill_alpha = 0.2

            # 主题
            curdoc().theme = "light_minimal"

            file_path = os.path.join(group, f"{file_name.upper()}_{data_dir}.html")
            output_file(file_path)
            save(p)

            return {
                f"{file_name}_max": f"{float(max_value):.2f}",
                f"{file_name}_avg": f"{float(avg_value):.2f}",
                f"{file_name}_loc": os.path.join(const.SUMMARY, data_dir, os.path.basename(file_path))
            }

        fg_list, bg_list = await DataBase.query_data(self.db, data_dir)
        os.makedirs(group := os.path.join(self.download, const.SUMMARY, data_dir), exist_ok=True)

        fg_data_dict, bg_data_dict = await asyncio.gather(
            draw("fg", fg_list), draw("bg", bg_list)
        )

        logger.info(f"{data_dir} Handler Done ...")

        return fg_data_dict | bg_data_dict | {"minor_title": data_dir}


if __name__ == '__main__':
    pass
