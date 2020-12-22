import paramiko as pm
import pandas as pd
import multiprocessing as mp
import re
import os
from itaflogger import *
from dbcon import *


class SSHCtrl:
	__cinf = None
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
		self.__cinf = pd.DataFrame()
		for col in columns:
			self.__cinf[col] = []
		for i, row in enumerate(coninfo):
			temp = {}
			for j, col in enumerate(columns):
				temp[col] = row[j]
			self.__cinf.loc[i] = temp
		self.__cinf['client'] = None
		self.__cinf = self.__cinf.astype({'port':int})
		

	def connect(self, hostip, hostport, userid, userpasswd):
		client = pm.SSHClient()
		client.set_missing_host_key_policy(pm.AutoAddPolicy())
		try:
			client.connect(hostip, port=hostport, username=userid, password=userpasswd, timeout=10)
		except Exception as e:
			self.__lgr.error(e)
			return None
		return client

	def connectall(self, cno=None) :
		'''
		cno : [list] Client number ex)[0,2,6], None is All of clients
		'''
		ci = self.__cinf
		if cno == None:
			cno = range(len(self.__cinf.index))

		for rc in cno:
			if ci['client'][rc] != None:
				continue
			else:	
				ci['client'][rc] = self.connect(str(ci['ip'][rc]), int(ci['port'][rc]), str(ci['userid'][rc]), str(ci['passwd'][rc]))
		

	def showclients(self):
		print(self.__cinf)
		return self.__cinf

	def runcmd(self, client, cmd):
		'''
		Run one or more Commands. There in no relation between Commands.
		:client obj(SSHClient): paramko SSH Client object 
		:cmd str or list : Command to run on the client
		'''
		if type(cmd) == str:
			try:
				stdin, stdout, stderr = client.exec_command(cmd)
			except Exception as e:
				self.__lgr.error(e)
				return -1
			return stdout,stderr
		elif type(cmd) == list:
			dict_ret = {'cmd':cmd, 'stdout':[], 'stderr':[]}
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
			return dict_ret
		else:
			self.__lgr.error('wrong type cmd parameter')
			return -1

	def runonshell(self, client, cmdlines):
		'''
		:param obj(SSHClient) client
		:param list cmdlines
		Run one or more Commands on interactive shell
		'''
		sh = client.invoke_shell()
		dict_ret = {'cmd':cmdlines, 'recv':[]}
		for cmd in cmdlines:
			ret = sh.send(cmd)
			buf = ''
			while sh.recv_ready():
				buf += sh.recv(4096)
			dict_ret['recv'].append(re.split('\n|\r', buf.decode('ascii')))
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

	def getfileslist(self, path):
		'''
		searching all of files in srcpath and return list of files
		'''
		flist = []
		for dpath, dnames, fnames in os.walk(path):
			for fn in fnames:
				flist.append(dpath + os.sep + fn)
		return flist

	def getlocalpath(self, path):
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
		sftp = pm.SFTPClient.from_transport(client.get_transport())
		srcbase = os.path.basename(srcpath)
		srcfiles = self.getlocalpath(srcpath)

		# Check source path exists
		if srcfiles == []:
			__lgr.error('param srcpath Not exists')
			return -1
		
		# Check dstpath exists
		isrmt = self.isrmtfile(client, dstpath)
		if self.isrmtfile(client, dstpath) != 2:
			sftp.mkdir(dstpath)

		# Check destination path on target server exist
		# If directory does not exist, create directory
		for path in srcfiles:
			sftp.put(dstpath + os.sep + path.replace(srcbase,''))
		sftp.close()

	def get(self, client, dstpath):
		pass

	def runcmd_mp(self, cmd, cno=None, client=None):
		pass

	def close(self, idx):
		client = self.__cinf['client'][idx]
		if client != -1 or pd.isna(client) == False:
			try :
				client.close()
			except Exception as e:
				self.__lgr.error(e)
				return -1
			self.__cinf['client'][idx] == -1
		else:
			return 0

if __name__ =='__main__':
	pass