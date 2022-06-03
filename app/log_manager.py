import os
import pymsteams as pymsteams
from pathlib import Path
import uuid
import yaml
import logging
from io import StringIO
from pathlib import Path
import colorlog
from datetime import date


class LogManager:

    def __init__(self, branch: str, save_path: Path):
        try:
            self._info = []
            self._warning = []
            self._error = []
            test = uuid.uuid4().hex
            self.logger = logging.getLogger(test)
            self.BRANCH = branch
            self.PATH_FOR_ROOT = Path(__file__).parent.parent
            self.PATH_FOR_CONFIG = self.PATH_FOR_ROOT.joinpath('config.yaml')

            # Config 파일 설정
            with open(self.PATH_FOR_CONFIG, 'r') as f:
                config = yaml.safe_load(f)
            self.PATH_FOR_SAVE = save_path.joinpath(config['DEFAULT']['EXPORT_DIR'], 'out.log')
            self.teams_designer = pymsteams.connectorcard(config['TEAMS']['DESIGNER_URL'])
            self.teams_test = pymsteams.connectorcard(config['TEAMS']['TEST_URL'])
            self.teams_developer = pymsteams.connectorcard(config['TEAMS']['DEVELOPER_URL'])
            self.row_for_max_buffer = 50
            if self.is_service_branch(branch):
                self.teams_target = self.teams_test
            else:
                self.teams_target = self.teams_designer

            _format_file = '[%(levelname)-7s] %(asctime)s: %(message)s '
            _format_console = '[%(levelname)-7s] %(asctime)s: %(message)s '

            self.FORM_FILE = logging.Formatter(_format_file, "%m/%d/%Y %H:%M:%S ")
            self.FORM_CONSOLE = colorlog.ColoredFormatter(_format_console, "%m/%d/%Y %H:%M:%S ")

            # ------- CONSOLE LOGGER
            self.main_handler = logging.StreamHandler()
            self.main_handler.setLevel(logging.INFO)
            self.main_handler.setFormatter(self.FORM_CONSOLE)

            # ------- FILE LOGGER
            self.file_handler = logging.FileHandler(self.PATH_FOR_SAVE, 'w', 'utf-8')
            self.file_handler.setLevel(logging.INFO)
            self.file_handler.setFormatter(self.FORM_FILE)

            # Excel Git Repo에 로그파일 저장 : 보류
            # self.logger.addHandler(self.file_handler)
            self.logger.addHandler(self.main_handler)
        except Exception as e:
            pass

    def add_info(self, msg, idx: int = None):
        if idx:
            self._info.insert(idx, msg)
        else:
            if isinstance(msg, list):
                self._info = self._info + msg
            else:
                self._info.append(msg)
        self._info = self._info[:self.row_for_max_buffer]

    def add_warning(self, msg, idx: int = None):
        if idx:
            self._warning.insert(idx, msg)
        else:
            if isinstance(msg, list):
                self._warning = self._warning + msg
            else:
                self._warning.append(msg)
        self._warning = self._warning[:self.row_for_max_buffer]

    def add_error(self, msg: str, idx: int = None):
        if idx:
            self._error.insert(idx, msg)
        else:
            if isinstance(msg, list):
                self._error = self._error + msg
            else:
                self._error.append(msg)
        self._error = self._error[:self.row_for_max_buffer]

    def has_info(self) -> bool:
        return True if len(self._info) > 0 else False

    def has_warning(self) -> bool:
        return True if len(self._warning) > 0 else False

    def has_error(self) -> bool:
        return True if len(self._error) > 0 else False

    def info(self, msg: str = None):
        if msg == '':
            return
        if msg:
            self.logger.info(msg)
            return
        if self.has_info():
            self.logger.info('\n'.join(self._info))
            self._info = []

    def warning(self, msg: str = None):
        if msg == '':
            return
        if msg:
            self.logger.warning(msg)
            return
        if self.has_warning():
            self.logger.warning('\n'.join(self._warning))
            self._warning = []

    def error(self, msg: str = None):
        if msg == '':
            return
        if msg:
            self.logger.error(msg)
            return
        if self.has_error():
            self.logger.error('\n'.join(self._error))
            self._error = []

    def send_designer(self, msg: str = None):
        if msg:
            # self.logger.info(msg)
            # self.target.text(msg).send()
            pass
        else:
            if self.has_info():
                # self.target.text('\n\n'.join(self._info)).send()
                self.info()
            if self.has_warning():
                # self.target.text('\n\n'.join(self._warning)).send()
                self.warning()

    def send_developer(self, msg):
        if not self.is_service_branch(self.BRANCH):
            return
        if msg:
            # self.developer.text(msg).send()
            # self.logger.info(msg)
            pass
        else:
            if self.has_info():
                # self.developer.text('\n\n'.join(self._info)).send()
                self.info()
            if self.has_warning():
                # self.developer.text('\n\n'.join(self._warning)).send()
                self.warning()

    @staticmethod
    def is_service_branch(branch) -> bool:
        if branch != 'main' and branch != 'dev' \
                and branch != 'qa' and branch != 'qa2' and branch != 'qa3' \
                and branch != 'cbt' and branch != 'obt':
            return False
        return True

    def destory(self):
        self.info()
        self.warning()
        self.error()
        for handler in self.logger.handlers:
            self.logger.removeHandler(handler)
            handler.close()
