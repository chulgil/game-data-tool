
# import all required library
import git
import xlrd
import json
import pandas as pd
from pathlib import Path

PATH_FOR_EXCEL = "./excel/Data.xlsx"
PATH_FOR_GIT = Path(".git")
sheets = xlrd.open_workbook(PATH_FOR_EXCEL).sheet_names()

# 시트명으로 JSON파일 생성
for sheet in sheets:
    excel_data_fragment = pd.read_excel(PATH_FOR_EXCEL, sheet_name=sheet)
    json_data = excel_data_fragment.to_json(orient='records')
    json_str = json.loads(json_data)

    print('\n', json_str)
    with open("./json/" + sheet + ".json", "w", encoding='utf-8') as f:
        json.dump(json_str, f, ensure_ascii=False, indent=4, sort_keys=True, separators=(',', ': '))


