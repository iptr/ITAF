import multiprocessing
import os
import threading
import socket
import time
import sys
import commonlib
import select
import asyncio
import packetutil
from multiprocessing import Process, Lock, Queue

socket.setdefaulttimeout(10)

class DbmsUser:
    def __init__(self,service_port):
        self.service_port = service_port

    def run(self,process_count = 30, thread_count = 300):
        datafile = 'db_test.txt'
        repeat = 1
        time_out = 5
        sleep_time = 0
        verbose = False

        if not os.path.exists(datafile):
            print('ERROR:', datafile, 'is not exist.')
            sys.exit(-1)

        hexdata = commonlib.readFileLines(datafile)
        packets = packetutil.PacketReader.read(hexdata)

        totalTest = repeat * process_count
        curCount = 0

        def callback(arg):
            arg[0] = arg[0] + 1
            print('%d/%d' % (totalTest, arg[0]), end=' ')

        callback_arg = [curCount]

        process_list = []

        q = Queue()
        for i in range(process_count):
            dbms_sock_object = packetutil.VirtualConnector(self.service_port + i, "192.168.4.87", 3970)
            process_list.append(Worker(i + 1,  dbms_sock_object,packets,
                                       time_out, repeat, sleep_time, verbose,
                                       callback, callback_arg, thread_count,q))

        for i in process_list:
            print('process starting : ', i.num)
            i.start()
        for i in process_list:
            i.join()
            print('process joined.', i.num)

class Worker(multiprocessing.Process):
    def __init__(self, num, dbms_sock_object, packets,
                 timeout, repeat, sleep, verbose,
                 callback, callback_arg, thread_count,q):
        multiprocessing.Process.__init__(self)
        self.num = num
        self.dbms_sock_object = dbms_sock_object
        self.packets = packets
        self.timeout = timeout
        self.repeat = repeat
        self.sleep = sleep
        self.verbose = verbose
        self.callback = callback
        self.callback_arg = callback_arg
        self.cancelFlag = False
        self.progressCallback = None
        self.progressCallbackArg = None
        self.thread_count = thread_count
        self.q = q

    def run(self):
        '''
        시작 하는 함수

        '''
        thread_list = []

        # 반복 횟수가 0 일경우
        if self.repeat == 0:
            pass
        # 반복 횟수가 지정되어 있을 경우
        else:
            for i in range(self.repeat):
                # 쓰레드 생성
                for j in range(self.thread_count):
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

    def test(self):
        '''
        패킷 테스트 하는 함수
        '''
        if self.cancelFlag:
            self.callback(self.callback_arg)
            return
        dbms_sock = self.dbms_sock_object.dbModeConnect(512)
        self.q.put(dbms_sock)

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
                time.sleep(0.3)

            except socket.timeout:
                print('T(%d/0)' % len(packet.packet), end=' ')
                sys.stdout.flush()
            if self.progressCallback:
                self.progressCallback(self.progressCallbackArg, pos_end - pos)
            pos = pos_end

            if self.cancelFlag:
                break

        if dbms_sock:
            dbms_sock.close()
        if self.sleep != 0:
            time.sleep(self.sleep)

        print("Session wait %d." % self.num)
        self.callback(self.callback_arg)

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
                        if self.sleep != 0:
                            time.sleep(self.sleep)

        except Exception as e:
            print("error")

if __name__ == '__main__':
    abc = DbmsUser(3306)
    abc.run()