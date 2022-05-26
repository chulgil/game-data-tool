import asyncio
import logging
from pathlib import Path

if __name__ == '__main__' or __name__ == "decimal":
    from app import *

    logger = logging.getLogger()
    logging.basicConfig(
        format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p',
        filename='out.log', filemode="w", encoding='utf-8', level=logging.INFO)
else:
    from app.libs.excel_to_db.app import *


async def sync_prisma(branch: str):
    # 프리즈마 초기화
    prisma = PrismaManager(branch)
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


def excel_to_json(branch: str, modified_list: list, server_type: str, working_dir: Path):
    """
    변경된 Excel만 추출후 Json변환
    @param branch: 브랜치
    @param modified_list: 수정된 파일경로
    @param server_type: 기획데이터:server Info데이터:info 클라이언트데이터:client
    @param working_dir:
    @return:
    """
    logging.info(f"[{branch} 브랜치] 변경된 Excel로드후 Json변환을 진행합니다. [데이터 타입 : {server_type}]")

    d_manager = DataManager(branch, ServerType.value_of(server_type), working_dir)

    # Excel로드후 Json변환
    d_manager.excel_to_json(modified_list)


def excel_to_csharp(branch: str, excel_work_path: Path, commit_id: str):
    logging.info(f"[{branch} 브랜치] 전체 Excel로드후 C# 스크립트 변환을 진행합니다.")

    d_manager = DataManager(branch, ServerType.CLIENT, excel_work_path)
    g_manager = GitManager(GitTarget.CLIENT)
    # 체크아웃 성공시에만 진행
    if not g_manager.checkout(branch):
        g_manager.destroy()
        return
    c_manager = CSharpManager(branch, commit_id, g_manager.PATH_FOR_WORKING)
    c_manager.save_entity(d_manager.get_schema_all())
    c_manager.save_enum(d_manager.get_enum_data())
    d_manager.save_json_all(g_manager.PATH_FOR_WORKING.joinpath("data_all.json"))

    # 수정된 파일이 있다면
    if g_manager.is_modified():
        # 변환된 Json파일을 Git서버로 자동 커밋
        g_manager.push()
    g_manager.destroy()


def excel_to_schema_all(branch: str, working_dir: Path):
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


def get_branch_from_webhook(webhook: dict) -> str:
    g_manager = GitManager(GitTarget.EXCEL)
    return g_manager.get_branch_from_webhook(webhook)


def excel_to_data(branch: str, server_type: str, git_head_back=1):
    """
    변경된 Excel추출후 json, prisma schema파일 저장
    @param branch: Git브랜치
    @param server_type: 기획데이터:server Info데이터:info 클라데이터:client
    @param git_head_back: Git Head~[git_head_back] 이력 가져오는 레벨
    @return:
    """
    # Git 초기화 및 다운로드
    g_manager = GitManager(GitTarget.EXCEL)

    # 체크아웃 성공시에만 진행
    if not g_manager.checkout(branch):
        g_manager.destroy()
        return

    modified_list = g_manager.get_modified_excel(git_head_back)
    if len(modified_list) == 0:
        g_manager.destroy()
        return
    excel_to_json(branch, modified_list, server_type, g_manager.PATH_FOR_WORKING)
    excel_to_schema_all(branch, g_manager.PATH_FOR_WORKING)

    # 수정된 파일이 있다면
    if g_manager.is_modified():
        excel_to_csharp(branch, g_manager.PATH_FOR_WORKING, g_manager.get_last_commit())
        f_manager = FtpManager(branch, g_manager.get_last_tag())
        d_manager = DataManager(branch, ServerType.CLIENT, g_manager.PATH_FOR_WORKING)
        f_manager.send(d_manager.get_json())
        # 변환된 Json파일을 Git서버로 자동 커밋
        g_manager.push()
    g_manager.destroy()


def excel_to_data_all(branch: str):
    """
    전체 Excel추출후 json, prisma schema파일 저장
    @param branch: Git브랜치
    """
    # Git 초기화 및 다운로드
    g_manager = GitManager(GitTarget.EXCEL)

    # # 체크아웃 성공시에만 진행
    if not g_manager.checkout(branch):
        g_manager.destroy()
        return

    excel_to_json_all(branch, g_manager.PATH_FOR_WORKING)
    excel_to_schema_all(branch, g_manager.PATH_FOR_WORKING)

    # 수정된 파일이 있다면
    if g_manager.is_modified():
        excel_to_csharp(branch, g_manager.PATH_FOR_WORKING, g_manager.get_last_commit())
        f_manager = FtpManager(branch, g_manager.get_last_tag())
        d_manager = DataManager(branch, ServerType.CLIENT, g_manager.PATH_FOR_WORKING)
        f_manager.send(d_manager.get_json())

        # 변환된 Json파일을 Git서버로 자동 커밋
        g_manager.push()

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

    server_data = DataManager(branch, ServerType.SERVER, g_manager.PATH_FOR_WORKING)
    info_data = DataManager(branch, ServerType.INFO, g_manager.PATH_FOR_WORKING)
    b_manager = DBManager(branch)
    await b_manager.insert_all_table(server_data.get_jsonmap())
    await b_manager.insert_all_table(info_data.get_jsonmap())


def test(branch: str):
    """
    전체 Excel추출후 json, prisma schema파일 저장
    @param branch: Git브랜치
    """
    # Git 초기화 및 다운로드
    g_manager = GitManager(GitTarget.EXCEL)

    # # 체크아웃 성공시에만 진행
    if not g_manager.checkout(branch):
        g_manager.destroy()
        return

    excel_to_csharp(branch, g_manager.PATH_FOR_WORKING, g_manager.get_last_commit())

    g_manager.destroy()


if __name__ == '__main__' or __name__ == "decimal":
    # For test
    excel_to_data_all('local')
    # excel_to_data('local', 'all')
    # excel_to_data_all('test')
    # check_excel('test')
    # asyncio.run(migrate('test'))
    # test('test')
    pass
