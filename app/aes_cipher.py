import base64
from Cryptodome.Cipher import AES


class AESCipher(object):

    def __init__(self, key):
        self.bs = AES.block_size
        self.key = key.encode('utf-8')
        self.iv = bytes([0x00] * 16)

    def encrypt(self, content):
        cipher = AES.new(self.key, AES.MODE_CBC, self.iv)
        content_padding = self._pad(content)
        encrypt_bytes = cipher.encrypt(content_padding.encode('utf-8'))
        result = str(base64.b64encode(encrypt_bytes), encoding='utf-8')
        return result

    def decrypt(self, content):
        cipher = AES.new(self.key, AES.MODE_CBC, self.iv)
        content = base64.b64decode(content)
        text = cipher.decrypt(content).decode('utf-8')
        return text

    def _pad(self, s):
        return s + (self.bs - len(s) % self.bs) * chr(self.bs - len(s) % self.bs)
