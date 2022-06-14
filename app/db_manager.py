from datetime import datetime
import yaml
from pathlib import Path


class DBManager:

    def __init__(self, branch: str, working_dir):
        from . import LogManager
        self.splog = LogManager(branch, working_dir)
        self.BRANCH = branch
        self._info = f'[{branch} 브랜치]'
        self.splog.PREFIX = self._info
        self.PATH_FOR_WORKING = working_dir
        self.PATH_FOR_ROOT = Path(__file__).parent.parent
        self.PATH_FOR_CONFIG = self.PATH_FOR_ROOT.joinpath('config.yaml')
        try:
            from prisma import Prisma
            self.db = Prisma()
            # Config 파일 설정
            with open(self.PATH_FOR_CONFIG, 'r') as f:
                config = yaml.safe_load(f)
            self.DBLIST = config['DATABASE']
        except Exception as e:
            self.splog.error(f'PRISMA DB 초기화 ERROR : \n{e}')

    async def restore_all_table(self, json_map: dict):
        await self.db.connect()
        # Json파일 가져오기
        for json_key, json_data in json_map.items():
            try:
                await self.restore_table(json_key, json_data)
            except Exception as e:
                self.splog.add_error(f'서버 테이블 데이터 {json_key} Error :\n {str(e)}')
        await self.destory()

    async def update_version_info(self, commit_id: str, res_url: str):
        await self.db.connect()
        # Json파일 가져오기
        try:
            _market_type = 3000
            from prisma.models import version_check_info
            version_check_info = await self.db.version_check_info.find_first(where={'market_type': _market_type})

            if version_check_info:  # Update
                res = await self.db.version_check_info.update(
                    where={'version_check_info_key': version_check_info.version_check_info_key},
                    data={'res_ver': commit_id, 'apply_dt': datetime.now()}
                )
                self.splog.add_info(f'테이블 UPDATE 성공 : version_check_info')
            else:  # Insert
                res = await self.db.version_check_info.create(
                    {
                        'server_type': 1,
                        'market_type': _market_type,
                        'client_ver': '0.0.1',
                        'is_update_require': 0,
                        'res_ver': commit_id,
                        'res_url': res_url,
                        'apply_dt': datetime.now(),
                        'reg_dt': datetime.now(),
                        'status': 'A'
                    }
                )
                self.splog.add_info(f'테이블 INSERT 성공 : version_check_info')

        except Exception as e:
            self.splog.add_error(f'테이블 UPDATE Error : version_check_info \n {str(e)}')

        await self.destory()

    async def restore_table(self, table_name: str, json_data: list):
        try:
            table = getattr(self.db, table_name)
            await table.delete_many()
            await table.create_many(
                json_data
            )
            self.splog.add_info(f'테이블 데이터 RESTORE 성공 : {table_name}')
        except Exception as e:
            self.splog.add_error(f'테이블 데이터 RESTORE 실패 : {table_name} \n {json_data.pop()} \n {str(e)}')

    async def insert_table(self, table_name: str, json_data: list):
        try:
            table = getattr(self.db, table_name)
            await table.create(
                json_data
            )
            self.splog.add_info(f'테이블 데이터 INSERT 성공 : {table_name}')
        except Exception as e:
            self.splog.add_error(f'테이블 데이터 INSERT 실패 : {table_name} \n {str(e)}')

    async def destory(self):
        await self.db.disconnect()
        self.splog.destory()
