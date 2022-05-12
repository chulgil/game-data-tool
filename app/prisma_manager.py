import logging
import os
from enum import Enum, auto
from pathlib import Path

import yaml
from subprocess import run
import re


class MigrateType(Enum):
    CREATE_ONLY = auto
    DEV = auto
    DEPLOY = auto
    FORCE = auto


class PrismaManager:

    def __init__(self, branch: str):
        self.BRANCH = branch
        self.ROOT_DIR = Path(__file__).parent.parent
        self.PATH_FOR_PRISMA = self.ROOT_DIR.joinpath('prisma')
        self.PATH_FOR_CONFIG = self.ROOT_DIR.joinpath('config.yaml')
        self.PATH_FOR_ENV = self.PATH_FOR_PRISMA.joinpath('.env')
        # Config 파일 설정
        with open(self.PATH_FOR_CONFIG, 'r') as f:
            config = yaml.safe_load(f)
        self.CONFIG_DB = config['DATABASE']
        self.PATH_FOR_SAVE_DIR = self.ROOT_DIR.joinpath(config['DEFAULT']['ROOT_DATA_DIR'], 'prisma')
        self.PATH_FOR_SCHEMA = self.PATH_FOR_SAVE_DIR.joinpath('schema.prisma')

        # Prisma 스키마 폴더 생성
        if not self.PATH_FOR_SAVE_DIR.exists():
            os.mkdir(self.PATH_FOR_SAVE_DIR)

    def sync(self) -> bool:
        try:
            os.chdir(self.PATH_FOR_PRISMA.parent)
            self._init_prisma_config()
            res = run(['prisma db pull'], shell=True)
            if not res.stderr:
                logging.info(f"[DB:{self.BRANCH}] 서버 PRISMA 동기화 완료")
                return True
        except Exception as e:
            logging.error(f"[DB:{self.BRANCH}] 서버 PRISMA 동기화 에러: {str(e)}")
        return False

    def init_prisma(self) -> bool:
        try:
            os.chdir(self.PATH_FOR_PRISMA.parent)
            self._init_prisma_config()
            res = run(['prisma generate'], shell=True)
            if not res.stderr:
                logging.info(f"[DB:{self.BRANCH}] 서버 PRISMA 초기화 완료")
                return True
        except Exception as e:
            logging.error(f"[DB:{self.BRANCH}] 서버 PRISMA 초기화 에러: /n {str(e)}")
        return False

    # .env 파일에  디비 경로를 설정
    # ex) DATABASE_URL="sqlserver://db.com:1433;database=data_db;user=sa;password=pass;encrypt=DANGER_PLAINTEXT"
    def _init_prisma_config(self):
        db_path = self._get_db_by_branch()
        db_path = 'DATABASE_URL="' + db_path + '"'
        with open(self.PATH_FOR_ENV, 'w', encoding='utf-8') as f:
            f.write(db_path)

    # 브랜치 명으로 Config설정에 있는 디비 경로를 가져온다.
    def _get_db_by_branch(self) -> str:
        db_name = {
            "main": "DEV2",
        }.get(self.BRANCH, str(self.BRANCH).upper())
        return self.CONFIG_DB[db_name]

    @staticmethod
    def migrate(option: MigrateType):

        if option == MigrateType.CREATE_ONLY:
            pass

        elif option == MigrateType.FORCE:
            pass

        # print(table_info)
        # table_name = ''
        # schema = self._get_default_schema()
        # for key in table_info.keys():
        #     table_name = key
        #     rows = table_info[key]
        #     schema = schema + self._convet_schema(table_name, rows)
        # print(schema)
        # self._save_schema(schema)
        print("스키마생성")

    def save_schema(self, table_info: dict):
        table_name = ''
        schema = self._get_default_schema()
        for key in table_info.keys():
            table_name = key
            rows = table_info[key]
            schema = schema + self._convet_schema(table_name, rows)
        try:
            # 지정한 경로로 Prisma 스키마 파일 저장
            with open(self.PATH_FOR_SCHEMA, "w", encoding='utf-8') as f:
                f.write(schema)
            logging.info(f'Prisma 스키마 저장 완료: {table_name}')
        except Exception as e:
            logging.error(f'Prisma 스키마 저장 Error: {table_name}\n{str(e)}')

        #
        # # 파일 경로로 부터 / Sever / file.csv 를 잘라온다.
        # paths = str(save_path).split('/')
        # name = paths.pop()
        # path = paths.pop()
        # logging.info(f"Json 파일 저장 성공 : {path}/{name}")

    def _convet_schema(self, table_name: str, rows: list) -> str:
        schema = ''
        try:
            tab = '    '
            schema = schema + f'\nmodel {table_name} ' + '{ \n'
            for row in rows:
                row = self._convert_sqlserver(row)
                schema = schema + '  ' + tab.join(row)
                schema = schema + '\n'
            schema = schema + '}\n'
        except Exception as e:
            logging.error(f'Prisma 스키마 변환 Error: {table_name}\n{str(e)}')
        return schema

    def _convert_sqlserver(self, row: list) -> list:
        """
        Prisma 디비 포멧으로 변환 :
        디비필드, 디비타입, 스키마타입
        ['id', 'long', '@auto'] -> ['id', 'BigInt', '@auto']
        """
        row[1] = self._convert_datatype(row[1], row[2])
        row[2] = self._convert_option(row[1], row[2])
        return row

    @staticmethod
    def _convert_datatype(col: str, option: str) -> str:
        res = col.lower()
        if res == 'long':
            res = 'BigInt'
        elif res == 'datetime':
            res = 'DateTime'
        elif res == 'bool':
            res = 'Boolean'
        else:
            res = col.title()
        from re import match
        if match(r'@null', option):
            res = res + '?'
        return res

    @staticmethod
    def _convert_option(datatype: str, option: str) -> str:
        """
        Prisma 형식의 디비 포멧으로 변환
        @auto -> '@id  @default(autoincrement())'
        @null -> ''
        @size(5) -> db.NVarChar(5)
        @ref(xxx.xx) -> ''
        """
        res = option
        res = re.sub(r'\(\'(\W+)\'\)', r'("\1")', res)
        if datatype == 'String':
            res = re.sub(r'@size\((\d+)\)', r'@db.NVarChar(\1)', res)
        res = res.replace('@auto', '@id  @default(autoincrement())')
        res = res.replace('@null', '')
        res = re.sub(r'@size\(\d+\)', '', res)
        res = re.sub(r'@ref\(\D+\)', '', res)
        return res

    @staticmethod
    def _get_default_schema():
        return '''
generator db {
  provider  = "prisma-client-py"
  interface = "asyncio"
}

datasource db {
  provider = "sqlserver"
  url      = env("DATABASE_URL")
}
       '''
