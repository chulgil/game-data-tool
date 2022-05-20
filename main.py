import asyncio
import logging

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


async def update_table(branch: str, data_type: DataType):
    # 프리즈마 초기화
    p_manager = PrismaManager(branch)

    # Git 초기화 및 다운로드
    g_manager = GitManager()

    # 체크아웃 성공시에만 진행
    if not g_manager.checkout(branch):
        return

    # 변환된 Json파일을 디비로 저장
    manager = DBManager(branch)
    d_manager = DataManager(branch, data_type)
    json_map = d_manager.get_jsonmap()
    await manager.insert_all_table(json_map)


def excel_to_json_all(branch: str):
    """전체 Excel을 추출후 Json변환
        """
    logging.info(f"[{branch} 브랜치] 전체 Excel로드후 Json변환을 진행합니다.")

    # 전체 Excel로드후 Json변환
    d_manager = DataManager(branch, DataType.ALL)
    d_manager.delete_json_all()
    d_manager.excel_to_json(d_manager.get_excelpath_all())


def excel_to_json(branch: str, modified_list: list, data_type: str):
    """
    변경된 Excel만 추출후 Json변환
    @param branch: 브랜치
    @param modified_list: 수정된 파일경로
    @param data_type: 기획데이터:server Info데이터:info 클라이언트데이터:client
    @return:
    """
    logging.info(f"[{branch} 브랜치] 변경된 Excel로드후 Json변환을 진행합니다. [데이터 타입 : {data_type}]")

    d_manager = DataManager(branch, DataType.value_of(data_type))

    # Excel로드후 Json변환
    d_manager.excel_to_json(modified_list)


def excel_to_schema_all(branch: str):
    """
    전체 Excel추출후 아래 데이터 타입만 Prisma 스키마변환
    data_type: 기획데이터:server Info데이터:info
    @param branch: Git브랜치
    """
    logging.info(f"[{branch} 브랜치]  전체 Excel로드후 Prisma변환을 진행합니다.")
    # 프리즈마 초기화
    p_manager = PrismaManager(branch)
    d_manager = DataManager(branch, DataType.ALL)
    table_info = {}
    for _path in d_manager.get_excelpath_all():
        table_info.update(d_manager.get_table_info(_path))
    p_manager.save_schema(table_info)


def get_branch_from_webhook(webhook: dict) -> str:
    g_manager = GitManager()
    return g_manager.get_branch_from_webhook(webhook)


def excel_to_data(branch: str, data_type: str, git_head_back=1):
    """
    변경된 Excel추출후 json, prisma schema파일 저장
    @param branch: Git브랜치
    @param data_type: 기획데이터:server Info데이터:info 클라데이터:client
    @param git_head_back: Git Head~[git_head_back] 이력 가져오는 레벨
    @return:
    """
    # Git 초기화 및 다운로드
    g_manager = GitManager()

    # # 체크아웃 성공시에만 진행
    if not g_manager.checkout(branch):
        return

    modified_list = g_manager.get_modified_excel(git_head_back)
    if len(modified_list) == 0:
        return
    excel_to_json(modified_list, data_type)
    excel_to_schema_all(branch)

    d_manager = DataManager(branch, DataType.ALL)
    d_manager.check_excel(modified_list)

    # 수정된 파일이 있다면
    if g_manager.is_modified():
        # 변환된 Json파일을 Git서버로 자동 커밋
        g_manager.push()


def excel_to_data_all(branch: str):
    """
    전체 Excel추출후 json, prisma schema파일 저장
    @param branch: Git브랜치
    """
    # Git 초기화 및 다운로드
    g_manager = GitManager()

    # # 체크아웃 성공시에만 진행
    if not g_manager.checkout(branch):
        return

    excel_to_json_all(branch)

    # 프리즈마 스키마 초기화 및 저장
    excel_to_schema_all(branch)

    d_manager = DataManager(branch, DataType.ALL)
    d_manager.check_excel(d_manager.get_excelpath_all())

    # 수정된 파일이 있다면
    if g_manager.is_modified():
        # 변환된 Json파일을 Git서버로 자동 커밋
        g_manager.push()


def check_excel(branch: str):
    # Git 초기화 및 다운로드
    g_manager = GitManager()

    # # 체크아웃 성공시에만 진행
    if not g_manager.checkout(branch):
        return

    d_manager = DataManager(branch, DataType.ALL)
    d_manager.check_excel(d_manager.get_excelpath_all())


async def migrate(branch: str):
    """
    Prisma 스키마 로드 후 해당 브랜치 디비에 반영
    @param branch: Git브랜치 -> Config에 DB접속정보가 브랜치별로 존재
    @return:
    """
    # Git 초기화 및 다운로드
    # g_manager = GitManager()
    #
    # # # 체크아웃 성공시에만 진행
    # if not g_manager.checkout(branch):
    #     return

    # commit = g_manager.get_last_commit()
    prisma = PrismaManager(branch)
    prisma.migrate(MigrateType.FORCE, 'test')

    server_data = DataManager(branch, DataType.SERVER)
    info_data = DataManager(branch, DataType.INFO)
    b_manager = DBManager(branch)
    await b_manager.insert_all_table(server_data.get_jsonmap())
    await b_manager.insert_all_table(info_data.get_jsonmap())


if __name__ == '__main__' or __name__ == "decimal":
    # For test
    # excel_to_json_all('test')
    # excel_to_data_all('test')
    # excel_to_data('local', 'all')
    # excel_to_data_all('test')
    # check_excel('test')
    # asyncio.run(migrate('test'))
    pass
