import multiprocessing
import os
import threading
import socket
import time
import sys
import commonlib
import select
import packetutil
from multiprocessing import Process, Lock, Queue

socket.setdefaulttimeout(10)
CONFPATH = "conf/dbms_tester.conf"

class DbmsUser:
    def __init__(self):
        pass

    def run(self):
        conf = commonlib.readConfFile(CONFPATH)

        packet_list = conf['PACKET_LIST_CSV']
        packet_list = commonlib.getlistfromcsv(packet_list)

        target_list = conf['SERVER_LIST_CSV']
        target_list = commonlib.getlistfromcsv(target_list)

        cert_info_list = conf['CERT_LIST_CSV']
        cert_info_list = commonlib.getlistfromcsv(cert_info_list)

        # 프로세스 개수와 타겟 개수가 1대1 매칭이 안될 경우
        if len(target_list) != int(conf['SERVICE_COUNT']):
            return

        if len(packet_list) != int(conf['SERVICE_COUNT']):
            return

        process_count = int(conf['SERVICE_COUNT'])

        curCount = 0

        def callback(arg):
            arg[0] = arg[0] + 1

        callback_arg = [curCount]
        start_time = time.time()
        process_list = []
        q = Queue()
        for i in range(process_count):
            hexdata = commonlib.readFileLines(str(''.join(packet_list[i])))
            packets = packetutil.PacketReader.read(hexdata)
            dbms_sock_object = packetutil.VirtualConnector(target_ip=str(target_list[i][1]),service_port=int(target_list[i][2]), dbsafer_ip=conf['DBSAFER_GW_IP'], dbsafer_port=int(conf['DYNAMIC_PORT']),svcnum=int(target_list[i][3]),cert_info_list=cert_info_list[i])
            process_list.append(Worker(i + 1,  dbms_sock_object,packets,
                                      conf, target_list[i],callback, callback_arg, q))
        for i in process_list:
            print('process starting : ', i.num)
            i.start()
        for i in process_list:
            i.join()
            print('process joined.', i.num)
        elapsed_time = time.time() - start_time
        print('\n')
        print(
            'Done. [%02d:%02d:%02.2d]' % (int(elapsed_time) / 60 / 60, int(elapsed_time) / 60 % 60, elapsed_time % 60))

class Worker(multiprocessing.Process):
    def __init__(self, num, dbms_sock_object, packets,
                 conf, target_list,callback, callback_arg, q):
        multiprocessing.Process.__init__(self)
        self.num = num
        self.dbms_sock_object = dbms_sock_object
        self.packets = packets
        self.conf = conf
        self.target_list = target_list
        self.callback = callback
        self.callback_arg = callback_arg
        self.cancelFlag = False
        self.progressCallback = None
        self.progressCallbackArg = None
        self.q = q

    def run(self):
        '''
        시작 하는 함수

        '''

        thread_list = []

        # 반복 횟수가 0 일경우
        if self.conf['REPEAT_COUNT'] == 0:
            pass
        # 반복 횟수가 지정되어 있을 경우
        else:
            for i in range(int(self.conf['REPEAT_COUNT'])):
                # 쓰레드 생성
                for j in range(int(self.conf['THREAD_PER_PROC'])):
                    thread = threading.Thread(target=self.test)
                    thread_list.append(thread)
                for j in thread_list:
                    j.start()
                for j in thread_list:
                    j.join()

                if (self.cancelFlag):
                    break

        if self.cancelFlag:
            print("Job canceled %d." % self.num)
        else:
            print("End %d." % self.num)

    def cancel(self):
        self.cancelFlag = True

    def test(self,j):
        '''
        패킷 테스트 하는 함수
        '''
        if self.cancelFlag:
            self.callback(self.callback_arg)
            return
        dbms_sock = self.dbms_sock_object.dbModeConnect(512)
        self.q.put(dbms_sock)

        while True:
            pos = 0
            packet = ''
            # 패킷 길이 확인 및 전송
            while pos < len(self.packets):
                if pos < len(self.packets):
                    packet = self.packets[pos]
                pos_end = pos + 1

                while pos_end < len(self.packets):
                    packet2 = self.packets[pos_end]
                    if packet.direction != packet2.direction:
                        break
                    pos_end += 1
                try:
                    # 패킷 전송
                    self.send_packet(pos, pos_end, dbms_sock)

                except socket.timeout:
                    print('T(%d/0)' % len(packet.packet), end=' ')
                    sys.stdout.flush()
                if self.progressCallback:
                    self.progressCallback(self.progressCallbackArg, pos_end - pos)
                pos = pos_end

                if self.cancelFlag:
                    break

            if int(self.conf['SLEEP']) != 0:
                time.sleep(int(self.conf['SLEEP']))

            self.callback(self.callback_arg)

        print("Session wait %d." % self.num)

    def send_packet(self, pos, pos_end, dbms_sock):
        try:
            sendedPacket = 0
            sended = 0
            recvedPacket = 0
            recved = 0
            direction = self.packets[pos].direction
            if direction:
                inputs = []
                outputs = [dbms_sock, ]
            else:
                inputs = [dbms_sock, ]
                outputs = []

            packetLen = pos_end - pos

            (readable, writeable, exceptional) = select.select(inputs,outputs,inputs)
            print(self.packets[pos].packet)
            if not (readable or writeable or exceptional):
                # timeout
                while recvedPacket < packetLen:
                    sys.stdout.flush()
                    recved = 0
                    recvedPacket += 1
                return

            for s in readable:
                sendSize = 0
                if pos + recvedPacket < len(self.packets):
                    sendSize = len(self.packets[pos].packet)
                r = s.recv(100000000)

                while r:
                    if recvedPacket >= packetLen:
                        print('X', end=' ')
                        sys.stdout.flush()
                        break
                    packet = self.packets[pos + recvedPacket].packet

                    compareSize = len(packet) - recved
                    if len(r) < compareSize:
                        compareSize = len(r)
                    recved += compareSize
                    if recved == len(packet):
                        recvedPacket += 1
                        if recvedPacket == packetLen:
                            if len(r) != compareSize:
                                # has extra packet.
                                sys.stdout.flush()
                                break
                        recved = 0
                        sys.stdout.flush()

                    r = r[compareSize:]

            for s in writeable:
                print(pos + sendedPacket)
                packet = self.packets[pos + sendedPacket].packet
                if sended == 0:
                    r = s.send(packet)
                else:
                    r = s.send(packet[sended:])
                if r > 0:
                    sended += r
                    if len(packet) <= sended:
                        sended = 0
                        sendedPacket += 1
                        if int(self.conf['SLEEP']) != 0:
                            time.sleep(int(self.conf['SLEEP']))

        except Exception as e:
            print("error")

if __name__ == '__main__':
    abc = DbmsUser()
    abc.run()