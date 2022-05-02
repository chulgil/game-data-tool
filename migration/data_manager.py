import os
import json
import logging
import shutil
from dateutil import parser
import pandas as pd
from pathlib import Path
from pandas import DataFrame
import warnings
from enum import Enum, auto


class DataType(Enum):
    ALL = auto()
    SERVER = auto()
    CLIENT = auto()
    INFO = auto()


class DataManager:

    def __init__(self, data_type: DataType):
        self.DATA_TYPE = data_type
        self.ROOT_DIR = Path(__file__).parent.parent
        self.PATH_FOR_CONFIG = self.ROOT_DIR.joinpath('config.json')
        # Config 파일 설정
        with open(self.PATH_FOR_CONFIG, 'r') as f:
            config = json.load(f)
        self._set_config(config)
        self._set_folder()
        warnings.filterwarnings('ignore', category=UserWarning, module='openpyxl')

    def _set_config(self, config):
        self.PATH_FOR_ROOT = self.ROOT_DIR.joinpath(config['DEFAULT']['ROOT_DATA_DIR'])
        self.PATH_FOR_EXCEL = self.PATH_FOR_ROOT.joinpath(config['DEFAULT']['EXCEL_DIR'])
        self.PATH_FOR_JSON = self.PATH_FOR_ROOT.joinpath("json")
        self.PATH_FOR_DATA = self.PATH_FOR_JSON.joinpath("data")
        self.PATH_FOR_INFO = self.PATH_FOR_JSON.joinpath("info")
        self.PATH_FOR_CLIENT = self.PATH_FOR_JSON.joinpath("client")

    def _set_folder(self):
        # JSON 폴더 초기화
        if Path(self.PATH_FOR_JSON).is_dir():
            shutil.rmtree(self.PATH_FOR_JSON)
        # JSON 폴더 생성
        if self.DATA_TYPE == DataType.ALL or self.DATA_TYPE == DataType.SERVER:
            os.makedirs(self.PATH_FOR_DATA)
        if self.DATA_TYPE == DataType.ALL or self.DATA_TYPE == DataType.INFO:
            os.makedirs(self.PATH_FOR_INFO)
        if self.DATA_TYPE == DataType.ALL or self.DATA_TYPE == DataType.CLIENT:
            os.makedirs(self.PATH_FOR_CLIENT)

    def _get_filtered(self, df: DataFrame, targets: list) -> DataFrame:
        # 행의 개수가 2보다 적으면 무시
        if df.shape[0] < 2:
            return df

        # 데이터 프레임 1행 추출
        mask_df = df.iloc[0]

        # 필터링할 컬럼값을 추출
        filtered = mask_df[mask_df.isin(targets)].keys()
        # 적용타입행과 필드타입행을 제외한 2행부터 JSON추출
        data_df = df[filtered].iloc[2:]
        # 정의된 DB형식으로 데이터 포멧
        self._translate_asdb(data_df, df)
        return data_df

    @staticmethod
    def _save_json(df: DataFrame, save_path: Path, file_name: str):
        # 행의 개수가 0이면 무시
        if df.shape[1] == 0:
            return

        # Data frame을 JSON으로 변환
        json_data = df.to_json(orient='records')
        json_list = json.loads(json_data)

        # 지정한 경로로 Json파일 저장
        save_path = save_path.joinpath(file_name + ".json")
        with open(save_path, "w", encoding='utf-8') as f:
            json.dump(json_list, f, ensure_ascii=False, indent=4, sort_keys=True, separators=(',', ': '))
        logging.info(f"Json 파일 저장 성공 : {save_path.name}")

    # --------------------------------------------------------------
    # EXCEL의 데이터가 다음과 같을때 1번째 행은 디비속성 이다.
    # 디비속성 값으로 데이터를 포멧팅한다.
    # --------------------------------------------------------------
    # id     | name | reg_dt | reg_dt
    # 0 : SERVER | SERVER | CLIENT |  SERVER
    # 1 : int | string | datetime |  datetime <-- 디비속성
    # 2 :  | test |  2022.04.09 | 2021-03-09T00:00:00
    # --------------------------------------------------------------
    # Ref :
    # https://pandas.pydata.org/docs/reference/api/
    def _translate_asdb(self, data_df: DataFrame, filter_df: DataFrame):
        for col in data_df.columns:
            for i in data_df.index:
                field_type = filter_df.loc[1][col]
                field_value = filter_df.loc[i][col]
                data_df.loc[i][col] = self._value_astype(field_type, field_value)

    def _value_astype(self, column_type: str, column_value: any):
        try:
            if column_type == "string":
                return str(column_value)
            elif column_type == "float":
                return float(column_value)
            elif column_type == "int":
                return int(column_value)
            elif column_type == "long":
                return int(column_value)
            elif column_type == "datetime":
                return self.iso8601(column_value)
            else:
                return str(column_value)
        except Exception as e:
            logging.warning(str(f"Column[{column_value}]" + str(e)))
            return str(e)

    @staticmethod
    def iso8601(date_text: str) -> str:
        try:
            date = parser.parse(str(date_text))
            return date.astimezone().isoformat()
        except Exception as e:
            logging.warning(str(e))
            return str(e)

    def excel_to_json(self):
        # Excel파일 가져오기
        files = list(Path(self.PATH_FOR_EXCEL).rglob(r"*.xls*"))
        for excel in files:
            try:
                # 첫번째 시트를 JSON 타겟으로 설정
                df = pd.read_excel(excel, sheet_name=0)
                if self.DATA_TYPE == DataType.ALL or self.DATA_TYPE == DataType.SERVER:  # 파일 이름으로 JSON 파일 저장 : DATA
                    self._save_json(self._get_filtered(df, ['ALL', 'SERVER']), self.PATH_FOR_DATA, excel.stem)
                if self.DATA_TYPE == DataType.ALL or self.DATA_TYPE == DataType.INFO:  # 파일 이름으로 JSON 파일 저장 : INFO
                    self._save_json(self._get_filtered(df, ['INFO']), self.PATH_FOR_INFO, excel.stem)
                if self.DATA_TYPE == DataType.ALL or self.DATA_TYPE == DataType.CLIENT:  # 파일 이름으로 JSON 파일 저장 : CLIENT
                    self._save_json(self._get_filtered(df, ['ALL', 'CLIENT']), self.PATH_FOR_CLIENT, excel.stem)
            except Exception:
                logging.exception(excel)
