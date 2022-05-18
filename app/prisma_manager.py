import logging
import os
from enum import Enum, auto
from pathlib import Path

import yaml
from subprocess import run, CalledProcessError, check_output, STDOUT, PIPE
import re


class MigrateType(Enum):
    CREATE_ONLY = auto()
    DEV = auto()
    DEPLOY = auto()
    FORCE = auto()


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
        self.PATH_FOR_SAVE_SCHEMA = self.PATH_FOR_SAVE_DIR.joinpath('schema.prisma')
        self.PATH_FOR_BASE_SCHEMA = self.PATH_FOR_PRISMA.joinpath('schema.prisma')

        # Prisma 스키마 폴더 생성
        if not self.PATH_FOR_SAVE_DIR.exists():
            os.mkdir(self.PATH_FOR_SAVE_DIR)

    def sync(self) -> bool:
        try:
            os.chdir(self.PATH_FOR_PRISMA.parent)
            self._init_prisma_config()
            res = run(['prisma db pull'], shell=True)
            res = run(['prisma generate'], shell=True)
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

    def migrate(self, option: MigrateType, migrate_id: str):
        self.init_prisma()
        try:
            # 생성한 파일을 Prisma기본 생성경로로 덮어쓰기
            schema = ''
            with open(self.PATH_FOR_SAVE_SCHEMA, 'r') as f:
                schema = f.read()

            with open(self.PATH_FOR_BASE_SCHEMA, 'w') as f:
                f.write(schema)

            if option == MigrateType.DEV:
                run([f'prisma migrate dev --name {migrate_id}'], shell=True, check=True, stdout=PIPE,
                    stderr=STDOUT)

            elif option == MigrateType.CREATE_ONLY:
                run([f'prisma migrate dev --create-only'], shell=True, check=True, stdout=PIPE,
                    stderr=STDOUT)

            elif option == MigrateType.FORCE:
                run([f'prisma db push --accept-data-loss'], shell=True, check=True, stdout=PIPE,
                    stderr=STDOUT)

            logging.error(f'Prisma 마이그레이션 완료: {str(option)}')

        except CalledProcessError as e:
            logging.error(f'Prisma 마이그레이션 Error: \n{str(e.output)}')
        except Exception as e:
            logging.error(f'Prisma 마이그레이션 Error: \n{str(e)}')

    def save_schema(self, table_info: dict):
        table_name = ''
        schema = self._get_default_schema()
        for key in table_info.keys():
            table_name = key
            rows = table_info[key]
            new_schema = self._convet_schema(table_name, rows)
            if new_schema != '':
                logging.info(f'Prisma 스키마 저장 완료: {table_name}')
                schema = schema + new_schema
        try:
            # 지정한 경로로 Prisma 스키마 파일 저장
            with open(self.PATH_FOR_SAVE_SCHEMA, "w", encoding='utf-8') as f:
                f.write(schema)
        except Exception as e:
            logging.error(f'Prisma 스키마 저장 Error: {table_name}\n{str(e)}')

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
                row[1] = self._convert_datatype(row[1], row[2])
                row[2] = self._convert_option(row[1], row[2])
            rows = self._convert_combine(rows)
            for row in rows:
                schema = schema + '  ' + tab.join(row)
                schema = schema + '\n'
            schema = schema + '}\n'
        except Exception as e:
            logging.error(f'Prisma 스키마 변환 Error: {table_name}\n{str(e)}')
        return schema

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
    def _convert_combine(rows: list) -> list:
        """
        아이디가 복수 존재하는 경우:
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
