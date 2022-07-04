import pymsteams as pymsteams
import uuid
import yaml
import logging
from pathlib import Path
import colorlog
from time import perf_counter


class LogManager:

    def __init__(self, branch: str):
        try:
            self.start = perf_counter()
            self._info = []
            self._warning = []
            self._error = []
            test = uuid.uuid4().hex
            self.logger = logging.getLogger(test)
            self.PREFIX = ''
            self.BRANCH = branch
            self.PATH_FOR_ROOT = Path(__file__).parent.parent
            self.PATH_FOR_CONFIG = self.PATH_FOR_ROOT.joinpath('config.yaml')

            # Config 파일 설정
            with open(self.PATH_FOR_CONFIG, 'r') as f:
                config = yaml.safe_load(f)
            self.teams_designer = pymsteams.connectorcard(config['TEAMS']['DESIGNER_URL'])
            self.teams_test = pymsteams.connectorcard(config['TEAMS']['TEST_URL'])
            self.teams_developer = pymsteams.connectorcard(config['TEAMS']['DEVELOPER_URL'])
            self.row_for_max_buffer = 100
            if self.is_service_branch(branch):
                self.teams_target = self.teams_designer
            else:
                self.teams_target = self.teams_test

            _format_file = '[%(levelname)-7s] %(asctime)s: %(message)s '
            _format_console = '[%(levelname)-7s] %(asctime)s: %(message)s '

            self.FORM_FILE = logging.Formatter(_format_file, "%m/%d/%Y %H:%M:%S ")
            self.FORM_CONSOLE = colorlog.ColoredFormatter(_format_console, "%m/%d/%Y %H:%M:%S ")

            # ------- CONSOLE LOGGER
            self.main_handler = logging.StreamHandler()
            self.main_handler.setLevel(logging.INFO)
            self.main_handler.setFormatter(self.FORM_CONSOLE)

            # ------- FILE LOGGER
            # self.file_handler = logging.FileHandler(self.PATH_FOR_SAVE, 'w', 'utf-8')
            # self.file_handler.setLevel(logging.INFO)
            # self.file_handler.setFormatter(self.FORM_FILE)

            # Excel Git Repo에 로그파일 저장 : 보류
            # self.logger.addHandler(self.file_handler)
            # self.logger.addHandler(self.main_handler)
        except Exception as e:
            pass

    def add_info(self, msg, idx: int = -1):
        if idx > -1:
            self._info.insert(idx, f'{self.PREFIX} {str(msg)}')
        else:
            if isinstance(msg, list):
                self._info = self._info + msg
            else:
                self._info.append(f'{self.PREFIX} {str(msg)}')
        self._info = self._info[:self.row_for_max_buffer]

    def add_warning(self, msg, idx: int = -1):
        if idx > -1:
            self._warning.insert(idx, f'{self.PREFIX} {str(msg)}')
        else:
            if isinstance(msg, list):
                self._warning = self._warning + msg
            else:
                self._warning.append(f'{self.PREFIX} {str(msg)}')
        self._warning = self._warning[:self.row_for_max_buffer]

    def add_error(self, msg: str, idx: int = -1):
        if idx > -1:
            self._error.insert(idx, f'{self.PREFIX} {str(msg)}')
        else:
            if isinstance(msg, list):
                self._error = self._error + msg
            else:
                self._error.append(f'{self.PREFIX} {str(msg)}')
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
            self.logger.info(f'{self.PREFIX} {str(msg)}')
            return
        if self.has_info():
            self._info = list(set(self._info))
            self.logger.info('\n'.join(self._info))
            self._info = []

    def warning(self, msg: str = None):
        if msg == '':
            return
        if msg:
            self.logger.warning(f'{self.PREFIX} {str(msg)}')
            return
        if self.has_warning():
            self._warning = list(set(self._warning))
            self.logger.warning('\n'.join(self._warning))
            self._warning = []

    def error(self, msg: str = None):
        if msg == '':
            return
        if msg:
            self.logger.error(f'{self.PREFIX} {str(msg)}')
            return
        if self.has_error():
            self._error = list(set(self._error))
            self.logger.error('\n'.join(self._error))
            self._error = []

    def send_designer(self, msg: str = None):
        if not self.is_service_branch(self.BRANCH):
            return
        if msg:
            self.logger.info(f'{self.PREFIX} {str(msg)}')
            self.teams_target.text(f'{self.PREFIX} {str(msg)}').send()
        else:
            if self.has_info():
                self._info = list(set(self._info))
                self.teams_target.text('\n\n'.join(self._info)).send()
                self.info()
            if self.has_warning():
                self._warning = list(set(self._warning))
                self.teams_target.text('\n\n'.join(self._warning)).send()
                self.warning()

    def send_developer(self, msg: str = None):
        # if not self.is_service_branch(self.BRANCH):
        # return
        if msg:
            self.teams_developer.text(f'{self.PREFIX} {str(msg)}').send()
            self.logger.info(f'{self.PREFIX} {str(msg)}')
        else:
            if self.has_info():
                self._info = list(set(self._info))
                self.teams_developer.text('\n\n'.join(self._info)).send()
                self.info()
            if self.has_warning():
                self._warning = list(set(self._warning))
                self.teams_developer.text('\n\n'.join(self._warning)).send()
                self.warning()

    @staticmethod
    def is_service_branch(branch) -> bool:
        if branch == 'main' or branch == 'dev' or branch == 'qa' or branch == 'qa2' or branch == 'qa3' \
                or branch == 'cbt' or branch == 'obt':
            return True
        return False

    def destory(self):
        self.info()
        self.warning()
        self.error()
        for handler in self.logger.handlers:
            self.logger.removeHandler(handler)
            handler.close()

    def timer(self, msg=''):
        self.info(msg)
        self.start = perf_counter()

    def elapsed(self, msg=''):
        end = perf_counter()
        diff = end - self.start
        self.info(f'{msg} 처리 총 소요 시간 : {diff}')
