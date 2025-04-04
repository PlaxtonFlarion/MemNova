#      _                _
#     / \   _ __   __ _| |_   _ _______ _ __
#    / _ \ | '_ \ / _` | | | | |_  / _ \ '__|
#   / ___ \| | | | (_| | | |_| |/ /  __/ |
#  /_/   \_\_| |_|\__,_|_|\__, /___\___|_|
#                         |___/
#
# 版权所有 (c) 2024  Memrix(记忆星核)
# 此文件受 Memrix(记忆星核) 许可证的保护。您可以在 LICENSE.md 文件中查看详细的许可条款。
#
# Copyright (c) 2024  Memrix(记忆星核)
# This file is licensed under the Memrix(记忆星核) License. See the LICENSE.md file for more details.
#

import os
import time
import asyncio
import aiofiles
import aiosqlite
import numpy as np
from loguru import logger
from datetime import datetime
from bokeh.plotting import figure, save
from bokeh.io import curdoc, output_file
from bokeh.models import (
    ColumnDataSource, Span, HoverTool,
    DatetimeTickFormatter, BoxAnnotation, Range1d
)
from jinja2 import Environment, FileSystemLoader
from memnova import const
from engine.tackle import DataBase


class Analyzer(object):

    def __init__(self, db: "aiosqlite.Connection", download: str):
        self.db = db
        self.download = download

    async def form_report(self, template_dir: str, *args, **kwargs) -> None:
        loader = FileSystemLoader(template_dir)
        environment = Environment(loader=loader)
        template = environment.get_template(const.TEMPLATE_FILE)
        html = template.render(*args, **kwargs)

        html_file = os.path.join(self.download, f"Inform_{time.strftime('%Y%m%d%H%M%S')}.html")
        async with aiofiles.open(html_file, "w", encoding=const.ENCODING) as f:
            await f.write(html)
            logger.info(html_file)

    async def draw_memory(self, data_dir: str) -> dict[str, str]:

        async def draw(file_name, data_list):
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
                f"{file_name}_max": round(float(max_value), 2),
                f"{file_name}_avg": round(float(avg_value), 2),
                f"{file_name}_loc": os.path.join(const.SUMMARY, data_dir, os.path.basename(file_path))
            }

        fg_list, bg_list = await DataBase.query_data(self.db, data_dir)
        os.makedirs(group := os.path.join(self.download, const.SUMMARY, data_dir), exist_ok=True)

        fg, bg = await asyncio.gather(
            draw("fg", fg_list), draw("bg", bg_list)
        )

        logger.info(f"{data_dir} Handler Done ...")

        return fg | bg | {"minor_title": data_dir}


if __name__ == '__main__':
    pass
