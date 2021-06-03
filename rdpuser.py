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

socket.setdefaulttimeout(10)
CONFPATH = 'conf/rdp_tester.conf'

class rdpUser:
	'''
	rdp proxy Shooter Client Mode
	'''
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
		# if len(target_list) != int(conf['SERVICE_COUNT']):
		# 	return
		#
		# if len(packet_list) != int(conf['SERVICE_COUNT']):
		# 	return
		#
		# if len(cert_info_list) != int(conf['THREAD_PER_PROC']):
		# 	return

		curCount = 0

		def callback(arg):
			arg[0] = arg[0] + 1

		callback_arg = [curCount]

		process_list = []

		# TODO : pcap 파일을 적용 시킬 때 예문
		# # conf 파일의 패킷 파일을 가져와서 적용
		# pcap_mode = packetutil.PcapReader(packet_list[i])
		# # 해당 pcap 파일에서 stream 별로 나눈 리스트 반환
		# stream_data = pcap_mode.getPacketData()
		# stream_index = 0
		# if stream_index < 0 or stream_index > len(stream_data):
		# 	return
		# # 0번 스트림을 packet에 저장 (해당 저장한 packet Shoot)
		# # 1번 스트림을 사용하고 싶을 에는 stream_data[stream_index]
		# packet = stream_data[stream_index]

		for i in range(int(conf['SERVICE_COUNT'])):
			hexdata = commonlib.readFileLines(str(''.join(packet_list[i])))
			packets = packetutil.PacketReader.read(hexdata)
			terminal_sock_object = packetutil.VirtualConnector(target_ip=str(target_list[i][1]),service_port=int(target_list[i][2]), dbsafer_ip=conf['DBSAFER_GW_IP'], dbsafer_port=int(conf['DYNAMIC_PORT']),svcnum=int(target_list[i][3]),interface=conf['BIND_INTERFACE'])
			process_list.append(Worker(i + 1,  terminal_sock_object,packets,
									  conf, target_list[i],cert_info_list,callback, callback_arg))

		for i in process_list:
			print('process starting : ', i.num)
			i.start()
		for i in process_list:
			i.join()
			print('process joined.', i.num)

class Worker(multiprocessing.Process):
	'''
	multiprocessing Class
	'''
	def __init__(self, num, terminal_sock_object,packets,
				 conf, target_list,cert_info_list, callback, callback_arg):
		multiprocessing.Process.__init__(self)
		self.num = num
		self.terminal_sock_object = terminal_sock_object
		self.packets = packets
		self.conf = conf
		self.target_list = target_list
		self.cert_info_list = cert_info_list
		self.callback = callback
		self.callback_arg = callback_arg
		self.cancelFlag = False
		self.progressCallback = None
		self.progressCallbackArg = None

	def run(self):
		'''
		시작 하는 함수
		쓰레드 생성 후 각 쓰레드가 지정된 일을 처리
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
					thread = threading.Thread(target=self.test,args=(j,))
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

	def test(self,thread_count):
		'''
		패킷 테스트 하는 함수
		터미널 소켓을 연결, 해당 패킷 전송
		'''
		if self.cancelFlag:
			self.callback(self.callback_arg)
			return


		cert_info = self.cert_info_list[thread_count]
		terminal_sock = self.terminal_sock_object.rdpModeConnect(cert_info_list=cert_info)
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
					self.send_packet(pos, pos_end, terminal_sock)
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

			print("Session wait %d." % self.num)
			self.callback(self.callback_arg)

	def send_packet(self, pos, pos_end, terminal_sock):
		'''
		패킷 전송 하는 함수
		1회 호출시 1번의 send or recv 시행
		텔넷 관련 패킷을 먼저 1회 send or recv 한 후
		wta 패킷을 send
		'''
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


		(readable, writeable, exceptional) = select.select(inputs,outputs,inputs,int(self.conf['CLIENT_TIMEOUT']))

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

if __name__ == '__main__':
	abc = rdpUser()
	abc.run()





