import packetcontroler as pt


#테스트 코드
def dbsaferUdpPacket():
    packet = pt.Packet()
    host = "127.0.0.1"
    port = [21114 ,50011 ,3140 ,3159 ,3161 ,3143 ,3158 ,3160, 3120,3126]
    data = bytes.fromhex('00')
    for i in range(len(port)):
        packet.connectUdp(host,port[i])
        packet.sendUdpPacket(data)
        packet.closeUdpPacket()
    data = bytes.fromhex('01')
    for i in range(len(port)):
        packet.connectUdp(host, port[i])
        packet.sendUdpPacket(data)
        packet.closeUdpPacket()

if __name__ == '__main__':
    dbsaferUdpPacket()
