import logging
from migration import *

if __name__ == '__main__':

    # main : 기획자 브랜치
    # dev : 개발 브랜치
    # qa & qa2 & qa3 : QA 브랜치
    # local : 로컬 브랜치
    logger = logging.getLogger()
    logging.basicConfig(
        format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p',
        filename='out.log', encoding='utf-8', level=logging.INFO)

    # Git 초기화
    git_manager = GitManager('local')
    git_manager.pull()

    # 데이터
    manager = DataManager()
    manager.excel_to_json()

    # Git Push
    if git_manager.is_modified():
        git_manager.push()

    manager = DBManager('local')
    manager.init_info_db()
