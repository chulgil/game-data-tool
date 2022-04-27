import logging
from git import Repo
from pathlib import Path
import json
import shutil


class GitManager:
    GIT_BRANCH = None
    PATH_FOR_DATA_ROOT = None
    GIT_URL = None
    GIT_USER = None
    GIT_EMAIL = None
    GIT_PUSH_MSG = None
    PATH_FOR_GIT = None

    def __init__(self, branch):
        logging.basicConfig(filename='out.log', encoding='utf-8', level=logging.INFO)
        with open('config.json', 'r') as f:
            config = json.load(f)
        self.GIT_BRANCH = branch
        self._set_config(config)

    @classmethod
    def _set_config(cls, config):
        cls.PATH_FOR_DATA_ROOT = config['DEFAULT']['ROOT_DATA_DIR']
        cls.GIT_URL = config['GITSERVER']['URL']
        cls.GIT_USER = config['GITSERVER']['USER']
        cls.GIT_EMAIL = config['GITSERVER']['EMAIL']
        cls.GIT_PUSH_MSG = config['GITSERVER']['PUSH_MSG']
        cls.PATH_FOR_GIT = Path(cls.PATH_FOR_DATA_ROOT + "/.git")

    @classmethod
    def _init_git(cls):
        try:
            # GIT 기본 프로젝트 폴더 삭제
            shutil.rmtree(cls.GIT_BRANCH)
            repo = Repo.clone_from(cls.GIT_URL, cls.PATH_FOR_DATA_ROOT, branch='main')
            # GIT 초기 설정
            repo.config_writer().set_value("user", "name", cls.GIT_USER).release()
            repo.config_writer().set_value("user", "email", cls.GIT_EMAIL).release()
            repo.git.checkout(cls.GIT_BRANCH)
            logging.info('GIT 초기화 성공')
        except Exception as e:
            logging.warning('GIT Clone 에러 발생' + str(e))

    @classmethod
    def pull(cls):
        if cls.PATH_FOR_GIT.exists():
            repo = Repo(cls.PATH_FOR_GIT)
            repo.git.checkout(cls.GIT_BRANCH)
            origin = repo.remotes.origin
            origin.pull()
        else:
            cls._init_git()

    @classmethod
    def push(cls):
        try:
            cls.pull()
            cls._commit()
            repo = Repo(cls.PATH_FOR_GIT)
            origin = repo.remotes.origin
            origin.push()
            logging.info('GIT PUSH 성공')
        except Exception as e:
            logging.warning('GIT Push 에러 발생' + str(e))

    @classmethod
    def _commit(cls):
        try:
            repo = Repo(cls.PATH_FOR_GIT)
            repo.git.add(all=True)
            repo.index.commit(cls.GIT_PUSH_MSG)
            logging.info('GIT Commit 성공')
        except Exception as e:
            logging.warning('GIT Commit 에러 발생' + str(e))

    @classmethod
    def is_modified(cls) -> bool:
        repo = Repo(cls.PATH_FOR_GIT)
        if len(repo.untracked_files) > 0:
            logging.info("변경된 파일 : " + str(repo.untracked_files))
            return True
        else:
            logging.info("변경된 데이터가 없습니다.")
            return False
