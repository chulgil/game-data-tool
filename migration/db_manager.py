import json
import logging
import asyncio
import json
from prisma import Prisma
from pathlib import Path

class DBManager:


    def __init__(self, branch: str):
        # Config 파일 설정
        with open('config.json', 'r') as f:
            config = json.load(f)
        self.BRANCH = branch
        self.DBLIST = config['DATABASE']
        root_dir = config['DEFAULT']['ROOT_DATA_DIR'] + '/json'
        self.PATH_FOR_DATA = root_dir + '/data/'
        self.PATH_FOR_INFO = root_dir + '/info/'
        self.PATH_FOR_PRISMA = './prisma'
        self.PATH_FOR_ENV = self.PATH_FOR_PRISMA + '/.env'
        self.CONFIG_DB = config['DATABASE']
        self._init_prisma()

    def _init_prisma(self):
        self._init_prisma_config()

    # .env 파일에  디비 경로를 설정
    # ex) DATABASE_URL="sqlserver://db.com:1433;database=data_db;user=sa;password=pass;encrypt=DANGER_PLAINTEXT"
    def _init_prisma_config(self):
        db_path = self._get_db_by_branch()
        db_path = 'DATABASE_URL="'+db_path+'"'
        with open(self.PATH_FOR_ENV, 'w', encoding='utf-8') as f:
            f.write(db_path)

    # 브랜치 명으로 Config설정에 있는 디비 경로를 가져온다.
    def _get_db_by_branch(self) -> str:
        db_name = {
            "main": "DEV2",
        }.get(self.BRANCH, str(self.BRANCH).upper())
        return self.CONFIG_DB[db_name]


    async def init_info_tbs(self) -> None:
        db = Prisma()
        await db.connect()
        # Json파일 가져오기
        files = list(Path(self.PATH_FOR_INFO).rglob("*.json"))
        print(self.PATH_FOR_INFO)
        print(files)
        for file_path in files:
            try:
                with open(file_path, 'r') as f:
                    json_data = json.load(f)
                await self.create_info_tb(db, file_path.stem, json_data)
            except Exception as e:
                logging.info(self.BRANCH + '서버 테이블 데이터 Error : \r\n' + str(e))
        await db.disconnect()

    async def create_info_tb(self, db: Prisma, table_name: str, json_data: list) -> None:
        table = getattr(db, table_name)
        await table.delete_many()
        await table.create_many(
            json_data
        )
        logging.info(self.BRANCH + '서버 테이블 데이터 INSERT 완료 : ' + table_name)

    def init_info_db(self):
        asyncio.run(self.init_info_tbs())




