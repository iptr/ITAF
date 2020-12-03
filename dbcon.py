import pymysql as mysql
import json

CONF_PATH = 'conf/dbinfo.conf'

class dbController():
	"""
	conf/dbinfo.conf json형태의 설정파일을 바탕으로 
	Mysql에 접속하여 DML을 수행하고 원하는 형태로 데이터를 리턴함
	"""

	coninfo = {}
	db = None
	cur = None

	def __init__(self):
		with open(CONF_PATH) as jf :
			self.coninfo = json.load(jf)

	def isdbtbl(self, dbname, tblname):
		"""
		Return Values 
		0 : Both DB and table exist
		-1 : DB does not exist
		-2 : Table does not exist
		"""
		chkdbquery = "show databases like " + str(dbname)
		chktblquery = "SELECT COUNT(*) FROM Information_schema.tables "
		chktblquery += "WHERE table_schema='%s' and "%str(dbname)
		chktblquery += "table_name = '%s'"%str(tblname)
		if self.cur.execute(chkdbquery) == 0:
			return -1
		else :
			cur.execute(chktblquery)
			temp = cur.fetchone()
			if temp[0] == 0 :
				return -2
			else :
				return 0


	def connect(self):
		cinf = self.coninfo
		self.db = mysql.connect(host=cinf['host'], port=int(cinf['port']), user=cinf['userid'], passwd=cinf['passwd'])
		self.cur = self.db.cursor()

	def insert(self, dbname='', tblname='', value=[]) :
		if self.isdbtbl(dbname, tblname) != 0 :
			return -1
		query = "Insert into " + dbname + '.' + tblname
		query += " values()"%str(value).strip("[]")
		self.cur.execute()

	def query(self, sentence):
		self.cur.execute(sentence)
		buff = self.cur.fetchall()
		self.db.commit()
		return buff

	def disconnect(self):
		self.db.commit()
		self.db.close()

