import binascii
import hashlib


class HashXor:
    '''
    wta packet encryption class

    Encrypt plaintext using MD5 and XOR
    '''
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
        # print(result)
        # for i in range(len(result)):
        #     print(hex(result[i])[2:])
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
        print(result)
        print(len(result))
        return bytes(result)

class HashMd5:
    '''
    A class that hashes using MD5
    '''
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
    hash = "d7215ec453082f210d944938b0ecd53b"
    hash = binascii.unhexlify(hash)
    print(hash[0:16])
    print()
    a = HashXor(hash)
    data = "a889d7294a3a23325ef38cd15983566dbab9e7237078577637cce2b36dbb4e06b9e1d07b466e706142e19f8908d23520c6d3ad583c021a0d2084"
    data = binascii.unhexlify(data)
    print("dd")
    print(data)
    data_len = len(data)
    print("rrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrr")
    decry = a.decrypt(data,data_len)
    print(decry)
    print(data_len - 24)
    print()
    print()
    print()

    #
    # data = "0000b15c608918a40000009f0000006c0000b09500000000202d20436170747572696e672066726f6d20c0ccb4f5b3dd2028706f7274203331343129202d206c20283c4c423e3c52423e293d3d3d2057696e646f777320746578742064756d70203d3d3d0d0a5174355157696e646f7749636f6e202d20436170747572696e672066726f6d20c0ccb4f5b3dd2028706f72742033313431290d0a0d0a3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d0d0a"
    # data = binascii.unhexlify(data)
    #
    # ha2 = HashMd5(data)
    #
    # hi2 = ha2.hashing()
    # print(hi2)
    # hash = hi2
    # hash = binascii.unhexlify(hash)
    #
    # a = HashXor(hash)
    #
    # b = a.encrypt(data,len(data))
    # print(b)


   #
    # b = HashXor(hash)
    # data = "0000004a60891896000000220000000000000000000000004c6f67696e3a20746573743132333435203139322e3136382e342e31393020343039362030"
    # data = binascii.unhexlify(data)
    # c = b.encrypt(data,len(data))
    # print(c)
    # # test = [0 for i in range(1000)]
    # # for i in range(len(decry)):
    # #     test[i]=hex(decry[i])
    # # print(test)
    # haha = "0000004a60891896000000310000000000000000000000004c6f67696e3a207465737431323334352031302e37372e3136322e31312031373637362030"
    #
    # haha = binascii.unhexlify(haha)
    #
    # ha = HashMd5(haha)
    # hi = ha.hashing()
    #
    # print(hi)
    #
    # hash = hi
    # hash = binascii.unhexlify(hash)
    #
    # a = HashXor(hash)
    #
    # b = a.encrypt(haha,len(haha))
    # print(b)

