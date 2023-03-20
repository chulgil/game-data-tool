import os
import json
import re
import shutil
from re import match
from typing import Optional

import yaml
import time
from datetime import datetime
from dateutil import parser
import pandas as pd
from pathlib import Path
from pandas import DataFrame
import warnings
from enum import Enum, auto
from pprint import pprint

import pandas


class ConvertType(Enum):
    ALL = auto()
    SERVER = auto()
    CLIENT = auto()
    INFO = auto()
    MARKDOWN = auto()
    MARKDOWN_ENUM = auto()
    MARKDOWN_PROTOCOL = auto()
    MARKDOWN_ENTITY = auto()
    NONE = auto()

    @classmethod
    def value_of(cls, value: str):
        value = str(value)
        for k, v in cls.__members__.items():
            if k == value.upper():
                return v
        else:
            return ConvertType.NONE


class DataManager:

    def __init__(self, branch: str, convert_type: ConvertType, working_dir: Path):
        pandas.set_option('display.max_column', 50)  # print()에서 전체항목 표시
        warnings.filterwarnings('ignore', category=UserWarning, module='openpyxl')

        from . import LogManager
        self.splog = LogManager(branch)

        # Config 파일 설정
        self.ROOT_DIR = Path(__file__).parent.parent
        with open(self.ROOT_DIR.joinpath('config.yaml'), 'r') as f:
            config = yaml.safe_load(f)

        self.BRANCH = branch
        self.CONVERT_TYPE = convert_type
        self._info = f'[{branch} 브랜치]'
        self.PATH_FOR_WORKING = working_dir

        self.ROW_FOR_MAX_HEADER = 6  # EXCEL 헤더 맥스 값 : 1:memo, 2:desc, 3:tableId, 4:dataType, 5:schemaType 6:xxx
        # 가변필드 : 이 필드 값은 Excel Read 할 때 값이 변경됩니다.
        self.row_for_desc = -1
        self.row_for_server_type = 1
        self.row_for_data_type = 2
        self.row_for_data_option = 3
        self.row_for_data_start = 4
        self.row_for_max_print = 50

        self.IDX_DATA_TYPE_FROM_SERVER_TYPE = 1
        self.IDX_DATA_OPTION_FROM_SERVER_TYPE = 2
        self.IDX_DATA_DESC_FROM_SERVER_TYPE = -1
        self.IDX_DATA_DESCNEW_FROM_SERVER_TYPE = -2

        self.ITEM_KB_FOR_MARKDOWN_TABLE = r'\|(.*)\|(.*)\|(.*)\|'
        self._set_config(config)

        self.ENUM_DATA = {}
        if convert_type != ConvertType.MARKDOWN:
            self._set_folder()
            self.ENUM_DATA = self.get_enum_data()

    def _set_config(self, config):
        self.PATH_FOR_EXCEL = self.PATH_FOR_WORKING.joinpath(config['DEFAULT']['EXCEL_DIR'])
        self.PATH_FOR_DATA = self.PATH_FOR_EXCEL.joinpath('data')
        self.PATH_FOR_ENUM = self.PATH_FOR_EXCEL.joinpath('enum')
        self.ERROR_FOR_EXCEL = config['DEFAULT']['ERROR_TEXT']
        self.PATH_FOR_JSON = self.PATH_FOR_WORKING.joinpath(config['DEFAULT']['EXPORT_DIR'], "json")
        self.PATH_FOR_JSON_SERVER = self.PATH_FOR_JSON.joinpath("server")
        self.PATH_FOR_JSON_INFO = self.PATH_FOR_JSON.joinpath("info")
        self.PATH_FOR_JSON_CLIENT = self.PATH_FOR_JSON.joinpath("client")

        self.PATH_FOR_MARKDOWN = self.PATH_FOR_WORKING.joinpath("server")
        self.PATH_FOR_MD_PROTOCOL = self.PATH_FOR_JSON.joinpath(self.PATH_FOR_MARKDOWN, "protocol")
        self.PATH_FOR_MD_ENUM = self.PATH_FOR_JSON.joinpath(self.PATH_FOR_MARKDOWN, "enum")
        self.PATH_FOR_MD_ENTITY = self.PATH_FOR_JSON.joinpath(self.PATH_FOR_MARKDOWN, "entity")

        self.CHECK_FOR_ID = config['DEFAULT']['CHECK_SCHEMA_ID']

    def _set_folder(self):
        # JSON 폴더 초기화
        # if Path(self.PATH_FOR_JSON).is_dir():
        #     shutil.rmtree(self.PATH_FOR_JSON)
        # JSON 폴더 생성
        if self.CONVERT_TYPE == ConvertType.ALL or self.CONVERT_TYPE == ConvertType.SERVER:
            if not Path(self.PATH_FOR_JSON_SERVER).is_dir():
                os.makedirs(self.PATH_FOR_JSON_SERVER)
        if self.CONVERT_TYPE == ConvertType.ALL or self.CONVERT_TYPE == ConvertType.INFO:
            if not Path(self.PATH_FOR_JSON_INFO).is_dir():
                os.makedirs(self.PATH_FOR_JSON_INFO)
        if self.CONVERT_TYPE == ConvertType.ALL or self.CONVERT_TYPE == ConvertType.CLIENT:
            if not Path(self.PATH_FOR_JSON_CLIENT).is_dir():
                os.makedirs(self.PATH_FOR_JSON_CLIENT)

    def _get_filtered_data(self, df: DataFrame, targets: list) -> DataFrame:

        df = self._get_filtered_column(df, targets)
        option_df = self._get_data_option(df)

        if option_df is not None:
            df = self._del_auto_field(df)

        # 헤더행을 제외한 행부터 추출
        data_df = df.iloc[self.row_for_data_start:]
        data_df = data_df.reset_index(drop=True)
        type_df = df.iloc[self.row_for_data_type]
        self._translate_asdb(data_df, type_df, option_df)

        # Option값 @Id가 존재하면 데이터의 중복값 체크
        self._check_duplicated(data_df, type_df, option_df)

        # Pandas Dataframe 데이터 타입으로 변환
        data_df = self._set_pandas_type(data_df, type_df)

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
            if match(r'@auto', str(df[col][self.row_for_data_option])):
                res.append(col)
        return res

    def _get_data_option(self, df: DataFrame) -> Optional[DataFrame]:
        if self._is_data_option_row(df.iloc[self.row_for_data_option].values):
            return df.iloc[self.row_for_data_option]
        return None

    def get_invalid_option_row(self, df: DataFrame) -> dict:
        res = {}
        for col in df.columns:
            value = df[col][self.row_for_data_option]
            if match(r'^\w+', str(value)):
                res[col] = value
            if match(r'^\d+', str(value)):
                res[col] = value
        return res

    @staticmethod
    def _is_data_type_row(row: DataFrame) -> bool:
        """엑셀 데이터에서 해당 행에 데이터 타입 정보가 포함되어 있는지 확인한다.
            id table_id             table_sub_id    item_rate
            1   long      int            int        float
        """
        _match = r'int|string|datetime|float|short'
        filtered = list(filter(lambda v: match(_match, str(v)), row))
        if len(filtered) > 0:
            return True
        return False

    @staticmethod
    def _is_data_option_row(row: DataFrame) -> bool:
        """엑셀 데이터에서 해당 행에 스키마 정보가 포함되어 있는지 확인한다.
            id table_id             table_sub_id    item_rate
            1   long      int             int        float
            2  @auto      @id  @ref(sub_table_info.id)  @default(0)
        """
        filtered = list(filter(lambda v: match(r'^@[id|auto]+', str(v)), row))
        if len(filtered) > 0:
            return True
        return False

    def _get_filtered_column(self, df: DataFrame, targets: list) -> DataFrame:

        # 데이터 프레임 서버타입행 추출
        mask_df = df.iloc[self.row_for_server_type]

        # 필터링할 컬럼값을 추출
        filtered = mask_df[mask_df.isin(targets)].keys()
        return df[filtered]

    def _save_json(self, df: DataFrame, save_path: Path, file_name: str):
        # 행의 개수가 0이면 무시
        if df.shape[1] == 0:
            return

        # Data frame을 JSON으로 변환
        json_data = df.to_json(orient='records')
        json_list = json.loads(json_data)

        # 지정한 경로로 Json파일 저장
        _server_type = save_path.stem
        save_path = save_path.joinpath(file_name + ".json")
        with open(save_path, "w", encoding='utf-8') as f:
            json.dump(json_list, f, ensure_ascii=False, indent=4, separators=(',', ': '))

        # 파일 경로로 부터 / Sever / file.xxx 를 잘라온다.
        paths = str(save_path).split('/')
        name = paths.pop()
        path = paths.pop()
        self.splog.info(f"{self._info} [{_server_type}] Json 파일 저장 성공 : {path}/{name}")

        if self.splog.has_error():
            msg = f'{self._info} [{_server_type}] Excel파일에 미검증 데이터 존재 [{file_name}]'
            self.splog.add_error(msg, 0)
            self.splog.send_designer_all()

    def _check_duplicated(self, data_df: DataFrame, header_df: DataFrame, option_df: DataFrame) -> bool:
        """
        EXCEL의 데이터가 다음과 같을때 2번째 행은 디비속성 이다.
        디비속성 중 @id값이 존재하면 데이터의 중복을 체크한다.
        --------------------------------------------------------------
        #      id     | name | reg_dt | reg_dt
        # 0 : SERVER | SERVER | CLIENT |  SERVER
        # 1 : int | string | datetime |  datetime
        # 2 : @id | @default("") |  |   <-- 디비속성
        # 3 : 0 | test |  2022.04.09 | 2021-03-09T00:00:00
        """
        res = False
        for col in data_df.columns:
            if option_df is None:
                continue
            schema_type = option_df[col]
            if match(r'@id', schema_type):
                _duplicated = data_df.duplicated(col)
                for i, value in _duplicated.items():
                    if value is True:
                        row_id = i + self.row_for_data_start + 2
                        msg = 'Duplicate values exist'
                        data_df.loc[i][col] = f'{self.ERROR_FOR_EXCEL} {msg}'
                        self.splog.add_error(f'컬럼[{col}] 행[{row_id}] {msg}')
                        res = True
        return res

    # --------------------------------------------------------------
    # EXCEL의 데이터가 다음과 같을때 2번째 행은 디비속성 이다.
    # 디비속성 값으로 데이터를 포멧팅한다_save_json.
    # --------------------------------------------------------------
    #      id     | name | reg_dt | reg_dt
    # 0 : SERVER | SERVER | CLIENT |  SERVER
    # 1 : int | string | datetime |  datetime
    # 2 : @id | @default("") |  |   <-- 디비속성
    # 3 : 0 | test |  2022.04.09 | 2021-03-09T00:00:00
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
                if self.is_camel_case(col):
                    self.splog.add_warning(f' 컬럼명 [{col}]을 스네이크 형식[EX: 소문자_소문자]으로 변경해주세요.')

                row_id = i + self.row_for_data_start + 2
                info = f'컬럼[{col}] 행[{row_id}]'
                # print(f'{field_type} {field_value}')
                data_df.loc[i][col.strip()] = self._value_astype(field_type, field_value, schema_type, info)

    def _set_pandas_type(self, data_df: DataFrame, type_df: DataFrame) -> DataFrame:

        res = {}
        _head = data_df.columns
        try:
            for i in range(len(_head)):
                res[_head[i]] = self._astype(type_df[i])
            if len(res) == 0:
                return data_df
            return data_df.astype(res, errors='ignore')
        except Exception as e:
            self.splog.error(f'Dataframe 타입 변환 Error : \n {str(e)}')

    @staticmethod
    def _astype(column_type: str) -> str:
        # if column_type is None:
        # return "object"
        column_type = str(column_type).lower()
        if column_type == "string":
            return "object"
        elif column_type == "float" or column_type == "double":
            return "float64"
        elif column_type == "byte" or column_type == "short" or column_type == "int" or column_type == "long":
            return "int64"
        elif column_type == "bool" or column_type == "boolean":
            return "bool"
        elif column_type == "datetime":
            return "object"
        else:
            return "object"

    def _value_astype(self, column_type: str, column_value: str, schema_type: str, info: str):
        """
        엑셀에서 정의한 값을 타입별 기본 값으로 변환
        @param column_type: 엑셀에서 정의한 데이터 타입
        @param column_value: 엑셀에서 정의한 데이터 값
        @param schema_type: 엑셀에서 정의한 스키마옵션 값
        @param info: 컬럼과 행 정보
        @return: 변환된 문자열
        ref :
        https://blog.finxter.com/how-to-convert-a-string-to-a-double-in-python/
        """
        try:
            column_type = column_type.lower()
            if column_value == '':
                default = re.findall(r'@default\(?(\S+)\)', schema_type)
                if default:
                    column_value = default[0]
                    column_value = column_value.replace('\'', '')
                    column_value = column_value.replace('"', '')

            enum_type = re.findall(r'@enum\(?(\S+)\)', schema_type)
            if enum_type:
                _enum_type = enum_type[0]
                enum_value = self._value_from_enum(_enum_type, column_value)
                if enum_value < 0:
                    raise Exception(f'Enum타입이 존재하지 않습니다. : {_enum_type} [{column_value}]')
                return int(enum_value)

            if not re.search(r'@null', schema_type):  # not null type
                if column_value == '' and column_type != '':
                    raise Exception(f'[{column_type}] 공백은 허용되지 않습니다. 공백을 허용하려면 컬럼에 @null옵션을 추가해 주세요.')

            if column_value == '':
                if column_type == "datetime":
                    return None

            if column_type == "string" or column_type == "":
                return str(column_value)
            elif column_type == "float" or column_type == "double":
                return float(column_value)
            elif column_type == "int" or column_type == "short" or column_type == "byte":
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
                return self._iso8601(column_value)
            else:
                return str(column_value)
        except Exception as e:
            self.splog.add_error(f"{info} {str(e)}")
            return f'{self.ERROR_FOR_EXCEL} {str(e)}'

    def _value_from_enum(self, enum_type: str, enum_key: str) -> int:
        if self.ENUM_DATA.keys() == 0:
            return -1
        if enum_type not in self.ENUM_DATA:
            return -1
        if enum_key not in self.ENUM_DATA[enum_type]:
            return -1
        return self.ENUM_DATA[enum_type][enum_key][0]

    def _iso8601(self, date_text: str) -> str:
        """
        Excel에서 들어온 날짜형식의 스트링을 UTC타임존 포멧으로 변경
        @return: 변환된 문자열
        ref :
        https://stackoverflow.com/questions/79797/how-to-convert-local-time-string-to-utc
        https://twpower.github.io/29-iso8601-utc-and-python-example
        """
        try:
            local_timezone = time.strftime('%Z', time.localtime())
            if local_timezone != 'UTC':
                self._change_timezone()

            date = parser.parse(str(date_text))
            date = date.astimezone()
            iso = date.isoformat()
            return iso
        except Exception as e:
            msg = f'{self.ERROR_FOR_EXCEL} {str(e)}'
            raise Exception(msg)

    def _change_timezone(self):

        # 현재 시간을 가져옵니다.
        current_time = time.time()

        # 로컬 타임존을 변경하려는 타임존으로 설정합니다.
        os.environ['TZ'] = 'UTC'

        # 타임존을 변경합니다.
        time.tzset()

        # 변경된 타임존에서 현재 시간을 다시 가져옵니다.
        new_time = time.time()

        # 시간 차이를 계산합니다.
        time_diff = new_time - current_time

        msg = "변경된 로컬 타임존:" + time.strftime('%Y-%m-%d %H:%M:%S %Z', time.localtime())
        self.splog.add_info(msg)

    def _get_relation_infos(self, file_path: Path) -> list:
        """
        @ref(table.id) 옵션이 있는 컬럼을 가져온다.
        """
        try:
            # 첫번째 시트를 타겟으로 설정
            df = self._read_excel_for_data(file_path)
            res = []
            option_df = self._get_data_option(df)
            if option_df is None:
                return res
            for col, value in option_df.items():
                z = re.findall(r'@ref\(?(\S+)\)', str(value))
                if len(z) == 0:
                    continue
                _target = str(z[0]).split('.')
                if len(_target) == 1:
                    self.splog.add_error(
                        f'EXCEL양식에 미검증 데이터 존재 : 파일명[ {file_path.stem} ] 컬럼[ {col} ] 릴레이션 옵션이 잘못 되었습니다. {value}')
                    self.splog.add_error(f'올바른 사용예 : @ref(테이블명.아이디)')
                    continue
                target_table = _target[0]
                target_col = _target[1]
                path = list(Path(self.PATH_FOR_DATA).rglob(rf"{target_table}.xls*"))
                if len(path) == 0:
                    self.splog.add_error(f"[EXCEL: {file_path.stem}][{col}] 릴레이션 옵션의 {target_table}테이블이 존재 하지 않습니다.")
                    continue
                res.append([path[0], col, target_col])
                return res
        except Exception as e:
            self.splog.add_error(f'EXCEL[{file_path.stem}] get_relation_infos Error : {str(e)}')
            self.splog.send_designer_all()

    def _get_server_type_index(self, df: DataFrame):
        _idx = 0
        _type = None
        _row_for_max = self.ROW_FOR_MAX_HEADER
        _row_for_current = len(df.index)
        if _row_for_current < self.ROW_FOR_MAX_HEADER:
            _row_for_max = _row_for_current

        for i in range(_row_for_max):
            _type = ConvertType.value_of(df.iloc[i][0])
            if _type == ConvertType.ALL or _type == ConvertType.SERVER \
                    or _type == ConvertType.CLIENT or _type == ConvertType.INFO:
                _idx = i
        return _idx

    def _get_start_index(self, df: DataFrame):
        idx = self._get_server_type_index(df)
        idx_option = idx + self.IDX_DATA_OPTION_FROM_SERVER_TYPE
        if self._is_data_option_row(df.iloc[idx_option].to_numpy()):
            idx = idx_option
        else:
            idx = idx + self.IDX_DATA_TYPE_FROM_SERVER_TYPE
        idx = idx + 1
        return idx

    def _get_desc_row(self, df: DataFrame):
        """
        주석 행을 가져온다
        Examples::
            0  id  name
            1  삭제예정
            2  맵아이디  맵이름
            3  ALL  ALL
            4  @id

        :param df:
        :return:
        """
        row = {}
        idx = self._get_server_type_index(df)
        idx_desc = idx + self.IDX_DATA_DESC_FROM_SERVER_TYPE
        idx_desc_new = idx + self.IDX_DATA_DESCNEW_FROM_SERVER_TYPE

        if idx_desc < 0:
            for col in df.columns:
                row[col] = ''
            return row

        for col in df.columns:
            row[col] = df[col][idx_desc]
            if idx_desc_new > -1:
                desc_new = df[col][idx_desc_new]
                if desc_new == '':
                    continue
                row[col] = desc_new
        return row

    def _check_relation_data(self, origin_path: Path, target_path: Path, origin_col: str, target_col: str = ''):
        # print(f' {origin_path} , {target_path}, {origin_col} , {target_col}')
        try:
            origin_df = self._read_excel_for_data(origin_path)
        except Exception as e:
            self.splog.add_error(f'{self._info} Excel check Error: [{origin_path.stem}]\n{str(e)}')
            return
        try:
            target_df = self._read_excel_for_data(target_path)
        except Exception as e:
            self.splog.add_error(f'{self._info} Excel check Error: [{target_path.stem}]\n{str(e)}')
            return

        oidx = self._get_start_index(origin_df)
        tidx = self._get_start_index(target_df)
        odata = origin_df.iloc[oidx:]
        tdata = target_df.iloc[tidx:]
        _errors = []
        for value in odata[origin_col].to_numpy():
            if value == 0 or value == '' or value is None:
                continue
            if target_col == '':
                continue
            if target_col not in tdata:
                continue
            values = tdata[target_col].to_numpy()
            if value not in values:
                _errors.append(f'원본 행의 참조 값[{value}]')

        if len(_errors) > 0:
            _msg_head = f'원본 EXCEL[{origin_path.stem}][{origin_col}]의 참조 값이 타겟 [{target_path.stem}]에 존재 하지 않습니다.'
            _errors.insert(0, self._info + ' ' + _msg_head)
            self.splog.add_error(_errors)
        self.splog.info(f'EXCEL 체크 성공 : [{origin_path.stem}]')

    def check_excel_for_relation(self, excel_list: list):

        # Excel파일 가져오기
        for excel in excel_list:
            _path = Path(self.PATH_FOR_WORKING).joinpath(excel)
            rel_data = self._get_relation_infos(_path)
            if rel_data is None:
                continue
            for info in rel_data:
                self._check_relation_data(_path, info[0], info[1], info[2])

        self.splog.send_designer_all()

    def excel_to_json(self, excel_list: list):
        for excel in excel_list:
            self.save_json_task(excel)

    def save_json_task(self, excel: str):
        try:
            path = Path(self.PATH_FOR_WORKING).joinpath(excel)
            # 첫번째 시트를 JSON 타겟으로 설정
            df = self._read_excel_for_data(path)
            # 파일 이름으로 JSON 파일 저장 : DATA
            if self.CONVERT_TYPE == ConvertType.ALL or self.CONVERT_TYPE == ConvertType.SERVER:
                self._save_json(self._get_filtered_data(df, ['ALL', 'SERVER']), self.PATH_FOR_JSON_SERVER, path.stem)
            # 파일 이름으로 JSON 파일 저장 : INFO
            if self.CONVERT_TYPE == ConvertType.ALL or self.CONVERT_TYPE == ConvertType.INFO:
                self._save_json(self._get_filtered_data(df, ['INFO']), self.PATH_FOR_JSON_INFO, path.stem)
            # 파일 이름으로 JSON 파일 저장 : CLIENT
            if self.CONVERT_TYPE == ConvertType.ALL or self.CONVERT_TYPE == ConvertType.CLIENT:
                self._save_json(self._get_filtered_data(df, ['ALL', 'CLIENT']), self.PATH_FOR_JSON_CLIENT, path.stem)

            if self.CHECK_FOR_ID:
                _column_id = df.columns[0]
                if _column_id != self.CHECK_FOR_ID:
                    self.splog.add_error(f"미검증 데이터 존재 : 첫번째 컬럼[ {_column_id} ]을 {self.CHECK_FOR_ID} 로 변경해주세요.")

            if self.splog.has_warning():
                self.splog.add_error(f'{self._info} Excel to Json Error: [{path.stem}]\n', 0)
                self.splog.send_designer_all()
        except Exception as e:
            self.splog.add_error(f'{self._info} save_json_task Error: [{path.stem}]\n{str(e)}')

    def get_excelpath_all(self) -> list:
        return sorted(list(Path(self.PATH_FOR_DATA).rglob(r"*.xls*")))

    def get_jsonpath_all(self) -> list:
        return sorted(self._get_jsonpath_info() + self._get_jsonpath_server())

    def _get_jsonpath_info(self) -> list:
        return sorted(list(Path(self.PATH_FOR_JSON).rglob(r"*info/*.json")))

    def _get_jsonpath_server(self) -> list:
        return sorted(list(Path(self.PATH_FOR_JSON).rglob(r"*server/*.json")))

    def _get_jsonpath_client(self) -> list:
        return sorted(list(Path(self.PATH_FOR_JSON).rglob(r"*client/*.json")))

    def _get_enumpath(self) -> list:
        return sorted(list(Path(self.PATH_FOR_ENUM).rglob(r"*.xls*")))

    def get_markdown(self, target: ConvertType = None) -> dict:
        """
        변환타입별로 MarkDown을 가져온다.
        @return: 딕셔너리 값으로 리턴 { key (파일명) : value (Dict) }
        """
        res = {}

        _path = self._get_path_markdown(target)
        for _file in _path:
            try:
                f = open(_file, 'r')
                markdown = f.read()

                if target == ConvertType.MARKDOWN_ENUM:
                    res.update(self._markdown_to_enum(markdown))
                elif target == ConvertType.MARKDOWN_PROTOCOL:
                    res.update(self._markdown_to_protocol(markdown))
                elif target == ConvertType.MARKDOWN_ENTITY:
                    res.update(self._markdown_to_entity(markdown))

            except Exception as e:
                self.splog.add_error(f'MarkDown Load Error : {str(e)}')

            if self.splog.has_warning():
                p = str(_file).split('/')
                _path_md = '/'.join(p[len(p) - 3:])
                self.splog.add_error(f'MarkDown[{_path_md}] 변환 경고 :', 0)
                self.splog.send_developer_all()
                self.splog.warning()

        return res

    def _get_path_markdown(self, target: ConvertType) -> list:
        _path = []
        try:
            if target == ConvertType.MARKDOWN_ENUM:
                _path = list(Path(self.PATH_FOR_MD_ENUM).rglob(r"*.md"))
            elif target == ConvertType.MARKDOWN_PROTOCOL:
                _path = list(Path(self.PATH_FOR_MD_PROTOCOL).rglob(r"*.md"))
            elif target == ConvertType.MARKDOWN_ENTITY:
                _path = list(Path(self.PATH_FOR_MD_ENTITY).rglob(r"*.md"))
            return sorted(_path)
        except Exception as e:
            self.splog.send_developer(f'MarkDown 데이터 경로 Error :\r\n {str(e)}')
            return sorted(_path)

    def _markdown_to_enum(self, markdown: str) -> dict:
        """
        MARKDOWN 형식을 Enum스크립트 변환을 위한 오브젝트 형식으로 리턴합니다.
        Examples::
            ## enum_info
            > 설명
            >
            > 상세내용
            | type        | Name          | desc        |
            |-------------|---------------|-------------|
            | long        | facility_key  | 치료소 key     |
            | int[]       | test1         | desc test1  |
            | game_design | game_design   | 게임디자인       |
            ---

        :param markdown:

        :return:
            'ActorType': {
                None: [0, '사용안함'],
                Melee: [1, '근접 딜러'],
                Ranged: [2, '원거리 딜러']
            }
        """
        res = {}
        if markdown == '':
            return res
        try:

            _match = re.split(r'-{3,}\n', markdown)
            if not _match:
                return res
            for text in _match:
                enum = re.findall(r'##([\w\W]+?)\n', text)
                if not enum:
                    continue

                enum = enum[0].strip()
                desc = re.findall(r'>(.*)\n', text)
                _list = re.findall(self.ITEM_KB_FOR_MARKDOWN_TABLE, text)

                if enum in res:
                    self.splog.add_error(f' Enum[{enum}] 이 중복됩니다. ')

                _enum_values = []
                _check_key = {}
                _check_val = {}
                for item in _list[2:]:
                    _key = item[0].strip()
                    _val = item[1].strip()
                    _desc = item[2].strip()

                    if _key == '':
                        self.splog.add_error(f' Enum 데이터 키 [{_key}] 가 없습니다. ')
                    if _val == '':
                        self.splog.add_error(f' Enum 데이터 값 [{_val}] 가 없습니다. ')
                    if _key in _check_key:
                        self.splog.add_error(f' Enum 데이터 {enum}[{_key}] 가 중복됩니다. ')
                    if _val in _check_val:
                        self.splog.add_error(f' Enum 데이터 {enum}[{_val}] 가 중복됩니다. ')
                    _check_key[_key] = None
                    _check_val[_val] = None
                    _enum_values.append([_key, _val, _desc])

                items = {}

                for item in sorted(_enum_values):
                    items[item[1]] = [item[0], item[2]]
                res[enum] = {}
                res[enum]['desc'] = desc
                res[enum]['items'] = items
        except Exception as e:
            self.splog.add_error(f'markdown_to_enum Error : {e}')

        return res

    def _markdown_to_entity(self, markdown: str) -> dict:
        """
        MARKDOWN 형식을 Entity스크립트 변환을 위한 오브젝트 형식으로 리턴합니다.
        Examples::
            ## goods_info
            > 설명
            >
            > 상세내용
            | type        | Name          | desc        |
            |-------------|---------------|-------------|
            | long        | facility_key  | 치료소 key     |
            | int[]       | test1         | desc test1  |
            | game_design | game_design   | 게임디자인       |
            ---
        :param markdown:
        :return:
            'ActorType': {
                None: [0, '사용안함'],
                Melee: [1, '근접 딜러'],
                Ranged: [2, '원거리 딜러']
            }
        """
        res = {}
        if markdown == '':
            return res
        try:

            _match = re.split(r'-{3,}\n', markdown)
            if not _match:
                return res

            for text in _match:
                _class = re.findall(r'##([\w\W]+?)\n', text)
                if not _class:
                    continue
                _class = _class[0].strip()
                _desc = re.findall(r'>(.*)\n', text)
                _list = re.findall(self.ITEM_KB_FOR_MARKDOWN_TABLE, text)

                if _class in res:
                    self.splog.add_error(f' 같은 Entity[{_class}] 가 존재합니다. ')

                res[_class] = {}
                res[_class]['desc'] = _desc
                res[_class]['items'] = self._conv_entity_item(_class, _list[2:])

        except Exception as e:
            self.splog.add_error(f'markdown_to_entity Error : {e}')

        return res

    def _markdown_to_protocol(self, markdown: str) -> dict:
        """
        MARKDOWN 형식을 스크립트 변환을 위한 오브젝트 형식으로 리턴합니다.
        Examples::
            ## UnlockRewardBox
            > 해당 요청은 보상박스 언락입니다.
            >
            > 요청과 응답 프로토콜은 아래와 같습니다.

            ### Req : 1302
            | type | Name         | desc    |
            |:-----|:-------------|:--------|
            | long | facility_key | 치료소 key |

            ### Resp : 1303
            | type         | Name        | desc   |
            |:-------------|:------------|:-------|
            | clinic_resp  | clinic_resp | 치료소 정보 |
            | goods_info[] | goods_infos | 재화 정보  |
            ---
        :param markdown:
        :return:
            {'UnlockRewardBox':
              { 'desc': [' 해당 요청은 보상박스 언락입니다.',' 요청과 응답 프로토콜은 아래와 같습니다.'],
                'req_info': {'100': [(' long ', ' facility_key', ' 치료소key'),(' long ', ' facility_key ', ' 치료소 key ')]},
                'res_info': {'101': [('clinic_resp', 'clinic_resp','치료소 정보'),('goods_info[]','goods_infos',' 재화정보')]}
            }}
        """
        res = {}
        _check = {}
        if markdown == '':
            return res
        try:

            _match = re.split(r'-{3,}\n', markdown)
            if not _match:
                return res

            for text in _match:
                _mk = re.findall(r'##([\s+|\S+]+)###([\s+|\S+]+)###([\s+|\S+]+)', text)
                if _mk:
                    _header = _mk[0][0]
                    _req = _mk[0][1]
                    _res = _mk[0][2]
                    _class = re.findall(r'(.*)\n', _header)[0]
                    _class = _class.strip()
                    _desc = re.findall(r'>(.*)\n', _header)
                    _req_id = re.findall(r':\s?(.+)\n', _req)[0]
                    _req_list = re.findall(self.ITEM_KB_FOR_MARKDOWN_TABLE, _req)
                    _res_id = re.findall(r':\s?(.+)\n', _res)[0]
                    _res_list = re.findall(self.ITEM_KB_FOR_MARKDOWN_TABLE, _res)

                    if _class in res:
                        self.splog.add_error(f' 같은 클래스[{_class}]가 존재합니다. ')
                    if _req_id in _check:
                        self.splog.add_error(f' 같은 프로토콜ID[{_req_id}]가 클래스{_check[_req_id]}에 존재합니다. ')
                    if _res_id in _check:
                        self.splog.add_error(f' 같은 프로토콜ID[{_res_id}]가 클래스{_check[_res_id]}에 존재합니다. ')
                    _check[_req_id] = _class
                    _check[_res_id] = _class

                    res[_class] = {}
                    res[_class]['desc'] = _desc
                    res[_class]['req_info'] = {_req_id: self._conv_entity_item(_class, _req_list[2:])}
                    res[_class]['res_info'] = {_res_id: self._conv_entity_item(_class, _res_list[2:])}

        except Exception as e:
            print(e)

        return res

    def _conv_entity_item(self, entity_name: str, items: list) -> list:
        res = []

        if len(items[0]) < 2:
            self.splog.add_error(f' Markdown 정의[{entity_name}]에 형식 오류 : 컬럼수 -> {len(items[0])}')
            return res

        for item in items:
            _etype = item[0].strip()
            _ename = item[1].strip()
            _edesc = item[2].strip()
            if _etype == '' and _ename == '' and _edesc == '':
                continue

            # if self.is_camel_case(_etype):
            #     self.splog.add_error(f' Markdown 정의[{entity_name}]에 변수타입을 스네이크 형식으로 변경해주세요. {_etype}')
            #     continue

            if _etype == '':
                self.splog.add_error(f' Markdown 정의[{entity_name}]에 변수타입 누락 {_etype}')
                continue
            if _ename == '':
                self.splog.add_error(f' Markdown 정의[{entity_name}]에 변수명 누락 {_ename}')
                continue
            res.append((_etype, _ename, _edesc))
        return res

    @staticmethod
    def is_camel_case(s: str):
        return s != s.lower() and s != s.upper() and "_" not in s

    def get_jsonmap(self, target: ConvertType = None) -> dict:
        """
        변환타입별로 json을 가져온다.
        @return: 딕셔너리 값으로 리턴 { key (테이블명) : value (JsonData) }
        """
        res = {}
        json_path = ''
        file_name = ''

        try:
            if target is None:
                target = self.CONVERT_TYPE
            if target == ConvertType.SERVER:
                json_path = self._get_jsonpath_server()
            elif target == ConvertType.ALL:
                json_path = self.get_jsonpath_all()
            elif target == ConvertType.INFO:
                json_path = self._get_jsonpath_info()
            elif target == ConvertType.CLIENT:
                json_path = self._get_jsonpath_client()
            for _path in json_path:
                file_name = _path.stem
                with open(_path, 'r') as f:
                    res[file_name] = json.load(f)
        except Exception as e:
            self.splog.add_error(f'Json 데이터 {file_name} Error :\r\n {str(e)}')
        return res

    def delete_path(self, paths: list):
        for path in paths:
            shutil.rmtree(path, ignore_errors=True)

    def delete_json_all(self):
        if self.CONVERT_TYPE is not ConvertType.ALL:
            return
        if Path(self.PATH_FOR_JSON).is_dir():
            shutil.rmtree(self.PATH_FOR_JSON)
        self._set_folder()

    def get_schema_all(self, target: ConvertType = None) -> dict:
        table_info = {}
        if target is None:
            target = self.CONVERT_TYPE
        for _path in self.get_excelpath_all():
            try:
                table_info.update(self.get_schema(_path, target))
            except Exception as e:
                pass
        return table_info

    def get_schema(self, excel_path: str, target: ConvertType = None) -> dict:
        res = {}
        _path = self.PATH_FOR_WORKING.joinpath(excel_path)
        if not _path.exists():
            return res

        if target is None:
            target = self.CONVERT_TYPE
        try:
            df = self._read_excel_for_data(_path)
        except Exception as e:
            self.splog.add_error(f'{self._info} Excel get_schema Error: [{excel_path.stem}]\n{str(e)}')
            return res

        if target == ConvertType.CLIENT:
            df = self._get_filtered_column(df, ['ALL', 'CLIENT'])
        if target == ConvertType.INFO:
            df = self._get_filtered_column(df, ['INFO'])
        if target == ConvertType.SERVER:
            df = self._get_filtered_column(df, ['ALL', 'SERVER'])
        if target == ConvertType.ALL:
            df = self._get_filtered_column(df, ['ALL', 'SERVER', 'INFO', 'CLIENT'])

        table = []

        for col in df.columns:
            desc = self._get_desc_row(df)
            row = [col, df[col].values[self.row_for_data_type], df[col].values[self.row_for_data_option], desc[col]]
            table.append(row)
        return {_path.stem: table}

    def _read_excel_for_data(self, path: Path) -> DataFrame:

        df = self._read_excel(path)
        if df is None:
            raise Exception(f'처리할 수 있는 Excel양식이 아닙니다. [{path.stem}]\n')

        if True in df.columns.duplicated():
            dup_df = df.loc[:, df.columns.duplicated()]
            raise Exception(f"처리할 수 있는 Excel양식이 아닙니다. 중복된 컬럼이 존재합니다. [{path.stem}]\n{dup_df.columns.tolist()}")

        if not self._is_data_type_row(df.iloc[self.row_for_data_type].values):
            raise Exception(f"처리할 수 있는 Excel양식이 아닙니다. 첫번째 시트에 데이터 타입 (int, string ...)이 있는지 확인해 주세요. \n[{path.stem}]")

        if not self._is_data_option_row(df.iloc[self.row_for_data_option].values):
            raise Exception(f"처리할 수 있는 Excel양식이 아닙니다. 첫번째 시트에 디비스키마열 @id가 있는지 확인해 주세요. \n[{path.stem}]")

        invalid_option = self.get_invalid_option_row(df)
        if len(invalid_option.values()) > 0:
            raise Exception(f"처리할 수 있는 Excel양식이 아닙니다. 디비스키마열에 오류가 있는지 확인해 주세요. \n[{path.stem}] \n{invalid_option}")

        return df

    def _read_excel(self, path: Path) -> Optional[DataFrame]:
        try:
            # 첫번째 시트를 JSON 타겟으로 설정
            df = pd.read_excel(path, sheet_name=0, header=None)
            df.fillna('', inplace=True)
            return self._set_base_index(df)

        except Exception as e:
            self.splog.add_error(f'READ EXCEL ERROR[{path}] : {str(e)} ')
            return None

    def get_enum_data(self) -> dict:
        """
        Excel Enum Data를 딕셔너리로 가져온다.
        Examples::
            #----------------------------------------------------
            # id                             625
            # enum_type     enum_BuffContentType
            # enum_id                          4
            # enum_value                Relation
            # comment                  인연(추가 예정)
            #----------------------------------------------------
        :return:
            'ActorType': {
                None: [0, '사용안함'],
                Melee: [1, '근접 딜러'],
                Ranged: [2, '원거리 딜러']
            }
        """
        res = {}
        for _path in self._get_enumpath():
            try:
                df = self._read_excel(_path)
                data_df = self._get_filtered_data(df, ['ALL', 'SERVER', 'CLIENT', 'MEMO'])

                head = data_df.columns
                enum_type = {}
                for i, row in data_df.iterrows():
                    if row.enum_type not in res:
                        res[row.enum_type] = {}
                    self._check_enum_data(row, res)
                    res[row.enum_type][row.enum_value] = [row.enum_id, row.comment]
            except Exception as e:
                self.splog.add_error(f'{self._info} [Enum] Excel Error [{_path.stem}]')
        if self.splog.has_warning():
            self.splog.add_error(f'{self._info} [Enum] Excel 파일에 미검증 데이터 존재', 0)
            self.splog.send_designer_all()
        return res

    def _check_enum_data(self, row, data: dict):
        # {0: ['None', '사용안함'], 1: ['Melee', '근접 딜러'], 2: ['Ranged', '원거리 딜러']}
        _data = data[row.enum_type]
        _values = []
        for item in _data.values():
            _values.append(item[0])
        if len(_data) == 0:
            return
        if row.enum_id in _data:
            self.splog.add_error(f'컬럼[{row.enum_type}] ID[{row.id}] 에 중복된 키 값이 존재합니다.')
        if row.enum_value in _values:
            self.splog.add_error(f'컬럼[{row.enum_type}] ID[{row.id}] 에 중복된 키 값이 존재합니다.')

    def _set_base_index(self, df: DataFrame) -> DataFrame:
        """
        # 서버타입 행을 기준열로 설정
        Examples::
            # --------------------------------------------------------------
            # 0  memo
            # 1  descripton
            # 2  id     | name | reg_dt | reg_dt
            # 3  SERVER | SERVER | CLIENT |  SERVER <-- 서버타입
            # 4  int | string | datetime |  datetime
            # 5  @id | @default("") |  |
            # 6  0 | test |  2022.04.09 | 2021-03-09T00:00:00
            # --------------------------------------------------------------
        :note:
            * 서버타입 SERVER CLIENT INFO 가 하나라도 열에 존재하면 기준 열로 설정
            * Dataframe의 헤더 행을 기준행의 바로 윗 열의 id name reg_dt로 설정하고 1,2행은 처리에서 무시
            * EXCEL의 데이터가 다음과 같을때 헤더데이터가 가변일수 있음
        """
        _idx_server_type = self._get_server_type_index(df)
        if _idx_server_type < 1:
            raise Exception(f"처리할 수 있는 Excel양식이 아닙니다. 첫번째 시트에 서버타입 열이 있는지 확인해 주세요. ")

        _idx_header = _idx_server_type - 1
        df = df.rename(columns=df.iloc[_idx_header])
        df = df.reindex(df.index.drop(_idx_header)).reset_index(drop=True)

        self.row_for_desc = -1
        self.row_for_server_type = _idx_header
        self.row_for_data_type = _idx_header + 1
        self.row_for_data_option = _idx_header + 2
        self.row_for_data_start = _idx_header + 2
        if self._is_data_option_row(df.iloc[self.row_for_data_option].values):
            self.row_for_data_start = _idx_header + 3

        if self.row_for_server_type > 0:
            self.row_for_desc = 0
        return df

    def get_json(self, target: ConvertType = None):
        return json.dumps(self.get_jsonmap(target))

    def save_json_all(self, save_path: Path, target: ConvertType = None):
        with open(save_path, "w", encoding='utf-8') as f:
            json.dump(self.get_jsonmap(target), f, ensure_ascii=False, indent=4, separators=(',', ': '))

    @staticmethod
    def remove_file(path: Path):
        try:
            path.unlink()
        except IOError as e:
            pass
