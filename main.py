import logging

from app.libs.excel_to_db.migration.prisma_manager import PrismaManager
from app.libs.excel_to_db.migration.data_manager import DataManager, DataType
from app.libs.excel_to_db.migration.git_manager import GitManager



async def init_info(branch: str):

    # 프리즈마 초기화
    PrismaManager(branch)

    # Git 초기화 및 다운로드
    git_manager = GitManager(branch)
    git_manager.pull()

    # 변환된 Json파일을 디비로 저장
    from app.libs.excel_to_db.migration.db_manager import DBManager
    manager = DBManager(branch)
    await manager.init_info_tbs()


async def excel_to_infodb(branch: str):

    # 프리즈마 초기화
    PrismaManager(branch)

    # Git 초기화 및 다운로드
    git_manager = GitManager(branch)
    git_manager.pull()

    # Excel파일이 수정되었다면
    if git_manager.is_modified():
        # Excel로드후 Json변환
        manager = DataManager(DataType.INFO)
        manager.excel_to_json()

        # 변환된 Json파일을 Git서버로 자동 커밋
        git_manager.push()

        # 변환된 Json파일을 디비로 저장
        from app.libs.excel_to_db.migration.db_manager import DBManager
        manager = DBManager(branch)
        await manager.init_info_tbs()