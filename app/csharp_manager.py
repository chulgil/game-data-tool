import logging
import os
from pprint import pprint

import yaml
import pymsteams as pymsteams
from re import match
from pathlib import Path


class CSharpManager:

    def __init__(self, branch: str, commit: str, save_dir: Path):
        self.BRANCH = branch
        if commit == '':
            commit = 'default'
        self.COMMIT = commit
        self._error_msg = []
        self._info = f'[{branch} 브랜치] C#'
        self.ROOT_DIR = Path(__file__).parent.parent
        self.PATH_FOR_SAVE = save_dir
        self.PATH_FOR_SAVE_SERVER = self.PATH_FOR_SAVE.joinpath('Server')
        self.PATH_FOR_SAVE_PLANNING = self.PATH_FOR_SAVE.joinpath('Planning')
        self.PATH_FOR_CONFIG = self.ROOT_DIR.joinpath('config.yaml')
        self.PATH_FOR_ENTITY = self.PATH_FOR_SAVE_PLANNING.joinpath('AutoGenerated_PlaningEntity.cs')
        self.PATH_FOR_ENUM = self.PATH_FOR_SAVE_PLANNING.joinpath('AutoGenerated_PlaningEnum.cs')
        self.PATH_FOR_S_PROTOCOL = self.PATH_FOR_SAVE_SERVER.joinpath('AutoGenerated_ServerProtocol.cs')
        self.PATH_FOR_S_ENTITY = self.PATH_FOR_SAVE_SERVER.joinpath('AutoGenerated_ServerEntity.cs')
        self.PATH_FOR_S_ENUM = self.PATH_FOR_SAVE_SERVER.joinpath('AutoGenerated_ServerEnum.cs')
        self.PATH_FOR_S_PROXY = self.PATH_FOR_SAVE_SERVER.joinpath('AutoGenerated_ServerProxy.cs')
        self.TAB = '    '
        self.BR = '<br/>'

        # Config 파일 설정
        with open(self.PATH_FOR_CONFIG, 'r') as f:
            config = yaml.safe_load(f)
        self._set_config(config)
        self._set_folder()

    def _set_config(self, config):
        self.teams = pymsteams.connectorcard(config['TEAMS']['DESIGNER_URL'])
        self.COMMIT_URL = config['GITSERVER']['EXCEL_URL'] + '/src/commit'
        self.GIT_URL = config['GITSERVER']['EXCEL_URL']

    def _set_folder(self):
        if not Path(self.PATH_FOR_SAVE_SERVER).is_dir():
            os.makedirs(self.PATH_FOR_SAVE_SERVER)
        if not Path(self.PATH_FOR_SAVE_PLANNING).is_dir():
            os.makedirs(self.PATH_FOR_SAVE_PLANNING)

    def save_entity(self, table_info: dict):
        _table_name = ''
        _script = ''
        for key in table_info.keys():
            _table_name = str(key).upper()
            rows = table_info[key]
            new_script = self._convet_entity(_table_name, rows)
            if new_script != '':
                logging.info(f'{self._info} 스키마 저장 완료: {_table_name}')
                _script = _script + new_script
        _script = self._get_script_entity(_script)
        with open(self.PATH_FOR_ENTITY, "w", encoding='utf-8') as f:
            f.write(_script)

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
        _enum_name = ''
        _script = ''
        for _enum_name, enum_data in enum_info.items():
            _script = _script + self._convert_enum(_enum_name, enum_data, 1)
        _script = self._get_default_script_planing(_script)
        try:
            # 지정한 경로로 Prisma 스키마 파일 저장
            with open(self.PATH_FOR_ENUM, "w", encoding='utf-8') as f:
                f.write(_script)
        except Exception as e:
            logging.error(f'{self._info} ENUM 저장 Error: {self.PATH_FOR_ENUM.stem}\n{str(e)}')

    def save_protocol(self, info: dict):
        """
        Markdown에서 변환된 데이터를 C# Protocol으로 변환후 파일로 저장한다.
        # {'ClassName':
        #   { 'desc': [' 해당 요청은 보상박스 언락입니다.',' 요청과 응답 프로토콜은 아래와 같습니다.'],
        #     'req_info': {'100': [(' long ', ' facility_key', ' 치료소key'),(' long ', ' facility_key ', ' 치료소 key ')]},
        #     'res_info': {'101': [('clinic_resp', 'clinic_resp','치료소 정보'),('goods_info[]','goods_infos',' 재화정보')]}
        # }}
        """
        _using = '''
using AsyncModel;
using System.Collections;
using AutoGenerated.Server.Data;
using Server;'''
        _name_space = 'AutoGenerated.Server.Protocol'
        _script_protocol = ''
        _script_proxy = ''
        for _cls_name, _cls in info.items():
            _script_protocol = _script_protocol + self._get_script_protocol(_cls_name, _cls['desc'], _cls['req_info'],
                                                                            _cls['res_info'])

            _script_proxy = _script_proxy + self._get_script_proxy(_cls_name, _cls['desc'], _cls['req_info'],
                                                                   _cls['res_info'])
        _script_proxy = '''
    public partial class ServerProxy_Stateless : ServerProxy
    {{{0}
    }}'''.format(_script_proxy)

        _script_protocol = self._get_default_script_server(_using, _name_space, _script_protocol)
        _script_proxy = self._get_default_script_server(_using, _name_space, _script_proxy)

        try:
            with open(self.PATH_FOR_S_PROTOCOL, "w", encoding='utf-8') as f:
                f.write(_script_protocol)
            with open(self.PATH_FOR_S_PROXY, "w", encoding='utf-8') as f:
                f.write(_script_proxy)
        except Exception as e:
            logging.error(f'{self._info} 프로토콜 저장 Error: {self.PATH_FOR_S_PROTOCOL.stem}\n{str(e)}')

    def save_server_enum(self, enum_info: dict):
        """
        MARKDOWN에서 변환된 Enum 데이터를 C# Enum으로 변환후 파일로 저장한다.

        :param enum_info:
            'StatusCode': {
                'desc': [' 설명입니다.', ' '],
                'items': {
                    'NONE': ['0', 'NONE'],
                    'nohandler': ['300', 'no handler'],
                    'wrong_packet': ['-1', '잘못된 패킷데이터']
                }
            }
        """
        _enum_name = ''
        _script = ''
        for _enum_name, enum_data in enum_info.items():
            _dlist = [f'{self._comment(1)} {x.strip()}{self.BR}' for x in enum_data['desc'] if x.strip() != '']
            _cls_desc = '\n'.join(_dlist)
            _script = _script + f'\n{self._comment(1)} <summary>\n{_cls_desc}\n{self._comment(1)}</summary>'
            _script = _script + self._convert_enum(_enum_name, enum_data['items'], 1)
        _script = self._get_default_script_server('', 'AutoGenerated.Server.Data', _script)
        try:
            # 지정한 경로로 Prisma 스키마 파일 저장
            with open(self.PATH_FOR_S_ENUM, "w", encoding='utf-8') as f:
                f.write(_script)
        except Exception as e:
            logging.error(f'{self._info} ENUM 저장 Error: {self.PATH_FOR_S_ENUM.stem}\n{str(e)}')

    def save_server_entity(self, info: dict):
        """
        Markdown에서 변환된 데이터를 C# Protocol으로 변환후 파일로 저장한다.

        :param info:
            'ClassName': {
                'desc': [' 해당 요청은 보상박스 언락입니다.',' 요청과 응답 프로토콜은 아래와 같습니다.'],
                'req_info': {
                    '100': [(' long ', ' facility_key', ' 치료소key'),(' long ', ' facility_key ', ' 치료소 key ')]},
                'res_info': {
                    '101': [('clinic_resp', 'clinic_resp','치료소 정보'),('goods_info[]','goods_infos',' 재화정보')]
                }
            }
        """
        _using = '''
using System.Collections;
using Server.Data;'''
        _name_space = 'AutoGenerated.Server.Protocol'
        _script = ''
        for _name, _data in info.items():
            _script = _script + self._get_script_server_entity(_name, _data['desc'], _data['items'])
        _script = self._get_default_script_server(_using, 'AutoGenerated.Server.Data', _script)
        try:
            with open(self.PATH_FOR_S_ENTITY, "w", encoding='utf-8') as f:
                f.write(_script)
        except Exception as e:
            logging.error(f'{self._info} 서버 엔티티 저장 Error: {self.PATH_FOR_S_ENTITY.stem}\n{str(e)}')

    def _convet_entity(self, table_name: str, rows: list) -> str:
        """
        C# 스크립트 포멧으로 변환

        :param table_name: 테이블명
        :param rows:
            디비필드, 디비타입, 스키마타입
            ['id', 'long', '@auto']
        """
        script = ''
        try:
            if len(rows) < 1:
                return ''
            for row in rows[1:]:
                # 순서 주의 : 컨버팅 되지 않은 타입값으로 디비 스키마 값 변경
                d_type = self._convert_datatype(row[1], row[2])
                field = row[0]
                desc = str(row[3]).replace('\n', ' ')  # 메모의 개행 공백 치환
                if desc != '':
                    script = script + f'\n{self._comment(2)}<value>{desc}</value>'
                script = script + f'\n{self._tab(2)}public {d_type} {field} ' + '{ get; set; }'
        except Exception as e:
            logging.error(f'{self._info} 스키마 변환 Error: {table_name}\n{str(e)}')

        return '''
    public class {0} : TABLE_DATA
    {{{1}
    }}
    '''.format(table_name, script)

    def _convert_enum(self, enum_name: str, enum_data: dict, indent: int = 0) -> str:
        start = ''
        for i in range(0, indent):
            start = start + self.TAB
        newline = '\n' + start
        codeline = newline + self.TAB
        enum_rows = []
        for _id, item in enum_data.items():
            _str = ''
            enum_key = _id
            enum_value = item[0]
            enum_desc = item[1]
            if enum_desc != '':
                _str = f'{_str}{self._comment()}<summary>{enum_desc}</summary>\n{self.TAB * 2}'
            _str = f'{_str}{enum_key} = {enum_value},'
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

        enum_type = match(r'@enum\(?(\S+)\)', option)
        if enum_type:
            res = enum_type.group(1)
            return res

        if match(r'@null', option):
            res = res + '?'
        return res

    def _get_default_script_planing(self, script: str):
        return '''/*--------------------------------------------------------------------------------
  해당 파일은 Git서버<Excel Push>호출로 인한 자동생성 코드입니다.
  마지막 태그<{0}>기준으로 프로덕션에 픽스되며 이외 커밋은 개발용도로 생성됩니다.

  * 해당 파일을 수정할 시 잘못된 동작이 발생할 수 있습니다.
  * 기획자가 Excel파일 편집후 Git서버에 업로드시 해당 파일은 자동으로 재생성 됩니다.

  {1}/{0}
--------------------------------------------------------------------------------*/
using System;
using System.IO;
using UnityEngine;
    
namespace AutoGenerated.Planing.Data
{{
    {2}
}}'''.format(self.COMMIT, self.COMMIT_URL, script)

    def _get_script_entity(self, data: str):
        _script = '''
    public class TABLE_DATA
    {{
        public int id {{ get; set; }}
    }}

    {0}
        '''.format(data)
        return self._get_default_script_planing(_script)

    def _get_default_script_server(self, using: str, namespace: str, script: str):
        return '''/*--------------------------------------------------------------------------------
  해당 파일은 Git서버<Markdown Push>호출로 인한 자동생성 코드입니다.
  마지막 태그<{0}>기준으로 프로덕션에 픽스되며 이외 커밋은 개발용도로 생성됩니다.

  * 해당 파일을 수정할 시 잘못된 동작이 발생할 수 있습니다.
  * 개발자가 Markdown파일 편집후 Git서버에 업로드시 해당 파일은 자동으로 재생성 됩니다.

  {1}/{0}
--------------------------------------------------------------------------------*/
{2}

namespace {3}
{{
    {4}
}}'''.format(self.COMMIT, self.COMMIT_URL, using, namespace, script)

    def _get_script_protocol(self, cls_name: str, cls_desc: list, req: dict, res: dict):
        # /// 프로토콜 설명입니다.
        # /// 프로토콜 정보 : 요청[101] 응답[102]
        # _req : (' long  ', ' server_time             ', ' 서버시간  ')
        # _res : (' goods_info[] ', ' goods_infos      ', '         ')
        _req_id = next(iter(req))
        _res_id = next(iter(res))
        _cls_desc = []
        _cls_desc = _cls_desc + cls_desc
        _cls_desc.append(f' 프로토콜 코드 [ 요청 : {_req_id}, 응답 : {_res_id} ]')
        _dlist = [f'{self._comment(1)} {x.strip()}{self.BR}' for x in _cls_desc if x.strip() != '']
        _dlist.insert(0, '')
        _cls_desc = '\n'.join(_dlist)

        # 데이터 정제
        req_data = []
        res_data = []
        for _req in req[_req_id]:
            req_data.append([x.strip() for x in _req])
        for _res in res[_res_id]:
            res_data.append([x.strip() for x in _res])

        # /// <request>
        #     reward_key : UnLock 상자 아이템 Key<br/>
        # ///</request>
        _dlist = [f'{self._comment(1, 1)}{x[1]}: {x[2]}' for x in req_data]
        _dlist.insert(0, '') if len(_dlist) > 0 else None
        _req_desc = '\n'.join(_dlist)
        # /// reward_info : 훈련할 민병대
        # /// reward_info[] : 훈련할 민병대
        _dlist = [f'{self._comment(1, 1)}{x[0]}: {x[2]}' for x in res_data]
        _dlist.insert(0, '') if len(_dlist) > 0 else None
        _res_desc = '\n'.join(_dlist)

        _in_tab = self.TAB + self.TAB
        if len(req_data) > 0:
            _dlist = [f'{_in_tab}public {x[0]} {x[1]};' for x in req_data]
            _dlist.insert(0, '')
            _req_code = '\n'.join(_dlist)
        else:
            _req_code = ''
        if len(res_data) > 0:
            _dlist = [f'{_in_tab}{self.TAB} public {x[0]} {x[1]};' for x in res_data]
            _dlist.insert(0, '')
            _res_code = '\n'.join(_dlist)
        else:
            _res_code = ''
        return '''
    /// <summary>{0}
    /// </summary>
    /// <request>{1}
    /// </request>
    /// <response>{2}
    /// </response>
    public class {3} : common_structure
    {{{4}
        
        public class result : common_response
        {{{5}
        }}
        
        public Delivery<Response<result>> Do() 
        {{
            return Transaction.Do<{3}, Response<result>>(this); 
        }}
    }}
    '''.format(_cls_desc, _req_desc, _res_desc, cls_name, _req_code, _res_code)

    def _get_script_proxy(self, cls_name: str, cls_desc: list, req: dict, res: dict):
        _req_id = next(iter(req))
        _res_id = next(iter(res))
        _cls_desc = []
        _cls_desc = _cls_desc + cls_desc
        # /// 프로토콜 설명입니다.<br/>
        # /// 프로토콜 정보 : 요청[101] 응답[102]
        _cls_desc.append(f' 프로토콜 코드 [ 요청 : {_req_id}, 응답 : {_res_id} ]')
        _dlist = [f'{self._comment(2)} {x.strip()}{self.BR}' for x in _cls_desc if x.strip() != '']
        _dlist.insert(0, '')
        _cls_desc = '\n'.join(_dlist)

        # 데이터 정제
        req_data = []
        res_data = []
        for _req in req[_req_id]:
            req_data.append([x.strip() for x in _req])
        for _res in res[_res_id]:
            res_data.append([x.strip() for x in _res])

        # /// <param name="rewardKey">UnLock 상자 아이템</param>
        _dlist = [f'{self._comment(2, 0)} <param name="{self.snake_to_camel(x[1])}">{x[2]}</param>' for x in req_data]
        _dlist.insert(0, '') if len(_dlist) > 0 else None
        _req_desc = '\n'.join(_dlist)
        # /// reward_info : 훈련할 민병대
        # /// reward_info[] : 훈련할 민병대
        _dlist = [f'{self._comment(2, 1)}{x[0]}: {x[2]}' for x in res_data]
        _dlist.insert(0, '') if len(_dlist) > 0 else None
        _res_desc = '\n'.join(_dlist)

        # int rewardKey, long userId
        _dlist = [f'{self._tab(3)}{x[0]} {self.snake_to_camel(x[1])},' for x in req_data]
        _dlist.insert(0, '')
        _req_code = '\n'.join(_dlist)
        # reward_key = rewardKey, user_id = userId
        _dlist = [f'{self._tab(4)}{x[1]} = {self.snake_to_camel(x[1])},' for x in req_data]
        _dlist.insert(0, '')
        _res_code = '\n'.join(_dlist)
        return '''
        
        /// <summary>{0}
        /// </summary>
        /// <param name="gameInfo">GameInfo</param>{1}
        /// <param name="onResultHandler">response</param>
        /// <response>{2}
        /// </response>
        public void Request{3}(GameInfo gameInfo,{4}
            Action<Response<{3}.result>> onResultHandler)
        {{ 
            new {3}()
            {{
                uuid = gameInfo.UUID,{5}
                cmd = {6},
            }}.Do().Then((result) =>
            {{
                if (!OnErrorHandler(result))
                {{
                    onResultHandler(result);
                }}
            }});
        }}'''.format(_cls_desc, _req_desc, _res_desc, cls_name, _req_code, _res_code, _req_id)

    def _get_script_server_entity(self, cls_name: str, cls_desc: list, info: dict):

        """
        C# 스크립트 포멧으로 변환

        :param cls_name: 클래스명
        :param cls_desc: 클래스 설명 (개행구분 리스트)
            디비필드, 디비타입, 스키마타입
            ['id', 'long', '@auto']
        """
        script = ''
        _cls_desc = ''
        try:

            _dlist = [f'{self._comment(1)} {x.strip()}</br>' for x in cls_desc if x.strip() != '']
            if len(_dlist) > 0:
                _dlist.insert(0, f'{self._comment()} <summary>')
                _dlist.append(f'{self._comment(1)} </summary>')
                _cls_desc = '\n'.join(_dlist)

            for row in info:
                _type = row[0].strip()
                _field = row[1].strip()
                _desc = row[2].strip()
                if _desc != '':
                    script = script + f'{self._comment(2)}<value>{_desc}</value>\n'
                script = script + f'{self._tab(2)}public {_type} {_field} ' + '{ get; set; }\n'


        except Exception as e:
            logging.error(f'{self._info} 서버 MarkDown 엔티티 변환 Error: {cls_name}\n{str(e)}')
        return '''
    {0}
    public class {1}
    {{
{2}
    }}
    '''.format(_cls_desc, cls_name, script)

    def _comment(self, indent: int = 0, outdent: int = 0) -> str:
        return f'{self._tab(indent)}///{self._tab(outdent)}'

    def _tab(self, indent: int = 1) -> str:
        return f'{self.TAB * indent}'

    @staticmethod
    def snake_to_pascal(text: str) -> str:
        res = text.replace("_", " ").title().replace(" ", "")
        return res

    @staticmethod
    def snake_to_camel(text: str) -> str:
        temp = text.split('_')
        res = temp[0] + ''.join(x.title() for x in temp[1:])
        return res
