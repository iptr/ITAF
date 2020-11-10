import pymysql as mysql
import json

CONF_PATH = 'conf/dbinfo.conf'

class dbController():
	"""
	connect mysql and query	
	"""
	coninfo = {}
	db = None
	cur = None

	def __init__(self):
		with open(CONF_PATH) as jf :
			self.coninfo = json.load(jf)

	def connect(self):
		cinf = self.coninfo
		self.db = mysql.connect(host=cinf['host'], port=int(cinf['port']), user=cinf['userid'], passwd=cinf['passwd'])
		self.cur = self.db.cursor()

	def query(self, sentence):
		self.cur.execute(sentence)
		buff = self.cur.fetchall()
		self.db.commit()
		return buff

	def disconnect(self):
		self.db.commit()
		self.db.close()

