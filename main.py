import asyncio
import logging
from typing import Optional

import colorlog
from pathlib import Path

if __name__ == '__main__' or __name__ == "decimal":
    from app import *

    _format = '[%(levelname)-7s] %(asctime)s: %(message)s '
    _format_console = colorlog.ColoredFormatter(_format, "%m/%d/%Y %H:%M:%S ")
    logger = logging.getLogger()
    handler = logging.FileHandler('out.log', 'w', 'utf-8')
    handler.setFormatter(_format_console)
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)

    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.INFO)
    stream_handler.setFormatter(_format_console)
    logger.addHandler(stream_handler)


else:
    from app.libs.excel_to_db.app import *


def sync_prisma(branch: str):
    g_manager = GitManager(GitTarget.EXCEL)

    if not g_manager.checkout(branch):
        g_manager.destroy()
        return

    # 프리즈마 초기화
    prisma = PrismaManager(branch, g_manager.PATH_FOR_WORKING)
    prisma.sync()


async def update_table(branch: str, server_type: ServerType):
    # Git 초기화 및 다운로드
    g_manager = GitManager(GitTarget.EXCEL)

    # 체크아웃 성공시에만 진행
    if not g_manager.checkout(branch):
        g_manager.destroy()
        return

    # 프리즈마 초기화
    p_manager = PrismaManager(branch, g_manager.PATH_FOR_WORKING)

    # 변환된 Json파일을 디비로 저장
    b_manager = DBManager(branch, g_manager.PATH_FOR_WORKING)
    d_manager = DataManager(branch, server_type, g_manager.PATH_FOR_WORKING)
    json_map = d_manager.get_jsonmap()
    await b_manager.restore_all_table(json_map)


def excel_to_json_all(g_manager: GitManager):
    """전체 Excel을 추출후 Json변환
        """

    g_manager.splog.info("전체 Excel로드후 Json변환을 진행합니다.")

    # 전체 Excel로드후 Json변환
    d_manager = DataManager(g_manager.BRANCH, ServerType.ALL, g_manager.PATH_FOR_WORKING)
    d_manager.delete_json_all()
    d_manager.excel_to_json(d_manager.get_excelpath_all())


def excel_to_json(server_type: ServerType, g_manager: GitManager):
    """
    변경된 Excel만 추출후 Json변환
    @param server_type: 기획데이터:server Info데이터:info 클라이언트데이터:client
    @param g_manager: GitManager
    @return:
    """
    branch = g_manager.BRANCH
    g_manager.splog.info(f"변경된 Excel로드후 Json변환을 진행합니다. [데이터 타입 : {server_type.name}]")

    d_manager = DataManager(branch, server_type, g_manager.PATH_FOR_WORKING)

    # Excel로드후 Json변환
    d_manager.excel_to_json(g_manager.get_modified_excel())


def excel_to_entity(g_manager: GitManager):
    g_manager.splog.info("전체 Excel로드후 C# 스크립트 변환을 진행합니다.")

    d_manager = DataManager(g_manager.BRANCH, ServerType.CLIENT, g_manager.PATH_FOR_WORKING)
    g_manager_client = GitManager(GitTarget.CLIENT)
    # 체크아웃 성공시에만 진행
    if not g_manager_client.checkout(g_manager.BRANCH):
        g_manager_client.destroy()
        return
    c_manager = CSharpManager(g_manager.BRANCH, g_manager.BASE_TAG, g_manager_client.PATH_FOR_WORKING)
    c_manager.save_entity(d_manager.get_schema_all())
    c_manager.save_enum(d_manager.get_enum_data())
    d_manager.save_json_all(g_manager_client.PATH_FOR_WORKING.joinpath("data_all.json"))

    # 수정된 파일이 있다면
    if g_manager_client.is_modified():
        # 변환된 Json파일을 Git서버로 자동 커밋
        g_manager_client.push()
    g_manager_client.destroy()


def excel_to_enum(g_manager: GitManager):
    g_manager.splog.info("전체 Excel로드후 Enum 스크립트 변환을 진행합니다.")

    d_manager = DataManager(g_manager.BRANCH, ServerType.CLIENT, g_manager.PATH_FOR_WORKING)
    g_manager_client = GitManager(GitTarget.CLIENT)
    # 체크아웃 성공시에만 진행
    if not g_manager_client.checkout(g_manager.BRANCH):
        g_manager_client.destroy()
        return
    c_manager = CSharpManager(g_manager.BRANCH, g_manager.BASE_TAG, g_manager_client.PATH_FOR_WORKING)
    c_manager.save_enum(d_manager.get_enum_data())

    # 수정된 파일이 있다면
    if g_manager_client.is_modified():
        # 변환된 Json파일을 Git서버로 자동 커밋
        g_manager_client.push()
    g_manager_client.destroy()


def excel_to_schema(g_manager: GitManager):
    """
    전체 Excel추출후 아래 데이터 타입만 Prisma 스키마변환
    server_type: 기획데이터:server Info데이터:info
    @param g_manager: GitManager
    """
    g_manager.splog.info("전체 Excel로드후 Prisma변환을 진행합니다.")

    # 프리즈마 초기화
    p_manager = PrismaManager(g_manager.BRANCH, g_manager.PATH_FOR_WORKING)
    d_manager = DataManager(g_manager.BRANCH, ServerType.ALL, g_manager.PATH_FOR_WORKING)
    table_info = d_manager.get_schema_all()
    p_manager.save(table_info)


def get_commit_from_webhook(webhook: dict) -> dict:
    g_manager = GitManager(GitTarget.EXCEL)
    res = g_manager.load_commit_from_webhook(webhook)
    g_manager.destroy()
    return res


async def excel_to_data_all(branch: str):
    """
    최신 Excel Git 브랜치를 복제한후 데이터 변환을 호출한다.
    @param branch: Git브랜치
    """
    # Git 초기화 및 다운로드
    g_manager = GitManager(GitTarget.EXCEL)

    # # 체크아웃 성공시에만 진행
    if not g_manager.checkout(branch):
        g_manager.destroy()
        return
    check_excel(g_manager)
    excel_to_json_all(g_manager)

    await excel_to_server(g_manager)

    if g_manager.is_modified():
        g_manager.push()
    g_manager.destroy()


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
    g_manager = GitManager(GitTarget.EXCEL, webhook)
    # # 체크아웃 성공시에만 진행
    if not g_manager.checkout():
        g_manager.destroy()
        return

    username = webhook["head_commit"]["committer"]["username"]
    compare_url = webhook["compare_url"]

    # 변경사항이 없다면 무시
    if not compare_url:
        g_manager.splog.send_designer(f"[EXCEL변환요청:{username}] 변경사항이 없어 종료합니다.")
        return

    # 봇 PUSH 인 경우는 다시 PUSH하지 않고 메시지만 보낸다.
    bot = g_manager.is_bot_user()
    if bot:
        g_manager.splog.send_designer(f"변경 히스토리 URL : {compare_url}")
        return

    g_manager.splog.send_designer(f"[EXCEL변환요청:{username}] 변경사항을 적용합니다.")

    _new_tag = g_manager.NEW_TAG
    branch = g_manager.BRANCH
    g_manager.destroy()

    # 새로운 태그 요청 이후 PUSH가 있을 것을 가정하여 최신 Git을 Clone
    g_manager = GitManager(GitTarget.EXCEL)

    # 체크아웃 성공시에만 진행
    if not g_manager.checkout(branch):
        g_manager.destroy()
        return

    if _new_tag != '':
        g_manager.NEW_TAG = _new_tag
        await excel_to_data_taged(g_manager)
    else:
        await excel_to_data_modified(g_manager)

    # 수정된 Json 파일이 있다면 Excel Git서버로 자동 커밋
    if g_manager.is_modified():
        g_manager.push()
    g_manager.destroy()


async def excel_to_data_modified(g_manager: GitManager):
    modified_list = g_manager.get_modified_excel()
    if len(modified_list) == 0:
        g_manager.destroy()
        return
    check_excel(g_manager)
    excel_to_json(ServerType.ALL, g_manager)
    await excel_to_server(g_manager)


async def excel_to_data_taged(g_manager: GitManager):
    g_manager.splog.info(f"새로운 태그[{g_manager.NEW_TAG}] 요청으로 EXCEL 전체 변환을 시작합니다.")
    check_excel(g_manager)
    excel_to_json_all(g_manager)
    excel_to_entity(g_manager)
    excel_to_schema(g_manager)
    g_manager.save_base_tag_to_branch(g_manager.NEW_TAG)
    data_to_client_data(g_manager)
    prisma = PrismaManager(g_manager.BRANCH, g_manager.PATH_FOR_WORKING)
    prisma.migrate(MigrateType.FORCE, g_manager.BRANCH)
    await data_to_db(g_manager)
    await tag_to_db(g_manager)


def data_to_client_data(g_manager: GitManager):
    g_manager_client = GitManager(GitTarget.CLIENT)
    if not g_manager_client.checkout(g_manager.BRANCH):
        g_manager_client.destroy()
        return

    d_manager = DataManager(g_manager.BRANCH, ServerType.CLIENT, g_manager.PATH_FOR_WORKING)
    d_manager.save_json_all(g_manager_client.PATH_FOR_WORKING.joinpath("data_all.json"))
    # 수정된 파일이 있다면
    if g_manager_client.is_modified():
        # 변환된 Json파일을 Git서버로 자동 커밋
        g_manager_client.push()
    g_manager_client.destroy()

    f_manager = FtpManager(g_manager.BRANCH, g_manager.COMMIT_ID, g_manager.PATH_FOR_WORKING)
    f_manager.send(d_manager.get_json())
    g_manager.save_client_resource_to_branch(f_manager.get_resource_url())
    if g_manager.NEW_TAG != '':
        g_manager_client = GitManager(GitTarget.CLIENT)
        if not g_manager_client.checkout(g_manager.BRANCH):
            g_manager_client.destroy()
            return
        g_manager_client.push_tag_to_client(g_manager_client.COMMIT_ID, g_manager.NEW_TAG)
        g_manager_client.destroy()


async def excel_to_server(g_manager: GitManager):
    teams = LogManager(g_manager.BRANCH, g_manager.PATH_FOR_WORKING)
    if g_manager.is_modified_excel_enum():
        excel_to_enum(g_manager)
        teams.add_warning('Enum 데이터에 변동 사항이 있습니다. 확인 후 개발 진행이 필요합니다.')
        teams.send_developer()

    if g_manager.is_modified_excel_column():
        teams.info(f'EXCEL파일에 변동이 있어 스키마 변환을 진행합니다.')
        excel_to_entity(g_manager)
        excel_to_schema(g_manager)
        teams.add_warning('기획 데이터에 변동 사항이 있습니다. 확인 후 개발 진행이 필요합니다.')
        teams.send_developer()
    else:
        teams.send_designer(f'EXCEL파일에 변동이 있어 서버업데이트를 진행합니다.')
        data_to_client_data(g_manager)
        await data_to_db(g_manager)
        await tag_to_db(g_manager)
    teams.destory()


def check_excel(g_manager: GitManager):
    d_manager = DataManager(g_manager.BRANCH, ServerType.ALL, g_manager.PATH_FOR_WORKING)
    d_manager.check_excel_for_relation(d_manager.get_excelpath_all())


async def migrate(branch: str):
    """
    Prisma 스키마 로드 후 해당 브랜치 디비에 반영
    @param branch: Git브랜치 -> Config에 DB접속정보가 브랜치별로 존재
    @return:
    """
    # Git 초기화 및 다운로드
    g_manager = GitManager(GitTarget.EXCEL)

    # 체크아웃 성공시에만 진행
    if not g_manager.checkout(branch):
        g_manager.destroy()
        return

    # commit = g_manager.get_last_commit()
    prisma = PrismaManager(branch, g_manager.PATH_FOR_WORKING)
    prisma.migrate(MigrateType.FORCE, branch)
    await data_to_db(g_manager)
    await tag_to_db(g_manager)
    g_manager.destroy()


async def data_to_db(g_manager: GitManager):
    d_manager = DataManager(g_manager.BRANCH, ServerType.ALL, g_manager.PATH_FOR_WORKING)
    b_manager = DBManager(g_manager.BRANCH, g_manager.PATH_FOR_WORKING)
    await b_manager.restore_all_table(d_manager.get_jsonmap(ServerType.SERVER))
    await b_manager.restore_all_table(d_manager.get_jsonmap(ServerType.INFO))
    await b_manager.destory()


async def tag_to_db(g_manager: GitManager):
    b_manager = DBManager(g_manager.BRANCH, g_manager.PATH_FOR_WORKING)
    res_info = g_manager.get_client_resource_from_branch()
    if len(res_info.keys()) > 0:
        await b_manager.update_version_info(res_info['res_ver'], res_info['res_url'])
    await b_manager.destory()


async def test(branch: str):
    """
    전체 Excel추출후 json, prisma schema파일 저장
    @param branch: Git브랜치
    """
    # Git 초기화 및 다운로드

    # commit = {
    #     "branch": "test",
    #     "id": "89daf96c304500023db505ef1f87b373ec3ee1cd",
    #     "message": "Test: 데이터 체크\n",
    #     "url": "http://local.sp.snowpipe.net:3000/SPTeam/data-for-designer/commit/9298c34c094f40cff82648864e9abc7203b8dadd",
    #     "author": {
    #         "name": "CGLee",
    #         "email": "cglee@snowpipe.co.kr",
    #         "username": "CGLee"
    #     },
    #     "committer": {
    #         "name": "CGLee",
    #         "email": "cglee@snowpipe.co.kr",
    #         "username": "CGLee"
    #     },
    #     "verification": None,
    #     "timestamp": "2022-05-30T12:12:14+09:00",
    #     "added": [],
    #     "removed": [],
    #     "modified": [
    #         "excel/data/sub2_table_info.xlsx"
    #     ]
    # }
    webhook = {
        "ref": "refs/tags/v0.4.1_local",
        "before": "0000000000000000000000000000000000000000",
        "after": "e6e8968956803412d8a19be5d888776a6c1f3fac",
        "compare_url": "http://local.sp.snowpipe.net:3000/SPTeam/data-for-designer/compare/0000000000000000000000000000000000000000...e6e8968956803412d8a19be5d888776a6c1f3fac",
        "commits": [],
        "head_commit": {
            "id": "e6e8968956803412d8a19be5d888776a6c1f3fac",
            "message": "[서버/이철길] 테스트 데이터 추가\n",
            "url": "http://local.sp.snowpipe.net:3000/SPTeam/data-for-designer/commit/e6e8968956803412d8a19be5d888776a6c1f3fac",
            "author": {
                "name": "CGLee",
                "email": "cglee@snowpipe.co.kr",
                "username": "CGLee"
            },
            "committer": {
                "name": "CGLee",
                "email": "cglee@snowpipe.co.kr",
                "username": "CGLee"
            },
            "timestamp": "2022-06-08T19:40:10+09:00",
            "added": [],
            "removed": [
                "excel/data/info/~$server_info.xlsx"
            ],
            "modified": []
        },
        "repository": {
            "id": 8,
            "owner": {
                "id": 2,
                "login": "SPTeam",
                "full_name": "",
                "email": "",
                "avatar_url": "http://local.sp.snowpipe.net:3000/avatars/0b4e480645d9e5c45dfdf455829cd61d",
                "language": "",
                "last_login": "0001-01-01T00:00:00Z",
                "created": "2022-04-25T15:47:09+09:00",
                "location": "",
                "website": "",
                "description": "",
                "visibility": "limited",
                "followers_count": 0,
                "following_count": 0,
                "starred_repos_count": 0,
                "username": "SPTeam"
            },
            "name": "data-for-designer",
            "full_name": "SPTeam/data-for-designer",
            "description": "",
            "starred_repos_count": 0,
            "username": "CGLee"
        }
    }

    await excel_to_data_from_webhook(webhook)


if __name__ == '__main__' or __name__ == "decimal":
    # branch = 'local'
    # logging.info(f"[{branch} 브랜치] 전체 Excel로드후 C# 스크립트 변환을 진행합니다.")
    # g_manager = GitManager(GitTarget.EXCEL)
    # if not g_manager.checkout(branch):
    #     g_manager.destroy()
    # else:
    #     d_manager = DataManager(branch, ServerType.CLIENT, g_manager.PATH_FOR_WORKING)
    #     g_manager = GitManager(GitTarget.CLIENT)
    #     # 체크아웃 성공시에만 진행
    #     c_manager = CSharpManager(branch, 'commit_test', g_manager.PATH_FOR_WORKING)
    #     d_manager.get_enum_data()
    # For test
    # asyncio.run(excel_to_data_all('test'))
    # asyncio.run(excel_to_data_modified('test'))
    # asyncio.run(migrate('test'))
    asyncio.run(test('test'))
    pass
