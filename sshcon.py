import paramiko as pm
import pandas as pd
import multiprocessing as mp
import time
import re
import os
from itaflogger import *
from dbcon import *


class SSHCtrl:
	"""
	SSH프로토콜을 사용하여 대상서버에서 작업하는 클래스
	대상서버 접속정보는 DB에서 가져온다.

	Attr:
	cinf(DataFrame) : 대상서버 접속정보 및 ssh client 객체
	__lgr (Logger) : 로깅을 위한 인스턴스
	"""
	cinf = None
	__lgr = None
	
	def __init__(self):
		self.__lgr = Logger().getlogger("SSHCtrl")
		dbc = DBCtrl()
		dbc.connect()
		columns = dbc.getcolumns('itaf', 'server_info')
		columns.remove('ostype')
		coninfo = dbc.select('itaf', 'server_info', "ostype != 'Windows'", \
			cols=columns)
		dbc.close()
		self.cinf = pd.DataFrame()
		for col in columns:
			self.cinf[col] = []
		for i, row in enumerate(coninfo):
			temp = {}
			for j, col in enumerate(columns):
				temp[col] = row[j]
			self.cinf.loc[i] = temp
		self.cinf['client'] = None
		self.cinf = self.cinf.astype({'port':int})
		

	def connect(self, host, port, user, passwd):
		client = pm.SSHClient()
		client.set_missing_host_key_policy(pm.AutoAddPolicy())
		try:
			client.connect(host, port=port, username=user, password=passwd, timeout=5)
		except Exception as e:
			self.__lgr.error(e)
			print("Error : %s"%e)
			return None
		return client

	def connectall(self, cno=None) :
		'''
		cno : [list] Client number ex)[0,2,6], None is All of clients
		'''
		ci = self.cinf
		if cno == None:
			cno = range(len(self.cinf.index))

		for rc in cno:
			print(rc)
			if ci['client'][rc] != None:
				continue
			else:
				ci['client'][rc] = self.connect(str(ci['ip'][rc]), int(ci['port'][rc]), str(ci['userid'][rc]), str(ci['passwd'][rc]))
				print(ci['client'][rc])
		

	def showclients(self):
		print(self.cinf)
		return self.cinf

	def runcmd(self, client, cmd):
		'''
		Run one or more Commands. There in no relation between Commands.
		:param client : paramko SSH Client object 
		:param cmd [str or list] : Command to run on the client
		:return: dictionary of stdin, stdout, stderr
		'''
		dict_ret = {'cmd':cmd, 'stdout':[], 'stderr':[]}
		if type(client) == pm.client.SSHClient:
			pass
		elif int(client) < len(self.cinf['client']) > 0:
			client = self.cinf['client'][int(client)]
		else :
			self.__lgr.error('there is no %s client'%client)
			return -1

		if type(cmd) == str:
			try:
				stdin, stdout, stderr = client.exec_command(cmd)
			except Exception as e:
				self.__lgr.error(e)
				return -1
			dict_ret['stdout'].append(stdout.readlines())
			dict_ret['stderr'].append(stderr.readlines())
		elif type(cmd) == list:
			for line in enumerate(cmd):
				try:
					stdin, stdout, stderr = client.exec_command(line)
				except Exception as e:
					self.__lgr.error(e)
					dict_ret['stdout'].append(None)
					dict_ret['stderr'].append(None)
					continue
				dict_ret['stdout'].append(stdout.readlines())
				dict_ret['stderr'].append(stderr.readlines())
		else:
			self.__lgr.error('wrong type cmd parameter')
			return -1
		return dict_ret

	def runonshell(self, client, cmdlines):
		'''
		Run one or more Commands on interactive shell
		:param obj(SSHClient) client
		:param list cmdlines
		'''
		sh = client.invoke_shell()
		dict_ret = {'cmd':cmdlines, 'recv':[]}
		for cmd in cmdlines:
			ret = sh.send(cmd)
			buf = ''
			cnt = 0
			while True:
				if sh.recv_ready():
					buf += sh.recv(4096).decode('ascii')
				else :
					if buf == '':
						cnt += 1
						time.sleep(0.1)
						if cnt > 10:
							cnt = -1
							break
						else :
							continue
					else:
						break
			if cnt == -1 :
				dict_ret['recv'].append('')
			else:
				dict_ret['recv'].append(re.split('\n|\r', buf))
		sh.close()
		return dict_ret

	def isrmtfile(self, client, path):
		cmd = "if test -f %s;then echo \"file\";"%path
		cmd += "elif test -d %s;then echo \"directory\";fi"%path
		dict_ret = self.runcmd(client, cmd)
		if dict_ret['stdout'][0] == 'file':
			return 1
		elif dict_ret['stdout'][0] == 'directory':
			return 2
		else:
			return -1
	
	def getfileslist(self, path, client=None):
		'''
		path에 해당되는 디렉토리내 모든 파일 및 디렉토리 목록을 리턴한다.
		client를 입력받을 경우 원격지의 path에 대해서 수행한다.
		:param path: 디렉토리 경로
		:param client: ssh client object
		'''
		flist = []
		if client != None :
			cmd = "file `find %s`|grep -v directory"%path
			ret = self.runcmd(client, cmd)
			if len(ret['stdout'][0]) > 0 :
				for line in ret['stdout'][0]:
					flist.append(line.strip(':')[0])
		else:
			for dpath, dnames, fnames in os.walk(path):
				for fn in fnames:
					flist.append(dpath + os.sep + fn)
		return flist

	def getlocalpath(self, path):
		'''
		path가 존재하는지 파일인지 디렉토리인지 확인하고 디렉토리일경우 디렉토리 하위의 모든 파일들을 리턴한다.
		path의 파일명에 와일드카드(*,?)가 존재할경우 다수의 파일목록을 리턴한다.
		'''
		flist = []
		dname = os.path.dirname(path)
		bname = os.path.basename(path)
		# Check whether the path is a directory
		if os.path.isdir(path):
			flist = self.getfileslist(path)
			return flist
		
		# whether path is a file
		if os.path.isfile(path):
			flist.append(path)
			return flist

		# check the path includes wild cards and get files as the pattern
		if re.search("\*|\?", bname) != None:
			if re.fullmatch('\*+', bname):
				patt = re.compile('\S*')
			elif re.fullmatch('\?+', bname) != None:
				patt = re.compile(bname.replace('?','.'))
			else:
				patt = '^' + bname.replace('.','\.').replace('?','.').replace('*','\S*') + '$'
				patt = re.compile(patt)
			
			try:
				dlist = os.listdir(dname)
			except:
				__lgr.error("%s directory does Not exist")
				return flist

			for fn in dlist:
				if re.fullmatch(patt, fn) != None:
					tmppath = dname + os.sep + fn
					if os.path.isdir(tmppath):
						flist += self.getfileslist(tmppath)
					elif os.path.isfile(tmppath):
						flist.append(tmppath)
					else:
						pass
			return flist
		return flist

	def put(self, client, srcpath, dstpath):
		'''
		ssh 클라이언트를 통해 원본경로의 내용을 대상경로로 업로드한다.
		:client: ssh client object
		:srcpath: source path to upload
		:dstpath: target path to upload
		'''
		sftp = pm.SFTPClient.from_transport(client.get_transport())
		srcbase = os.path.basename(srcpath)
		srcfiles = self.getlocalpath(srcpath)

		# Check source path exists
		if srcfiles == []:
			__lgr.error('param srcpath Not exists')
			return -1
		
		# Check destination path on target server exist
		# If directory does not exist, create directory
		isrmt = self.isrmtfile(client, dstpath)
		if self.isrmtfile(client, dstpath) != 2:
			sftp.mkdir(dstpath)

		for path in srcfiles:
			sftp.put(dstpath + os.sep + path.replace(srcbase,''))
		sftp.close()

	def get(self, client, dstpath):
		# TODO(jycho) : implement get function
		# Create SFTPClient
		sftp = pm.SFTPClient.from_transport(client.get_transport())
		dstfiles = []
		# Check Dstpath


		# get directory or files
		pass

	def runcmd_mp(self, cmd, cno=None, client=None):
		pass

	def close(self, idx):
		client = self.cinf['client'][idx]
		if client != -1 or pd.isna(client) == False:
			try :
				client.close()
			except Exception as e:
				self.__lgr.error(e)
				return -1
			self.cinf['client'][idx] == -1
		else:
			return 0

if __name__ == '__main__':
	pass