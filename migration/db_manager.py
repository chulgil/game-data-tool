import logging
import asyncio
import json
import yaml
from prisma import Prisma
from pathlib import Path


class DBManager:

    def __init__(self, branch: str):
        self.BRANCH = branch
        self.ROOT_DIR = Path(__file__).parent.parent
        self.PATH_FOR_CONFIG = self.ROOT_DIR.joinpath('config.yaml')
        # Config 파일 설정
        with open(self.PATH_FOR_CONFIG, 'r') as f:
            config = yaml.safe_load(f)
        self.DBLIST = config['DATABASE']


    async def init_info_tbs(self, json_map: dict):
        db = Prisma()
        await db.connect()
        # Json파일 가져오기
        for json_key, json_data in json_map.items():
            try:
                await self.create_info_tb(db, json_key, json_data)
            except Exception as e:
                logging.info(self.BRANCH + f'서버 테이블 데이터 {json_key} Error :\r\n {str(e)}')
        await db.disconnect()


    async def create_info_tb(self, db: Prisma, table_name: str, json_data: list):
        try:
            table = getattr(db, table_name)
            await table.delete_many()
            await table.create_many(
                json_data
            )
            logging.info(f'{self.BRANCH} 서버 테이블 데이터 INSERT 성공 : {table_name}')
        except Exception as e:
            logging.info(f'{self.BRANCH} 서버 테이블 데이터 INSERT 실패 : {table_name} \n {str(e)}')


    async def select_info_tb(self, db: Prisma, table_name: str):
        table = getattr(db, table_name)
        data = await table.find_many()
        logging.info(f'{self.BRANCH} 서버 테이블 데이터 SELECT 성공 : ' + table_name)
        return data

    def init_info_db(self):
        asyncio.run(self.init_info_tbs())
