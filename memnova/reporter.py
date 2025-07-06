#   ____                       _
#  |  _ \ ___ _ __   ___  _ __| |_ ___ _ __
#  | |_) / _ \ '_ \ / _ \| '__| __/ _ \ '__|
#  |  _ <  __/ |_) | (_) | |  | ||  __/ |
#  |_| \_\___| .__/ \___/|_|   \__\___|_|
#            |_|
#
# ==== Notes: License ====
# Copyright (c) 2024  Memrix :: 记忆星核
# This file is licensed under the Memrix :: 记忆星核 License. See the LICENSE.md file for more details.

import os
import time
from pathlib import Path
from memnova import const


class Reporter(object):

    def __init__(self, src_total_place: str, vault: str, classify_type: str):
        self.total_dir = os.path.join(src_total_place, const.TOTAL_DIR)
        self.before_time = time.time()

        self.classify_dir = os.path.join(self.total_dir, classify_type)
        if not (classify_dir := Path(self.classify_dir)).exists():
            classify_dir.mkdir(parents=True, exist_ok=True)

        vault = vault or time.strftime("%Y%m%d%H%M%S", time.localtime(self.before_time))

        self.group_dir = os.path.join(self.classify_dir, vault)
        if not (group_dir := Path(self.group_dir)).exists():
            group_dir.mkdir(parents=True, exist_ok=True)

        self.db_file = os.path.join(self.total_dir, const.DB_FILE)
        self.log_file = os.path.join(self.group_dir, f"{const.APP_NAME}_log_{vault}.log")
        self.team_file = os.path.join(self.group_dir, f"{const.APP_NAME}_team_{vault}.yaml")


if __name__ == '__main__':
    pass
