import os
import re
import json
import logging
import shutil
import pandas as pd
from pathlib import Path
from pandas import DataFrame


class DataManager:
    PATH_FOR_ROOT = None
    PATH_FOR_EXCEL = None
    PATH_FOR_JSON = None
    PATH_FOR_DATA = None
    PATH_FOR_INFO = None
    PATH_FOR_CLIENT = None

    def __init__(self):
        # Config 파일 설정
        with open('config.json', 'r') as f:
            config = json.load(f)
        self._set_config(config)
        self._set_folder()

    @classmethod
    def _set_config(cls, config):
        cls.PATH_FOR_ROOT = config['DEFAULT']['ROOT_DATA_DIR']
        cls.PATH_FOR_EXCEL = cls.PATH_FOR_ROOT + config['DEFAULT']['EXCEL_DIR']
        cls.PATH_FOR_JSON = cls.PATH_FOR_ROOT + "/json"
        cls.PATH_FOR_DATA = cls.PATH_FOR_JSON + "/data"
        cls.PATH_FOR_INFO = cls.PATH_FOR_JSON + "/info"
        cls.PATH_FOR_CLIENT = cls.PATH_FOR_JSON + "/client"

    @classmethod
    def _set_folder(cls):
        # JSON 폴더 초기화
        shutil.rmtree(cls.PATH_FOR_JSON)
        # JSON 폴더 생성
        os.makedirs(cls.PATH_FOR_DATA)
        os.makedirs(cls.PATH_FOR_INFO)
        os.makedirs(cls.PATH_FOR_CLIENT)

    @classmethod
    def _get_filtered(cls, df: DataFrame, targets: list) -> DataFrame:
        # 행의 개수가 2보다 적으면 무시
        if df.shape[0] < 2:
            return df
        # 데이터 프레임 1행 추출
        mask_df = df.iloc[0]
        # 필터링할 컬럼값을 추출
        filtered = mask_df[mask_df.isin(targets)].keys()
        # 적용타입행과 필드타입행을 제외한 2행부터 JSON추출
        return df[filtered].iloc[2:]

    # EXCEL의 데이터가 다음과 같을때 필드 명 중복이 있을 경우
    # DATAFRAME에 필드명이 reg_dt.1 로 들어오므로 .1을 자른다.
    # ------------------------------------------------
    # id     | name | reg_dt | reg_dt
    # SERVER | SERVER | DATE |  SERVER
    # 1  | test |  2022.04.09 | 2021-03-09T00:00:00
    # ------------------------------------------------
    @classmethod
    def _translate_json(cls, data_list: list):
        match_str = r'\.\w'
        for data in data_list:
            str_match = [_ for _ in data.keys() if re.search(match_str, _)]
            for key in str_match:
                new_key = re.sub(match_str, '', key)
                data[new_key] = data.pop(key)

    @classmethod
    def _save_json(cls, df: DataFrame, save_path: str, file_name: str):
        # 행의 개수가 0이면 무시
        if df.shape[1] == 0:
            return

        # Data frame을 JSON으로 변환
        json_data = df.to_json(orient='records')
        json_list = json.loads(json_data)
        cls._translate_json(json_list)

        # 지정한 경로로 Json파일 저장
        save_path = save_path + "/" + file_name + ".json"
        with open(save_path, "w", encoding='utf-8') as f:
            json.dump(json_list, f, ensure_ascii=False, indent=4, sort_keys=True, separators=(',', ': '))
        logging.info("Json 파일 저장 성공 : " + save_path)

    @classmethod
    def excel_to_json(cls):
        # Excel파일 가져오기
        files = list(Path(cls.PATH_FOR_EXCEL).rglob(r"*.xls*"))
        for excel in files:
            try:
                # 첫번째 시트를 JSON 타겟으로 설정
                df = pd.read_excel(excel, sheet_name=0)
                # 파일 이름으로 JSON 파일 저장 : DATA
                cls._save_json(cls._get_filtered(df, ['ALL', 'SERVER']), cls.PATH_FOR_DATA, excel.stem)
                # 파일 이름으로 JSON 파일 저장 : INFO
                cls._save_json(cls._get_filtered(df, ['INFO']), cls.PATH_FOR_INFO, excel.stem)
                # 파일 이름으로 JSON 파일 저장 : CLIENT
                cls._save_json(cls._get_filtered(df, ['ALL', 'CLIENT']), cls.PATH_FOR_CLIENT, excel.stem)
            except Exception:
                logging.exception(excel)
