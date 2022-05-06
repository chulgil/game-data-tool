import logging

from app.libs.excel_to_db.migration.prisma_manager import PrismaManager
from app.libs.excel_to_db.migration.data_manager import DataManager, DataType
from app.libs.excel_to_db.migration.git_manager import GitManager


async def sync_prisma(branch: str):
    # 프리즈마 초기화
    prisma = PrismaManager(branch)
    prisma.sync()


async def init_info(branch: str):
    # 프리즈마 초기화
    PrismaManager(branch)

    # Git 초기화 및 다운로드
    git_manager = GitManager()

    # 체크아웃 성공시에만 진행
    if not git_manager.checkout(branch):
        return

    if git_manager.pull():  # PULL 성공시에만 진행
        # 변환된 Json파일을 디비로 저장
        from app.libs.excel_to_db.migration.db_manager import DBManager
        manager = DBManager(branch)
        await manager.init_info_tbs()


def excel_to_json(branch: str, data_type: str):

    # Git 초기화 및 다운로드
    git_manager = GitManager()

    # 체크아웃 성공시에만 진행
    if not git_manager.checkout(branch):
        return

    # PULL 성공시에만 진행
    if not git_manager.pull():
        return

    logging.info(f"Excel로드후 Json변환을 진행합니다. [데이터 타입 : {data_type}]")
    # Excel로드후 Json변환
    target = DataType.value_of(data_type)
    manager = DataManager(target)
    manager.excel_to_json()

    # 수정된 파일이 있다면
    if git_manager.is_modified():
        # 변환된 Json파일을 Git서버로 자동 커밋
        git_manager.push()


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
    # excel_to_json('dev', 'info')
