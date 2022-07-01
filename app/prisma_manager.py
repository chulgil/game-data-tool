import os
from enum import Enum, auto
from pathlib import Path
from importlib.machinery import SourceFileLoader
from datetime import datetime
import yaml
from subprocess import run, CalledProcessError, check_output, STDOUT, PIPE
import re


class MigrateType(Enum):
    CREATE_ONLY = auto()
    DEV = auto()
    DEPLOY = auto()
    FORCE = auto()


class DBType(Enum):
    DATA_DB = auto()
    INFO_DB = auto()


class UserType(Enum):
    ADMIN = auto()
    USER = auto()


class PrismaManager:

    def __init__(self, branch: str, load_dir: Path, user_type: UserType = UserType.USER):
        self.config = None
        from . import LogManager
        self.data_db = None
        self.info_db = None
        self.splog = LogManager(branch)
        self.splog.PREFIX = f"[{branch} 브랜치] PRISMA[{user_type.name}]"
        self.BRANCH = branch
        self.USER_TYPE = user_type
        self.PATH_FOR_ROOT = Path(__file__).parent.parent

        # Config 파일 설정
        self.PATH_FOR_CONFIG = self.PATH_FOR_ROOT.joinpath('config.yaml')
        with open(self.PATH_FOR_CONFIG, 'r') as f:
            self.config = yaml.safe_load(f)
        if 'DATA_DB' not in self.config['DATABASE']:
            self.splog.warning(f'CONFIG DATABASE[DATA_DB] 가 존재하지 않습니다.')
            return
        if 'INFO_DB' not in self.config['DATABASE']:
            self.splog.warning(f'CONFIG DATABASE[INFO_DB] 가 존재하지 않습니다.')
            return
        self.PATH_FOR_SAVE_DIR = self.PATH_FOR_ROOT.joinpath('prisma', user_type.name.lower(), branch)
        self.PATH_FOR_BASE_SCHEMA = load_dir.joinpath(self.config['DEFAULT']['EXPORT_DIR'], 'prisma', 'schema.prisma')
        self.PATH_FOR_DATA_SCHEMA = self.PATH_FOR_SAVE_DIR.joinpath('data_schema.prisma')
        self.PATH_FOR_INFO_SCHEMA = self.PATH_FOR_SAVE_DIR.joinpath('info_schema.prisma')
        self.PATH_FOR_DATA_SOURCE = self.PATH_FOR_SAVE_DIR.joinpath(DBType.DATA_DB.name.lower(), '__init__.py')
        self.PATH_FOR_INFO_SOURCE = self.PATH_FOR_SAVE_DIR.joinpath(DBType.INFO_DB.name.lower(), '__init__.py')

        # Prisma 스키마 폴더 생성
        if not self.PATH_FOR_SAVE_DIR.exists():
            os.makedirs(self.PATH_FOR_SAVE_DIR)

    def sync(self) -> bool:
        try:
            self.init_prisma()

            os.chdir(self.PATH_FOR_SAVE_DIR)

            from prisma_cleanup import cleanup
            cleanup()
            data_schema = self._get_schema_path(DBType.DATA_DB)
            res = run([f'prisma db pull --schema={data_schema}'], shell=True)
            res = run([f'prisma generate --schema={data_schema}'], shell=True)

            info_schema = self._get_schema_path(DBType.INFO_DB)
            res = run([f'prisma db pull --schema={info_schema}'], shell=True)
            res = run([f'prisma generate --schema={info_schema}'], shell=True)

            self._load_db_source()

            if not res.stderr:
                self.splog.info(f"동기화 완료")
                return True
        except Exception as e:
            self.splog.error(f"동기화 에러: {str(e)}")
        return False

    def init_prisma(self) -> bool:
        try:
            # 생성한 파일을 Prisma기본 생성경로로 덮어쓰기
            with open(self.PATH_FOR_BASE_SCHEMA, 'r') as f:
                base_schema = f.read()
            data_schema = self._get_default_schema(DBType.DATA_DB) + base_schema
            with open(self.PATH_FOR_DATA_SCHEMA, 'w') as f:
                f.write(data_schema)
            self.prisma_generate(DBType.DATA_DB)

            info_schema = self._get_default_schema(DBType.INFO_DB)
            with open(self.PATH_FOR_INFO_SCHEMA, 'w') as f:
                f.write(info_schema)
            res = run([f'prisma db pull --schema={self.PATH_FOR_INFO_SCHEMA}'], shell=True)
            self.prisma_generate(DBType.INFO_DB)
            self._load_db_source()
            return True
        except Exception as e:
            self.splog.error(f"초기화 에러: \n {str(e)}")
        return False

    # 브랜치 명으로 Config설정에 있는 디비 경로를 가져온다.
    def _get_db_by_branch(self, db_type: DBType) -> str:
        db_name = {
            "main": "DEV2",
        }.get(self.BRANCH, str(self.BRANCH).upper())
        config_db = self.config['DATABASE']
        if db_type == DBType.DATA_DB:
            if db_name in config_db[db_type.name]:
                return config_db[db_type.name][db_name]
            else:
                self.splog.warning(f"DB CONFIG에 DATA_DB[{db_name}] 가 존재 하지 않습니다.")
                return db_name
        if db_type == DBType.INFO_DB:
            if db_name in config_db[db_type.name]:
                return config_db[db_type.name][db_name]
            else:
                self.splog.warning(f"DB CONFIG에 INFO_DB[{db_name}] 가 존재 하지 않습니다.")
                return db_name

    def _get_schema_path(self, db_type: DBType) -> str:
        if db_type == DBType.DATA_DB:
            return str(self.PATH_FOR_DATA_SCHEMA)
        if db_type == DBType.INFO_DB:
            return str(self.PATH_FOR_INFO_SCHEMA)

    def prisma_generate(self, db_type: DBType = DBType.DATA_DB):
        print('--------------PRISMA GENERATE')
        schema = self._get_schema_path(db_type)
        res = run([f'prisma generate --schema={schema}'], shell=True)
        if not res.stderr:
            self.splog.info(f"초기화 완료")

    async def migrate(self, option: MigrateType, migrate_id: str):
        try:
            if not self.init_prisma():
                return

            data_schema = self._get_schema_path(DBType.DATA_DB)
            os.chdir(self.PATH_FOR_SAVE_DIR)
            if option == MigrateType.DEV:
                run([f'prisma migrate dev --name {migrate_id} --schema={data_schema}'], shell=True, check=True,
                    stdout=PIPE, stderr=STDOUT)

            elif option == MigrateType.CREATE_ONLY:
                run([f'prisma migrate dev --create-only --schema={data_schema}'], shell=True, check=True, stdout=PIPE,
                    stderr=STDOUT)

            elif option == MigrateType.FORCE:
                run([f'prisma db push --accept-data-loss --force-reset --schema={data_schema}'], shell=True, check=True,
                    stdout=PIPE,
                    stderr=STDOUT)

            await self.splog.info(f'Prisma DB 초기화 완료: {str(option)}')

        except CalledProcessError as e:
            self.splog.error(f'마이그레이션 Error: \n{str(e.output)}')
        except Exception as e:
            self.splog.error(f'마이그레이션 Error: \n{str(e)}')

    def save(self, table_info: dict):
        table_name = ''
        schema = ''
        for key in table_info.keys():
            table_name = key
            rows = table_info[key]
            new_schema = self._convet_schema(table_name, rows)
            if new_schema != '':
                self.splog.info(f'스키마 저장 완료: {table_name}')
                schema = schema + new_schema
        try:
            # 지정한 경로로 Prisma 스키마 파일 저장
            with open(self.PATH_FOR_DATA_SCHEMA, "w", encoding='utf-8') as f:
                f.write(schema)
        except Exception as e:
            self.splog.error(f'스키마 저장 Error: {table_name}\n{str(e)}')

    def _convet_schema(self, table_name: str, rows: list) -> str:
        """
        Prisma 디비 포멧으로 변환 :
        디비필드, 디비타입, 스키마타입
        ['id', 'long', '@auto'] -> ['id', 'BigInt', '@auto']
        """
        schema = ''
        try:
            tab = '    '
            schema = schema + f'\nmodel {table_name} ' + '{ \n'
            if len(rows) < 1:
                return ''
            for row in rows:
                # 순서 주의 : 컨버팅 되지 않은 타입값으로 디비 스키마 값 변경
                d_type = self._convert_datatype(row[1], row[2])
                option = self._convert_option(row[1], row[2])
                row[1] = d_type
                row[2] = option
            rows = self._convert_combine(rows)
            for row in rows:
                desc = ''
                item = row
                if len(item) > 3:
                    desc = item.pop()
                    desc = str(desc).replace('\n', ' ')  # 메모의 개행 공백 치환
                schema = schema + '  ' + tab.join(item)
                schema = schema + (' // ' + desc + '\n' if desc != '' else '\n')
            schema = schema + '}\n'
        except Exception as e:
            self.splog.error(f'스키마 변환 Error: {table_name}\n{str(e)}')
        return schema

    @staticmethod
    def _convert_datatype(col: str, option: str) -> str:
        res = col.lower()
        if res == 'long':
            res = 'BigInt'
        elif res == 'datetime':
            res = 'DateTime'
        elif res == 'bool' or res == 'boolean':
            res = 'Boolean'
        elif res == 'short' or res == 'byte':
            res = 'Int'
        else:
            res = col.title()
        if re.findall(r'@null', option):
            res = res + '?'
        return res

    @staticmethod
    def _convert_combine(rows: list) -> list:
        """
        DB스키마ID가 복수 존재하는 경우:
        item1 long  @id
        item2 int  @id
            -> @@id([season_no, user_no])
        """
        filtered = list(filter(lambda v: re.match(r'@id', v[2]), rows))
        if len(filtered) > 1:
            columns = list(zip(*filtered))
            ids = ','.join(columns[0])
            for row in rows:
                row[2] = row[2].replace('@id', '')
            rows.append(['', '', ''])
            rows.append([f'@@id([{ids}])', '', ''])
        return rows

    @staticmethod
    def _convert_option(datatype: str, option: str) -> str:
        """
        Prisma 형식의 디비 포멧으로 변환
        @auto -> @id  @default(autoincrement())
        @null -> ''
        @size(5) -> db.NVarChar(5)
        @ref(xxx.xx) -> ''
        아이디가 복수 존재하는 경우:
        item1 @id
        item2 @id
            -> @@id([season_no, user_no])
        """
        dt = datatype.lower()
        res = option
        res = re.sub(r'\(\'(\W+)\'\)', r'("\1")', res)
        if re.findall(r'@enum', res):
            res = re.sub(r'@enum\(\S+\)', '', res)
            res = re.sub(r'@default\(\S+\)', '', res)
        if dt == 'string':
            res = re.sub(r'@size\((\d+)\)', r'@db.NVarChar(\1)', res)
        if dt == 'short':
            res = res.replace('@db.SmallInt', '')
            res = res + ' @db.SmallInt'
        if dt == 'byte':
            res = res.replace('@db.TinyInt', '')
            res = res + ' @db.TinyInt'
        res = res.replace('@auto', '@id  @default(autoincrement())')
        res = res.replace('@null', '')
        res = re.sub(r'@size\(\d+\)', '', res)
        res = re.sub(r'@ref\(\D+\)', '', res)
        return res

    def _get_default_schema(self, db_type: DBType):

        output = self._get_db_by_branch(db_type)
        return '''
generator db {{
  provider  = "prisma-client-py"
  interface = "asyncio"
  output = "{0}"
}}

datasource db {{
  provider = "sqlserver"
  url      = "{1}"
}}
       '''.format(db_type.name.lower(), output)

    def _load_db_source(self):
        try:
            source = SourceFileLoader('client', str(self.PATH_FOR_DATA_SOURCE)).load_module()
            self.data_db = source.Prisma()
        except Exception as e:
            self.splog.error(f'DATA DB 접속 ERROR : \n{e}')
        try:
            source = SourceFileLoader('client', str(self.PATH_FOR_INFO_SOURCE)).load_module()
            self.info_db = source.Prisma()
        except Exception as e:
            self.splog.error(f'INFO DB 접속 ERROR : \n{e}')

    async def restore_all_table(self, json_map: dict):
        if not self.data_db:
            return
        await self.data_db.connect()
        # Json파일 가져오기
        i = 0
        for json_key, json_data in json_map.items():
            try:
                i = i + 1
                await self.restore_table(json_key, json_data)
            except Exception as e:
                self.splog.add_error(f'테이블 데이터 {json_key} Error :\n {str(e)}')
        await self.destory()
        self.splog.add_info(f'테이블 데이터 총 {i} 건 RESTORE 완료')

    async def update_version_info(self, commit_id: str, res_url: str):
        if not self.info_db:
            return
        await self.info_db.connect()
        # Json파일 가져오기
        try:
            _market_type = 3000
            version_check_info = await self.data_db.version_check_info.find_first(where={'market_type': _market_type})

            if version_check_info:  # Update
                res = await self.data_db.version_check_info.update(
                    where={'version_check_info_key': version_check_info.version_check_info_key},
                    data={'res_ver': commit_id, 'apply_dt': datetime.now()}
                )
                self.splog.add_info(f'테이블 UPDATE 성공 : version_check_info')
            else:  # Insert
                res = await self.data_db.version_check_info.create(
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
            table = getattr(self.data_db, table_name)
            await table.delete_many()
            await table.create_many(
                json_data
            )
            self.splog.add_info(f'테이블 데이터 RESTORE 성공 : {table_name}')
        except Exception as e:
            self.splog.add_error(f'테이블 데이터 RESTORE 실패 : {table_name} \n {str(e)}')

    async def insert_table(self, table_name: str, json_data: list):
        try:
            table = getattr(self.data_db, table_name)
            await table.create(
                json_data
            )
            self.splog.add_info(f'테이블 데이터 INSERT 성공 : {table_name}')
        except Exception as e:
            self.splog.add_error(f'테이블 데이터 INSERT 실패 : {table_name} \n {str(e)}')

    async def destory(self):
        if self.data_db:
            await self.data_db.disconnect()
        if self.info_db:
            await self.info_db.disconnect()
        self.splog.destory()
