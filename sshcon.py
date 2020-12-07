import paramiko
import pandas as pd
import multiprocessing as mp
from itaflogger import *
from dbcon import *


class SSHCtrl:
	__cinf=pd.DataFrame()
	__lgr=None
	clients = []

	def __init__(self):
		self.__lgr = Logger().getlogger("SSHCtrl")
		dbc = DBCtrl()
		dbc.connect()
		columns = dbc.getcolumns('itaf', 'server_info')
		columns.remove('ostype')
		coninfo = dbc.select('itaf', 'server_info', "ostype != 'Windows'", cols=columns)
		for col in columns:
			self.__cinf[col]=[]
		for row in coninfo:
			for i,col in enumerate(columns):
				self.__cinf[col].append(row[i])
		self.__cinf['client']=[]
		dbc.close()

	def connect(self, hostip, hostport, userid, userpasswd):
		client = pm.SSHClient()
		client.set_missing_host_key_policy(pm.AutoAddPolicy())
		try:
			client.connect(hostip, port=hostport, username=userid, password=userpasswd)
		except Exception as e:
			self.__lgr.error(e)
			return None
		return client

	def connect_all(self) :
		for r in self.__cinf.iloc:
			if r['client'] != None or pd.isna(r['client']) == False:
				continue
			else:
				r['client'] = connect(r['ip'], int(r['port']), r['userid'], r['passwd'])

	def show_clients(self):
		print(self.__cinf)

	def runcmd(self, client, cmd):

		pass

	def putfile(self, client, srcpath, dstip, dstpath):
		pass

	def getfile(self, client, dstip, dstpath):
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



