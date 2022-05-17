import os
import json
import logging
import shutil
from re import match
from typing import Optional

import yaml
from dateutil import parser
import pandas as pd
from pathlib import Path
from pandas import DataFrame
import warnings
from enum import Enum, auto

import numpy as np
import pandas


class DataType(Enum):
    ALL = auto()
    SERVER = auto()
    CLIENT = auto()
    INFO = auto()

    @classmethod
    def value_of(cls, value: str):

        for k, v in cls.__members__.items():
            if k == value.upper():
                return v
        else:
            return DataType.ALL


class DataManager:

    def __init__(self, data_type: DataType):
        self.DATA_TYPE = data_type
        self.ROOT_DIR = Path(__file__).parent.parent
        self.PATH_FOR_CONFIG = self.ROOT_DIR.joinpath('config.yaml')
        # Config 파일 설정
        with open(self.PATH_FOR_CONFIG, 'r') as f:
            config = yaml.safe_load(f)
        self._set_config(config)
        self._set_folder()
        pandas.set_option('display.max_column', 10)  # print()에서 전체항목 표시
        warnings.filterwarnings('ignore', category=UserWarning, module='openpyxl')

    def _set_config(self, config):
        self.PATH_FOR_ROOT = self.ROOT_DIR.joinpath(config['DEFAULT']['ROOT_DATA_DIR'])
        self.PATH_FOR_EXCEL = self.PATH_FOR_ROOT.joinpath(config['EXCEL']['EXCEL_DIR'])
        self.ERROR_FOR_EXCEL = config['EXCEL']['ERROR_TEXT']
        self.PATH_FOR_JSON = self.PATH_FOR_ROOT.joinpath("json")
        self.PATH_FOR_DATA = self.PATH_FOR_JSON.joinpath("data")
        self.PATH_FOR_INFO = self.PATH_FOR_JSON.joinpath("info")
        self.PATH_FOR_CLIENT = self.PATH_FOR_JSON.joinpath("client")
        self.ROW_FOR_DATA_HEADER = 0
        self.ROW_FOR_DATA_TYPE = 1
        self.ROW_FOR_DATA_OPTION = 2

    def _set_folder(self):
        # JSON 폴더 초기화
        # if Path(self.PATH_FOR_JSON).is_dir():
        #     shutil.rmtree(self.PATH_FOR_JSON)
        # JSON 폴더 생성
        if self.DATA_TYPE == DataType.ALL or self.DATA_TYPE == DataType.SERVER:
            if not Path(self.PATH_FOR_DATA).is_dir():
                os.makedirs(self.PATH_FOR_DATA)
        if self.DATA_TYPE == DataType.ALL or self.DATA_TYPE == DataType.INFO:
            if not Path(self.PATH_FOR_INFO).is_dir():
                os.makedirs(self.PATH_FOR_INFO)
        if self.DATA_TYPE == DataType.ALL or self.DATA_TYPE == DataType.CLIENT:
            if not Path(self.PATH_FOR_CLIENT).is_dir():
                os.makedirs(self.PATH_FOR_CLIENT)

    def _get_filtered_data(self, df: DataFrame, targets: list) -> DataFrame:

        df = self._get_filtered_column(df, targets)
        option_df = self._get_data_option(df)

        if option_df is not None:
            df = self._del_auto_field(df)
            # 적용타입 필드타입 스키마타입 행을 제외한 3행부터 JSON추출
            data_df = df.iloc[self.ROW_FOR_DATA_OPTION + 1:]
        else:
            # 적용타입행과 필드타입행을 제외한 2행부터 JSON추출
            data_df = df.iloc[self.ROW_FOR_DATA_TYPE + 1:]
        # 정의된 DB형식으로 데이터 포멧
        self._translate_asdb(data_df, df.iloc[1], option_df)
        return data_df

    def _del_auto_field(self, df: DataFrame) -> DataFrame:
        """
        엑셀 데이터에서 @auto필드가 있는 행을 삭제한다.
        id table_id             table_sub_id    item_rate
        1   long      int        float
        2  @auto      @id  @ref(sub_table_info.id)  @default(0)
        """
        for col in self._get_auto_field(df):
            del df[col]
        return df

    def _get_auto_field(self, df: DataFrame) -> list:
        res = []
        for col in df.columns:
            if match(r'@auto', df[col][self.ROW_FOR_DATA_OPTION]):
                res.append(col)
        return res

    def _get_data_option(self, df: DataFrame) -> Optional[DataFrame]:
        if self._is_data_option_row(df):
            return df.iloc[self.ROW_FOR_DATA_OPTION]
        return None

    def get_invalid_option_row(self, df: DataFrame) -> dict:
        res = {}
        for col in df.columns:
            value = df[col][self.ROW_FOR_DATA_OPTION]
            if match(r'^\w+', value):
                res[col] = value
        return res

    def _is_data_option_row(self, df: DataFrame) -> bool:
        """엑셀 데이터에서 2번째 행에 스키마 정보가 포함되어 있는지 확인한다.
            id table_id             table_sub_id    item_rate
            1   long      int                      int        float
            2  @auto      @id  @ref(sub_table_info.id)  @default(0)
        """
        try:
            filtered = list(filter(lambda v: match(r'^@\D+$', v), df.iloc[self.ROW_FOR_DATA_OPTION].values))
            if len(filtered) > 0:
                return True
        except Exception as e:
            return False
        return False

    def _get_filtered_column(self, df: DataFrame, targets: list) -> DataFrame:

        # 데이터 프레임 1행 추출
        mask_df = df.iloc[self.ROW_FOR_DATA_HEADER]

        # 필터링할 컬럼값을 추출
        filtered = mask_df[mask_df.isin(targets)].keys()
        return df[filtered]

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
            json.dump(json_list, f, ensure_ascii=False, indent=4, separators=(',', ': '))

        # 파일 경로로 부터 / Sever / file.csv 를 잘라온다.
        paths = str(save_path).split('/')
        name = paths.pop()
        path = paths.pop()
        logging.info(f"Json 파일 저장 성공 : {path}/{name}")

    # --------------------------------------------------------------
    # EXCEL의 데이터가 다음과 같을때 1번째 행은 디비속성 이다.
    # 디비속성 값으로 데이터를 포멧팅한다_save_json.
    # --------------------------------------------------------------
    # id     | name | reg_dt | reg_dt
    # 0 : SERVER | SERVER | CLIENT |  SERVER
    # 1 : int | string | datetime |  datetime <-- 디비속성
    # 2 :  | test |  2022.04.09 | 2021-03-09T00:00:00
    # --------------------------------------------------------------
    # Ref :
    # https://pandas.pydata.org/docs/reference/api/
    def _translate_asdb(self, data_df: DataFrame, header_df: DataFrame, option_df: DataFrame):
        for col in data_df.columns:
            for i in data_df.index:
                field_type = header_df[col]
                field_value = data_df[col][i]
                schema_type = ''
                if option_df is not None:
                    schema_type = option_df[col]
                data_df.loc[i][col] = self._value_astype(field_type, field_value, schema_type)

    def _value_astype(self, column_type: str, column_value: str, schema_type: str):
        """
        엑셀에서 정의한 값을 타입별 기본 값으로 변환
        @param column_type: 엑셀에서 정의한 데이터 타입
        @param column_value: 엑셀에서 정의한 데이터 값
        @return: 변환된 문자열
        ref :
        https://blog.finxter.com/how-to-convert-a-string-to-a-double-in-python/
        """
        try:
            column_type = column_type.lower()
            if column_value == '':
                default = match(r'@default\(?(\S+)\)', schema_type)
                if default:
                    column_value = default.group(1)
                    column_value = column_value.replace('\'', '')
                    column_value = column_value.replace('"', '')

            if self._is_null_numeral(column_type, column_value):
                if not match(r'@null', schema_type):  # not null type
                    if column_value == '':
                        raise Exception('Not allowed space')

            if column_value == '':
                return None

            if column_type == "string":
                return str(column_value)
            elif column_type == "float" or column_type == "double":
                return float(column_value)
            elif column_type == "int":
                return int(column_value)
            elif column_type == "bool" or column_type == "boolean":
                v = column_value
                if v == 0 or v == '0' or v == 'false' or v == 'False' or v is False:
                    return False
                elif v == 1 or v == '1' or v == 'true' or v == 'True' or v is True:
                    return True
                else:
                    raise Exception('Please input bool type')
            elif column_type == "long" or column_type == "bicint":
                return int(column_value)
            elif column_type == "datetime":
                return self.iso8601(column_value)
            else:
                return str(column_value)
        except Exception as e:
            msg = f'{self.ERROR_FOR_EXCEL} {str(e)}'
            logging.warning(str(f"Column[{column_value}] {msg}"))
            return msg

    @staticmethod
    def _is_null_numeral(column_type: str, column_value: str) -> bool:
        """
        데이터 타입이 숫자 타입이고 값이 null인 경우 True 반환
        """
        if (column_type == "float" or column_type == "int" or column_type == "long") \
                and column_value == '':
            return True
        return False

    def iso8601(self, date_text: str) -> str:
        try:
            date = parser.parse(str(date_text))
            return date.astimezone().isoformat()
        except Exception as e:
            msg = f'{self.ERROR_FOR_EXCEL} {str(e)}'
            logging.warning(msg)
            return msg

    def excel_to_json(self, excel_list: list):
        # Excel파일 가져오기
        for excel in excel_list:
            try:
                _path = Path(self.PATH_FOR_ROOT).joinpath(excel)
                # 첫번째 시트를 JSON 타겟으로 설정
                df = pd.read_excel(_path, sheet_name=0)
                # 모든 데이터의 null값을 초기화
                df.replace(to_replace=np.NaN, value='', inplace=True)
                if self.DATA_TYPE == DataType.ALL or self.DATA_TYPE == DataType.SERVER:  # 파일 이름으로 JSON 파일 저장 : DATA
                    self._save_json(self._get_filtered_data(df, ['ALL', 'SERVER']), self.PATH_FOR_DATA, _path.stem)
                if self.DATA_TYPE == DataType.ALL or self.DATA_TYPE == DataType.INFO:  # 파일 이름으로 JSON 파일 저장 : INFO
                    self._save_json(self._get_filtered_data(df, ['INFO']), self.PATH_FOR_INFO, _path.stem)
                if self.DATA_TYPE == DataType.ALL or self.DATA_TYPE == DataType.CLIENT:  # 파일 이름으로 JSON 파일 저장 : CLIENT
                    self._save_json(self._get_filtered_data(df, ['ALL', 'CLIENT']), self.PATH_FOR_CLIENT, _path.stem)
            except Exception:
                logging.exception(excel)

    def get_excelpath_all(self) -> list:
        return list(Path(self.PATH_FOR_EXCEL).rglob(r"*.xls*"))

    def get_jsonpath_all(self) -> list:
        return list(Path(self.PATH_FOR_JSON).rglob(r"*.json"))

    def _get_jsonpath_info(self) -> list:
        return list(Path(self.PATH_FOR_JSON).rglob(r"*info/*.json"))

    def _get_jsonpath_server(self) -> list:
        return list(Path(self.PATH_FOR_JSON).rglob(r"*data/*.json"))

    def get_jsonmap(self, json_paths=None):
        """
        서버정보별로 json을 가져온다.
        @return: 딕셔너리 값으로 리턴 { key (테이블명) : value (JsonData) }
        """
        res = {}
        json_path = ''
        file_name = ''
        if json_paths is None:
            json_paths = []
        try:
            if self.DATA_TYPE == DataType.SERVER:
                json_path = self._get_jsonpath_server()
            if self.DATA_TYPE == DataType.ALL:
                json_path = self.get_jsonpath_all()
            if self.DATA_TYPE == DataType.INFO:
                json_path = self._get_jsonpath_info()

            for _path in json_path:
                file_name = _path.stem
                with open(_path, 'r') as f:
                    res[file_name] = json.load(f)
        except Exception as e:
            logging.warning(f'Json 데이터 {file_name} Error :\r\n {str(e)}')
        return res

    def get_excel(self, name: str) -> list:
        return list(Path(self.PATH_FOR_EXCEL).rglob(f"{name}.xls*"))

    def delete_json_as_excel(self):
        """Excel리스트에 없는 Json파일 삭제
        """
        for _json in self.get_jsonpath_all():
            exist = self.get_excel(_json.stem)
            if len(exist) == 0:
                _json.unlink(True)

    def get_table_info(self, json_path: str) -> dict:
        res = {}
        _path = self.PATH_FOR_ROOT.joinpath(json_path)
        if not _path.exists():
            return res

        # 첫번째 시트를 JSON 타겟으로 설정
        df = pd.read_excel(_path, sheet_name=0)
        df.replace(to_replace=np.NaN, value='', inplace=True)

        invalid_option = self.get_invalid_option_row(df)
        if len(invalid_option.values()) > 0:
            logging.warning(f"처리할 수 있는 Excel양식이 아닙니다. 디비스키마열에 오류가 있는지 확인해 주세요. \n{_path} \n{invalid_option}")
            return res

        if not self._is_data_option_row(df):
            logging.warning(f"처리할 수 있는 Excel양식이 아닙니다. 첫번째 시트에 디비스키마열이 있는지 확인해 주세요. \n{_path}")
            return res

        df = self._get_filtered_column(df, ['ALL', 'SERVER', 'INFO'])
        df.drop([0], axis=0, inplace=True)
        table = []
        for col in df.columns:
            row = [col, df[col].values[self.ROW_FOR_DATA_HEADER], df[col].values[self.ROW_FOR_DATA_TYPE]]
            table.append(row)

        return {_path.stem: table}
