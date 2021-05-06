import binascii
import hashlib


class HashXor:
    def __init__(self,hash):
        self.hash = hash
        self.pos = 0
        self.old_ch = 127

    def encrypt(self, data, data_len):
        result = [0 for i in range(data_len)]

        data_index = 0
        while data_len > 0:
            result[data_index] = data[data_index] ^ self.hash[self.pos]
            result[data_index] = result[data_index] ^ self.old_ch
            self.old_ch = result[data_index]

            data_len = data_len - 1
            self.pos = self.pos + 1
            data_index = data_index + 1

            if self.pos == len(self.hash):
                self.pos = 0

        self.pos = 0
        self.old_ch = 127
        return result


    def decrypt(self, data, data_len):
        ch = ""
        result = [0 for i in range(data_len)]
        data_index = 0
        while data_len > 0:
            ch = data[data_index]
            result[data_index] = data[data_index] ^ self.hash[self.pos]
            result[data_index] = result[data_index] ^ self.old_ch

            self.old_ch = ch
            data_len = data_len - 1
            self.pos = self.pos + 1
            data_index = data_index + 1

            if self.pos == len(self.hash):
                self.pos = 0

        self.pos = 0
        self.old_ch = 127

        return result

class HashMd5:
    def __init__(self,text):
        self.text = text

    def hashing(self):
        result = [0 for i in range(4096)]

        hashing = hashlib.md5()
        hashing.update(self.text[16:])
        result = hashing.hexdigest()

        return result


if __name__ == '__main__':
    #md5 해시값
    hash = "07f119b85cb7b1e3974f880d28ff6337"
    hash = binascii.unhexlify(hash)
    a = HashXor(hash)
    data = "47b6af174bfc4dae7555bade985d1e5930b1db0639fb38be0977cdf7f13e73745d9da42d46c74194235c"
    data = binascii.unhexlify(data)
    print(data)
    data_len = len(data)
    decry = a.decrypt(data,data_len)
    print(decry)
    test = [0 for i in range(100)]
    for i in range(len(decry)):
        test[i]=hex(decry[i])
        print(test[i])

    #hash 받아서 [0:16] 은 헤더로 들어감 v = hash[0:16] -> HashXor(v)
    #hash 받아서 나머지는 바디로 들어감
