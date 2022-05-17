import asyncio
import logging

from app import PrismaManager, GitManager, DBManager, MigrateType, DataType, DataManager


async def sync_prisma(branch: str):
    # 프리즈마 초기화
    prisma = PrismaManager(branch)
    prisma.sync()


async def update_table(branch: str, data_type: DataType):
    # 프리즈마 초기화
    p_manager = PrismaManager(branch)

    # Git 초기화 및 다운로드
    git_manager = GitManager()

    # 체크아웃 성공시에만 진행
    if not git_manager.checkout(branch):
        return

    # 변환된 Json파일을 디비로 저장
    manager = DBManager(branch)
    data_manager = DataManager(data_type)
    json_map = data_manager.get_jsonmap()
    await manager.insert_all_table(json_map)


def excel_to_json_all(branch: str):
    """전체 Excel을 추출후 Json변환
        """
    logging.info(f"전체 Excel로드후 Json변환을 진행합니다. [브랜치 : {branch}]")
    # 전체 Excel로드후 Json변환
    data_manager = DataManager(DataType.ALL)
    data_manager.excel_to_json(data_manager.get_all_excelpath())
    data_manager.delete_json_as_excel()


def excel_to_json(modified_list: list, data_type: str):
    """
    변경된 Excel만 추출후 Json변환
    @param modified_list: 수정된 파일경로
    @param data_type: 기획데이터:server Info데이터:info 클라이언트데이터:client
    @return:
    """
    logging.info(f"변경된 Excel로드후 Json변환을 진행합니다. [데이터 타입 : {data_type}]")

    data_manager = DataManager(DataType.value_of(data_type))
    data_manager.delete_json_as_excel()

    # Excel로드후 Json변환
    data_manager.excel_to_json(modified_list)


def excel_to_schema_all(branch: str):
    """
    전체 Excel추출후 아래 데이터 타입만 Prisma 스키마변환
    data_type: 기획데이터:server Info데이터:info
    @param branch: Git브랜치
    """
    logging.info(f"전체 Excel로드후 Prisma변환을 진행합니다. [브랜치 : {branch}]")
    # 프리즈마 초기화
    p_manager = PrismaManager(branch)
    data_manager = DataManager(DataType.ALL)
    table_info = {}
    for _path in data_manager.get_all_excelpath():
        table_info.update(data_manager.get_table_info(_path))
    p_manager.save_schema(table_info)


def get_branch_from_webhook(webhook: dict) -> str:
    git_manager = GitManager()
    return git_manager.get_branch_from_webhook(webhook)


def excel_to_data(branch: str, data_type: str, git_head_back=1):
    """
    변경된 Excel추출후 json, prisma schema파일 저장
    @param branch: Git브랜치
    @param data_type: 기획데이터:server Info데이터:info 클라데이터:client
    @param git_head_back: Git Head~[git_head_back] 이력 가져오는 레벨
    @return:
    """
    # Git 초기화 및 다운로드
    git_manager = GitManager()

    # # 체크아웃 성공시에만 진행
    if not git_manager.checkout(branch):
        return

    modified_list = git_manager.get_modified_excel(git_head_back)
    if len(modified_list) == 0:
        return
    excel_to_json(modified_list, data_type)
    excel_to_schema_all(branch)


def excel_to_data_all(branch: str):
    """
    전체 Excel추출후 json, prisma schema파일 저장
    @param branch: Git브랜치
    """
    # Git 초기화 및 다운로드
    git_manager = GitManager()

    # # 체크아웃 성공시에만 진행
    if not git_manager.checkout(branch):
        return

    excel_to_json_all(branch)

    # 프리즈마 스키마 초기화 및 저장
    excel_to_schema_all(branch)

    # 수정된 파일이 있다면
    if git_manager.is_modified():
        # 변환된 Json파일을 Git서버로 자동 커밋
        git_manager.push()


async def migrate(branch: str):
    """
    Prisma 스키마 로드 후 해당 브랜치 디비에 반영
    @param branch: Git브랜치 -> Config에 DB접속정보가 브랜치별로 존재
    @return:
    """
    # Git 초기화 및 다운로드
    git_manager = GitManager()
    #
    # # # 체크아웃 성공시에만 진행
    if not git_manager.checkout(branch):
        return

    commit = git_manager.get_last_commit()
    prisma = PrismaManager(branch)
    prisma.migrate(MigrateType.FORCE, commit)

    data_manager = DataManager(DataType.ALL)
    json_map = data_manager.get_jsonmap()
    db_manager = DBManager(branch)
    await db_manager.insert_all_table(json_map)


if __name__ == '__main__':
    # main : 기획자 브랜치
    # dev : 개발 브랜치
    # qa & qa2 & qa3 : QA 브랜치
    # local : 로컬 브랜치
    logger = logging.getLogger()
    logging.basicConfig(
        format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p',
        filename='out.log', filemode="w", encoding='utf-8', level=logging.INFO)

    # For test
    # excel_to_schema_all('local')
    excel_to_data_all('local')
    # asyncio.run(db_migration('local'))
    # asyncio.run(migrate('local'))
