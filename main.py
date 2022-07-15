import asyncio
import logging

# import cProfile

if __name__ == '__main__':
    from app import *

    _format = '[%(levelname)-7s] %(asctime)s: %(message)s '
    # _format_console = colorlog.ColoredFormatter(_format, "%m/%d/%Y %H:%M:%S ")
    logger = logging.getLogger()
    handler = logging.FileHandler('out.log', 'w', 'utf-8')
    # handler.setFormatter(_format_console)
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)

    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.INFO)
    # stream_handler.setFormatter(_format_console)
    logger.addHandler(stream_handler)


else:
    # from app import *
    from app.libs.excel_to_db.app import *


def sync_prisma(br: str):
    db_task = TaskManager(TaskType.SYNC_DB, branch=br)
    if db_task.start():
        g_manager = GitManager(GitTarget.EXCEL, br)
        if not g_manager.checkout():
            g_manager.destroy()
            db_task.done()
            return

        # 프리즈마 초기화
        prisma = PrismaManager(br, g_manager.PATH_FOR_WORKING)
        prisma.init_schema()
        prisma.destory()
        db_task.done()


async def update_table(br: str):
    db_task = TaskManager(TaskType.UPDATE_DATA_DB, branch=br)
    if db_task.start():
        # Git 초기화 및 다운로드
        g_manager = GitManager(GitTarget.EXCEL, branch=br)

        # 체크아웃 성공시에만 진행
        if not g_manager.checkout():
            g_manager.destroy()
            db_task.done()
            return
        prisma = PrismaManager(br, g_manager.PATH_FOR_WORKING)
        await data_to_db(g_manager, prisma)
        await tag_to_db(g_manager, prisma)
        await prisma.destory()
        g_manager.destroy()
        db_task.done()


async def excel_to_data_all_from_branch(br: str):
    """
    최신 Excel Git 브랜치를 복제한후 데이터 변환을 호출한다.
    @param br: Git브랜치
    """
    # Git 초기화 및 다운로드
    task = TaskManager(TaskType.EXCEL, br)
    if task.start():

        g_manager = GitManager(GitTarget.EXCEL, branch=br)
        # # 체크아웃 성공시에만 진행
        if not g_manager.checkout():
            g_manager.destroy()
            task.done()
            return
        excel_to_json_all(g_manager)

        await excel_to_server(g_manager)

        if g_manager.is_modified():
            g_manager.push()
        g_manager.destroy()

        task.done()


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
    if not webhook["head_commit"]:
        return

    g_manager = GitManager(GitTarget.EXCEL, webhook=webhook)
    tag = g_manager.load_tag_from_webhook(webhook)
    if tag:
        g_manager = GitManager(GitTarget.EXCEL, tag=tag)

    # # 체크아웃 성공시에만 진행
    if not webhook["head_commit"] or not g_manager.checkout():
        g_manager.destroy()
        return

    username = webhook["head_commit"]["committer"]["username"]
    message = webhook["head_commit"]["message"]
    compare_url = webhook["compare_url"]

    if g_manager.NEW_TAG != '':
        excel_to_data_taged(g_manager.NEW_TAG)
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

        markdown_to_script(g_manager.BRANCH)

        await excel_to_data_modified(g_manager.BRANCH)


async def excel_to_data_modified(br: str):
    excel_task = TaskManager(TaskType.EXCEL, branch=br)
    if excel_task.start():
        g_manager = GitManager(GitTarget.EXCEL, branch=br)
        if not g_manager.checkout():
            excel_task.done()
            return
        excel_to_json_modified(ConvertType.ALL, g_manager)
        await excel_to_server(g_manager)
        # 수정된 Json 파일이 있다면 Excel Git서버로 자동 커밋
        if g_manager.is_modified():
            g_manager.push()
        g_manager.destroy()
        excel_task.done()


def excel_to_data_taged(tag: str):
    db_task = TaskManager(TaskType.EXCEL_TAG, tag=tag)
    if db_task.start():
        g_manager = GitManager(GitTarget.EXCEL, tag=tag)
        if not g_manager.checkout():
            db_task.done()
            return
        g_manager.splog.info(f"새로운 태그[{g_manager.NEW_TAG}] 요청으로 클라이언트 태그 및 데이터 전송을 시작합니다.")

        gc_manager = GitManager(GitTarget.CLIENT, branch=g_manager.BRANCH)
        if not gc_manager.checkout():
            gc_manager.destroy()
            db_task.done()
            return

        send_data_to_client(g_manager, gc_manager)
        gc_manager.push_tag_to_client(tag)
        gc_manager.destroy()
        db_task.done()


def send_data_to_client(g_manager: GitManager, gc_manager: GitManager):
    if g_manager.BASE_TAG != '':
        d_manager = DataManager(g_manager.BRANCH, ConvertType.CLIENT, g_manager.PATH_FOR_WORKING)
        d_manager.save_json_all(gc_manager.PATH_FOR_WORKING.joinpath("data_all.json"))
        if gc_manager.is_modified():
            f_manager = FtpManager(g_manager.BRANCH, g_manager.COMMIT, g_manager.PATH_FOR_WORKING)
            f_manager.send(d_manager.get_json())
            g_manager.save_client_resource_to_branch(f_manager.get_resource_url())
            gc_manager.push()


async def excel_to_server(g_manager: GitManager):
    gc_manager = GitManager(GitTarget.CLIENT, branch=g_manager.BRANCH)
    if not gc_manager.checkout():
        gc_manager.destroy()
        return

    if g_manager.is_modified_excel_enum():
        send_enum_to_client(g_manager, gc_manager)
        if gc_manager.is_modified():
            g_manager.splog.add_info('Enum 데이터에 변동 사항이 있습니다. 서버 및 클라 개발을 진행 해 주세요.', 0)
            g_manager.splog.send_developer_all()
            gc_manager.push()

    if g_manager.is_modified_excel_column():
        send_data_to_client(g_manager, gc_manager)
        g_manager.splog.add_info('기획 데이터의 컬럼에 변동 사항이 있습니다. 개발후 DB 마이그레이션을 진행 해 주세요.', 0)
        g_manager.splog.send_developer_all()
        g_manager.splog.send_designer('기획 데이터의 컬럼에 변동 사항이 있습니다. 개발자가 확인 후 다음 프로세스로 진행됩니다.')

    else:
        g_manager.splog.info(f'EXCEL파일 데이터 수정으로 인한 데이터 업데이트를 진행합니다.')
        send_data_to_client(g_manager, gc_manager)
        prisma = PrismaManager(g_manager.BRANCH, g_manager.PATH_FOR_WORKING)
        await data_to_db(g_manager, prisma)
        await tag_to_db(g_manager, prisma)
        await prisma.destory()


async def migrate(br: str):
    # Git 초기화 및 다운로드
    db_task = TaskManager(TaskType.MIGRATE_DB, branch=br)
    if db_task.start():
        g_manager = GitManager(GitTarget.EXCEL, branch=br)

        # 체크아웃 성공시에만 진행
        if not g_manager.checkout():
            g_manager.destroy()
            db_task.done()
            return

        excel_to_schema(g_manager)
        if g_manager.is_modified():
            g_manager.push()

        prisma = PrismaManager(br, g_manager.PATH_FOR_WORKING)
        prisma.migrate(MigrateType.FORCE, br)
        g_manager.destroy()
        db_task.done()

        await update_table(br)


async def data_to_db(g_manager: GitManager, p_manager: PrismaManager):
    d_manager = DataManager(g_manager.BRANCH, ConvertType.SERVER, g_manager.PATH_FOR_WORKING)
    await p_manager.restore_all_table(d_manager.get_jsonmap(ConvertType.SERVER))


async def tag_to_db(g_manager: GitManager, p_manager: PrismaManager):
    res_info = g_manager.get_client_resource_from_branch()
    if len(res_info.keys()) > 0:
        await p_manager.update_version_info(res_info['res_ver'], res_info['res_url'])


def excel_to_json_all(g_manager: GitManager):
    """전체 Excel을 추출후 Json변환
        """

    g_manager.splog.info("전체 Excel로드후 Json변환을 진행합니다.")

    # 전체 Excel로드후 Json변환
    d_manager = DataManager(g_manager.BRANCH, ConvertType.ALL, g_manager.PATH_FOR_WORKING)
    d_manager.delete_json_all()
    excel_paths = d_manager.get_excelpath_all()
    d_manager.excel_to_json(excel_paths)


def excel_to_json_modified(convert_type: ConvertType, g_manager: GitManager):
    """
    변경된 Excel만 추출후 Json변환
    @param convert_type: 기획데이터:server Info데이터:info 클라이언트데이터:client
    @param g_manager: GitManager
    @return:
    """
    g_manager.splog.info(f"변경된 Excel로드후 Json변환을 진행합니다. [데이터 타입 : {convert_type.name}]")

    d_manager = DataManager(g_manager.BRANCH, convert_type, g_manager.PATH_FOR_WORKING)
    modified_excel = g_manager.get_modified_excel(5)
    # Excel로드후 Json변환
    d_manager.delete_path(g_manager.get_deleted_json())
    d_manager.excel_to_json(modified_excel)
    d_manager.check_excel_for_relation(modified_excel)


def send_entity_to_client(g_manager: GitManager, gc_manager: GitManager):
    g_manager.splog.info("전체 Excel로드후 C# 스크립트 변환을 진행합니다.")

    d_manager = DataManager(g_manager.BRANCH, ConvertType.CLIENT, g_manager.PATH_FOR_WORKING)
    c_manager = CSharpManager(g_manager.BRANCH, g_manager.COMMIT, gc_manager.PATH_FOR_WORKING)
    c_manager.save_entity(d_manager.get_schema_all())
    c_manager.save_enum(d_manager.get_enum_data())
    d_manager.save_json_all(gc_manager.PATH_FOR_WORKING.joinpath("data_all.json"))


def send_enum_to_client(g_manager: GitManager, gc_manager: GitManager):
    g_manager.splog.info("전체 Excel로드후 Enum 스크립트 변환을 진행합니다.")
    d_manager = DataManager(g_manager.BRANCH, ConvertType.ALL, g_manager.PATH_FOR_WORKING)
    c_manager = CSharpManager(g_manager.BRANCH, g_manager.COMMIT, gc_manager.PATH_FOR_WORKING)
    c_manager.save_enum(d_manager.get_enum_data())


def excel_to_schema(g_manager: GitManager):
    """
    전체 Excel추출후 아래 데이터 타입만 Prisma 스키마변환
    @param g_manager: GitManager
    """
    g_manager.splog.info("전체 Excel로드후 Prisma변환을 진행합니다.")

    # 프리즈마 초기화
    p_manager = PrismaManager(g_manager.BRANCH, g_manager.PATH_FOR_WORKING)
    d_manager = DataManager(g_manager.BRANCH, ConvertType.SERVER, g_manager.PATH_FOR_WORKING)
    data_table = d_manager.get_schema_all(ConvertType.SERVER)
    p_manager.save(data_table, DBType.DATA_DB)


def markdown_to_script(br: str):
    g_manager = GitManager(GitTarget.EXCEL, branch=br)
    gc_manager = GitManager(GitTarget.CLIENT, branch=br)
    if not g_manager.checkout() or not gc_manager.checkout():
        return
    task = TaskManager(TaskType.MARKDOWN, branch=br)
    g_manager.splog.info("전체 Markdown 로드 후 C# Script변환을 진행합니다.")
    d_manager = DataManager(br, ConvertType.MARKDOWN, g_manager.PATH_FOR_WORKING)
    c_manager = CSharpManager(br, g_manager.COMMIT, gc_manager.PATH_FOR_WORKING)
    try:
        _obl = d_manager.get_markdown(ConvertType.MARKDOWN_PROTOCOL)
        c_manager.save_protocol(_obl)
        _obl = d_manager.get_markdown(ConvertType.MARKDOWN_ENUM)
        c_manager.save_server_enum(_obl)
        _obl = d_manager.get_markdown(ConvertType.MARKDOWN_ENTITY)
        c_manager.save_server_entity(_obl)
        if gc_manager.is_modified():
            gc_manager.push()
            g_manager.splog.info("Markdown C# Script 변환을 완료합니다.")
        else:
            g_manager.splog.info("Markdown C# Script 변경사항이 없습니다.")

    except Exception as e:
        g_manager.splog.error(f"MarkdownC# Script변환 에러: {str(e)}")
    finally:
        task.done()


def check_to_excel(br: str):
    db_task = TaskManager(TaskType.EXCEL_CHECK, branch=br)
    if db_task.start():
        g_manager = GitManager(GitTarget.EXCEL, branch=br)
        if not g_manager.checkout():
            return
        g_manager.splog.info("전체 Excel 로드 후 릴레이션 체크를 합니다.")
        d_manager = DataManager(br, ConvertType.MARKDOWN, g_manager.PATH_FOR_WORKING)
        d_manager.check_excel_for_relation(d_manager.get_excelpath_all())
        db_task.done()


def check():
    task = TaskManager(TaskType.SCHEDULER)
    task.status()


async def scheduler():
    await asyncio.sleep(1)
    job_task = TaskManager(TaskType.SCHEDULER)
    if not job_task.load_task():
        job_task.splog.info("대기열에 작업이 없습니다.")
        return
    task = job_task.pop_task()
    if task is None:
        return
    task_type = next(iter(task))
    _task_val = next(iter(task.values()))
    task_branch = next(iter(_task_val))
    task_tag = list(_task_val.values())[0]

    if task_type == TaskType.EXCEL:
        if task_branch is None:
            return
        await excel_to_data_modified(task_branch)
        return

    if task_type == TaskType.EXCEL_TAG:
        if task_tag is None:
            return
        excel_to_data_taged(task_tag)
        return

    if task_type == TaskType.MIGRATE_DB:
        await migrate(task_branch)

    if task_type == TaskType.SYNC_DB:
        sync_prisma(task_branch)

    if task_type == TaskType.EXCEL_CHECK:
        check_to_excel(task_branch)


async def test():
    webhook = {
        "ref": "refs/heads/test_cg",
        "before": "1dfafc5434b2728a8c7eb768e91a4fbc5333732e",
        "after": "fbb72920444da56065c5244bf746e6b343078c76",
        "compare_url": "http://main.sp.snowpipe.net:3000/SPTeam/data-for-designer/compare/1dfafc5434b2728a8c7eb768e91a4fbc5333732e...fbb72920444da56065c5244bf746e6b343078c76",
        "commits": [
            {
                "id": "fbb72920444da56065c5244bf746e6b343078c76",
                "message": "삭제 'export/out.log'\n",
                "url": "http://main.sp.snowpipe.net:3000/SPTeam/data-for-designer/commit/fbb72920444da56065c5244bf746e6b343078c76",
                "author": {
                    "name": "[서버] 이철길",
                    "email": "cglee@snowpipe.co.kr",
                    "username": "CGLee"
                },
                "committer": {
                    "name": "[서버] 이철길",
                    "email": "cglee@snowpipe.co.kr",
                    "username": "CGLee"
                },
                "verification": None,
                "timestamp": "2022-07-13T12:55:52+09:00",
                "added": [],
                "removed": [
                    "export/out.log"
                ],
                "modified": []
            }
        ],
        "head_commit": {
            "id": "fbb72920444da56065c5244bf746e6b343078c76",
            "message": "삭제 'export/out.log'\n",
            "url": "http://main.sp.snowpipe.net:3000/SPTeam/data-for-designer/commit/fbb72920444da56065c5244bf746e6b343078c76",
            "author": {
                "name": "[서버] 이철길",
                "email": "cglee@snowpipe.co.kr",
                "username": "CGLee"
            },
            "committer": {
                "name": "[서버] 이철길",
                "email": "cglee@snowpipe.co.kr",
                "username": "CGLee"
            },
            "verification": None,
            "timestamp": "2022-07-13T12:55:52+09:00",
            "added": [],
            "removed": [
                "export/out.log"
            ],
            "modified": []
        },
    }

    await excel_to_data_from_webhook(webhook)

    # pprint(g_manager.get_deleted_json())
    # pprint(g_manager.get_modified_excel())
    # markdown_to_script(g_manager, gc_manager)
    # task = TaskManager(TaskType.EXCEL, g_manager)
    # task.init(g_manager)
    # gc_manager = GitManager(GitTarget.CLIENT, branch)
    # if not gc_manager.checkout():
    #     gc_manager.destroy()
    #     return
    # markdown_to_script(g_manager, gc_manager)
    # gc_manager.push()
    # await migrate(branch)
    # print(task.pop_task())


if __name__ == '__main__':
    branch = 'test_cg'

    # logging.info(f"[{branch} 브랜치] 전체 Excel로드후 C# 스크립트 변환을 진행합니다.")
    # asyncio.run(migrate(branch))

    excel_to_data_taged('v0.6.1_local')
    # asyncio.run(excel_to_data_all_from_branch(branch))
    # asyncio.run(excel_to_data_modified(branch))
    # asyncio.run(migrate(branch))
    # asyncio.run(update_table(branch, ConvertType.SERVER))
    # asyncio.run(test(branch))
    # asyncio.run(scheduler())
    # sync_prisma(branch)
    # markdown_to_script(branch)
    # asyncio.run(update_table(branch))
    # check_to_excel(branch)
    # asyncio.run(excel_to_data_all_from_branch(branch))
    pass
