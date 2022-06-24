import os
import uuid
from enum import Enum, auto
from typing import Optional

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

    def __init__(self, target: GitTarget, branch: str = 'main', webhook: dict = None):

        if branch == '':
            branch = 'main'
        self.BRANCH = branch
        self._repo = None
        self.info = ''
        self.COMMIT_ID = ''
        self.BASE_COMMIT_ID = ''
        self.GIT_PUSH_MSG = ''
        self.NEW_TAG = ''
        self.BASE_TAG = ''
        self.IS_ADMIN = False
        self.GIT_TARGET = target
        self.PATH_FOR_ROOT = Path(__file__).parent.parent
        self.PATH_FOR_CONFIG = self.PATH_FOR_ROOT.joinpath('config.yaml')

        with open(self.PATH_FOR_CONFIG, 'r') as f:
            config = yaml.safe_load(f)
        self._set_config(config)
        self.HEAD_COMMIT = None

        if isinstance(webhook, dict):
            self.load_tag_from_webhook(webhook)
            self.load_commit_from_webhook(webhook)

        self.PATH_FOR_TARGET = self.PATH_FOR_ROOT.joinpath('import')
        self.PATH_FOR_WORKING = None
        self.PATH_FOR_WORKING_TAG = None
        self.PATH_FOR_BRANCH_CONFIG = None
        self._set_save_target()

        from . import LogManager
        self.splog = LogManager(self.BRANCH)
        self._init_git()

    def _set_config(self, config):
        if self.GIT_TARGET == GitTarget.EXCEL:
            self.GIT_URL = config['GITSERVER']['EXCEL_SSH']
        elif self.GIT_TARGET == GitTarget.CLIENT:
            self.GIT_URL = config['GITSERVER']['CLIENT_SSH']
        self.GIT_USER = config['GITSERVER']['USER']
        self.GIT_EMAIL = config['GITSERVER']['EMAIL']
        self.GIT_PUSH_MSG = config['GITSERVER']['PUSH_MSG']
        self.COMPILE_EXCEL = re.compile(rf"{config['DEFAULT']['EXCEL_DIR']}/[data | info]*/\S+[xls | xlsx]$")
        self.COMPILE_ENUM = re.compile(rf"{config['DEFAULT']['EXCEL_DIR']}/enum/\S+[xls | xlsx]$")
        self.COMPILE_JSON = re.compile(r"\D+json$")

    def _init_git(self):
        try:
            if not Path(self.PATH_FOR_WORKING).is_dir():
                self._repo = Repo.clone_from(self.GIT_URL, self.PATH_FOR_WORKING)
                # GIT 초기 설정
                writer = self._repo.config_writer()
                writer.set_value("user", "name", self.GIT_USER)
                writer.set_value("user", "email", self.GIT_EMAIL)
                writer.release()
                del writer
            else:
                self._repo = Repo(self.PATH_FOR_WORKING)
            if self.NEW_TAG != '':
                self.load_branch_from_tag(self.NEW_TAG)

            self._origin = self._repo.remotes.origin
            self.info = self._brn()
            self.splog.PREFIX = self.info

            self.splog.info('GIT 초기화 성공')

            # m = self._repo.head.reference
            # res = self._repo.git.branch('-a', '--contains', 'e316b2')
            # print(f'HEAD REF : {m.commit.hexsha}')
            # print(f'HEAD REF : {self.get_last_commit()}')

        except Exception as e:
            self.splog.info(f'GIT 초기화 Error \r\n{str(e)}')

    def get_branches(self) -> list:
        # data = Git().execute('git ls-remote -h git_url')
        if not self._repo:
            return []
        return [h.name.split('/')[-1] for h in self._repo.remotes.origin.refs]

    def get_tags(self) -> list:
        if not self._repo:
            return []
        return [h.name.split('/')[-1] for h in self._repo.tags]

    def pull(self) -> bool:
        try:
            if self._is_empty_branch():
                return False
            self._origin.pull(self.BRANCH)
            self.splog.info('GIT PULL 성공')
            return True
        except Exception as e:
            self.splog.error(f'GIT PULL Error \r\n{str(e)}')
        return False

    def push(self) -> bool:
        try:
            if self._is_empty_branch():
                return False
            self._commit()
            self._origin.push()
            self.splog.info('GIT PUSH 성공')
            return True
        except Exception as e:
            self.splog.error(f'GIT Push Error \r\n' + str(e))
        return False

    def _brn(self) -> str:
        if hasattr(self, '_repo'):
            return f'[GIT_{self.GIT_TARGET.name}][{self._repo.active_branch.name} 브랜치 {self.BASE_TAG}]'
        return ''

    def load_branch_from_tag(self, new_tag: str):
        self.splog.info(f"태그로 부터 브랜치를 설정합니다. [{new_tag}]")
        res = self._repo.git.branch('-a', '--contains', f'tags/{new_tag}')
        branch = res.split('/').pop()
        commit_id = self._repo.git.rev_parse(new_tag, short=True)
        self.BRANCH = branch
        self.COMMIT_ID = commit_id
        return branch

    def load_branch_from_commit(self, commit_id: str):
        self.splog.info(f"커밋아이디로 브랜치를 설정합니다. [{commit_id}]")
        res = self._repo.git.branch('-a', '--contains', commit_id)
        branch = res.split('/').pop()
        self.BRANCH = branch
        return branch

    def _checkout(self, cmd: str):
        if cmd in self._repo.remote().refs:
            self._repo.git.checkout(cmd)
        else:
            self._repo.git.checkout('-b', cmd)
            self.splog.info(f"브랜치를 새로 생성합니다. [{cmd}]")
            self.push()

    def _reset(self):
        self._repo.git.clean('-fdx')
        self._repo.git.reset('--hard', f'origin/{self.BRANCH}')
        # if self.COMMIT_ID != '':
        # self._repo.head.reset(commit=self.COMMIT_ID, index=True, working_tree=True)
        # else:
        # self._repo.head.reset(index=True, working_tree=True)

    def checkout(self, branch: str = '', commit_id: str = '') -> bool:
        try:
            self._reset()
            if self.COMMIT_ID != '':
                commit_id = self.COMMIT_ID
            if commit_id != '':
                self.load_branch_from_commit(commit_id)
                self.COMMIT_ID = self.get_current_commit()
            else:
                self.BRANCH = branch
                self.splog.BRANCH = branch
                self.COMMIT_ID = self.get_last_commit()

            if not Path(self.PATH_FOR_WORKING).is_dir():
                self._repo = Repo.clone_from(self.GIT_URL, self.PATH_FOR_WORKING, branch=self.BRANCH)
            else:
                self._repo = Repo(self.PATH_FOR_WORKING)
            self._checkout(self.BRANCH)
            self._reset()
            self.pull()

            self.BASE_TAG = self.get_base_tag_from_branch()
            self._set_save_target()

            self.info = self._brn()
            self.splog.PREFIX = self.info
            self._checkout_base()

            self.splog.info(f'GIT CEHCKOUT 성공 [{self.COMMIT_ID}]')
            return True
        except Exception as e:
            self.splog.error(f'GIT CHECKOUT Error \r\n{str(e)}')
        return False

    def _checkout_base(self):
        # 비교할 파일이 존재하면 리포지토리를 복제한다.
        if self.BASE_TAG != '':
            try:
                if not Path(self.PATH_FOR_WORKING_TAG).is_dir():
                    _old_repo = Repo.clone_from(self.GIT_URL, self.PATH_FOR_WORKING_TAG, branch=self.BRANCH)
                else:
                    _old_repo = Repo(self.PATH_FOR_WORKING_TAG)
                self.BASE_COMMIT_ID = _old_repo.commit().hexsha
                _old_repo.git.checkout(self.BASE_TAG)
                _old_repo.git.clean('-fdx')
                self.splog.info(f'BASE GIT CEHCKOUT 성공 [{self.BASE_COMMIT_ID}]')
            except Exception as e:
                self.splog.info(f'GIT 브랜치에 BASE TAG가 존재하지 않습니다. [{self.BASE_TAG}]: {str(e)}')

    def _commit(self):
        try:
            self._repo.git.add(all=True)
            self._repo.index.commit(self.GIT_PUSH_MSG)
        except Exception as e:
            self.splog.error(f'GIT Commit Error \r\n{str(e)}')

    def load_tag_from_webhook(self, webhook: dict) -> Optional[str]:
        try:
            # 레퍼런스에서 마지막 문자열(브랜치명) 추출 ex) "ref": "refs/tags/v0.5.0"
            z = re.match(r'refs/tags/(\S+)', webhook['ref'])
            if not z:
                return None
            tag = str(z.group(1))
            commit = webhook['head_commit']
            self.HEAD_COMMIT = commit
            self.GIT_PUSH_MSG = f'{self.GIT_PUSH_MSG} [{commit["committer"]["name"]}] : {commit["message"]}'
            self.NEW_TAG = tag
            return tag
        except Exception as e:
            self.splog.error(f"Webhook format Error : {str(e)}")
            return None
        # return webhook["head_commit"]["id"]

    #
    # Ref :
    # https://docs.gitea.io/en-us/webhooks/
    # https://nixing.mx/posts/configure-gitea-webhooks.html
    def load_commit_from_webhook(self, webhook: dict) -> dict:
        """
        :param webhook: from git server
        :return:
        dict {
          "ref": "refs/heads/test",
          "compare_url": "http://local.sp.snowpipe.net:3000/SPTeam/data-for-designer/compare/26794f0bb185d810b62d4ec5a175c1bcfe721d50...3f0af8253315b6538e70dd453e2be7343b39c5f4",
          "head_commit": {
            "id": "3f0af8253315b6538e70dd453e2be7343b39c5f4",
            "message": "[Excel자동변환]",
            "url": "http://local.sp.snowpipe.net:3000/SPTeam/data-for-designer/commit/3f0af8253315b6538e70dd453e2be7343b39c5f4",
            "committer": {
              "name": "spbot",
              "email": "spbot@snowpipe.co.kr",
              "username": "spbot"
            },
            "added": [],
            "removed": [],
            "modified": [
              "export/prisma/schema.prisma"
            ]
          },
        """
        res = {}
        try:
            res = webhook["head_commit"]
            self.HEAD_COMMIT = res

            # 레퍼런스에서 마지막 문자열(브랜치명) 추출 ex) "ref": "refs/heads/main"
            z = re.match(r'refs/heads/(\S+)', webhook["ref"])
            if not z:
                return res
            branch = str(z.group(1))
            self.BRANCH = branch
            self.GIT_PUSH_MSG = f'{self.GIT_PUSH_MSG} [{res["committer"]["name"]}] : {res["message"]}'
            self.COMMIT_ID = self.HEAD_COMMIT["id"]
            return res
        except Exception as e:
            self.splog.error(f"Webhook format Error : {str(e)}")
        return res

    # 자동봇 유저인지 확인
    def is_bot_user(self, name: str = ''):
        if name == '' and self.HEAD_COMMIT is not None:
            name = self.HEAD_COMMIT['committer']['username']
        return True if name == self.GIT_USER else False

    def is_modified(self) -> bool:
        changed = [item.a_path for item in self._repo.index.diff(None)]
        if len(changed) > 0:
            self.splog.add_info(f'변경된 파일 : {str(changed)}')
            return True
        if len(self._repo.untracked_files) > 0:
            self.splog.add_info(f'변경된 파일 : {str(self._repo.untracked_files)}')
            return True

        self.splog.info('변경된 데이터가 없습니다.')
        return False

    def _is_empty_branch(self) -> bool:
        if not self.BRANCH:
            self.splog.warning('설정할 브랜치가 없습니다.')
            return True
        return False

    def get_modified_excel(self, head_cnt=2) -> list:
        """과거 이력중 엑셀파일 경로만 추출
        """
        data = []
        for i in range(1, head_cnt + 1):
            _diff = self._repo.index.diff(f'HEAD~{i}')
            data = data + self._get_diff_excel(_diff, self.COMPILE_EXCEL)
            data = data + self._get_diff_excel(_diff, self.COMPILE_ENUM)
        if len(data) == 0:
            self.splog.info('변경된 EXCEL이 없습니다.')
            return []

        # 중복제거
        data = set(data)
        return list(data)

    @staticmethod
    def _get_diff_excel(diff_index, excel: re):
        res = []
        for diff_item in diff_index:
            value = diff_item.a_rawpath.decode('utf-8')
            if excel.match(value):
                res.append(value)
        return res

    def _get_diff_json(self, diff_index):
        res = []
        for diff_item in diff_index:
            value = diff_item.a_rawpath.decode('utf-8')
            if self.COMPILE_JSON.match(value):
                res.append(value)
        return res

    def get_current_commit(self) -> str:
        return self._repo.git.rev_parse(self.COMMIT_ID, short=True)

    def get_last_commit(self) -> str:
        return self._repo.git.rev_parse(self._repo.head, short=True)

    def get_last_tag(self) -> str:
        tags = sorted(self._repo.tags, key=lambda t: t.commit.committed_datetime)
        latest_tag = str(tags[-1])
        return latest_tag

    def get_base_tag_from_branch(self) -> str:
        """
        Branch에 있는 config.yaml파일로 부터 마지막 태그를 읽어들인다.
        :return:
        """
        try:
            with open(self.PATH_FOR_BRANCH_CONFIG, 'r') as f:
                config = yaml.safe_load(f)
            if 'LAST_TAG' in config:
                return config['LAST_TAG']
        except FileNotFoundError as e:
            pass
        except Exception as e:
            self.splog.warning(str(e))
        return ''

    def save_base_tag_to_branch(self, tag):
        try:
            data = {'LAST_TAG': tag}
            with open(self.PATH_FOR_BRANCH_CONFIG, 'w') as f:
                yaml.dump(data, f)
            self.BASE_TAG = tag
        except IOError as e:
            self.splog.warning(str(e))

    def get_client_resource_from_branch(self) -> dict:
        try:
            with open(self.PATH_FOR_BRANCH_CONFIG, 'r') as f:
                config = yaml.safe_load(f)
            return {'res_ver': config["CLIENT_RES_VER"], 'res_url': config["CLIENT_RES_URL"]}
        except Exception as e:
            self.splog.warning(str(e))
        return {}

    def save_client_resource_to_branch(self, resource_url: str):
        config = {}
        try:
            with open(self.PATH_FOR_BRANCH_CONFIG, 'r') as f:
                config = yaml.safe_load(f)
        except IOError as e:
            self.splog.warning(str(e))

        config["CLIENT_RES_VER"] = self.COMMIT_ID
        config["CLIENT_RES_URL"] = resource_url

        try:
            with open(self.PATH_FOR_BRANCH_CONFIG, 'w') as f:
                config = yaml.dump(config, f)
        except IOError as e:
            self.splog.warning(str(e))

    def is_modified_excel_enum(self) -> bool:
        # Excel 리파지토리 이면서 태그가 없는 경우는 새로운 파일추가로 수정된 필드 있음으로 간주
        if self.BASE_COMMIT_ID == '':
            self.splog.add_info('태그가 존재하지 않아 신규 ENUM데이터로 할당 합니다.')
            return True

        # 마지막 태그 기준으로 수정된 엑셀파일 추출
        _diff = self._repo.index.diff(self.BASE_COMMIT_ID).iter_change_type('M')
        _mod_files = self._get_diff_excel(_diff, self.COMPILE_ENUM)
        # 수정된 엑셀파일이 없으면 리턴
        if len(_mod_files) > 0:
            return True
        return False

    def is_modified_excel_column(self) -> bool:
        res = False

        # Excel 리파지토리 이면서 태그가 없는 경우는 새로운 파일추가로 수정된 필드 있음으로 간주
        if self.BASE_COMMIT_ID == '':
            self.splog.add_info('태그가 존재하지 않아 신규 기획데이터로 할당 합니다.')
            return True

        # 마지막 태그 기준으로 삭제된 엑셀파일 추출
        _diff = self._repo.index.diff(self.BASE_COMMIT_ID).iter_change_type('A')
        _del_files = self._get_diff_excel(_diff, self.COMPILE_EXCEL)
        if len(_del_files) > 0:
            self.splog.add_info('삭제 파일 리스트 ')
            self.splog.add_info(_del_files)
            res = True
        # 마지막 태그 기준으로 추가된 엑셀파일 추출
        _diff = self._repo.index.diff(self.BASE_COMMIT_ID).iter_change_type('D')
        _add_files = self._get_diff_excel(_diff, self.COMPILE_EXCEL)
        if len(_add_files) > 0:
            self.splog.add_info('추가 파일 리스트 ')
            self.splog.add_info(_add_files)
            res = True

        # 마지막 태그 기준으로 수정된 엑셀파일 추출
        _diff = self._repo.index.diff(self.BASE_COMMIT_ID).iter_change_type('M')
        _mod_files = self._get_diff_excel(_diff, self.COMPILE_EXCEL)
        # 수정된 엑셀파일이 없으면 리턴
        if len(_mod_files) == 0:
            return res

        from . import DataManager, ConvertType
        data_old = DataManager(self.BRANCH, ConvertType.ALL, self.PATH_FOR_WORKING_TAG)
        data_new = DataManager(self.BRANCH, ConvertType.ALL, self.PATH_FOR_WORKING)

        diffs = []
        for path in _mod_files:
            _old = data_old.get_schema(path)
            _new = data_new.get_schema(path)
            diff = self.diff_schema(path, _old, _new)
            if len(diff) > 0:
                diffs.append(f'변경 컬럼 내역 : [{path}]')
                diffs = diffs + diff
        if len(diffs) > 0:
            self.splog.add_info(diffs)
            return True
        return res

    def diff_schema(self, path: str, old_schema: dict, new_schema: dict) -> list:
        """
        스키마 구성 ->
        table : [
            [필드, 데이터타입, 디비스키마, 설명(옵션)],
            [id, long, @id, '자동증가'],
            ...
        ]
        """
        res = []
        info = {0: "데이터 필드", 1: "데이터 타입", 2: "스키마 타입", 3: "데이터 주석"}
        try:
            v1 = list(old_schema.values())[0]
            v2 = list(new_schema.values())[0]
            if len(v1) == 0 or len(v2) == 0:
                return res
            if len(v1) != len(v2):
                return [f"컬럼 수 {len(v1)} : {len(v2)}"]
            if len(v1[0]) != len(v2[0]):
                return [f"데이터 정의행 {len(v1[0])} : {len(v2[0])}"]

            for x in range(len(v1)):
                for y in range(len(v1[0])):
                    if v1[x][y] != v2[x][y]:
                        old = 'null' if v1[x][y] == '' else v1[x][y]
                        new = 'null' if v2[x][y] == '' else v2[x][y]
                        res.append(f"[{info[y]}:{v2[0]}] {old} -> {new}")
        except Exception as e:
            self.splog.error(f"스키마 비교 Error : {path} \r {str(e)}")

        return res

    def push_tag_to_client(self, tag: str):
        if tag == '':
            return
        if self.GIT_TARGET is not GitTarget.CLIENT:
            return
        if tag in self._repo.tags:
            self.splog.info(f'TAG[{tag}]가 이미 존재하여 삭제합니다.')
            self._repo.delete_tag(self._repo.tags[tag])
            self._origin.push(f':refs/tags/{tag}')
        self.splog.info(f'TAG[{tag}]를 생성 합니다.')
        self._repo.create_tag(tag, message='Automatic tag "{0}"'.format(tag))
        self._origin.push(self._repo.tags)

    def set_admin(self):
        self.IS_ADMIN = True

    def _set_save_target(self, is_admin: bool = False):
        _target = None
        if is_admin:
            _target = self.PATH_FOR_TARGET.joinpath('admin', self.GIT_TARGET.name.lower())
        else:
            _target = self.PATH_FOR_TARGET.joinpath('user', self.GIT_TARGET.name.lower())

        if self.NEW_TAG != '':
            self.PATH_FOR_WORKING = _target.joinpath(self.NEW_TAG)
        else:
            self.PATH_FOR_WORKING = _target.joinpath(self.BRANCH)

        self.PATH_FOR_WORKING_TAG = _target.joinpath(self.BASE_TAG)
        self.PATH_FOR_BRANCH_CONFIG = self.PATH_FOR_WORKING.joinpath("config.yaml")

    def destroy(self):
        try:
            self.splog.destory()
            # shutil.rmtree(self.PATH_FOR_WORKING)
            # shutil.rmtree(self.PATH_FOR_WORKING_BASE)
        except Exception:
            pass

    def _random_path(self, config) -> Path:
        return self.PATH_FOR_ROOT.joinpath(config['DEFAULT']['EXPORT_DIR'],
                                           str(date.today()) + '_' + uuid.uuid4().hex)
