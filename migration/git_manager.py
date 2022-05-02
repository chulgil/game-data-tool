import logging
from git import Repo, GitCommandError
from pathlib import Path
import json
import shutil


class GitManager:

    def __init__(self, branch):
        self.BRANCH = branch
        self.ROOT_DIR = Path(__file__).parent.parent
        self.PATH_FOR_CONFIG = self.ROOT_DIR.joinpath('config.json')
        with open(self.PATH_FOR_CONFIG, 'r') as f:
            config = json.load(f)
        self._set_config(config)
        if self.PATH_FOR_GIT.exists():
            self._repo = Repo(self.PATH_FOR_GIT)
            self._origin = self._repo.remotes.origin
        else:
            self._init_git()

    def _set_config(self, config):
        self.PATH_FOR_DATA_ROOT = self.ROOT_DIR.joinpath(config['DEFAULT']['ROOT_DATA_DIR'])
        self.GIT_URL = config['GITSERVER']['URL']
        self.GIT_USER = config['GITSERVER']['USER']
        self.GIT_EMAIL = config['GITSERVER']['EMAIL']
        self.GIT_PUSH_MSG = config['GITSERVER']['PUSH_MSG']
        self.PATH_FOR_GIT = self.PATH_FOR_DATA_ROOT.joinpath(".git")

    def _init_git(self):
        try:
            # GIT 기본 프로젝트 폴더 삭제
            if Path(self.BRANCH).is_dir():
                shutil.rmtree(self.BRANCH)
            self._repo = Repo.clone_from(self.GIT_URL, self.PATH_FOR_DATA_ROOT, branch='main')
            # GIT 초기 설정
            self._repo.config_writer().set_value("user", "name", self.GIT_USER).release()
            self._repo.config_writer().set_value("user", "email", self.GIT_EMAIL).release()
            self._repo.config_writer().set_value("pull.ff", "only", self.GIT_EMAIL).release()
            self._origin = self._repo.remotes.origin
            logging.info(str(self._brn()) + 'GIT 초기화 성공')
            self._checkout()
        except Exception as e:
            logging.error(str(self._brn()) + 'GIT Clone Error \r\n' + str(e))

    def pull(self):
        try:
            self._checkout()
            if self._repo.is_dirty():
                self._repo.git.stash()
                self._origin.pull()
                self._repo.git.stash('pop')
            else:
                self._origin.pull()
            logging.info(str(self._brn()) + 'GIT PULL 성공')
        except Exception as e:
            logging.error(str(self._brn()) + 'GIT PULL Error \r\n' + str(e))

    def push(self):
        try:
            self._commit()
            self._origin.push()
            logging.info(str(self._brn()) + 'GIT PUSH 성공')
        except Exception as e:
            logging.error(str(self._brn()) + 'GIT Push Error \r\n' + str(e))

    def _brn(self) -> str:
        return '[' + self._repo.active_branch.name + ' 브랜치] '

    def _checkout(self):
        try:
            self._repo.git.checkout(self.BRANCH)
            logging.info(str(self._brn()) + 'GIT CEHCKOUT')
        except Exception as e:
            logging.error(str(self._brn()) + 'GIT CEHCKOUT Error \r\n' + str(e))

    def _commit(self):
        try:
            self._repo.git.add(all=True)
            self._repo.index.commit(self.GIT_PUSH_MSG)
            logging.info(str(self._brn()) + 'GIT Commit 성공')
        except Exception as e:
            logging.error(str(self._brn()) + 'GIT Commit Error \r\n' + str(e))

    def is_modified(self) -> bool:
        changed = [item.a_path for item in self._repo.index.diff(None)]
        if len(changed) > 0:
            logging.info(str(self._brn()) + "변경된 파일 : " + str(changed))
            return True
        if len(self._repo.untracked_files) > 0:
            logging.info(str(self._brn()) + "변경된 파일 : " + str(self._repo.untracked_files))
            return True

        logging.info(str(self._brn()) + "변경된 데이터가 없습니다.")
        return False
