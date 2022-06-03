import logging
import asyncio
import os
import yaml
from pathlib import Path
from subprocess import run


class DBManager:

    def __init__(self, branch: str, save_dir):
        from prisma import Client
        from . import LogManager
        self.splog = LogManager(branch, save_dir)

        self.db = Client()
        self.BRANCH = branch
        self._info = f'[{branch} 브랜치]'
        self.PATH_FOR_ROOT = Path(__file__).parent.parent
        self.PATH_FOR_CONFIG = self.PATH_FOR_ROOT.joinpath('config.yaml')

        # Config 파일 설정
        with open(self.PATH_FOR_CONFIG, 'r') as f:
            config = yaml.safe_load(f)
        self.DBLIST = config['DATABASE']


    async def insert_all_table(self, json_map: dict):
        await self.db.connect()
        # Json파일 가져오기
        for json_key, json_data in json_map.items():
            try:
                await self.insert_table(self.db, json_key, json_data)
            except Exception as e:
                self.splog.add_error(self._info + f'서버 테이블 데이터 {json_key} Error :\r\n {str(e)}')

        await self.db.disconnect()
        self.splog.info()
        self.splog.error()

    async def insert_table(self, db, table_name: str, json_data: list):
        try:
            table = getattr(db, table_name)
            await table.delete_many()
            await table.create_many(
                json_data
            )
            self.splog.add_info(f'{self._info} 테이블 데이터 INSERT 성공 : {table_name}')
        except Exception as e:
            self.splog.add_error(f'{self._info} 테이블 데이터 INSERT 실패 : {table_name} \n {str(e)}')

    async def select_info_tb(self, db, table_name: str):
        table = getattr(db, table_name)
        data = await table.find_many()
        return data
