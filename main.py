import asyncio
import logging

from app.prisma_manager import PrismaManager
from app.data_manager import DataManager, DataType
from app.git_manager import GitManager


async def sync_prisma(branch: str):
    # 프리즈마 초기화
    prisma = PrismaManager(branch)
    prisma.sync()


async def init_info_db(branch: str):
    # 프리즈마 초기화
    p_manager = PrismaManager(branch)

    # Git 초기화 및 다운로드
    git_manager = GitManager()

    # 체크아웃 성공시에만 진행
    if not git_manager.checkout(branch):
        return

    # 변환된 Json파일을 디비로 저장
    from app.libs.excel_to_db.app.db_manager import DBManager
    manager = DBManager(branch)
    data_manager = DataManager(DataType.INFO)
    json_map = data_manager.get_jsonmap()
    await manager.init_info_tbs(json_map)


async def init_server_db(branch: str):
    # 프리즈마 초기화
    p_manager = PrismaManager(branch)

    # Git 초기화 및 다운로드
    git_manager = GitManager()

    # 체크아웃 성공시에만 진행
    if not git_manager.checkout(branch):
        return

    # 변환된 Json파일을 디비로 저장
    from app.libs.excel_to_db.app.db_manager import DBManager
    manager = DBManager(branch)

    data_manager = DataManager(DataType.INFO)
    modified_path = git_manager.get_modified_json()
    json_map = data_manager.get_jsonmap(modified_path)
    await manager.init_info_tbs(json_map)


def all_excel_to_json(branch: str, data_type: str):
    """전체 Excel을 추출후 Json변환
        """
    # Git 초기화 및 다운로드
    git_manager = GitManager()

    # 체크아웃 성공시에만 진행
    if not git_manager.checkout(branch):
        return

    logging.info(f"전체 Excel로드후 Json변환을 진행합니다. [데이터 타입 : {data_type}]")

    # 전체 Excel로드후 Json변환
    data_manager = DataManager(DataType.value_of(data_type))
    data_manager.excel_to_json(data_manager.get_all_excelpath())
    data_manager.delete_json_as_excel()

    # 수정된 파일이 있다면
    if git_manager.is_modified():
        # 변환된 Json파일을 Git서버로 자동 커밋
        git_manager.push()


def excel_to_json(branch: str, data_type: str, head_cnt=1):
    """변경된 Excel만 추출후 Json변환
    """
    # Git 초기화 및 다운로드
    git_manager = GitManager()

    # 체크아웃 성공시에만 진행
    if not git_manager.checkout(branch):
        return

    logging.info(f"변경된 Excel로드후 Json변환을 진행합니다. [데이터 타입 : {data_type}]")

    data_manager = DataManager(DataType.value_of(data_type))
    data_manager.delete_json_as_excel()

    modified_list = git_manager.get_modified_excel(head_cnt)
    print(modified_list)
    if len(modified_list) == 0:
        return

    # Excel로드후 Json변환
    data_manager.excel_to_json(modified_list)

    # 수정된 파일이 있다면
    if git_manager.is_modified():
        # 변환된 Json파일을 Git서버로 자동 커밋
        git_manager.push()


async def create_table():
    branch = "local"
    # 프리즈마 초기화
    # p_manager = PrismaManager(branch)

    # Git 초기화 및 다운로드
    git_manager = GitManager()

    # 체크아웃 성공시에만 진행
    if not git_manager.checkout(branch):
        return
    modified_list = git_manager.get_modified_excel()
    data_manager = DataManager(DataType.SERVER)
    for _path in modified_list:
        data_manager.get_table_info(_path)


def get_branch_from_webhook(webhook: dict) -> str:
    git_manager = GitManager()
    return git_manager.get_branch_from_webhook(webhook)


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
    excel_to_json('local', 'init')
    # asyncio.run(create_table())
