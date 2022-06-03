import asyncio
import logging
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

else:
    from app.libs.excel_to_db.app import *


async def sync_prisma(branch: str):
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

    # 프리즈마 초기화
    p_manager = PrismaManager(branch, g_manager.PATH_FOR_WORKING)

    # 체크아웃 성공시에만 진행
    if not g_manager.checkout(branch):
        g_manager.destroy()
        return

    # 변환된 Json파일을 디비로 저장
    manager = DBManager(branch)
    d_manager = DataManager(branch, server_type)
    json_map = d_manager.get_jsonmap()
    await manager.insert_all_table(json_map)


def excel_to_json_all(branch: str, working_dir: Path):
    """전체 Excel을 추출후 Json변환
        """

    logging.info(f"[{branch} 브랜치] 전체 Excel로드후 Json변환을 진행합니다.")

    # 전체 Excel로드후 Json변환
    d_manager = DataManager(branch, ServerType.ALL, working_dir)
    d_manager.delete_json_all()
    d_manager.excel_to_json(d_manager.get_excelpath_all())


def excel_to_json(branch: str, modified_list: list, server_type: ServerType, working_dir: Path):
    """
    변경된 Excel만 추출후 Json변환
    @param branch: 브랜치
    @param modified_list: 수정된 파일경로
    @param server_type: 기획데이터:server Info데이터:info 클라이언트데이터:client
    @param working_dir:
    @return:
    """
    logging.info(f"[{branch} 브랜치] 변경된 Excel로드후 Json변환을 진행합니다. [데이터 타입 : {server_type.name}]")

    d_manager = DataManager(branch, server_type, working_dir)

    # Excel로드후 Json변환
    d_manager.excel_to_json(modified_list)


def excel_to_entity(branch: str, excel_work_path: Path, commit_id: str):
    logging.info(f"[{branch} 브랜치] 전체 Excel로드후 C# 스크립트 변환을 진행합니다.")

    d_manager = DataManager(branch, ServerType.CLIENT, excel_work_path)
    g_manager_client = GitManager(GitTarget.CLIENT)
    # 체크아웃 성공시에만 진행
    if not g_manager_client.checkout(branch):
        g_manager_client.destroy()
        return
    c_manager = CSharpManager(branch, commit_id, g_manager_client.PATH_FOR_WORKING)
    c_manager.save_entity(d_manager.get_schema_all())
    c_manager.save_enum(d_manager.get_enum_data())
    d_manager.save_json_all(g_manager_client.PATH_FOR_WORKING.joinpath("data_all.json"))

    # 수정된 파일이 있다면
    if g_manager_client.is_modified():
        # 변환된 Json파일을 Git서버로 자동 커밋
        g_manager_client.push()
    g_manager_client.destroy()


def excel_to_enum(branch: str, excel_work_path: Path, commit_id: str):
    logging.info(f"[{branch} 브랜치] 전체 Excel로드후 Enum 스크립트 변환을 진행합니다.")

    d_manager = DataManager(branch, ServerType.CLIENT, excel_work_path)
    g_manager_client = GitManager(GitTarget.CLIENT)
    # 체크아웃 성공시에만 진행
    if not g_manager_client.checkout(branch):
        g_manager_client.destroy()
        return
    c_manager = CSharpManager(branch, commit_id, g_manager_client.PATH_FOR_WORKING)
    c_manager.save_enum(d_manager.get_enum_data())

    # 수정된 파일이 있다면
    if g_manager_client.is_modified():
        # 변환된 Json파일을 Git서버로 자동 커밋
        g_manager_client.push()
    g_manager_client.destroy()


def excel_to_schema(branch: str, working_dir: Path):
    """
    전체 Excel추출후 아래 데이터 타입만 Prisma 스키마변환
    server_type: 기획데이터:server Info데이터:info
    @param branch: Git브랜치
    @param working_dir: 작업폴더 경로
    """
    logging.info(f"[{branch} 브랜치] 전체 Excel로드후 Prisma변환을 진행합니다.")

    # 프리즈마 초기화
    p_manager = PrismaManager(branch, working_dir)
    d_manager = DataManager(branch, ServerType.ALL, working_dir)
    table_info = d_manager.get_schema_all()
    p_manager.save(table_info)


def get_commit_from_webhook(webhook: dict) -> dict:
    g_manager = GitManager(GitTarget.EXCEL)
    return g_manager.get_commit_from_webhook(webhook)


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
    excel_to_json_all(branch, g_manager.PATH_FOR_WORKING)
    #
    if g_manager.is_modified():
        g_manager.push()

    await excel_to_server(branch, g_manager)


async def excel_to_data_modified(commit: dict = None):
    """
    Git Push 발생후 Webhook에서 이 메서드가 호출됨
    git commit id를 기준으로 리포지토리를 복제한후 데이터 변환을 호출한다.
    @param commit: 호출 파라미터 상세
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
    branch = commit["branch"]
    g_manager = GitManager(GitTarget.EXCEL, commit)

    # # 체크아웃 성공시에만 진행
    if not g_manager.checkout(commit["id"]):
        g_manager.destroy()
        return

    modified_list = g_manager.get_modified_excel()
    if len(modified_list) == 0:
        g_manager.destroy()
        return

    excel_to_json(branch, modified_list, ServerType.ALL, g_manager.PATH_FOR_WORKING)

    # 수정된 Json 파일이 있다면 Excel Git서버로 자동 커밋
    if g_manager.is_modified():
        g_manager.push()

    await excel_to_server(branch, g_manager)


def data_to_client(branch, g_manager):
    g_manager_client = GitManager(GitTarget.CLIENT)
    # 체크아웃 성공시에만 진행
    if not g_manager_client.checkout(branch):
        g_manager_client.destroy()
        return
    d_manager = DataManager(branch, ServerType.CLIENT, g_manager.PATH_FOR_WORKING)
    d_manager.save_json_all(g_manager_client.PATH_FOR_WORKING.joinpath("data_all.json"))
    # 수정된 파일이 있다면
    if g_manager_client.is_modified():
        # 변환된 Json파일을 Git서버로 자동 커밋
        g_manager_client.push()
    g_manager_client.destroy()

    f_manager = FtpManager(branch, g_manager.get_last_tag())
    f_manager.send(d_manager.get_json())


async def excel_to_server(branch: str, g_manager: GitManager):
    teams = LogManager(branch, g_manager.PATH_FOR_WORKING)
    if g_manager.is_modified_excel_column():
        teams.send_designer(f'EXCEL파일에 변동이 있어 스키마 변환을 진행합니다.')
        excel_to_schema(branch, g_manager.PATH_FOR_WORKING)
        excel_to_entity(branch, g_manager.PATH_FOR_WORKING, g_manager.get_last_commit())
    else:
        teams.send_designer(f'EXCEL파일에 변동이 있어 서버업데이트를 진행합니다.')
        excel_to_enum(branch, g_manager.PATH_FOR_WORKING, g_manager.get_last_commit())
        data_to_client(branch, g_manager)
        await data_to_db(branch, g_manager)

    g_manager.destroy()


def check_excel(branch: str):
    # Git 초기화 및 다운로드
    g_manager = GitManager(GitTarget.EXCEL)

    # # 체크아웃 성공시에만 진행
    if not g_manager.checkout(branch):
        g_manager.destroy()
        return

    d_manager = DataManager(branch, ServerType.ALL, g_manager.PATH_FOR_WORKING)
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
    await data_to_db(branch, g_manager.PATH_FOR_WORKING)
    g_manager.destroy()


async def data_to_db(branch: str, save_path: Path):
    d_manager = DataManager(branch, ServerType.ALL, save_path)
    b_manager = DBManager(branch, save_path)
    await b_manager.insert_all_table(d_manager.get_jsonmap(ServerType.SERVER))
    await b_manager.insert_all_table(d_manager.get_jsonmap(ServerType.INFO))


async def test(branch: str):
    """
    전체 Excel추출후 json, prisma schema파일 저장
    @param branch: Git브랜치
    """
    # Git 초기화 및 다운로드

    commit = {
        "branch": "test",
        "id": "89daf96c304500023db505ef1f87b373ec3ee1cd",
        "message": "Test: 데이터 체크\n",
        "url": "http://local.sp.snowpipe.net:3000/SPTeam/data-for-designer/commit/9298c34c094f40cff82648864e9abc7203b8dadd",
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
        "verification": None,
        "timestamp": "2022-05-30T12:12:14+09:00",
        "added": [],
        "removed": [],
        "modified": [
            "excel/data/sub2_table_info.xlsx"
        ]
    }
    await excel_to_data_modified(commit)
    # g_manager.destroy()


#

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
    asyncio.run(excel_to_data_all('test'))
    # asyncio.run(excel_to_data_modified('test'))
    # check_excel('test')
    # asyncio.run(migrate('test'))
    # asyncio.run(test('test'))
    pass
