import logging
import asyncio
import json
from prisma import Prisma
from pathlib import Path


class DBManager:

    def __init__(self, branch: str):
        self.BRANCH = branch
        self.ROOT_DIR = Path(__file__).parent.parent
        self.PATH_FOR_CONFIG = self.ROOT_DIR.joinpath('config.json')
        # Config 파일 설정
        with open(self.PATH_FOR_CONFIG, 'r') as f:
            config = json.load(f)
        self.DBLIST = config['DATABASE']
        json_path = self.ROOT_DIR.joinpath(config['DEFAULT']['ROOT_DATA_DIR'] + '/json')
        self.PATH_FOR_DATA = json_path.joinpath('data')
        self.PATH_FOR_INFO = json_path.joinpath('info')

    async def init_info_tbs(self) -> None:
        db = Prisma()
        await db.connect()
        # Json파일 가져오기
        files = list(Path(self.PATH_FOR_INFO).rglob("*.json"))
        for file_path in files:
            try:
                with open(file_path, 'r') as f:
                    json_data = json.load(f)
                await self.create_info_tb(db, file_path.stem, json_data)
            except Exception as e:
                logging.info(self.BRANCH + f'서버 테이블 데이터 {file_path.stem} Error :\r\n {str(e)}')
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
