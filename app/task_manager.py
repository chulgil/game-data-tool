from datetime import datetime
from enum import auto, Enum
from pathlib import Path
from typing import Optional

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

    def __init__(self, task_type: TaskType, branch: str = 'main', tag: str = ''):
        self.PATH_FOR_SCHEDULER = Path(__file__).parent.parent.joinpath('export', 'scheduler.yaml')
        self.BRANCH = branch
        self.NEW_TAG = tag
        self.SCHEDULER_TASK = False
        self.TASK_TYPE = task_type
        self.OVERTIME = 120  # 작업시간이 3분 초과한경우
        if task_type == TaskType.SCHEDULER:
            self.SCHEDULER_TASK = True
            self.load_task()

        from . import LogManager
        self.splog = LogManager(self.BRANCH)
        self.TASK = self._create_task()

        _info = f'[Task:{self.TASK_TYPE.name}]'
        _info = f'{_info}[{self._br()}]'
        self.splog.PREFIX = _info

    def init(self, g_manager: GitManager):

        self.BRANCH = g_manager.BRANCH
        self.NEW_TAG = g_manager.NEW_TAG

        config = self._load_config()
        if not config:
            working = {}
            tasks = []
            for br in g_manager.get_branches():
                working[br] = None
            for tg in g_manager.get_tags():
                working[tg] = None
            config = {'working': working, 'tasks': tasks}
        else:
            working = config['working']
            for br in g_manager.get_branches():
                if br not in working:
                    working[br] = None
            for br in g_manager.get_tags():
                if br not in working:
                    working[br] = None

        self._save_config(config)

    def _br(self):
        if self.TASK_TYPE == TaskType.EXCEL_TAG:
            return self.NEW_TAG
        else:
            return self.BRANCH

    def load_task(self) -> bool:
        config = self._load_config()
        if len(config['tasks']) == 0:
            return False
        task = config['tasks'][-1]
        info = str(task).split('::')
        self.TASK_TYPE = TaskType.value_of(info[0])
        self.BRANCH = info[1]
        if self.TASK_TYPE == TaskType.EXCEL_TAG:
            self.NEW_TAG = info[2]
        return True

    def _create_task(self):
        _key = f'{self.TASK_TYPE.name}::{self.BRANCH}'
        if self.TASK_TYPE == TaskType.EXCEL:
            # return f'{_key}::{self.COMMIT_ID}
            return f'{_key}'
        elif self.TASK_TYPE == TaskType.EXCEL_TAG:
            return f'{_key}::{self.NEW_TAG}'
        else:
            return _key

    def _has_task(self):
        config = self._load_config()
        if config['tasks'] is not None and self.TASK in config['tasks']:
            return True
        return False

    def is_locked(self):
        self._save_overtime()
        config = self._load_config()
        return config['working'][self._br()]

    def _load_config(self):
        try:
            with open(self.PATH_FOR_SCHEDULER, 'r') as f:
                config = yaml.safe_load(f)
        except Exception:
            return None
        return config

    def _save_config(self, config: dict):
        with open(self.PATH_FOR_SCHEDULER, 'w') as f:
            yaml.dump(config, f)

    def _save_overtime(self):
        config = self._load_config()
        work = config['working']
        try:
            started = datetime.fromisoformat(str(work[self._br()]))
            overtime = datetime.now() - started
            overtime = overtime.seconds
        except Exception:
            overtime = 9999

        # 설정 분 이상 지난경우 초기화
        if overtime > self.OVERTIME:
            work[self._br()] = None
        self._save_config(config)

    def _lock(self, locked: bool = True):
        config = self._load_config()
        work = config['working']
        if locked:
            work[self._br()] = datetime.now()
        else:
            work[self._br()] = None

        self._save_config(config)

    def start(self) -> bool:
        self.splog.timer(f'작업을 시작합니다.')
        if self.is_locked():
            self.add_task()
            return False
        self._lock(True)
        return True

    def done(self):
        self._lock(False)
        self.splog.elapsed(f'작업을 종료합니다.')

    def pop_task(self) -> Optional[dict]:
        self.splog.info(f'작업을 대기열에서 삭제합니다.')
        config = self._load_config()
        if config['tasks'] is None or len(config['tasks']) == 0:
            return None
        task = config['tasks'].pop(-1)
        tl = task.split('::')
        if len(tl) < 3:
            tl.append('')
        task_type = TaskType.value_of(tl[0])
        task_value = {tl[1]: tl[2]}
        self._save_config(config)
        return {task_type: task_value}

    def add_task(self) -> bool:
        self.splog.info(f'이미 실행중인 작업이 존재하여 대기열에 추가합니다.')
        config = self._load_config()

        if self._has_task():
            self.splog.info(f'대기열에 이미 존재합니다.')
            return False
        if config['tasks'] is None:
            config['tasks'] = []
        config['tasks'].insert(0, self.TASK)
        self._save_config(config)
        return True

    def status(self):
        config = self._load_config()
        self.splog.info(config)
