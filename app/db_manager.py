import importlib.util as ilu

import yaml
from pathlib import Path


class DBManager:

    def __init__(self, branch: str, working_dir):
        from . import LogManager
        self.splog = LogManager(branch)
        self.BRANCH = branch
        self._info = f'[{branch} 브랜치]'
        self.splog.PREFIX = self._info
        self.PATH_FOR_WORKING = working_dir
        self.PATH_FOR_ROOT = Path(__file__).parent.parent


