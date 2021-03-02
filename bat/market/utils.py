
from Crypto.Cipher import AES, DES


def generate_uri(url, query_parameters):
    uri = url + "?"
    for key, value in query_parameters.items():
        uri = uri + key + "=" + value + "&"
    print(uri[:-1])
    return uri[:-1]


class CryptoCipher(object):

    @classmethod
    def encrypt(cls, text):
        text = str(text)
        AES_obj = AES.new('This is a key123', AES.MODE_CBC, 'This is an IV456')
        return AES_obj.encrypt(text)

    @classmethod
    def decrypt(cls, text):
        AES_obj = AES.new('This is a key123', AES.MODE_CBC, 'This is an IV456')
        plain_text = AES_obj.decrypt(text).decode("utf-8")
        return plain_text
