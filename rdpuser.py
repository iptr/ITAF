import binascii
import os
import threading
import socket
import time
import sys
import select
import commonlib
from multiprocessing import Process, Lock, Queue
import multiprocessing
import asyncio
import cProfile
import pickle
import packetutil
import wtapacket
import wtaproxymaker


# 스택 사이즈 결정
if sys.version_info >= (3, 5):
	threading.stack_size(1024 * 1024 * 1024 * 2)

# 기본 타임아웃 시간 설정
socket.setdefaulttimeout(3)

class Worker(multiprocessing.Process):

	def __init__(self, num, connector, packets,
				 timeout, repeat, sleep, verbose,
				 callback, callback_arg,thread_count,wta_packet,que):
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
		self.wta_packet = wta_packet
		self.q = que

	def setProgressCallback(self, callback, callbackarg):
		self.progressCallback = callback
		self.progressCallbackArg = callbackarg

	async def createAsyncio(self):
		t = asyncio.create_task(self.test())
		await t

	def callAsyncio(self):
		loop = asyncio.new_event_loop()
		asyncio.set_event_loop(loop)
		try:
			loop.run_until_complete(self.createAsyncio())
		finally:
			loop.close()
		asyncio.set_event_loop(None)

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
					thread = threading.Thread(target=self.callAsyncio)
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

	async def test(self):
		'''
		패킷 테스트 하는 함수
		'''
		if self.cancelFlag:
			self.callback(self.callback_arg)
			return

		# try:
		print("Connecting %d..." % self.num)
		# 각 세션 소켓 반환
		(terminal_socket,telnet_socket,wta_socket,wta_info_socket) = await self.connector.rdpModeConnect()
		try:
			self.q.put(terminal_socket)
			self.q.put(telnet_socket)
			self.q.put(wta_socket)
			self.q.put(wta_info_socket)

		except Exception as e:
			print("ERROR")
		print("Connected %d." % self.num)

		if self.timeout:
			terminal_socket.settimeout(self.timeout)

		pos = 0
		wta_pos = 0
		wta_pos_end = 0
		flag = 0
		# 패킷 길이 확인 및 전송
		login_id='shyoon_test_1'
		w = wtapacket.WtaPacketMaker()
		wta_info = w.collectInfo(wta_info_socket)
		wta_packet = wtaproxymaker.WtaProxyPacketMaker(wta_info, login_id)
		wta_packet.makePacket()

		packet_t = []
		packet_t.append(wta_packet.startSignal())
		packet_t.append(wta_packet.dynamicPacketMaker(terminal_socket.getpeername()[1]))
		packet_t.append(wta_packet.encryptPacket())
		while pos < len(self.packets) or wta_pos < len(self.wta_packet) + len(packet_t):
			if pos < len(self.packets):
				packet = self.packets[pos]
				pos_end = pos + 1

			if wta_pos_end < len(self.wta_packet) + len(packet_t) - 1:
				wta_pos_end = wta_pos + 1

			while pos_end < len(self.packets):
				packet2 = self.packets[pos_end]
				if packet.direction != packet2.direction:
					break
				pos_end += 1


			try:
				# 패킷 전송
				await self.send_packet(pos, pos_end, terminal_socket,telnet_socket,wta_socket,wta_pos,wta_pos_end,flag,packet_t)
				flag = flag + 1
			except socket.timeout:
				print('T(%d/0)' % len(packet.packet), end=' ')
				sys.stdout.flush()
			if self.progressCallback:
				self.progressCallback(self.progressCallbackArg, pos_end - pos)
			pos = pos_end
			wta_pos = wta_pos_end
			if self.cancelFlag:
				break

		if self.sleep != 0:
			time.sleep(self.sleep)

		print("Session wait %d." % self.num)
		# except Exception as e:
		# 	print("sendError")
		# 	print(e)

		self.callback(self.callback_arg)

	async def send_packet(self, pos, pos_end, terminal_sock, telnet_socket, wta_socket, wta_pos, wta_pos_end,flag,packet_t):
		'''
		select를 이용하여 패킷 송수신을 담당하는 함수
		'''
		sendedPacket = 0
		sended = 0
		recvedPacket = 0
		recved = 0
		direction = self.packets[pos].direction
		if direction:
			sendSocket = telnet_socket#terminal_sock
			recvSocket = terminal_sock#telnet_socket
		else:
			sendSocket = terminal_sock#telnet_socket
			recvSocket = telnet_socket#terminal_sock

		packetLen = pos_end - pos

		wta_stop_pos = len(self.wta_packet) + len(packet_t) -1
		print(len(self.wta_packet), len(packet_t), wta_pos, wta_pos_end)

		if wta_pos_end < wta_stop_pos:
			print("WTA SEND")
			if flag < 3:
				wta_socket.send(packet_t[wta_pos])
			else:
				wta_socket.send(self.wta_packet[wta_pos-3].packet)

		while sendedPacket < packetLen or recvedPacket < packetLen:
			if sendedPacket < packetLen:
				outputs=[sendSocket,]
				# if direction == False:
				# 	(readable, writeable, exceptional) = select.select([ ], [c_sock,s_sock,wta_s_sock,], [ ], self.timeout)
				# else:
				# 	break
			else:
				outputs=[]
				# (readable, writeable, exceptional) = select.select([ c_sock,s_sock,wta_s_sock,], [], [ ], self.timeout)
				#(readable, writeable, exceptional) = select.select([recvSocket, ], outputs, [recvSocket, ], self.timeout)

			(readable, writeable, exceptional) = select.select([recvSocket, ], outputs, [recvSocket, ], self.timeout)

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
				packet = self.packets[pos + sendedPacket].packet
				if sended == 0:
					#print("Send")
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
			# if flag == 0:
			# 	w = wtapacket.WtaPacketMaker()
			# 	w.makePacket(client_ip='10.77.162.11', client_port=3389, wta_proxy_port=3141,
			# 				 service_port=4095,
			# 				 service_ip="192.168.4.190")
			# 	#print(w.encryptPacket())
			# 	#wta_socket.send(w.encryptPacket())
			# 	flag = 1

		# if flag == 1:
		# 	login_id = "abcde"
		#
		# 	wta_packet = wtaproxymaker.WtaProxyPacketMaker(wta_info, login_id)
		# 	wta_packet.makePacket()
		# 	start = wta_packet.setHead()
		# 	wta_socket.send(start)
		# 	encry = wta_packet.encryptPacket()
		# 	wta_socket.send(encry)
		# 	for k in range(100):
		# 		wta_socket.send(bytes.fromhex(
		# 			"51f21174cf90a53f9f41f545c8f44dd62edc7c54fbe25fc45b1aef9951a5e85203f150b17eee4b74cba77274dd5960c3e07b0417f80ed9897b1a2fa6dadb252e5f85e4ff42a6232f81f4305cb46d00bacb113c048927bed30e71add520e984053da1d4cf7794115aa099187dd15070d6a768440dcf55a1ea4050f2de78e8ca6b73e29c8669d4512dd3e26353e97457e69703607bd9690cffd46026be568ab70e2dab9add2387130597dc246b9e5727cca06f430af855cdcf6d11d9a1549ded066aa589c032af00"))


				#print(self.wta_packet[wta_pos-3].packet)
			# w = wtapacket.WtaPacketMaker()
			# w.makePacket(client_ip='10.77.162.11', client_port=3389+self.num, wta_proxy_port=3141, service_port=4095+self.num,
			# 			 service_ip="192.168.4.190")
			#
			# wta_socket.send(w.encryptPacket())



def runTest(process_count = 128, thread_count = 100):
	datafile = 'packet_tester.txt'
	datafile2 = 'packet_tester2.txt'
	repeat = 1
	time_out = 5
	sleep_time = 0
	verbose = False

	if not os.path.exists(datafile):
		print('ERROR:', datafile, 'is not exist.')
		sys.exit(-1)

	hexdata = commonlib.readFileLines(datafile)
	packets = packetutil.PacketReader.read(hexdata)

	hexdata = commonlib.readFileLines(datafile2)
	wta_packet = packetutil.PacketReader.read(hexdata)

	totalTest = repeat * process_count
	curCount = 0

	def callback(arg):
		arg[0] = arg[0] + 1
		print('%d/%d' % (totalTest, arg[0]), end=' ')

	callback_arg = [curCount]

	start_time = time.time()

	process_list = []

	test = Queue()
	# connected = []
	# for i in range(process_count):
	# 	connector = packetutil.VirtualConnector(3389+i, "192.168.4.190", 4095+i)
	# 	connected.append(connector)

	connecte = packetutil.VirtualConnector(3389,"192.168.4.190",4095)

	for i in range(process_count):
		process_list.append(Worker(i + 1, connecte, packets,
							  time_out, repeat, sleep_time, verbose,
							  callback, callback_arg,thread_count,wta_packet,test))

	for i in process_list:
		print('process starting : ', i.num)
		i.start()
	for i in process_list:
		i.join()
		print('process joined.', i.num)

	test.close()

	elapsed_time = time.time() - start_time
	print('\n')
	print('Done. [%02d:%02d:%02.2d]' % (int(elapsed_time) / 60 / 60, int(elapsed_time) / 60 % 60, elapsed_time % 60))

if __name__ == '__main__':
	#cProfile.run("runTest(1,2)")
	runTest(1,1)


