import os
import logging
import shutil
from re import match
from typing import Optional

import pymsteams as pymsteams
import yaml
from dateutil import parser
from pathlib import Path


class CSharpManager:

    def __init__(self, branch: str, tag: str, commit_id, save_dir: Path):
        self.BRANCH = branch
        self.TAG = tag
        self.COMMIT_ID = commit_id
        self._error_msg = []
        self._info = f'[{branch} 브랜치]'
        self.ROOT_DIR = Path(__file__).parent.parent
        self.PATH_FOR_SAVE = save_dir
        self.PATH_FOR_CONFIG = self.ROOT_DIR.joinpath('config.yaml')
        self.PATH_FOR_ENTITY = self.PATH_FOR_SAVE.joinpath('AutoGenerated_Entity.cs')
        self.PATH_FOR_ENUM = self.PATH_FOR_SAVE.joinpath('AutoGenerated_Enum.cs')
        self.TAB = '    '
        # Config 파일 설정
        with open(self.PATH_FOR_CONFIG, 'r') as f:
            config = yaml.safe_load(f)
        self._set_config(config)

    def _set_config(self, config):
        self.teams = pymsteams.connectorcard(config['TEAMS']['DESIGNER_URL'])
        self.COMMIT_URL = config['GITSERVER']['EXCEL_URL'] + '/src/commit'
        self.GIT_URL = config['GITSERVER']['EXCEL_URL']

    def save_entity(self, table_info: dict):
        table_name = ''
        schema = ''
        for key in table_info.keys():
            table_name = str(key).upper()
            rows = table_info[key]
            new_schema = self._convet_entity(table_name, rows)
            if new_schema != '':
                logging.info(f'{self._info} 스키마 저장 완료: {table_name}')
                schema = schema + new_schema
        schema = self._get_default_entity(schema)
        with open(self.PATH_FOR_ENTITY, "w", encoding='utf-8') as f:
            f.write(schema)

    def save_enum(self, enum_info: dict):
        """
        Excel에서 변환된 Enum 데이터를 C# Enum으로 변환후 파일로 저장한다.
        # enum_info ->
            'ActorType': {
                0: ['None', '사용안함'],
                1: ['Melee', '근접 딜러'],
                2: ['Ranged', '원거리 딜러']
            }
        """
        enum_name = ''
        schema = ''
        for enum_name, enum_data in enum_info.items():
            schema = schema + self._convert_enum(enum_name, enum_data, 1)
        schema = self._get_default_csharp(schema)
        try:
            # 지정한 경로로 Prisma 스키마 파일 저장
            with open(self.PATH_FOR_ENUM, "w", encoding='utf-8') as f:
                f.write(schema)
        except Exception as e:
            logging.error(f'{self._info} ENUM 저장 Error: {self.PATH_FOR_ENUM.stem}\n{str(e)}')

    def _convet_entity(self, table_name: str, rows: list, indent: int = 0) -> str:
        """
        C# 스크립트 포멧으로 변환 :
        디비필드, 디비타입, 스키마타입
        ['id', 'long', '@auto'] -> ['id', 'int', '@auto']
        """
        schema = ''
        try:
            start = self.TAB
            newline = '\n' + start
            schema = schema + newline + f'public class {table_name} : TABLE_DATA'
            schema = schema + newline + '{' + newline
            if len(rows) < 1:
                return ''
            for row in rows[1:]:
                # 순서 주의 : 컨버팅 되지 않은 타입값으로 디비 스키마 값 변경
                d_type = self._convert_datatype(row[1], row[2])
                field = row[0]
                desc = str(row[3]).replace('\n', ' ')  # 메모의 개행 공백 치환
                schema = schema + self.TAB + f'public {d_type} {field} ' + '{ get; set; } '
                schema = schema + ('// ' + desc + newline if desc != '' else newline)
            schema = schema + '}' + newline
        except Exception as e:
            logging.error(f'{self._info} 스키마 변환 Error: {table_name}\n{str(e)}')
        return schema

    def _convert_enum(self, enum_name: str, enum_data: dict, indent: int = 0) -> str:

        start = ''
        for i in range(0, indent):
            start = start + self.TAB
        newline = '\n' + start
        codeline = newline + self.TAB
        enum_rows = []
        for id, item in enum_data.items():
            _str = ''
            enum_key = item[0]
            enum_value = id
            enum_desc = item[1]
            _str = f'{enum_key} = {enum_value},'
            if enum_desc != '':
                _str = f'{_str} // {enum_desc}'
            enum_rows.append(_str)

        return '''
    public enum {0}
    {{
        {1}
    }}
        '''.format(enum_name, codeline.join(enum_rows))

    @staticmethod
    def _convert_datatype(col: str, option: str) -> str:
        res = col.lower()
        if res == 'bool' or res == 'boolean':
            res = 'bool'
        elif res == 'datetime':
            res = 'DateTime'

        from re import match
        if match(r'@null', option):
            res = res + '?'
        return res

    def _get_default_csharp(self, data: str):
        return '''
//------------------------------------------------------------------------------
// <auto-generated>
//    해당 파일은 <Git서버[Excel] Push>호출로 인한 자동생성 코드입니다.
//    TAG: {0}
//    GIT URL: {1}
//    COMMIT: {2}/{3}
//
//    * 해당 파일을 수정할 시 잘못된 동작이 발생할 수 있습니다.
//    * 기획자가 Excel파일 편집후 GIT서버에 업로드시 해당 파일은 자동으로 재생성 됩니다.
// </auto-generated>
//------------------------------------------------------------------------------

namespace Planing.Data
{{
    using System;
    using System.IO;
    using UnityEngine;

    {4}
}}
        '''.format(self.TAG, self.GIT_URL, self.COMMIT_URL, self.COMMIT_ID, data)

    def _get_default_entity(self, data: str):
        _data = '''
    public class TABLE_DATA
    {{
        public int id {{ get; set; }}
    }}

    {0}
        '''.format(data)
        return self._get_default_csharp(_data)
