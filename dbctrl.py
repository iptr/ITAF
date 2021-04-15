import pymysql as mysql
import json
from taiflogger import *


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



    def __init__(self):
        # json 형태의 설정파일을 읽고 접속정보를 읽어옴
        self.cinf = {}
        self.db = None
        self.cur = None

    def connect(self, host=None, port=None, user=None, passwd=None, db=None,
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
                try:
                    self.db = mysql.connect(host=host, port=int(\
                        port), user=user, passwd=passwd, charset=charset)
                    cur = self.db.cursor()
                    cur.execute("create database %s"%(db))
                except Exception as e:
                    return -1
        else:
            cif = self.cinf
            try:
                self.db = mysql.connect(host=cif['host'], port=int(cif['port']), 
                						user=cif['userid'], passwd=cif['passwd'], 
                						db=cif['dbname'], charset=cif['charset'])
            except Exception as e:
                try:
                    self.db = mysql.connect(host=cif['host'], port=int(cif['port']),
                                            user=cif['userid'], passwd=cif['passwd'],
                                            charset=cif['charset'])
                    cur = self.db.cursor()
                    cur.execute("create database %s"%(cif['dbname']))

                except Exception as e:
                    return -1

        return self.db

    def setCursor(self,db):
        self.cur = db.cursor()
        return self.cur

    def checkDBExist(self, dbname=""):
        """
        Check DB exists

        Args:
                dbname : db name to check

        Returns :
                Result of DB existence(int)
                0 : DB 존재
                -1 : DB 없음(실패)
        """
        query = "show databases like \'%s\'" % str(dbname)
        if dbname == '' or self.cur.execute(query) == 0:
            return -1
        return 0

    def checkTableExist(self, dbname='', tblname=''):
        """
        Check Table exists

        Args:
                tblname : Table name to check

        Returns :
                Result of table existence(int)
                0 : 테이블 존재
                -1 : 테이블 없음(실패)
        """
        query = "SELECT COUNT(*) FROM Information_schema.tables "
        query += "WHERE table_schema=\'%s\' and " % str(dbname)
        query += "table_name = \'%s\'" % str(tblname)
        if dbname == '' or tblname == '':
            return -1
        else:
            self.cur.execute(query)
            temp = self.cur.fetchone()
            if temp[0] == '0':
                return -1
            else:
                return 0

    def getColumns(self, dbname='', tblname=''):
        """
        Get specific column's label
        Args:
                dbname(str) : DB name
                tblname(str) : Table name
        Returns :
                list of Column's label
        """
        if self.checkDBExist(dbname) != 0 or self.checkTableExist(tblname) != 0:
            return -1
        query = 'select * from %s.%s limit 1' % (dbname, tblname)
        self.cur.execute(query)
        desc = self.cur.description
        cols = []
        for row in desc:
            cols.append(row[0])
        return cols

    def insert(self, dbname='', tblname='', column=[],value=[]):
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
        if self.checkDBExist(dbname) != 0 or self.checkTableExist(dbname,tblname) != 0 or value == []:
            #self.lgr.error('Could not Insert DATA')
            return -1

        query = "Insert into " + dbname + '.' + tblname
        query += "(%s)"%(str(column).strip("[]")).replace("'","")
        query += " values(%s)" % (str(value).strip("[]"))

        try:
            ret = self.cur.execute(query)
        except Exception as e:
            #self.lgr.error(e)
            print(e)
            return -1

        if ret > 0:
            #self.lgr.info('%s inserted to %s.%s' % (value, dbname, tblname))
            return 0
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
        contents = []

        if self.checkDBExist(dbname) != 0 or self.checkTableExist(dbname,tblname) != 0:
            #self.lgr.debug("db or table name not exist")
            print("DB,TABLE!!")
            return contents

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
            print(e)
            #self.lgr.error(e)
            return contents

        if without_header == False:
            contents.append(self.getcolumns(dbname, tblname))

        try:
            while True:
                temp = self.cur.fetchone()
                if temp == None:
                    break
                contents.append(list(temp))
        except Exception as e:
            #self.lgr.error(e)
            return contents
        return contents

    def delete(self,dbname='', tblname='', case=''):
        """
        Run delete query
        Example:

        Args:
                dbname(str) : DB name
                tblname(str) : Table name
                case(str) : Case without "where"
        Returns:
                0 < : Error

        """

        if self.checkDBExist(dbname) != 0 or self.checkTableExist(dbname,tblname) != 0:
            return -1

        query = "delete from " + dbname + '.' + tblname

        if case != '':
            query += " where %s" % (case)

        try:
            self.cur.execute(query)
        except Exception as e:
            return -1

        self.db.commit()

        return 0

    def update(self, dbname='', tblname='', case='', cols=[], value=[]):
        """
        Run update query
        Example:

        Args:
                dbname(str) : DB name
                tblname(str) : Table name
                case(str) : Case without "where"
                cols(list) : update columns
                value(list) : Value matching column
        Returns:
                0 < : Error

        """

        if self.checkDBExist(dbname) != 0 or self.checkTableExist(dbname,tblname) != 0:
            return -1

        if (len(cols) == 0 or len(value) == 0) or (len(cols) != len(value)):
            return -1

        query = "update " + dbname + '.' + tblname + " set "

        for i in range(len(cols)):
            if type(value[i]) is int:
                query += "%s = %d "%(cols[i],value[i])
            else:
                query += "%s = '%s' "%(cols[i],value[i])

            if i != (len(cols) - 1):
                query +=","

        if case != '':
            query += " where %s" % (case)
        print(query)
        try:
            self.cur.execute(query)
        except Exception as e:
            print(e)
            return -1

        self.db.commit()

        return 0

    def close(self):
        self.db.commit()
        self.db.close()

class VerifyDBS(DBCtrl):
    db = None
    cur = None
    
    def __init__(self):
        pass
        
    def getTermSess(self):
        pass
    
    def getTermCMD(self):
        pass
    
    def getFTPSess(self):
        pass
    
    def getFTPRet(self):
        pass

