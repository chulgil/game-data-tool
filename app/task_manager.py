from enum import auto, Enum
from pathlib import Path
from pprint import pprint
import yaml
from . import GitManager


class TaskType(Enum):
    NONE = auto()
    EXCEL = auto()  # EXCEL변환
    EXCEL_TAG = auto()  # TAG로 EXCEL변환
    MIGRATE_DB = auto()  # 브랜치의 디비 초기화
    UPDATE_TB_INFO = auto()  # 브랜치의 INFO테이블 업데이트
    UPDATE_TB_DATA = auto()  # 브랜치의 DATA테이블 업데이트
    SCHEDULER = auto()  # TASK에 저장되어있는 스케쥴로 실행

    @classmethod
    def value_of(cls, value: str):
        value = str(value)
        for k, v in cls.__members__.items():
            if k == value.upper():
                return v
        else:
            return TaskType.NONE


class TaskManager:

    def __init__(self, task_type: TaskType, branch: str = '', tag: str = '', commit: str = ''):
        self.PATH_FOR_SCHEDULER = Path(__file__).parent.parent.joinpath('export', 'scheduler.yaml')
        self.BRANCH = branch
        self.NEW_TAG = tag
        self.COMMIT_ID = commit
        self.SCHEDULER_TASK = False
        self.TASK_TYPE = task_type
        if task_type == TaskType.SCHEDULER:
            self.SCHEDULER_TASK = True
            self.load_task()

        from . import LogManager
        self.splog = LogManager(self.BRANCH)
        self.TASK = self._create_task()

        _info = f'[Task:{self.TASK_TYPE.name}]'
        if self.NEW_TAG != '':
            _info = f'{_info}[{self.NEW_TAG}]'
        else:
            _info = f'{_info}[{self.BRANCH}]'
        _info = f'{_info}{self.TASK}'
        self.splog.PREFIX = _info

    def init(self, g_manager: GitManager):
        working = {'branch': {}, 'tag': {}}
        tasks = []

        for br in g_manager.get_branches():
            working['branch'][br] = False
        for tg in g_manager.get_tags():
            working['tag'][tg] = False
        data = {'working': working, 'tasks': tasks}
        self.save_config(data)

    def load_task(self) -> bool:
        config = self.load_config()
        if len(config['tasks']) == 0:
            return False
        task = config['tasks'][-1]
        info = str(task).split('::')
        self.TASK_TYPE = TaskType.value_of(info[0])
        self.BRANCH = info[1]
        if self.TASK_TYPE == TaskType.EXCEL:
            self.COMMIT_ID = info[2]
        if self.TASK_TYPE == TaskType.EXCEL_TAG:
            self.NEW_TAG = info[2]
        return True

    def _create_task(self):
        _key = f'{self.TASK_TYPE.name}::{self.BRANCH}'
        if self.TASK_TYPE == TaskType.EXCEL:
            return f'{_key}::{self.COMMIT_ID}'
        elif self.TASK_TYPE == TaskType.EXCEL_TAG:
            return f'{_key}::{self.NEW_TAG}'
        else:
            return _key

    def _has_task(self):
        config = self.load_config()
        if self.TASK in config['tasks']:
            return True
        return False

    def is_working(self):
        config = self.load_config()
        work = config['working']
        if self.NEW_TAG != '':
            if self.NEW_TAG in work['tag']:
                return work['tag'][self.NEW_TAG]
        if self.BRANCH in work['branch']:
            return work['branch'][self.BRANCH]

    def load_config(self):
        with open(self.PATH_FOR_SCHEDULER, 'r') as f:
            config = yaml.safe_load(f)
        return config

    def save_config(self, config: dict):
        with open(self.PATH_FOR_SCHEDULER, 'w') as f:
            yaml.dump(config, f)

    def _set_working(self, working: bool = True):
        config = self.load_config()
        work = config['working']
        if self.TASK_TYPE == TaskType.EXCEL_TAG:
            work['tag'][self.NEW_TAG] = working
        else:
            work['branch'][self.BRANCH] = working
        self.save_config(config)

    def start(self) -> bool:
        self.splog.timer(f'작업을 시작합니다.')
        if self.is_working():
            self.add_task()
            return False
        self._set_working(True)
        return True

    def done(self):
        if self.SCHEDULER_TASK:
            self.pop_task()
        self._set_working(False)
        self.splog.elapsed(f'작업을 종료합니다.')

    def pop_task(self) -> dict:
        self.splog.info(f'작업을 대기열에서 삭제합니다.')
        config = self.load_config()
        tasks = config['tasks']
        if len(tasks) == 0:
            return None
        task = tasks.pop(-1)
        self.save_config(config)
        return task

    def add_task(self) -> bool:
        self.splog.info(f'작업을 대기열에 추가합니다.')
        config = self.load_config()
        tasks = config['tasks']

        if self._has_task():
            self.splog.info(f'대기열에 이미 존재합니다.')
            return False
        tasks.insert(0, self.TASK)
        self.save_config(config)
        return True

    def do_task(self):
        data = self.pop_task()
        pprint(data)

    def status(self):
        config = self.load_config()
        self.splog.info(config)
