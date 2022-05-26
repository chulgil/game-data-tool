import logging
import io
import yaml
from pathlib import Path
import ftplib


class FtpManager:

    def __init__(self, branch: str, version: str):
        self.BRANCH = branch
        self.PATH_FOR_ROOT = Path(__file__).parent.parent
        self.PATH_FOR_CONFIG = self.PATH_FOR_ROOT.joinpath('config.yaml')
        self.EXPORT_JSON = 'data_all.json'
        self.VERSION = version
        self._info = f'[{branch} 브랜치 {version}] '
        with open(self.PATH_FOR_CONFIG, 'r') as f:
            config = yaml.safe_load(f)
        self._set_config(config)

    def _set_config(self, config):
        self.FTP_URL = config['FTPSERVER']['URL']
        self.FTP_USER = config['FTPSERVER']['USER']
        self.FTP_PASS = config['FTPSERVER']['PASS']
        self.FTP_DIR = config['FTPSERVER']['EXPORT_DIR']

    def send(self, save_data: str):
        try:
            _save_path = Path().joinpath(self.FTP_DIR, self.BRANCH, self.VERSION)
            _save_file = _save_path.joinpath(self.EXPORT_JSON)
            ftp_server = ftplib.FTP(self.FTP_URL, self.FTP_USER, self.FTP_PASS)
            ftp_server.encoding = "utf-8"
            self.mkdir(ftp_server, str(_save_path))
            bio = io.BytesIO(save_data.encode())
            ftp_server.storbinary(f'STOR {self.EXPORT_JSON}', bio)
            ftp_server.quit()
            logging.info(self._info + 'FTP전송 완료')
        except Exception as e:
            logging.error(self._info + 'FTP전송 실패 \n' + str(e))

    def mkdir(self, ftp_server: ftplib, current_dir: str):
        if current_dir != "":
            try:
                ftp_server.cwd(current_dir)
            except ftplib.error_perm:
                self.mkdir(ftp_server, "/".join(current_dir.split("/")[:-1]))
                _new_dir = current_dir.split("/")[-1]
                ftp_server.mkd(_new_dir)
                ftp_server.cwd(_new_dir)
