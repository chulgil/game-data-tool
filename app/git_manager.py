import logging
import uuid
from enum import Enum, auto

import pymsteams as pymsteams
import yaml
from git import Repo, GitCommandError
from pathlib import Path
import shutil
import re
from datetime import date


class GitTarget(Enum):
    EXCEL = auto()
    CLIENT = auto()
    NONE = auto()

    @classmethod
    def value_of(cls, value: str):
        value = str(value)
        for k, v in cls.__members__.items():
            if k == value.upper():
                return v
        else:
            return GitTarget.NONE


class GitManager:

    def __init__(self, target: GitTarget):
        self.BRANCH = None
        self.GIT_TARGET = target
        self.PATH_FOR_ROOT = Path(__file__).parent.parent
        self.PATH_FOR_CONFIG = self.PATH_FOR_ROOT.joinpath('config.yaml')
        with open(self.PATH_FOR_CONFIG, 'r') as f:
            config = yaml.safe_load(f)
        self._set_config(config)
        self._init_git()

    def _set_config(self, config):
        self.teams = pymsteams.connectorcard(config['TEAMS']['DESIGNER_URL'])

        # self.PATH_FOR_WORKING = self.PATH_FOR_ROOT.joinpath(config['DEFAULT']['EXPORT_DIR'], str(self.GIT_TARGET.name))
        self.PATH_FOR_WORKING = self.PATH_FOR_ROOT.joinpath(config['DEFAULT']['EXPORT_DIR'],
                                                            str(date.today()) + '_' + uuid.uuid4().hex)
        if self.GIT_TARGET == GitTarget.EXCEL:
            self.GIT_URL = config['GITSERVER']['EXCEL_SSH']
        elif self.GIT_TARGET == GitTarget.CLIENT:
            self.GIT_URL = config['GITSERVER']['CLIENT_SSH']
        self.GIT_USER = config['GITSERVER']['USER']
        self.GIT_EMAIL = config['GITSERVER']['EMAIL']
        self.GIT_PUSH_MSG = config['GITSERVER']['PUSH_MSG']
        self.COMPILE_EXCEL = re.compile(rf"{config['DEFAULT']['EXCEL_DIR']}\S+[xls | xlsx]$")
        self.COMPILE_JSON = re.compile(r"\D+json$")

    def _init_git(self):
        try:
            # GIT 기본 프로젝트 폴더 삭제
            if Path(self.PATH_FOR_WORKING).is_dir():
                shutil.rmtree(self.PATH_FOR_WORKING)
            self._repo = Repo.clone_from(self.GIT_URL, self.PATH_FOR_WORKING, branch=self.BRANCH)
            # GIT 초기 설정
            writer = self._repo.config_writer()
            writer.set_value("user", "name", self.GIT_USER)
            writer.set_value("user", "email", self.GIT_EMAIL)
            writer.release()
            del writer
            self._origin = self._repo.remotes.origin
            logging.info(str(self._brn()) + 'GIT 초기화 성공')
        except Exception as e:
            logging.error(str(self._brn()) + 'GIT Clone Error \r\n' + str(e))

    def pull(self) -> bool:
        try:
            if self._is_empty_branch():
                return False
            self._origin.pull()
            logging.info(str(self._brn()) + 'GIT PULL 성공')
            return True
        except Exception as e:
            logging.error(str(self._brn()) + 'GIT PULL Error \r\n' + str(e))
        return False

    def push(self) -> bool:
        try:
            if self._is_empty_branch():
                return False
            self._commit()
            self._origin.push()
            logging.info(str(self._brn()) + 'GIT PUSH 성공')
            return True
        except Exception as e:
            logging.error(str(self._brn()) + 'GIT Push Error \r\n' + str(e))
        return False

    def _brn(self) -> str:
        if hasattr(self, '_repo'):
            return '[' + self._repo.active_branch.name + ' 브랜치] '
        return ''

    def checkout(self, branch: str) -> bool:
        try:
            self._repo.head.reset(index=True, working_tree=True)
            self._repo.git.checkout(branch)
            self.BRANCH = branch
            logging.info(str(self._brn()) + 'GIT CEHCKOUT 성공')
            return True
        except Exception as e:
            logging.error(str(self._brn()) + 'GIT CEHCKOUT Error \r\n' + str(e))
        return False

    def _commit(self):
        try:
            self._repo.git.add(all=True)
            self._repo.index.commit(self.GIT_PUSH_MSG)
            # logging.info(str(self._brn()) + 'GIT Commit 성공')
        except Exception as e:
            logging.error(str(self._brn()) + 'GIT Commit Error \r\n' + str(e))

    # Ref :
    # https://docs.gitea.io/en-us/webhooks/
    # https://nixing.mx/posts/configure-gitea-webhooks.html
    def get_branch_from_webhook(self, webhook: dict) -> str:
        try:
            username = webhook["head_commit"]["committer"]["username"]
            compare_url = webhook["compare_url"]

            # 레퍼런스에서 마지막 문자열(브랜치명) 추출 ex) "ref": "refs/heads/main"
            branch = webhook["ref"].split("/").pop()

            _info = f'[{branch} 브랜치]'

            # 변경사항이 없다면 무시
            if not compare_url:
                msg = f"[EXCEL변환요청:{username}] {_info} 변경사항이 없어 종료합니다."
                self.teams.text(msg).send()
                logging.info(msg)
                return ''

            # 봇 PUSH 인 경우는 다시 PUSH하지 않고 메시지만 보낸다.
            if self._is_bot_user(username):
                msg = f"{_info} 변경 히스토리 URL : {compare_url}"
                self.teams.text(msg).send()
                logging.info(msg)
                return ''

            msg = f"[EXCEL변환요청:{username}] {_info} 변경사항을 적용합니다."
            self.teams.text(msg).send()
            logging.info(msg)
            return branch
        except Exception as e:
            logging.exception(f"Webhook format Error : {webhook}")
        return ''

    # 자동봇 유저인지 확인
    def _is_bot_user(self, name: str):
        return True if name == self.GIT_USER else False

    def is_modified(self) -> bool:
        changed = [item.a_path for item in self._repo.index.diff(None)]
        if len(changed) > 0:
            msg = str(self._brn()) + "변경된 파일 : " + str(changed)
            logging.info(msg)
            self.teams.text(msg).send()
            return True
        if len(self._repo.untracked_files) > 0:
            logging.info(str(self._brn()) + "변경된 파일 : " + str(self._repo.untracked_files))
            return True

        msg = str(self._brn()) + "변경된 데이터가 없습니다."
        self.teams.text(msg).send()
        logging.info(msg)
        return False

    def _is_empty_branch(self) -> bool:
        if not self.BRANCH:
            logging.warning(str(self._brn()) + "설정할 브랜치가 없습니다.")
            return True
        return False

    def get_modified_excel(self, head_cnt=1) -> list:
        """과거 이력중 엑셀파일 경로만 추출
        """
        data = []
        for i in range(1, head_cnt + 1):
            _diff = self._repo.index.diff(f'HEAD~{i}')
            data = data + self._get_diff_excel(_diff)
        if len(data) == 0:
            logging.info(str(self._brn()) + "변경된 EXCEL이 없습니다.")
            return []

        # 중복제거
        data = set(data)
        return list(data)

    def get_modified_json(self, head_cnt=1) -> list:
        """과거 이력중 JSON파일 경로만 추출
        """
        data = []
        for i in range(1, head_cnt + 1):
            _diff = self._repo.index.diff(f'HEAD~{i}')
            data = data + self._get_diff_excel(_diff)
        if len(data) == 0:
            logging.info(str(self._brn()) + "변경된 Json이 없습니다.")
            return []

        # 중복제거
        data = set(data)
        return list(data)

    def _get_diff_excel(self, diff_index):
        res = []
        for diff_item in diff_index:
            value = diff_item.a_rawpath.decode('utf-8')
            if self.COMPILE_EXCEL.match(value):
                res.append(value)
        return res

    def _get_diff_json(self, diff_index):
        res = []
        for diff_item in diff_index:
            value = diff_item.a_rawpath.decode('utf-8')
            if self.COMPILE_JSON.match(value):
                res.append(value)
        return res

    def get_last_commit(self) -> str:
        return self._repo.git.rev_parse(self._repo.head, short=True)

    def get_last_tag(self) -> str:
        tags = sorted(self._repo.tags, key=lambda t: t.commit.committed_datetime)
        latest_tag = str(tags[-1])
        return latest_tag

    def destroy(self):
        shutil.rmtree(self.PATH_FOR_WORKING)
