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

socket.setdefaulttimeout(100)

class rdpServer:
	def __init__(self,service_port):
		self.service_port = service_port

	def run(self,process_count = 1, thread_count = 1):
		datafile = 'packet_tester.txt'
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


		for i in range(process_count):
			terminal_sock_object = packetutil.VirtualConnector(self.service_port + i, "192.168.4.190", 4101 + i)
			process_list.append(Worker(i + 1,  terminal_sock_object,packets,
									   time_out, repeat, sleep_time, verbose,
									   callback, callback_arg, thread_count))

		for i in process_list:
			print('process starting : ', i.num)
			i.start()
		for i in process_list:
			i.join()
			print('process joined.', i.num)

class Worker(multiprocessing.Process):
	def __init__(self, num, terminal_sock_object,packets,
				 timeout, repeat, sleep, verbose,
				 callback, callback_arg,thread_count):
		multiprocessing.Process.__init__(self)
		self.num = num
		self.terminal_sock_object = terminal_sock_object
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

		pos = 0
		packet = ''

		terminal_sock = self.terminal_sock_object.rdpModeConnect()

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
				self.send_packet(pos, pos_end, terminal_sock)
			except socket.timeout:
				print('T(%d/0)' % len(packet.packet), end=' ')
				sys.stdout.flush()
			if self.progressCallback:
				self.progressCallback(self.progressCallbackArg, pos_end - pos)
			pos = pos_end

			if self.cancelFlag:
				break

		if self.sleep != 0:
			time.sleep(self.sleep)

		print("Session wait %d." % self.num)
		self.callback(self.callback_arg)

	def send_packet(self, pos, pos_end, terminal_sock):
		sendedPacket = 0
		sended = 0
		recvedPacket = 0
		recved = 0
		direction = self.packets[pos].direction
		if direction:
			inputs = []
			outputs = [terminal_sock, ]
		else:
			inputs = [terminal_sock, ]
			outputs = []

		packetLen = pos_end - pos
		print("ddd")
		print(self.packets[pos+sendedPacket].packet)
		print(len(self.packets))
		# while sendedPacket < packetLen or recvedPacket < packetLen:
		# 	print("whdgkq")
		# 	print(sendedPacket)
		# 	print(packetLen)
		# 	print(recvedPacket)
		# 	if sendedPacket < packetLen:
		# 		outputs = [terminal_sock, ]
		# 	else:
		# 		outputs = []

		(readable, writeable, exceptional) = select.select(inputs,outputs,inputs)

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


				# if direction:
				# 	r = terminal_sock.send(packet)
				# else:
				# 	r = terminal_sock.send(packet)
				# 	wta_server_sock.send(packet)
				# 	wta_manager_sock.send(packet)

			else:
				r = s.send(packet[sended:])
			if r > 0:
				sended += r
				if len(packet) <= sended:
					sended = 0
					sendedPacket += 1
					if self.sleep != 0:
						time.sleep(self.sleep)
if __name__ == '__main__':
	abc = rdpServer(3389)
	abc.run()





