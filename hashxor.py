import binascii
import hashlib


class HashXor:
    def __init__(self,hash):
        self.hash = hash[0:16]
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

        return bytes(result)


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

        return bytes(result)

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
    hash = "c11b784f3b23fd5130f7e0754d6b2e34"
    hash = binascii.unhexlify(hash)
    print(hash[0:16])
    print()
    a = HashXor(hash)
    data = "fdb39984fa973e3054ea4777075d4543b29ad5a9a1b2782350eb4272714e3f42d3f5bccac3ce02656db46520581d0508c396a1b1d9bf10176eda7f555e7a017bfed891d4"
    data = binascii.unhexlify(data)
    print(data)
    data_len = len(data)
    decry = a.decrypt(data,data_len)
    print(decry)
    # test = [0 for i in range(1000)]
    # for i in range(len(decry)):
    #     test[i]=hex(decry[i])
    # print(test)


