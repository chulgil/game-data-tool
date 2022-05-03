import logging
import os
from pathlib import Path
import yaml
from prisma_cleanup import cleanup

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
        self._init_prisma()

    def sync(self):
        try:
            cleanup()
            os.chdir(self.PATH_FOR_PRISMA.parent)
            self._init_prisma_config()
            os.system("prisma db pull")
            logging.info(f"[DB:{self.BRANCH}] 서버 PRISMA 동기화 완료")
        except Exception as e:
            logging.error(f"[DB:{self.BRANCH}] 서버 PRISMA 동기화 에러: /n {str(e)}")

    def _init_prisma(self):
        try:
            os.chdir(self.PATH_FOR_PRISMA.parent)
            self._init_prisma_config()
            os.system("prisma generate")
            logging.info(f"[DB:{self.BRANCH}] 서버 PRISMA 초기화 완료")
        except Exception as e:
            logging.error(f"[DB:{self.BRANCH}] 서버 PRISMA 초기화 에러: /n {str(e)}")

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
