import asyncio
import logging
from pprint import pprint
import yaml

# import cProfile

if __name__ == '__main__' or __name__ == "decimal":
    from app import *

    _format = '[%(levelname)-7s] %(asctime)s: %(message)s '
    # _format_console = colorlog.ColoredFormatter(_format, "%m/%d/%Y %H:%M:%S ")
    logger = logging.getLogger()
    handler = logging.FileHandler('out.log', 'w', 'utf-8')
    # handler.setFormatter(_format_console)
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)

    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.INFO)
    # stream_handler.setFormatter(_format_console)
    logger.addHandler(stream_handler)


else:
    # from app import *
    from app.libs.excel_to_db.app import *


def sync_prisma(branch: str):
    g_manager = GitManager(GitTarget.EXCEL, branch)

    if not g_manager.checkout():
        g_manager.destroy()
        return

    # 프리즈마 초기화
    prisma = PrismaManager(branch, g_manager.PATH_FOR_WORKING)
    prisma.sync()


async def update_table(branch: str, convert_type: ConvertType):
    db_task = TaskManager(TaskType.UPDATE_TB_DATA, branch=branch)
    if convert_type == ConvertType.INFO:
        db_task = TaskManager(TaskType.UPDATE_TB_INFO, branch=branch)

    if db_task.start():
        # Git 초기화 및 다운로드
        g_manager = GitManager(GitTarget.EXCEL, branch)

        # 체크아웃 성공시에만 진행
        if not g_manager.checkout():
            g_manager.destroy()
            return

        prisma = PrismaManager(branch, g_manager.PATH_FOR_WORKING)
        d_manager = DataManager(branch, convert_type, g_manager.PATH_FOR_WORKING)
        await prisma.restore_all_table(d_manager.get_jsonmap(ConvertType.INFO))
        await prisma.destory()
        await tag_to_db(g_manager, prisma)
        db_task.done()


def excel_to_json_all(g_manager: GitManager):
    """전체 Excel을 추출후 Json변환
        """

    g_manager.splog.info("전체 Excel로드후 Json변환을 진행합니다.")

    # 전체 Excel로드후 Json변환
    d_manager = DataManager(g_manager.BRANCH, ConvertType.ALL, g_manager.PATH_FOR_WORKING)
    d_manager.delete_json_all()
    excel_paths = d_manager.get_excelpath_all()
    d_manager.excel_to_json(excel_paths)
    d_manager.check_excel_for_relation(excel_paths)


def excel_to_json_modified(convert_type: ConvertType, g_manager: GitManager):
    """
    변경된 Excel만 추출후 Json변환
    @param convert_type: 기획데이터:server Info데이터:info 클라이언트데이터:client
    @param g_manager: GitManager
    @return:
    """
    branch = g_manager.BRANCH
    g_manager.splog.info(f"변경된 Excel로드후 Json변환을 진행합니다. [데이터 타입 : {convert_type.name}]")

    d_manager = DataManager(branch, convert_type, g_manager.PATH_FOR_WORKING)
    modified_excel = g_manager.get_modified_excel(5)
    # Excel로드후 Json변환
    d_manager.delete_path(g_manager.get_deleted_json())
    d_manager.excel_to_json(modified_excel)
    d_manager.check_excel_for_relation(modified_excel)


def excel_to_entity(g_manager: GitManager, gc_manager: GitManager):
    g_manager.splog.info("전체 Excel로드후 C# 스크립트 변환을 진행합니다.")

    d_manager = DataManager(g_manager.BRANCH, ConvertType.CLIENT, g_manager.PATH_FOR_WORKING)
    c_manager = CSharpManager(g_manager.BRANCH, g_manager.COMMIT, gc_manager.PATH_FOR_WORKING)
    c_manager.save_entity(d_manager.get_schema_all())
    c_manager.save_enum(d_manager.get_enum_data())
    d_manager.save_json_all(gc_manager.PATH_FOR_WORKING.joinpath("data_all.json"))


def excel_to_enum(g_manager: GitManager, gc_manager: GitManager):
    g_manager.splog.info("전체 Excel로드후 Enum 스크립트 변환을 진행합니다.")
    d_manager = DataManager(g_manager.BRANCH, ConvertType.CLIENT, g_manager.PATH_FOR_WORKING)
    c_manager = CSharpManager(g_manager.BRANCH, g_manager.COMMIT, gc_manager.PATH_FOR_WORKING)
    c_manager.save_enum(d_manager.get_enum_data())


def excel_to_schema(g_manager: GitManager):
    """
    전체 Excel추출후 아래 데이터 타입만 Prisma 스키마변환
    @param g_manager: GitManager
    """
    g_manager.splog.info("전체 Excel로드후 Prisma변환을 진행합니다.")

    # 프리즈마 초기화
    p_manager = PrismaManager(g_manager.BRANCH, g_manager.PATH_FOR_WORKING)
    d_manager = DataManager(g_manager.BRANCH, ConvertType.SERVER, g_manager.PATH_FOR_WORKING)
    data_table = d_manager.get_schema_all(ConvertType.SERVER)
    p_manager.save(data_table, DBType.DATA_DB)


def markdown_to_script(g_manager: GitManager, gc_manager: GitManager):
    g_manager.splog.info("전체 Markdown 로드 후 C# Script변환을 진행합니다.")
    d_manager = DataManager(branch, ConvertType.MARKDOWN, g_manager.PATH_FOR_WORKING)
    c_manager = CSharpManager(branch, g_manager.COMMIT, gc_manager.PATH_FOR_WORKING)
    _obl = d_manager.get_markdown(ConvertType.MARKDOWN_PROTOCOL)
    c_manager.save_protocol(_obl)
    _obl = d_manager.get_markdown(ConvertType.MARKDOWN_ENUM)
    c_manager.save_server_enum(_obl)
    _obl = d_manager.get_markdown(ConvertType.MARKDOWN_ENTITY)
    c_manager.save_server_entity(_obl)


def get_commit_from_webhook(webhook: dict) -> dict:
    g_manager = GitManager(GitTarget.EXCEL, None, webhook)
    res = g_manager.load_commit_from_webhook(webhook)
    g_manager.destroy()
    return res


async def excel_to_data_all_from_branch(branch: str):
    """
    최신 Excel Git 브랜치를 복제한후 데이터 변환을 호출한다.
    @param branch: Git브랜치
    """
    # Git 초기화 및 다운로드
    g_manager = GitManager(GitTarget.EXCEL, branch)

    task = TaskManager(TaskType.EXCEL, branch)
    task.init(g_manager)

    if task.start():

        # # 체크아웃 성공시에만 진행
        if not g_manager.checkout():
            g_manager.destroy()
            return
        excel_to_json_all(g_manager)

        await excel_to_server(g_manager)

        if g_manager.is_modified():
            g_manager.push()
        g_manager.destroy()

        task.done()


async def excel_to_data_from_webhook(webhook: dict = None):
    """
    Git Push 발생후 Webhook에서 이 메서드가 호출됨
    git commit id를 기준으로 리포지토리를 복제한후 데이터 변환을 호출한다.
    @param webhook: 호출 파라미터 상세
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
    g_manager = GitManager(GitTarget.EXCEL, webhook=webhook)
    # # 체크아웃 성공시에만 진행
    if not webhook["head_commit"] or not g_manager.checkout():
        g_manager.destroy()
        return

    username = webhook["head_commit"]["committer"]["username"]
    message = webhook["head_commit"]["message"]
    compare_url = webhook["compare_url"]

    if g_manager.NEW_TAG != '':
        await excel_to_data_taged(g_manager)
    else:
        # 변경사항이 없다면 무시
        if not compare_url:
            g_manager.splog.send_designer(f"[EXCEL변환요청:{username}] 변경사항이 없어 종료합니다.")
            return

        # 봇 PUSH 인 경우는 다시 PUSH하지 않고 메시지만 보낸다.
        if g_manager.is_bot_user():
            g_manager.splog.send_designer(f"변경 히스토리 URL : {compare_url}")
            return

        g_manager.splog.send_designer(f"[EXCEL변환요청:{username}] 변경사항을 적용합니다. \n\n {message}")
        await excel_to_data_modified(g_manager)


async def excel_to_data_modified_all(branch: str):
    g_manager = GitManager(GitTarget.EXCEL, branch=branch)
    if not g_manager.checkout():
        g_manager.destroy()
        return
    await excel_to_data_modified(g_manager)


async def excel_to_data_modified(g_manager: GitManager):
    excel_task = TaskManager(TaskType.EXCEL, branch=g_manager.BRANCH)
    if excel_task.start():
        excel_to_json_modified(ConvertType.ALL, g_manager)
        await excel_to_server(g_manager)
        # 수정된 Json 파일이 있다면 Excel Git서버로 자동 커밋
        if g_manager.is_modified():
            g_manager.push()
        g_manager.destroy()
        excel_task.done()


async def excel_to_data_taged(g_manager: GitManager):
    g_manager.splog.info(f"새로운 태그[{g_manager.NEW_TAG}] 요청으로 DB업데이트 및 클라이언트 태그 전송을 시작합니다.")

    db_task = TaskManager(TaskType.EXCEL_TAG, branch=g_manager.BRANCH)
    if db_task.start():

        gc_manager = GitManager(GitTarget.CLIENT, g_manager.BRANCH)
        if not gc_manager.checkout():
            gc_manager.destroy()
            return
        data_to_client_data(g_manager, gc_manager)
        if gc_manager.is_modified():
            gc_manager.push()
        if g_manager.NEW_TAG != '':
            gc_manager.push_tag_to_client(g_manager.NEW_TAG)
        gc_manager.destroy()

        prisma = PrismaManager(g_manager.BRANCH, g_manager.PATH_FOR_WORKING)
        prisma.migrate(MigrateType.FORCE, g_manager.BRANCH)
        await data_to_db(g_manager, prisma)
        await tag_to_db(g_manager, prisma)
        if g_manager.is_modified():
            g_manager.push()
        db_task.done()


async def excel_to_data_all_from_tag(tag: str):
    g_manager = GitManager(GitTarget.EXCEL, branch='main', tag=tag)
    if not g_manager.checkout():
        g_manager.destroy()
        return
    await excel_to_data_taged(g_manager)
    gc_manager = GitManager(GitTarget.CLIENT, g_manager.BRANCH)
    if not gc_manager.checkout():
        gc_manager.destroy()
        return
    # g_manager.GIT_PUSH_MSG = f'{g_manager.GIT_PUSH_MSG} API 호출로 인한 EXCEL전체 변환'
    # g_manager.splog.info(f"새로운 태그[{g_manager.NEW_TAG}] 요청으로 EXCEL 전체 변환을 시작합니다.")
    #
    # excel_to_json_all(g_manager)
    # excel_to_schema(g_manager)
    # excel_to_entity(g_manager, gc_manager)
    # excel_to_enum(g_manager, gc_manager)
    # data_to_client_data(g_manager, gc_manager)
    # if gc_manager.is_modified():
    #     gc_manager.push()
    #     gc_manager.destroy()
    # if g_manager.is_modified():
    #     g_manager.push()
    #
    # prisma = PrismaManager(g_manager.BRANCH, g_manager.PATH_FOR_WORKING)
    # prisma.migrate(MigrateType.FORCE, g_manager.BRANCH)
    # await data_to_db(g_manager, prisma)
    # await tag_to_db(g_manager, prisma)
    # g_manager.destroy()


def data_to_client_data(g_manager: GitManager, gc_manager: GitManager):
    d_manager = DataManager(g_manager.BRANCH, ConvertType.CLIENT, g_manager.PATH_FOR_WORKING)
    if g_manager.NEW_TAG != '':
        f_manager = FtpManager(g_manager.BRANCH, g_manager.COMMIT, g_manager.PATH_FOR_WORKING)
        f_manager.send(d_manager.get_json())
        g_manager.save_client_resource_to_branch(f_manager.get_resource_url())
        d_manager.remove_file(gc_manager.PATH_FOR_WORKING.joinpath("data_all.json"))
    else:
        if g_manager.LAST_MODIFIED:
            d_manager.save_json_all(gc_manager.PATH_FOR_WORKING.joinpath("data_all.json"))


async def excel_to_server(g_manager: GitManager):
    gc_manager = GitManager(GitTarget.CLIENT, g_manager.BRANCH)
    if not gc_manager.checkout():
        gc_manager.destroy()
        return

    markdown_to_script(g_manager, gc_manager)

    if g_manager.is_modified_excel_enum():
        excel_to_enum(g_manager, gc_manager)
        msg = 'Enum 데이터에 변동 사항이 있습니다. 개발자가 확인 후 다음 프로세스로 진행됩니다.'
        g_manager.splog.add_warning(msg)
        g_manager.splog.send_developer()
        g_manager.splog.send_designer(msg)

    if g_manager.is_modified_excel_column():
        g_manager.splog.info(f'EXCEL파일에 변동이 있어 스키마 변환을 진행합니다.')
        excel_to_entity(g_manager, gc_manager)
        excel_to_schema(g_manager)
        if not g_manager.splog.is_service_branch(g_manager.BRANCH):
            data_to_client_data(g_manager, gc_manager)
        msg = '기획 데이터의 컬럼에 변동 사항이 있습니다. 개발자가 확인 후 다음 프로세스로 진행됩니다.'
        g_manager.splog.add_warning(msg)
        g_manager.splog.send_developer()
        g_manager.splog.send_designer(msg)
    else:
        if g_manager.LAST_MODIFIED:
            g_manager.splog.send_designer(f'EXCEL파일 데이터 수정으로 인한 데이터 업데이트를 진행합니다.')
            data_to_client_data(g_manager, gc_manager)
            await data_to_db(g_manager)
            await tag_to_db(g_manager)

    if gc_manager.is_modified():
        gc_manager.push()
    if g_manager.NEW_TAG != '':
        gc_manager.push_tag_to_client(g_manager.NEW_TAG)
    gc_manager.destroy()


async def migrate(branch: str, is_admin: bool = False):
    """
    Prisma 스키마 로드 후 해당 브랜치 디비에 반영
    @param branch: Git브랜치 -> Config에 DB접속정보가 브랜치별로 존재
    @return:
    """
    # Git 초기화 및 다운로드
    g_manager = GitManager(GitTarget.EXCEL, branch)
    if is_admin:
        g_manager.set_admin()

    # 체크아웃 성공시에만 진행
    if not g_manager.checkout():
        g_manager.destroy()
        return

    db_task = TaskManager(TaskType.MIGRATE_DB, branch=branch)
    if db_task.start():
        prisma = PrismaManager(branch, g_manager.PATH_FOR_WORKING)
        prisma.migrate(MigrateType.FORCE, branch)
        await data_to_db(g_manager, prisma)
        await tag_to_db(g_manager, prisma)
        g_manager.destroy()
        db_task.done()


async def data_to_db(g_manager: GitManager, p_manager: PrismaManager):
    d_manager = DataManager(g_manager.BRANCH, ConvertType.SERVER, g_manager.PATH_FOR_WORKING)
    await p_manager.restore_all_table(d_manager.get_jsonmap(ConvertType.SERVER))
    await p_manager.restore_all_table(d_manager.get_jsonmap(ConvertType.INFO))
    await p_manager.destory()


async def tag_to_db(g_manager: GitManager, p_manager: PrismaManager):
    res_info = g_manager.get_client_resource_from_branch()
    if len(res_info.keys()) > 0:
        await p_manager.update_version_info(res_info['res_ver'], res_info['res_url'])
    await p_manager.destory()


async def check(branch: str):
    task = TaskManager(TaskType.SCHEDULER)
    if not task.load_task():
        return
    pass


async def scheduler():
    await asyncio.sleep(1)
    job_task = TaskManager(TaskType.SCHEDULER)
    if not job_task.load_task():
        job_task.splog.info("대기열에 작업이 없습니다.")
        return
    task = job_task.pop_task()
    if task is None:
        return
    task_type = next(iter(task))
    _task_val = next(iter(task.values()))
    task_branch = next(iter(_task_val))
    task_tag = list(_task_val.values())[0]

    if task_type == TaskType.EXCEL:
        excel_task = TaskManager(TaskType.EXCEL, branch=task_branch)
        g_manager = GitManager(GitTarget.EXCEL, branch=task_branch)
        if not g_manager.checkout():
            g_manager.destroy()
            return
        await excel_to_data_modified(g_manager)
        return

    if task_type == TaskType.EXCEL_TAG:
        tag_task = TaskManager(TaskType.EXCEL_TAG, branch=task_branch, tag=task_tag)
        g_manager = GitManager(GitTarget.EXCEL, branch=task_branch, tag=task_tag)
        if not g_manager.checkout():
            g_manager.destroy()
            return
        await excel_to_data_taged(g_manager)
        return

    if task_type == TaskType.MIGRATE_DB:
        db_task = TaskManager(TaskType.MIGRATE_DB, branch=task_branch)
        await migrate(task_branch)


async def test(branch: str):
    webhook = {'ref': 'refs/heads/test_cg', 'before': 'c993fb440425f46a1b382e78bc7f969ea4ba602f',
               'after': 'b11ad53f806660152ea855c33bd0ede6d59cc855',
               'compare_url': 'http://local.sp.snowpipe.net:3000/SPTeam/data-for-designer/compare/c993fb440425f46a1b382e78bc7f969ea4ba602f...b11ad53f806660152ea855c33bd0ede6d59cc855',
               'commits': [{'id': 'b11ad53f806660152ea855c33bd0ede6d59cc855', 'message': '[서버/이철길] 테스트 데이터 추가\n',
                            'url': 'http://local.sp.snowpipe.net:3000/SPTeam/data-for-designer/commit/b11ad53f806660152ea855c33bd0ede6d59cc855',
                            'author': {'name': 'CGLee', 'email': 'cglee@snowpipe.co.kr', 'username': 'CGLee'},
                            'committer': {'name': 'CGLee', 'email': 'cglee@snowpipe.co.kr', 'username': 'CGLee'},
                            'verification': None, 'timestamp': '2022-07-05T11:54:55+09:00', 'added': [], 'removed': [],
                            'modified': ['excel/data/zone_data.xlsx']}],
               'head_commit': {'id': 'b11ad53f806660152ea855c33bd0ede6d59cc855', 'message': '[서버/이철길] 테스트 데이터 추가\n',
                               'url': 'http://local.sp.snowpipe.net:3000/SPTeam/data-for-designer/commit/b11ad53f806660152ea855c33bd0ede6d59cc855',
                               'author': {'name': 'CGLee', 'email': 'cglee@snowpipe.co.kr', 'username': 'CGLee'},
                               'committer': {'name': 'CGLee', 'email': 'cglee@snowpipe.co.kr', 'username': 'CGLee'},
                               'verification': None, 'timestamp': '2022-07-05T11:54:55+09:00', 'added': [],
                               'removed': [],
                               'modified': ['excel/data/zone_data.xlsx']}, 'repository': {'id': 8, 'owner': {'id': 2,
                                                                                                             'login': 'SPTeam',
                                                                                                             'full_name': '',
                                                                                                             'email': '',
                                                                                                             'avatar_url': 'http://local.sp.snowpipe.net:3000/avatars/0b4e480645d9e5c45dfdf455829cd61d',
                                                                                                             'language': '',
                                                                                                             'is_admin': False,
                                                                                                             'last_login': '0001-01-01T00:00:00Z',
                                                                                                             'created': '2022-04-25T15:47:09+09:00',
                                                                                                             'restricted': False,
                                                                                                             'active': False,
                                                                                                             'prohibit_login': False,
                                                                                                             'location': '',
                                                                                                             'website': '',
                                                                                                             'description': '',
                                                                                                             'visibility': 'limited',
                                                                                                             'followers_count': 0,
                                                                                                             'following_count': 0,
                                                                                                             'starred_repos_count': 0,
                                                                                                             'username': 'SPTeam'},
                                                                                          'name': 'data-for-designer',
                                                                                          'full_name': 'SPTeam/data-for-designer',
                                                                                          'description': '',
                                                                                          'empty': False,
                                                                                          'private': False,
                                                                                          'fork': False,
                                                                                          'template': False,
                                                                                          'parent': None,
                                                                                          'mirror': False,
                                                                                          'size': 86516,
                                                                                          'html_url': 'http://local.sp.snowpipe.net:3000/SPTeam/data-for-designer',
                                                                                          'ssh_url': 'ssh://git@local.sp.snowpipe.net:222/SPTeam/data-for-designer.git',
                                                                                          'clone_url': 'http://local.sp.snowpipe.net:3000/SPTeam/data-for-designer.git',
                                                                                          'original_url': '',
                                                                                          'website': '',
                                                                                          'stars_count': 0,
                                                                                          'forks_count': 0,
                                                                                          'watchers_count': 23,
                                                                                          'open_issues_count': 0,
                                                                                          'open_pr_counter': 0,
                                                                                          'release_counter': 0,
                                                                                          'default_branch': 'main',
                                                                                          'archived': False,
                                                                                          'created_at': '2022-04-25T21:09:48+09:00',
                                                                                          'updated_at': '2022-07-04T20:49:43+09:00',
                                                                                          'permissions': {'admin': True,
                                                                                                          'push': True,
                                                                                                          'pull': True},
                                                                                          'has_issues': True,
                                                                                          'internal_tracker': {
                                                                                              'enable_time_tracker': True,
                                                                                              'allow_only_contributors_to_track_time': True,
                                                                                              'enable_issue_dependencies': True},
                                                                                          'has_wiki': True,
                                                                                          'has_pull_requests': True,
                                                                                          'has_projects': True,
                                                                                          'ignore_whitespace_conflicts': True,
                                                                                          'allow_merge_commits': True,
                                                                                          'allow_rebase': True,
                                                                                          'allow_rebase_explicit': True,
                                                                                          'allow_squash_merge': True,
                                                                                          'default_merge_style': 'merge',
                                                                                          'avatar_url': 'http://local.sp.snowpipe.net:3000/repo-avatars/8-d9bb3e12bc1348e1106d08357fe1e0dd',
                                                                                          'internal': False,
                                                                                          'mirror_interval': '',
                                                                                          'mirror_updated': '0001-01-01T00:00:00Z',
                                                                                          'repo_transfer': None},
               'pusher': {'id': 1, 'login': 'CGLee', 'full_name': '[서버] 이철길', 'email': 'cglee@snowpipe.co.kr',
                          'avatar_url': 'http://local.sp.snowpipe.net:3000/avatar/72952e4475064e0b3582bf23cd38834f',
                          'language': '', 'is_admin': False, 'last_login': '0001-01-01T00:00:00Z',
                          'created': '2022-04-25T15:20:04+09:00', 'restricted': False, 'active': False,
                          'prohibit_login': False, 'location': '', 'website': '', 'description': '[서버] 이철길',
                          'visibility': 'public', 'followers_count': 0, 'following_count': 0, 'starred_repos_count': 0,
                          'username': 'CGLee'},
               'sender': {'id': 1, 'login': 'CGLee', 'full_name': '[서버] 이철길', 'email': 'cglee@snowpipe.co.kr',
                          'avatar_url': 'http://local.sp.snowpipe.net:3000/avatar/72952e4475064e0b3582bf23cd38834f',
                          'language': '', 'is_admin': False, 'last_login': '0001-01-01T00:00:00Z',
                          'created': '2022-04-25T15:20:04+09:00', 'restricted': False, 'active': False,
                          'prohibit_login': False, 'location': '', 'website': '', 'description': '[서버] 이철길',
                          'visibility': 'public', 'followers_count': 0, 'following_count': 0, 'starred_repos_count': 0,
                          'username': 'CGLee'}}

    await excel_to_data_from_webhook(webhook)

    # pprint(g_manager.get_deleted_json())
    # pprint(g_manager.get_modified_excel())
    # markdown_to_script(g_manager, gc_manager)
    # task = TaskManager(TaskType.EXCEL, g_manager)
    # task.init(g_manager)
    # gc_manager = GitManager(GitTarget.CLIENT, branch)
    # if not gc_manager.checkout():
    #     gc_manager.destroy()
    #     return
    # await excel_to_data_modified(g_manager)
    # markdown_to_script(g_manager, gc_manager)
    # gc_manager.push()
    # await migrate(branch)
    # print(task.pop_task())


if __name__ == '__main__' or __name__ == "decimal":
    branch = 'main'

    # logging.info(f"[{branch} 브랜치] 전체 Excel로드후 C# 스크립트 변환을 진행합니다.")
    # asyncio.run(migrate(branch))
    # asyncio.run(excel_to_data_all_from_tag('v0.5.1'))
    # asyncio.run(excel_to_data_all_from_branch(branch))
    # asyncio.run(excel_to_data_modified_all(branch))
    # asyncio.run(update_table(branch, ConvertType.ALL))
    # asyncio.run(scheduler())

    pass
