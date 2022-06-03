import logging
import uuid
from enum import Enum, auto

import yaml
from git import Repo
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

    def __init__(self, target: GitTarget, commit: dict = None):

        self._info = ''
        self.BRANCH = None
        if commit is not None and 'branch' in commit:
            self.BRANCH = commit["branch"]

        self.COMMIT = commit

        self.COMMIT_ID = ''
        self.GIT_TARGET = target
        self.PATH_FOR_ROOT = Path(__file__).parent.parent
        self.PATH_FOR_CONFIG = self.PATH_FOR_ROOT.joinpath('config.yaml')
        with open(self.PATH_FOR_CONFIG, 'r') as f:
            config = yaml.safe_load(f)
        self._set_config(config)
        from . import LogManager
        self.splog = LogManager(self.BRANCH, self.PATH_FOR_WORKING)
        self._init_git()

    def _set_config(self, config):

        # self.PATH_FOR_WORKING = self.PATH_FOR_ROOT.joinpath(config['DEFAULT']['EXPORT_DIR'], str(self.GIT_TARGET.name))
        self.PATH_FOR_WORKING = self._random_path(config)
        self.PATH_FOR_WORKING_LAST = self._random_path(config)
        if self.GIT_TARGET == GitTarget.EXCEL:
            self.GIT_URL = config['GITSERVER']['EXCEL_SSH']
        elif self.GIT_TARGET == GitTarget.CLIENT:
            self.GIT_URL = config['GITSERVER']['CLIENT_SSH']
        self.GIT_USER = config['GITSERVER']['USER']
        self.GIT_EMAIL = config['GITSERVER']['EMAIL']
        self.GIT_PUSH_MSG = config['GITSERVER']['PUSH_MSG']
        self.COMPILE_EXCEL = re.compile(rf"{config['DEFAULT']['EXCEL_DIR']}\/data\S+[xls | xlsx]$")
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
            self._info = self._brn()
            self.splog.info(f'{self._info} GIT 초기화 성공')

            if self.COMMIT is not None:
                self.GIT_PUSH_MSG = f'{self.GIT_PUSH_MSG} [{self.COMMIT["committer"]["name"]}] : {self.COMMIT["message"]}'
                self.COMMIT_ID = self.COMMIT["id"]

            # 비교할 파일이 존재하면 리포지토리를 복제한다.
            if self._is_diff_excel_files():
                _base_tag = self.get_base_tag_from_branch()
                _old_repo = Repo.clone_from(self.GIT_URL, self.PATH_FOR_WORKING_LAST, branch=self.BRANCH)
                _old_repo.git.checkout(_base_tag)

        except Exception as e:
            self.splog.info(f'{self._info} GIT Clone Error \r\n{str(e)}')

    def pull(self) -> bool:
        try:
            if self._is_empty_branch():
                return False
            self._origin.pull()
            self.splog.info(f'{self._info} GIT PULL 성공')
            return True
        except Exception as e:
            self.splog.error(f'{self._info} GIT PULL Error \r\n{str(e)}')
        return False

    def push(self) -> bool:
        try:
            if self._is_empty_branch():
                return False
            self._commit()
            self._origin.push()
            self.splog.info(f'{self._info} GIT PUSH 성공')
            return True
        except Exception as e:
            self.splog.error(f'{self._info} GIT Push Error \r\n' + str(e))
        return False

    def _brn(self) -> str:
        if hasattr(self, '_repo'):
            return f'[GIT_{self.GIT_TARGET.name}][{self._repo.active_branch.name} 브랜치 {self.get_base_tag_from_branch()}]'
        return ''

    def checkout(self, branch: str, commit_id: str = '') -> bool:
        from . import LogManager
        try:

            if self.COMMIT_ID != '':
                commit_id = self.COMMIT_ID
            if commit_id != '':
                self._repo.head.reset(commit=commit_id, index=True, working_tree=True)
            else:
                self._repo.head.reset(index=True, working_tree=True)
                self.BRANCH = branch
                self._repo.git.checkout(branch)
                self.splog = LogManager(self.BRANCH, self.PATH_FOR_WORKING)

            self._info = self._brn()
            self.splog.info(f'{self._info} GIT CEHCKOUT 성공')
            return True
        except Exception as e:
            self.splog.error(f'{self._info} GIT CEHCKOUT Error \r\n{str(e)}')
        return False

    def _commit(self):
        try:
            self._repo.git.add(all=True)
            self._repo.index.commit(self.GIT_PUSH_MSG)
        except Exception as e:
            self.splog.error(f'{self._info} GIT Commit Error \r\n{str(e)}')

    # Ref :
    # https://docs.gitea.io/en-us/webhooks/
    # https://nixing.mx/posts/configure-gitea-webhooks.html
    def get_commit_from_webhook(self, webhook: dict) -> dict:
        """
        :param webhook: from git server
        :return:
        dict {
            "branch" : "test",
            "id": "5dc78789cadafe7bc73adf8031a9b6ba9236af2c",
            "message": "teste\n",
            "url": "http://url:3000/SPTeam/data-for-designer/commit/5dc78789cadafe7bc73adf8031a9b6ba9236af2c",
            "author": {
              "name": "기획자",
              "email": "designer@snowpipe.co.kr",
              "username": "designer"
            },
            "committer": {
              "name": "기획자",
              "email": "designer@snowpipe.co.kr",
              "username": "designer"
            },
            "verification": null,
            "timestamp": "2022-05-04T16:40:46+09:00",
            "added": [],
            "removed": [],
            "modified": [
              "excel/data/zone_data.json"
            ]
        }
        """
        try:
            res = {}
            username = webhook["head_commit"]["committer"]["username"]
            compare_url = webhook["compare_url"]

            # 레퍼런스에서 마지막 문자열(브랜치명) 추출 ex) "ref": "refs/heads/main"
            branch = webhook["ref"].split("/").pop()

            _info = f'[{branch} 브랜치]'

            # 변경사항이 없다면 무시
            if not compare_url:
                self.splog.send_designer(f"[EXCEL변환요청:{username}] {_info} 변경사항이 없어 종료합니다.")
                return res

            # 봇 PUSH 인 경우는 다시 PUSH하지 않고 메시지만 보낸다.
            if self._is_bot_user(username):
                self.splog.send_designer(f"{_info} 변경 히스토리 URL : {compare_url}")
                return res

            self.splog.send_designer(f"[EXCEL변환요청:{username}] {_info} 변경사항을 적용합니다.")
            res = webhook["head_commit"]
            res["branch"] = branch
            return res
        except Exception:
            self.splog.error(f"Webhook format Error : {webhook}")
        return {}

    # 자동봇 유저인지 확인
    def _is_bot_user(self, name: str):
        return True if name == self.GIT_USER else False

    def is_modified(self) -> bool:
        changed = [item.a_path for item in self._repo.index.diff(None)]
        if len(changed) > 0:
            self.splog.add_info(f'{self._info} 변경된 파일 : {str(changed)}')
            return True
        if len(self._repo.untracked_files) > 0:
            self.splog.add_info(f'{self._info} 변경된 파일 : {str(self._repo.untracked_files)}')
            return True

        self.splog.add_info(f'{self._info} 변경된 데이터가 없습니다.')
        return False

    def _is_empty_branch(self) -> bool:
        if not self.BRANCH:
            self.splog.warning(f'{self._info} 설정할 브랜치가 없습니다.')
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
            self.splog.info(f'{self._info} 변경된 EXCEL이 없습니다.')
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

    def get_base_tag_from_branch(self) -> str:
        """
        Branch에 있는 config.yml파일로 부터 마지막 태그를 읽어들인다.
        :return:
        """
        try:
            _path = self.PATH_FOR_WORKING.joinpath('config.yml')
            with open(_path, 'r') as f:
                config = yaml.safe_load(f)

            if 'LAST_TAG' in config:
                return config['LAST_TAG']
        except IOError as e:
            self.splog.warning(str(e))
        return ''

    def _is_diff_excel_files(self) -> bool:
        """
        비교할 태그 리파지토리에 수정된 엑셀파일이 있는지 확인 한다.
        추가 삭제는 무시
        """
        # 클라이언트 리파지토리인 경우 무시
        if self.GIT_TARGET is not GitTarget.EXCEL:
            return False

        _base_tag = self.get_base_tag_from_branch()
        if _base_tag == '':
            return False

        # 마지막 태그 기준으로 변경된 엑셀파일만 추출
        _diff = self._repo.index.diff(_base_tag).iter_change_type('M')
        _mod = self._get_diff_excel(_diff)

        if len(_mod) > 0:
            return True
        return False

    def is_modified_excel_column(self) -> bool:
        res = False

        self.splog.add_info(f'{self._info} 기획데이터에 변동 사항이 있습니다. 확인 후 개발 진행이 필요합니다.')
        _base_tag = self.get_base_tag_from_branch()

        # Excel 리파지토리 이면서 태그가 없는 경우는 새로운 파일추가로 수정된 필드 있음으로 간주
        if _base_tag == '':
            self.splog.add_info(f'{self._info} 태그가 존재하지 않아 신규 기획데이터로 할당 합니다.')
            return True

        # 마지막 태그 기준으로 삭제된 엑셀파일 추출
        _diff = self._repo.index.diff(_base_tag).iter_change_type('A')
        _del_files = self._get_diff_excel(_diff)
        if len(_del_files) > 0:
            self.splog.add_info(f'삭제 파일 리스트 ')
            self.splog.add_info(f'{_del_files}')
            res = True
        # 마지막 태그 기준으로 추가된 엑셀파일 추출
        _diff = self._repo.index.diff(_base_tag).iter_change_type('D')
        _add_files = self._get_diff_excel(_diff)
        if len(_add_files) > 0:
            self.splog.add_info(f'추가 파일 리스트 ')
            self.splog.add_info(f'{_add_files}')
            res = True

        # 마지막 태그 기준으로 수정된 엑셀파일 추출
        _diff = self._repo.index.diff(_base_tag).iter_change_type('M')
        _mod_files = self._get_diff_excel(_diff)

        # 수정된 엑셀파일이 없으면 리턴
        if len(_mod_files) == 0:
            return res

        from . import DataManager, ServerType
        data_old = DataManager(self.BRANCH, ServerType.ALL, self.PATH_FOR_WORKING_LAST)
        data_new = DataManager(self.BRANCH, ServerType.ALL, self.PATH_FOR_WORKING)

        diffs = []
        for path in _mod_files:
            _old = data_old.get_schema(path)
            _new = data_new.get_schema(path)
            diff = self.diff_schema(_old, _new)
            if len(diff) > 0:
                diffs.append(f'변경 컬럼 내역 : [{path}]')
                diffs = diffs + diff
        if len(diffs) > 0:
            self.splog.add_info(diffs)
        return res

    @staticmethod
    def diff_schema(old_schema: dict, new_schema: dict) -> list:
        """
        스키마 구성 ->
        table : [
            [필드, 데이터타입, 디비스키마, 설명(옵션)],
            [id, long, @id, '자동증가'],
            ...
        ]
        """
        res = []
        v1 = list(old_schema.values())[0]
        v2 = list(new_schema.values())[0]

        if len(v1) != len(v2):
            return [f"컬럼 수 {len(v1)} : {len(v2)}"]
        if len(v1[0]) != len(v2[0]):
            return [f"데이터 정의행 {len(v1[0])} : {len(v2[0])}"]
        for x in range(len(v1)):
            for y in range(len(v1[0])):
                if v1[x][y] != v2[x][y]:
                    res.append(f"데이터 항목 {v1[x][y]} : {v2[x][y]}")
        return res

    def destroy(self):
        try:
            self.splog.destory()
            # shutil.rmtree(self.PATH_FOR_WORKING)
            shutil.rmtree(self.PATH_FOR_WORKING_LAST)
        except Exception:
            pass

    def _random_path(self, config) -> Path:
        return self.PATH_FOR_ROOT.joinpath(config['DEFAULT']['EXPORT_DIR'],
                                           str(date.today()) + '_' + uuid.uuid4().hex)
