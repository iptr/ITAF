import os
import threading
import socket
import time
import sys
import select
import commonlib
from multiprocessing import Process, Lock, Queue
import multiprocessing
import packetutil



# 스택 사이즈 결정
if sys.version_info >= (3, 5):
	threading.stack_size(1024 * 1024 * 1024 * 2)

# 기본 타임아웃 시간 설정
#socket.setdefaulttimeout(100)

class Worker(multiprocessing.Process):

	def __init__(self, num, connector, packets,
				 timeout, repeat, sleep, verbose,
				 callback, callback_arg,thread_count,que):
		multiprocessing.Process.__init__(self)
		self.num = num
		self.connector = connector
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
		self.q = que

	def setProgressCallback(self, callback, callbackarg):
		self.progressCallback = callback
		self.progressCallbackArg = callbackarg

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

		# try:
		print("Connecting %d..." % self.num)
		# 각 세션 소켓 반환
		(dbms_sock) = self.connector.dbmsModeServer()
		self.q.put(dbms_sock)

		print("Connected %d." % self.num)


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

			if dbms_sock:
				pass
			else:
				break

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
			print(pos,pos_end,len(self.packets))
			if self.cancelFlag:
				break

		if self.sleep != 0:
			time.sleep(self.sleep)

		print("Session wait %d." % self.num)

		self.callback(self.callback_arg)



	def send_packet(self, pos, pos_end, dbms_sock):
		'''
		select를 이용하여 패킷 송수신을 담당하는 함수
		'''
		try:
			sendedPacket = 0
			sended = 0
			recvedPacket = 0
			recved = 0
			direction = self.packets[pos].direction
			if direction:
				inputs = [dbms_sock, ]
				outputs = [ ]
			else:
				inputs = [ ]
				outputs = [dbms_sock, ]

			packetLen = pos_end - pos

			(readable, writeable, exceptional) = select.select(inputs, outputs, inputs)

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
				print(pos)
				packet = self.packets[pos].packet
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

def runTest(process_count = 128, thread_count = 100):
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

	start_time = time.time()

	process_list = []

	q = Queue()

	for i in range(process_count):
		connecte = packetutil.VirtualServer(3306 + i, "192.168.4.87", 3970,1)
		process_list.append(Worker(i + 1, connecte, packets,
							  time_out, repeat, sleep_time, verbose,
							  callback, callback_arg,thread_count,q))

	for i in process_list:
		print('process starting : ', i.num)
		i.start()
	for i in process_list:
		i.join()
		print('process joined.', i.num)

	q.close()

	elapsed_time = time.time() - start_time
	print('\n')
	print('Done. [%02d:%02d:%02.2d]' % (int(elapsed_time) / 60 / 60, int(elapsed_time) / 60 % 60, elapsed_time % 60))

if __name__ == '__main__':
	#cProfile.run("runTest(1,2)")
	runTest(30,50)