import socket as skt
from struct import pack
from ipaddress import IPv4Address



class OmsHelloPkt:
    "oms_dms 접속시 전달할 요청메시지 패킷 Payload"
    def __init__(self):
        pass
    
    def set(self, command=b'10',
            length=b'xffff', 
            structhash=b'0',
            checkcode=b'CK'):
        self.command = command
        self.length = length
        self.structhash = structhash
        self.checkcode = checkcode
    

class OmsLoginPkt:
    
    def __init__(self):
        pass
    
    def set(self, 
            cmd,):
        pass