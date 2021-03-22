import logging
import time
import dbctrl

class MysqlHandler(logging.Handler):
    """
    Call the Mysql handlers for the specified record.

    This method is used for logs a record to the specified Mysql DB, as
    well as those created locally. Logger-level filtering is applied.
    """

    create_db = """create database log_db"""

    initial_sql = """CREATE TABLE IF NOT EXISTS log(
                Created text,
                Name text,
                LogLevelName text,
                Message text,
                fileName text,
                FuncName text,
                LineNo int
                )"""

    insertion_sql = """INSERT INTO log(
                Created,
                Name,
                LogLevelName,
                Message,
                fileName,
                FuncName,
                LineNo
                )
                VALUES (
                '%(dbtime)s',
                '%(name)s',
                '%(levelname)s',
                '%(msg)s',
                '%(filename)s',
                '%(funcName)s',
                %(lineno)d
                );
                """

    def __init__(self, db):
        # 기본 핸들러 함수 이용
        logging.Handler.__init__(self)
        self.db = db
        self.conn = ""
        self.cur = ""

    def formatDBTime(self, record):
        # 현재 시간 받아오기
        record.dbtime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(record.created))

    def emit(self, record):

        db_information = dbctrl.DBCtrl()

        if len(self.db) == 0:
            return -1

        # DB 연결
        self.conn = db_information.connect(host=self.db['host'], port=self.db['port'], user=self.db['dbuser'],
                                           passwd=self.db['dbpassword'], db=self.db['dbname'])
        # 연결된 DB 정보로 cursor 생성
        self.cur = db_information.setCursor(self.conn)

        # table이 존재하는지 확인
        table_exist_check = db_information.checkTableExist("log")

        # table 존재 여부 확인
        if table_exist_check != 0:
            try:
                self.cur.execute(MysqlHandler.initial_sql)
            except:
                self.conn.rollback()
                self.cur.close()
                self.conn.close()
                exit(-1)
            else:
                self.conn.commit()
        self.format(record)
        self.formatDBTime(record)

        if record.exc_info:
            record.exc_text = logging._defaultFormatter.formatException(record.exc_info)
        else:
            record.exc_text = ""

        if isinstance(record.__dict__['message'], str):
            record.__dict__['message'] = record.__dict__['message'].replace("'", "''")

        if isinstance(record.__dict__['msg'], str):
            record.__dict__['msg'] = record.__dict__['msg'].replace("'", "''")

        sql = MysqlHandler.insertion_sql % record.__dict__

        try:
            self.cur.execute(sql)
        except Exception as e:
            self.cur.close()
            self.cur = self.conn.cursor()
            try:
                self.cur.execute(MysqlHandler.initial_sql)
            except:
                self.conn.rollback()
                self.cur.close()
                self.conn.close()
                exit(-1)
            else:
                self.conn.commit()
                self.cur.close()
                self.cur = self.conn.cursor()
                self.cur.execute(sql)
                self.conn.commit()

        else:
            self.conn.commit()
