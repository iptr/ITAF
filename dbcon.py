import pymysql as mysql
import json
import inspect
from itaflogger import *

CONF_PATH = 'conf/dbinfo.conf'

class DBCtrl():
	"""
	conf/dbinfo.conf json형태의 설정파일을 바탕으로 
	Mysql에 접속하여 DML을 수행하고 원하는 형태로 데이터를 리턴함
	"""
	
	__coninfo = {}
	__lgr = None
	db = None
	cur = None
	
	def __init__(self):
		self.__lgr = Logger().getlogger("DBController")
		try :
			jf = open(CONF_PATH)
			self.__coninfo = json.load(jf)
			jf.close()
		except Exception as e:
			self.__lgr.error('%s %s'%(CONF_PATH,e))
			raise e

	def connect(self):
		cinf = self.__coninfo
		try:
			self.db = mysql.connect(host=cinf['host'], port=int(cinf['port']), user=cinf['userid'], passwd=cinf['passwd'])
		except Exception as e:
			self.__lgr.error('%s %s'%(CONF_PATH,e))
			raise e
		self.cur = self.db.cursor()

	def isdbtbl(self, dbname='', tblname=''):
		"""
		Return Values 
		0 : Both DB and table exist
		-1 : DB does not exist
		-2 : Table does not exist
		"""
		chkdbquery = "show databases like \'%s\'"%str(dbname)
		chktblquery = "SELECT COUNT(*) FROM Information_schema.tables "
		chktblquery += "WHERE table_schema=\'%s\' and "%str(dbname)
		chktblquery += "table_name = \'%s\'"%str(tblname)
		if dbname == '' or tblname == '':
			self.__lgr.error('DB name or table name is blank')
			return -1
		if self.cur.execute(chkdbquery) == 0:
			self.__lgr.error('%s DB Not exist')
			return -2
		else :
			self.cur.execute(chktblquery)
			temp = self.cur.fetchone()
			if temp[0] == '0' :
				self.__lgr.error('%s Table Not exist')
				return -3
			else :
				self.__lgr.debug('%s.%s exist'%(dbname, tblname))
				return 0

	def getcolumns(self, dbname='', tblname=''):
		if self.isdbtbl(dbname, tblname) != 0 :
			return -1
		query='select * from %s.%s limit 1'%(dbname,tblname)
		self.cur.execute(query)
		desc = self.cur.description
		cols = []
		for row in desc:
			cols.append(row[0])
		return cols

	def insert(self, dbname='', tblname='', value=[]):
		if self.isdbtbl(dbname, tblname) != 0 or value==[]:
			self.__lgr.error('Could not Insert DATA')
			return -1
		query = "Insert into " + dbname + '.' + tblname
		query += " values(%s)"%(str(value).strip("[]"))
		try:
			ret = self.cur.execute(query)
		except Exception as e:
			self.__lgr.error(e)
			return -2
		if ret > 0 :
			self.__lgr.info('%s inserted to %s.%s'%(value,dbname,tblname))
			return ret
		self.db.commit()

	def select(self, dbname='', tblname='', case='', cols=[], without_header=True):
		if self.isdbtbl(dbname, tblname) != 0:
			return -1

		if len(cols) == 0 :
			query = "select * from"
		else:
			query = "select %s from"%','.join(cols)
		query += " %s.%s"%(dbname,tblname)
		if case != '':
			query += " where %s"%(case)
		
		try:
			self.cur.execute(query)
		except Exception as e:
			self.__lgr.error(e)
			return -2

		lines = []
		if without_header == False:
			lines.append(getcolumns(dbname,tblname))

		try:
			while True:
				temp = self.cur.fetchone()
				if temp == None:
					break
				lines.append(list(temp))
		except Exception as e:
			self.__lgr.error(e)
			return -3
		return lines

	def close(self):
		self.db.commit()
		self.db.close()

