import socket

class Packet:
    def __init__(self):
        self.tcp_sock = -1
        self.udp_sock = -1

    def connectTcp(self,host,port):
        self.tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        if self.tcp_sock.connect((host,port)) == -1:
            return -1

    def connectUdp(self,host,port):
        self.udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        if self.udp_sock.connect((host,port)) == -1:
            return -1

    def sendTcpPacket(self,msg):
        msg = msg.encode()
        len = self.tcp_sock.send(msg)

        return len

    def sendUdpPacket(self,msg):
        if not type(msg) is bytes:
            msg = msg.encode()
        len = self.udp_sock.send(msg)

        return len

    def recvTcpPacket(self,size):
        data = self.tcp_sock.recv(size)

        return data.decode()

    def recvUdpPacket(self,size):
        data = self.udp_sock.recv(size)

        return data.decode()

    def closeTcpPacket(self):
        self.tcp_sock.close()

    def closeUdpPacket(self):
        self.udp_sock.close()

if __name__ == '__main__':
    a = Packet()
    a.connectUdp("127.0.0.1",50011)
    print(a.sendUdpPacket("."))
    print(a.recvUdpPacket(1024))
