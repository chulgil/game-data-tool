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
            self.TIMEOUT = 5
            self.error_count = 0

            # Config 파일 설정
            try:
                with open(self.PATH_FOR_CONFIG, 'r') as f:
                    config = yaml.safe_load(f)
                    self.TIMEOUT = config['TEAMS']['TIMEOUT']
                    self.is_test = config['TEAMS']['IS_TEST']
            except Exception as e:
                print(e)

            try:
                self.teams_designer = pymsteams.connectorcard(config['TEAMS']['DESIGNER_URL'],
                                                              http_timeout=self.TIMEOUT)
                self.teams_test = pymsteams.connectorcard(config['TEAMS']['TEST_URL'], http_timeout=self.TIMEOUT)
                self.teams_developer = pymsteams.connectorcard(config['TEAMS']['DEVELOPER_URL'],
                                                               http_timeout=self.TIMEOUT)
                self.teams_dev = pymsteams.connectorcard(config['TEAMS']['DEV_URL'], http_timeout=self.TIMEOUT)
            except Exception as e:
                print(f'팀즈 메신저 타임아웃 에러 :{str(e)}')

            self.row_for_max_buffer = 100
            if self.is_live_branch(branch):
                self.teams_target = self.teams_designer
            elif self.is_test_branch(branch):
                self.teams_target = self.teams_test
            else:
                self.teams_developer = self.teams_dev
                self.teams_target = self.teams_dev

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
        self.error_count = self.error_count + 1
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

    def send_designer(self, msg: str):
        if not self.teams_target:
            return
        if msg != '':
            self.logger.info(f'{self.PREFIX} {str(msg)}')
            try:
                self.send(self.teams_target.text(f'{self.PREFIX} {str(msg)}'))
            except Exception as e:
                print(e)

    def send_designer_all(self):
        if not self.teams_target:
            return
        if self.has_info():
            self._info = list(set(self._info))
            try:
                self.send(self.teams_target.text('\n\n'.join(self._info)))
            except Exception as e:
                print(e)
            self.info()
        if self.has_warning():
            self._warning = list(set(self._warning))
            try:
                self.send(self.teams_target.text('\n\n'.join(self._warning)))
            except Exception as e:
                print(e)
            self.warning()
        if self.has_error():
            self._error = list(set(self._error))
            try:
                self.send(self.teams_target.text('\n\n'.join(self._error)))
            except Exception as e:
                print(e)
            self.error()

    def send_developer(self, msg: str):
        if not self.teams_developer:
            return
        if msg != '':
            try:
                self.send(self.teams_developer.text(f'{self.PREFIX} {str(msg)}'))
            except Exception as e:
                print(e)
            self.logger.info(f'{self.PREFIX} {str(msg)}')

    def send_developer_all(self):
        if not self.teams_developer:
            return
        if self.has_info():
            self._info = list(set(self._info))
            try:
                self.send(self.teams_developer.text('\n\n'.join(self._info)))
            except Exception as e:
                print(e)
            self.info()
        if self.has_warning():
            self._warning = list(set(self._warning))
            try:
                self.send(self.teams_developer.text('\n\n'.join(self._warning)))
            except Exception as e:
                print(e)
            self.warning()

    def send_developer_warning(self):
        if not self.teams_developer:
            return
        if self.has_warning():
            self._warning = list(set(self._warning))
            try:
                self.send(self.teams_developer.text('\n\n'.join(self._warning)))
            except Exception as e:
                print(e)
            self.warning()

    def send(self, card: pymsteams.connectorcard):
        if self.is_test:
            return
        card.send()

    @staticmethod
    def is_live_branch(branch) -> bool:
        if branch == 'live' or branch == 'qa' or branch == 'qa2' or branch == 'qa3' \
                or branch == 'cbt' or branch == 'review':
            return True
        return False

    @staticmethod
    def is_test_branch(branch) -> bool:
        if branch == 'dev':
            return True
        return False

    def exist_error(self) -> bool:
        return self.error_count > 0

    def destory(self):
        self.info()
        self.warning()
        self.error()
        self.error_count = 0
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
