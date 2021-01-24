import re
import socket
import random

def skt_chk_ip(addr):
    try:
        socket.inet_aton(addr)
        return True
    except:
        return False
    
def re_chk_ip(addr):
    patt = re.compile("((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)")
    if patt.fullmatch(addr):
        return True
    else:
        return False
    
    
if __name__ == '__main__':
    for i in range(1000):
        temp = []
        for j in range(4):
            temp.append(str(random.randrange(0,300)))
        addr = '.'.join(temp)
        if skt_chk_ip(addr) != re_chk_ip(addr):
            print(addr, skt_chk_ip(addr), re_chk_ip(addr))
            