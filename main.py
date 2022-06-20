import asyncio
import logging

import colorlog

if __name__ == '__main__' or __name__ == "decimal":
    from app import *

    _format = '[%(levelname)-7s] %(asctime)s: %(message)s '
    _format_console = colorlog.ColoredFormatter(_format, "%m/%d/%Y %H:%M:%S ")
    logger = logging.getLogger()
    handler = logging.FileHandler('out.log', 'w', 'utf-8')
    handler.setFormatter(_format_console)
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)

    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.INFO)
    stream_handler.setFormatter(_format_console)
    logger.addHandler(stream_handler)


else:
    from app.libs.excel_to_db.app import *


def sync_prisma(branch: str):
    g_manager = GitManager(GitTarget.EXCEL)

    if not g_manager.checkout(branch):
        g_manager.destroy()
        return

    # 프리즈마 초기화
    prisma = PrismaManager(branch, g_manager.PATH_FOR_WORKING)
    prisma.sync()


async def update_table(branch: str, convert_type: ConvertType):
    # Git 초기화 및 다운로드
    g_manager = GitManager(GitTarget.EXCEL)

    # 체크아웃 성공시에만 진행
    if not g_manager.checkout(branch):
        g_manager.destroy()
        return

    # 변환된 Json파일을 디비로 저장
    b_manager = DBManager(branch, g_manager.PATH_FOR_WORKING)
    d_manager = DataManager(branch, convert_type, g_manager.PATH_FOR_WORKING)
    json_map = d_manager.get_jsonmap()
    await b_manager.restore_all_table(json_map)
    res_info = g_manager.get_client_resource_from_branch()
    if len(res_info.keys()) > 0:
        await b_manager.update_version_info(res_info['res_ver'], res_info['res_url'])


def excel_to_json_all(g_manager: GitManager):
    """전체 Excel을 추출후 Json변환
        """

    g_manager.splog.info("전체 Excel로드후 Json변환을 진행합니다.")

    # 전체 Excel로드후 Json변환
    d_manager = DataManager(g_manager.BRANCH, ConvertType.ALL, g_manager.PATH_FOR_WORKING)
    d_manager.delete_json_all()
    d_manager.excel_to_json(d_manager.get_excelpath_all())


def excel_to_json(convert_type: ConvertType, g_manager: GitManager):
    """
    변경된 Excel만 추출후 Json변환
    @param convert_type: 기획데이터:server Info데이터:info 클라이언트데이터:client
    @param g_manager: GitManager
    @return:
    """
    branch = g_manager.BRANCH
    g_manager.splog.info(f"변경된 Excel로드후 Json변환을 진행합니다. [데이터 타입 : {convert_type.name}]")

    d_manager = DataManager(branch, convert_type, g_manager.PATH_FOR_WORKING)

    # Excel로드후 Json변환
    d_manager.excel_to_json(g_manager.get_modified_excel())


def excel_to_entity(g_manager: GitManager, gc_manager: GitManager):
    g_manager.splog.info("전체 Excel로드후 C# 스크립트 변환을 진행합니다.")

    d_manager = DataManager(g_manager.BRANCH, ConvertType.CLIENT, g_manager.PATH_FOR_WORKING)
    c_manager = CSharpManager(g_manager.BRANCH, g_manager.BASE_TAG, g_manager.COMMIT_ID,
                              gc_manager.PATH_FOR_WORKING)
    c_manager.save_entity(d_manager.get_schema_all())
    c_manager.save_enum(d_manager.get_enum_data())
    d_manager.save_json_all(gc_manager.PATH_FOR_WORKING.joinpath("data_all.json"))


def excel_to_enum(g_manager: GitManager, gc_manager: GitManager):
    g_manager.splog.info("전체 Excel로드후 Enum 스크립트 변환을 진행합니다.")
    d_manager = DataManager(g_manager.BRANCH, ConvertType.CLIENT, g_manager.PATH_FOR_WORKING)
    c_manager = CSharpManager(g_manager.BRANCH, g_manager.BASE_TAG, g_manager.COMMIT_ID,
                              gc_manager.PATH_FOR_WORKING)
    c_manager.save_enum(d_manager.get_enum_data())


def excel_to_schema(g_manager: GitManager):
    """
    전체 Excel추출후 아래 데이터 타입만 Prisma 스키마변환
    @param g_manager: GitManager
    """
    g_manager.splog.info("전체 Excel로드후 Prisma변환을 진행합니다.")

    # 프리즈마 초기화
    p_manager = PrismaManager(g_manager.BRANCH, g_manager.PATH_FOR_WORKING)
    d_manager = DataManager(g_manager.BRANCH, ConvertType.ALL, g_manager.PATH_FOR_WORKING)
    table_info = d_manager.get_schema_all()
    p_manager.save(table_info)


def get_commit_from_webhook(webhook: dict) -> dict:
    g_manager = GitManager(GitTarget.EXCEL)
    res = g_manager.load_commit_from_webhook(webhook)
    g_manager.destroy()
    return res


async def excel_to_data_all_from_branch(branch: str):
    """
    최신 Excel Git 브랜치를 복제한후 데이터 변환을 호출한다.
    @param branch: Git브랜치
    """
    # Git 초기화 및 다운로드
    g_manager = GitManager(GitTarget.EXCEL)

    # # 체크아웃 성공시에만 진행
    if not g_manager.checkout(branch):
        g_manager.destroy()
        return
    check_excel(g_manager)
    excel_to_json_all(g_manager)

    await excel_to_server(g_manager)

    if g_manager.is_modified():
        g_manager.push()
    g_manager.destroy()


async def excel_to_data_from_webhook(webhook: dict = None):
    """
    Git Push 발생후 Webhook에서 이 메서드가 호출됨
    git commit id를 기준으로 리포지토리를 복제한후 데이터 변환을 호출한다.
    @param webhook: 호출 파라미터 상세
            dict {
            "branch" : "test",
            "id": "5dc78789cadafe7bc73adf8031a9b6ba9236af2c",
            "message": "teste\n",
            "url": "http://url:3000/SPTeam/data-for-designer/commit/5dc78789cadafe7bc73adf8031a9b6ba9236af2c",
            "author": {
              "name": "기획자",
              "email": "designer@snowpipe.co.kr",
              "username": "designer"
            },
            "committer": {
              "name": "기획자",
              "email": "designer@snowpipe.co.kr",
              "username": "designer"
            },
            "verification": null,
            "timestamp": "2022-05-04T16:40:46+09:00",
            "added": [],
            "removed": [],
            "modified": [
              "excel/data/zone_data.json"
            ]
        }

    """
    g_manager = GitManager(GitTarget.EXCEL, webhook)
    # # 체크아웃 성공시에만 진행
    if not webhook["head_commit"] or not g_manager.checkout():
        g_manager.destroy()
        return

    username = webhook["head_commit"]["committer"]["username"]
    message = webhook["head_commit"]["message"]
    compare_url = webhook["compare_url"]

    if g_manager.NEW_TAG != '':
        await excel_to_data_taged(g_manager)
    else:
        # 변경사항이 없다면 무시
        if not compare_url:
            g_manager.splog.send_designer(f"[EXCEL변환요청:{username}] 변경사항이 없어 종료합니다.")
            return

        # 봇 PUSH 인 경우는 다시 PUSH하지 않고 메시지만 보낸다.
        if g_manager.is_bot_user():
            g_manager.splog.send_designer(f"변경 히스토리 URL : {compare_url}")
            return

        g_manager.splog.send_designer(f"[EXCEL변환요청:{username}] 변경사항을 적용합니다. \n\n {message}")
        await excel_to_data_modified(g_manager)

    # 수정된 Json 파일이 있다면 Excel Git서버로 자동 커밋
    if g_manager.is_modified():
        g_manager.push()
    g_manager.destroy()


async def excel_to_data_modified(g_manager: GitManager):
    modified_list = g_manager.get_modified_excel()
    if len(modified_list) == 0:
        g_manager.destroy()
        return
    check_excel(g_manager)
    excel_to_json(ConvertType.ALL, g_manager)
    await excel_to_server(g_manager)


async def excel_to_data_taged(g_manager: GitManager):
    g_manager.splog.info(f"새로운 태그[{g_manager.NEW_TAG}] 요청으로 EXCEL 전체 변환을 시작합니다.")
    g_manager.save_base_tag_to_branch(g_manager.NEW_TAG)

    gc_manager = GitManager(GitTarget.CLIENT)
    if not gc_manager.checkout(g_manager.BRANCH):
        gc_manager.destroy()
        return

    data_to_client_data(g_manager, gc_manager)

    prisma = PrismaManager(g_manager.BRANCH, g_manager.PATH_FOR_WORKING)
    prisma.migrate(MigrateType.FORCE, g_manager.BRANCH)
    await data_to_db(g_manager)
    await tag_to_db(g_manager)


async def excel_to_data_all_from_tag(tag: str):
    g_manager = GitManager(GitTarget.EXCEL)
    g_manager.load_branch_from_tag(tag)
    if not g_manager.checkout():
        g_manager.destroy()
        return
    gc_manager = GitManager(GitTarget.CLIENT)
    if not gc_manager.checkout():
        gc_manager.destroy()
        return
    g_manager.GIT_PUSH_MSG = f'{g_manager.GIT_PUSH_MSG} API 호출로 인한 EXCEL전체 변환'
    g_manager.splog.info(f"새로운 태그[{g_manager.NEW_TAG}] 요청으로 EXCEL 전체 변환을 시작합니다.")

    check_excel(g_manager)
    excel_to_json_all(g_manager)
    excel_to_schema(g_manager)
    excel_to_entity(g_manager, gc_manager)
    excel_to_enum(g_manager, gc_manager)
    data_to_client_data(g_manager, gc_manager)
    if gc_manager.is_modified():
        gc_manager.push()
    gc_manager.destroy()
    g_manager.save_base_tag_to_branch(g_manager.NEW_TAG)
    if g_manager.is_modified():
        g_manager.push()

    prisma = PrismaManager(g_manager.BRANCH, g_manager.PATH_FOR_WORKING)
    prisma.migrate(MigrateType.FORCE, g_manager.BRANCH)
    await data_to_db(g_manager)
    await tag_to_db(g_manager)
    g_manager.destroy()


def data_to_client_data(g_manager: GitManager, gc_manager: GitManager):
    d_manager = DataManager(g_manager.BRANCH, ConvertType.CLIENT, g_manager.PATH_FOR_WORKING)
    d_manager.save_json_all(gc_manager.PATH_FOR_WORKING.joinpath("data_all.json"))

    f_manager = FtpManager(g_manager.BRANCH, g_manager.COMMIT_ID, g_manager.PATH_FOR_WORKING)
    f_manager.send(d_manager.get_json())
    g_manager.save_client_resource_to_branch(f_manager.get_resource_url())
    if g_manager.NEW_TAG != '':
        g_manager_client = GitManager(GitTarget.CLIENT)
        if not g_manager_client.checkout(g_manager.BRANCH):
            g_manager_client.destroy()
            return
        g_manager_client.push_tag_to_client(g_manager.NEW_TAG)
        g_manager_client.destroy()


async def excel_to_server(g_manager: GitManager):
    gc_manager = GitManager(GitTarget.CLIENT)
    if not gc_manager.checkout(g_manager.BRANCH):
        gc_manager.destroy()
        return

    if g_manager.is_modified_excel_enum():
        excel_to_enum(g_manager, gc_manager)
        msg = 'Enum 데이터에 변동 사항이 있습니다. 개발자가 확인 후 다음 프로세스로 진행됩니다.'
        g_manager.splog.add_warning(msg)
        g_manager.splog.send_developer()
        g_manager.splog.send_designer(msg)

    if g_manager.is_modified_excel_column():
        g_manager.splog.info(f'EXCEL파일에 변동이 있어 스키마 변환을 진행합니다.')
        excel_to_entity(g_manager, gc_manager)
        excel_to_schema(g_manager)
        if not g_manager.splog.is_service_branch(g_manager.BRANCH):
            data_to_client_data(g_manager, gc_manager)
        msg = '기획 데이터의 컬럼에 변동 사항이 있습니다. 개발자가 확인 후 다음 프로세스로 진행됩니다.'
        g_manager.splog.add_warning(msg)
        g_manager.splog.send_developer()
        g_manager.splog.send_designer(msg)
    else:
        g_manager.splog.send_designer(f'EXCEL파일 데이터 수정으로 인한 데이터 업데이트를 진행합니다.')
        data_to_client_data(g_manager, gc_manager)
        await data_to_db(g_manager)
        await tag_to_db(g_manager)

    if gc_manager.is_modified():
        gc_manager.push()
    gc_manager.destroy()


def check_excel(g_manager: GitManager):
    d_manager = DataManager(g_manager.BRANCH, ConvertType.ALL, g_manager.PATH_FOR_WORKING)
    d_manager.check_excel_for_relation(d_manager.get_excelpath_all())


async def migrate(branch: str):
    """
    Prisma 스키마 로드 후 해당 브랜치 디비에 반영
    @param branch: Git브랜치 -> Config에 DB접속정보가 브랜치별로 존재
    @return:
    """
    # Git 초기화 및 다운로드
    g_manager = GitManager(GitTarget.EXCEL)

    # 체크아웃 성공시에만 진행
    if not g_manager.checkout(branch):
        g_manager.destroy()
        return

    prisma = PrismaManager(branch, g_manager.PATH_FOR_WORKING)
    prisma.migrate(MigrateType.FORCE, branch)
    await data_to_db(g_manager)
    await tag_to_db(g_manager)
    g_manager.destroy()


async def data_to_db(g_manager: GitManager):
    d_manager = DataManager(g_manager.BRANCH, ConvertType.ALL, g_manager.PATH_FOR_WORKING)
    b_manager = DBManager(g_manager.BRANCH, g_manager.PATH_FOR_WORKING)
    await b_manager.restore_all_table(d_manager.get_jsonmap(ConvertType.SERVER))
    await b_manager.restore_all_table(d_manager.get_jsonmap(ConvertType.INFO))
    await b_manager.destory()


async def tag_to_db(g_manager: GitManager):
    b_manager = DBManager(g_manager.BRANCH, g_manager.PATH_FOR_WORKING)
    res_info = g_manager.get_client_resource_from_branch()
    if len(res_info.keys()) > 0:
        await b_manager.update_version_info(res_info['res_ver'], res_info['res_url'])
    await b_manager.destory()


async def test(branch: str):
    _path = '/Users/cglee/Dev/BackEnd/Python/fastapi-nano/app/libs/excel_to_db/export'
    from pathlib import Path
    _path = Path(_path)
    d_manager = DataManager(branch, ConvertType.MARKDOWN, _path)

    c_manager = CSharpManager(branch, 'tag', 'commit_id', _path)
    _obl = d_manager.get_markdown(ConvertType.MARKDOWN_PROTOCOL)
    c_manager.save_protocol(_obl)

    _obl = d_manager.get_markdown(ConvertType.MARKDOWN_ENUM)
    c_manager.save_server_enum(_obl)

    _obl = d_manager.get_markdown(ConvertType.MARKDOWN_ENTITY)
    c_manager.save_server_entity(_obl)

    # from pprint import pprint
    # pprint(_protocol)


if __name__ == '__main__' or __name__ == "decimal":
    branch = 'local'
    # logging.info(f"[{branch} 브랜치] 전체 Excel로드후 C# 스크립트 변환을 진행합니다.")
    # g_manager = GitManager(GitTarget.EXCEL)
    # if not g_manager.checkout(branch):
    #     g_manager.destroy()
    # check_excel(g_manager)
    # else:
    #     d_manager = DataManager(branch, ServerType.CLIENT, g_manager.PATH_FOR_WORKING)
    #     g_manager = GitManager(GitTarget.CLIENT)
    #     # 체크아웃 성공시에만 진행
    #     c_manager = CSharpManager(branch, 'commit_test', g_manager.PATH_FOR_WORKING)
    #     d_manager.get_enum_data()
    # For test
    # asyncio.run(excel_to_data_all('test'))
    # asyncio.run(excel_to_data_modified('test'))
    # asyncio.run(migrate('test'))
    # asyncio.run(excel_to_data_all_from_tag('v0.4.1_local'))

    # asyncio.run(migrate(branch))
    # asyncio.run(excel_to_data_all_from_branch(branch))

    asyncio.run(test(branch))

    pass
