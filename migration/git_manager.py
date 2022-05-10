import logging

import pymsteams as pymsteams
import yaml
from git import Repo, GitCommandError
from pathlib import Path
import shutil
import re


class GitManager:

    def __init__(self):
        self.BRANCH = None
        self.ROOT_DIR = Path(__file__).parent.parent
        self.PATH_FOR_CONFIG = self.ROOT_DIR.joinpath('config.yaml')
        with open(self.PATH_FOR_CONFIG, 'r') as f:
            config = yaml.safe_load(f)
        self._set_config(config)
        self.teams = pymsteams.connectorcard(config['TEAMS']['DESIGNER_URL'])
        self._init_git()

    def _set_config(self, config):
        self.PATH_FOR_DATA_ROOT = self.ROOT_DIR.joinpath(config['DEFAULT']['ROOT_DATA_DIR'])
        self.GIT_URL = config['GITSERVER']['URL']
        self.GIT_USER = config['GITSERVER']['USER']
        self.GIT_EMAIL = config['GITSERVER']['EMAIL']
        self.GIT_PUSH_MSG = config['GITSERVER']['PUSH_MSG']
        self.PATH_FOR_GIT = self.PATH_FOR_DATA_ROOT.joinpath(".git")
        self.COMPILE_EXCEL = re.compile(f"^{config['EXCEL']['EXCEL_DIR']}\D+xl(s|sx)$")

    def _init_git(self):
        try:
            # GIT 기본 프로젝트 폴더 삭제
            if Path(self.PATH_FOR_DATA_ROOT).is_dir():
                shutil.rmtree(self.PATH_FOR_DATA_ROOT)
            self._repo = Repo.clone_from(self.GIT_URL, self.PATH_FOR_DATA_ROOT, branch=self.BRANCH)
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
            logging.info(str(self._brn()) + 'GIT Commit 성공')
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

            # 변경사항이 없다면 무시
            if not compare_url:
                msg = f"[EXCEL변환요청:{username}] {branch} 브랜치에 변경사항이 없어 종료합니다."
                self.teams.text(msg)
                self.teams.send()
                logging.info(msg)
                return ''

            # 봇 PUSH 인 경우는 다시 PUSH하지 않고 메시지만 보낸다.
            if self._is_bot_user(username):
                msg = f"[{branch}] 브랜치 변경 히스토리 URL : {compare_url}"
                self.teams.text(msg)
                self.teams.send()
                logging.info(msg)
                return ''

            msg = f"[EXCEL변환요청:{username}] {branch} 브랜치에 변경사항을 적용합니다. 잠시만 기다려주세요..."
            self.teams.text(msg)
            self.teams.send()
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
            logging.info(str(self._brn()) + "변경된 파일 : " + str(changed))
            return True
        if len(self._repo.untracked_files) > 0:
            logging.info(str(self._brn()) + "변경된 파일 : " + str(self._repo.untracked_files))
            return True

        logging.info(str(self._brn()) + "변경된 데이터가 없습니다.")
        return False

    def _is_empty_branch(self) -> bool:
        if not self.BRANCH:
            logging.warning(str(self._brn()) + "설정할 브랜치가 없습니다.")
            return True
        return False

    # 엑셀파일의 추가와 편집 대상만 추출
    def get_modified_excel(self) -> list:
        excel = []
        _diff = self._repo.index.diff('HEAD~1')
        _list1 = self._get_diff_excel(_diff.iter_change_type('A'))
        _list2 = self._get_diff_excel(_diff.iter_change_type('M'))
        excel = _list1 + _list2
        if len(excel) == 0:
            logging.info(str(self._brn()) + "변경된 EXCEL이 없습니다.")
            return []

        # 중복제거
        excel = set(excel)
        return list(excel)


    def _get_diff_excel(self, diff_index):
        res = []
        for diff_item in diff_index:
            value = diff_item.a_rawpath.decode('utf-8')
            if self.COMPILE_EXCEL.match(value):
                res.append(value)
        return res

