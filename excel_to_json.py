import logging
import json
import os

import pandas as pd
from pathlib import Path

PATH_FOR_DATA = "./data-for-designer"
PATH_FOR_EXCEL = PATH_FOR_DATA + "/excel/"
PATH_FOR_JSON = PATH_FOR_DATA + "/json/"
PATH_FOR_SERVER = PATH_FOR_JSON + "server/"
PATH_FOR_CLIENT = PATH_FOR_JSON + "client/"


# Excel파일 가져오기
files = list(Path(PATH_FOR_EXCEL).glob(r"*.xls*"))

# JSON 폴더 생성
if not os.path.exists(PATH_FOR_SERVER):
    os.mkdir(PATH_FOR_SERVER)
if not os.path.exists(PATH_FOR_CLIENT):
    os.mkdir(PATH_FOR_CLIENT)

os.remove(PATH_FOR_SERVER)
os.remove(PATH_FOR_CLIENT)

# JSON 폴더 초기화

for excel in files:
    try:
        # 첫번째 시트를 JSON 타겟으로 설정
        df = pd.read_excel(excel, sheet_name=0)

        # 행의 개수가 2보다 적으면 무시
        if df.shape[0] < 2:
            continue

        # 데이터 프레임 1행 추출
        mask_df = df.iloc[0]

        # 서버에 적용할 컬럼값을 추출
        filter_s = mask_df[mask_df.isin(['ALL', 'SERVER'])].keys()

        # 클라이언트에 적용할 컬럼값을 추출
        filter_c = mask_df[mask_df.isin(['ALL', 'CLIENT'])].keys()

        # 적용타입행과 필드타입행을 제외한 2행부터 JSON추출
        df_server = df[filter_s].iloc[2:]
        df_client = df[filter_c].iloc[2:]


        # 파일 이름으로 JSON 파일 저장 : SERVER
        json_data = df_server.to_json(orient='records')
        json_str = json.loads(json_data)
        with open(PATH_FOR_SERVER + excel.stem + ".json", "w", encoding='utf-8') as f:
            json.dump(json_str, f, ensure_ascii=False, indent=4, sort_keys=True, separators=(',', ': '))

        # 파일 이름으로 JSON 파일 저장 : CLIENT
        json_data = df_client.to_json(orient='records')
        json_str = json.loads(json_data)
        with open(PATH_FOR_CLIENT + excel.stem + ".json", "w", encoding='utf-8') as f:
            json.dump(json_str, f, ensure_ascii=False, indent=4, sort_keys=True, separators=(',', ': '))

    except Exception as e:
        logging.exception(excel)
