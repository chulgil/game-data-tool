import base64
import hashlib
# from Cryptodome import Random
# from Cryptodome.Cipher import AES
#
#
# class AESCipher(object):
#
#     def __init__(self, key):
#         self.bs = AES.block_size
#         self.key = hashlib.sha256(key.encode()).digest()
#
#     def encrypt(self, raw):
#         # raw = self._pad(raw)
#         cipher = AES.new(self.key, AES.MODE_ECB)
#         return base64.b64encode(cipher.encrypt(raw.encode()))
#
#     def decrypt(self, enc):
#         enc = base64.b64decode(enc)
#         cipher = AES.new(self.key, AES.MODE_ECB)
#         return self._unpad(cipher.decrypt(enc)).decode('utf-8')
#
#     def _pad(self, s):
#         return s + (self.bs - len(s) % self.bs) * chr(self.bs - len(s) % self.bs)
#
#     @staticmethod
#     def _unpad(s):
#         return s[:-ord(s[len(s) - 1:])]
