import pymysql as mysql
import json
from . import taiflogger

CONF_PATH = 'conf/taif.conf'

class DBCtrl():
    """
    Mysql 접속/쿼리 수행하기 위한 클래스

    Attribute:
            cinf(Dict) : mysql 접속을 위한 접속 정보
            lgr(Obj:logger) : 인스턴스 상에서 발생하는 이벤트들에 대한 로거 object
            db (Obj:DBconnector) : DB Connecter Object
            cur (Ojb:DBCursor) : DB Cursor for querying
    """
    cinf = {}
    lgr = None
    db = None
    cur = None

    def __init__(self):
        # json 형태의 설정파일을 읽고 접속정보를 읽어옴
        self.lgr = Logger().getlogger("DBController")
        try:
            jf = open(CONF_PATH)
            temp = json.load(jf)
            jf.close()
        except Exception as e:
            self.lgr.error(e)
            raise e
        self.cinf = temp['TAIFDB']


    def connect(self, host=None, port=None, user=None, passwd=None, db=None,\
    	charset=None):
        """
        Connect to DB with cinf or parameters

        Example:
                connect("127.0.0.1","3306","root","toor",)

        Args:
                host(str) : DB host (Necessary)
                port(int) : DB port (Default : 3306)
                user(str) : DB userid (Necessary)
                passwd(str) : User's Password
                db(str) : DB name
                charset(str) : DB's Charactor set  EX) "utf8". "euckr"

        Returns:
                db(obj) : DB Connector
                cur(obj) : DB Cursor
        """
        if host != None and user != None:
            try:
                self.db = mysql.connect(host=host, port=int(\
                    port), user=user, passwd=passwd, db=db, charset=charset)
            except Exception as e:
                self.lgr.error(e)
                return -1
        else:
            cif = self.cinf
            try:
                self.db = mysql.connect(host=cif['host'], port=int(cif['port']), 
                						user=cif['userid'], passwd=cif['passwd'], 
                						db=cif['dbname'], charset=cif['charset'])
            except Exception as e:
                self.lgr.error(e)
                return -1
        self.cur = self.db.cursor()
        return self.db, self.cur

    def isdbtbl(self, dbname='', tblname=''):
        """
        Check DB and Table exists

        Args:
                dbname : DB name to check
                tblname : Table name to check

        Returns :
                Result of table existence(int)
                0 : Both DB and table exist
                -1 : DB does not exist
                -2 : Table does not exist
        """
        chkdbquery = "show databases like \'%s\'" % str(dbname)
        chktblquery = "SELECT COUNT(*) FROM Information_schema.tables "
        chktblquery += "WHERE table_schema=\'%s\' and " % str(dbname)
        chktblquery += "table_name = \'%s\'" % str(tblname)
        if dbname == '' or tblname == '':
            self.lgr.error('DB name or table name is blank')
            return -1
        if self.cur.execute(chkdbquery) == 0:
            self.lgr.error('%s DB Not exist')
            return -2
        else:
            self.cur.execute(chktblquery)
            temp = self.cur.fetchone()
            if temp[0] == '0':
                self.lgr.error('%s Table Not exist')
                return -3
            else:
                self.lgr.debug('%s.%s exist' % (dbname, tblname))
                return 0

    def getcolumns(self, dbname='', tblname=''):
        """
        Get specific column's label
        Args:
                dbname(str) : DB name
                tblname(str) : Table name
        Returns :
                list of Column's label
        """
        if self.isdbtbl(dbname, tblname) != 0:
            return -1
        query = 'select * from %s.%s limit 1' % (dbname, tblname)
        self.cur.execute(query)
        desc = self.cur.description
        cols = []
        for row in desc:
            cols.append(row[0])
        return cols

    def insert(self, dbname='', tblname='', value=[]):
        """
        Run Insert query
        Args:
                dbname(str) : DB name
                tblname(str) : Table name
                value(list) : Data to insert
        Returns:
                Integer Result of insert query
                0 < : Error
                0 = : Success
        """
        if self.isdbtbl(dbname, tblname) != 0 or value == []:
            self.lgr.error('Could not Insert DATA')
            return -1
        query = "Insert into " + dbname + '.' + tblname
        query += " values(%s)" % (str(value).strip("[]"))
        try:
            ret = self.cur.execute(query)
        except Exception as e:
            self.lgr.error(e)
            return -2
        if ret > 0:
            self.lgr.info('%s inserted to %s.%s' % (value, dbname, tblname))
            return ret
        self.db.commit()

    def select(self, dbname='', tblname='', case='', cols=[], \
    			without_header=True):
        """
        Run select query
        Example:

        Args:
                dbname(str) : DB name
                tblname(str) : Table name
                case(str) : Case without "where"
                cols(list) : columns to return result
                without_header(bool) : exclude header(col name)
        Returns:
                0 < : Error
                [[]]] list : Result of select query

        """
        if self.isdbtbl(dbname, tblname) != 0:
            self.lgr.debug("db or table name not exist")
            return -1

        if len(cols) == 0:
            query = "select * from"
        else:
            query = "select %s from" % ','.join(cols)
        query += " %s.%s" % (dbname, tblname)
        if case != '':
            query += " where %s" % (case)

        try:
            self.cur.execute(query)
        except Exception as e:
            self.lgr.error(e)
            return -2

        lines = []
        if without_header == False:
            lines.append(self.getcolumns(dbname, tblname))

        try:
            while True:
                temp = self.cur.fetchone()
                if temp == None:
                    break
                lines.append(list(temp))
        except Exception as e:
            self.lgr.error(e)
            return -3
        return lines

    def close(self):
        self.db.commit()
        self.db.close()
