import logging

from app.libs.excel_to_db.migration.data_manager import DataManager, DataType
from app.libs.excel_to_db.migration.db_manager import DBManager
from app.libs.excel_to_db.migration.git_manager import GitManager
from app.libs.excel_to_db.migration.prisma_manager import PrismaManager

if __name__ == '__main__':

    # main : 기획자 브랜치
    # dev : 개발 브랜치
    # qa & qa2 & qa3 : QA 브랜치
    # local : 로컬 브랜치
    logger = logging.getLogger()
    logging.basicConfig(
        format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p',
        filename='out.log', filemode="w", encoding='utf-8', level=logging.INFO)


async def init_info(branch: str):

    PrismaManager('local')

    # Git 초기화
    git_manager = GitManager('local')
    git_manager.pull()

    # 데이터
    manager = DataManager(DataType.INFO)
    manager.excel_to_json()
    # Git Push
    # if git_manager.is_modified():
    #     git_manager.push()

    #
    # manager = DBManager('local')
    # await manager.init_info_tbs()
    return None
