import time
import dbsaferudpsender
import dbctrl

class Service:
    '''
    dbsafer Service control class

    서비스 추가 제거 사용 정지 수정등을 행함
    '''
    def __init__(self):
        self.mysql = dbctrl.DBCtrl()
        #TODO : conf 파일 활용
        conn = self.mysql.connect(host="10.77.162.11", port=3306, user="safeusr",
                        passwd="dbsafer00", db="dbsafer3")
        self.mysql.setCursor(conn)

    def insertService(self,service_name,service_type,dest_ip,dest_port,gateway_ip,gateway_port):
        '''
        dbsafer 서비스 추가

        @param
            service_name - 서비스 이름
            service_type - DB 종류
            dest_ip - 도착지 아이피
            dest_port - 도착지 포트
            gateway_ip - 게이트웨이 아이피
            gateway_port - 게이트웨이 포트

        @return
            객체 번호 반환 (실패시 -1)
        '''
        col = ["no"]
        # services 테이블에 객체가 있는지 확인
        number_list = self.mysql.select("dbsafer3","services",cols=col)
        no = 1

        if len(number_list) <= 0:
            return -1

        # 서비스 명 중복 검사
        if len(self.mysql.select("dbsafer3","services","name='%s'"%(service_name),["name"])) != 0:
            return -1

        # DBSAFER 포트 중복 검사
        if len(self.mysql.select("dbsafer3","services","listenport='%s'"%(gateway_port),["listenport"])) != 0:
            return -1

        # 서버 주소, 포트 중복 검사
        if len(self.mysql.select("dbsafer3","services","destip='%s'"%(dest_ip),["destip"])) != 0:
            if len(self.mysql.select("dbsafer3", "services", "destport='%s'" % (dest_port), ["destport"])) != 0:
                return -1

        # 가장 마지막 객체 넘버 + 1
        no = int(number_list.pop()[0]) + 1

        # 필요 정보 선택
        column = ["no","name","type","destip","destport","listenip","listenport"]
        # 필요 정보에 맞는 값 설정
        value = [no,service_name,service_type,dest_ip,dest_port,gateway_ip,gateway_port]

        self.mysql.insert("dbsafer3","services",column,value)

        return no

    def updateService(self,service_number,service_name,service_type,dest_ip,dest_port,gateway_ip,gateway_port):
        '''
        서비스 객체 수정

        @param
            service_number - 서비스 고유 번호
            service_name - 변경하고자 하는 서비스 이름
            service_type - 변경하고자 하는 DB 타입
            dest_ip - 변경하고자 하는 도착지 아이피
            dest_port - 변경하고자 하는 도착지 포트
            gateway_ip - 변경하고자 하는 게이트웨이 아이피
            gateway_port - 변경하고자 하는 게이트웨이 포트

        @return
            True - 성공
            False - 실패
        '''
        # 객체가 존재하지 않을 경우
        if len(self.mysql.select("dbsafer3","services","no = %d"%(service_number))) == 0:
            return False

        column = ["name","type","destip","destport","listenip","listenport"]
        value = [service_name,service_type,dest_ip,dest_port,gateway_ip,gateway_port]

        # 업데이트 명령 실행
        if self.mysql.update("dbsafer3","services","no = %d"%(service_number),column,value) < 0:
            return False

        return True

    def deleteService(self,service_number):
        '''
        서비스 제거

        @param
            service_number - 제거하고자하는 서비스 번호

        @return
            True - 성공
            False - 실패
        '''
        # 서비스 존재 여부 확인
        if len(self.mysql.select("dbsafer3","services","no = %d"%(service_number))) == 0:
            return False

        # 서비스 삭제 시도
        if self.mysql.delete("dbsafer3","services","no = %d"%(service_number)) <0:
            return False

        return True


    def runService(self,service_number):
        '''
        선택한 서비스 구동

        @param
            service_number - 구동하고자 하는 서비스 번호

        @return
            True - 성공
            False - 실패
        '''
        # 객체 존재 여부 확인
        if len(self.mysql.select("dbsafer3","services","no = %d"%(service_number))) == 0:
            return False

        column = ["status", "stopped"]
        value = [3,1]

        # 서비스 구동 시도
        if self.mysql.update("dbsafer3", "services", "no = %d" % (service_number), column, value) < 0:
            return False

        return True

    def stopService(self,service_number):
        '''
        선택한 서비스 정지

        @param
            service_number - 정지하고자하는 서비스 번호

        @return
            True - 성공
            False - 실패
        '''
        # 객체 존재 여부 확인
        if len(self.mysql.select("dbsafer3","services","no = %d"%(service_number))) == 0:
            return False

        column = ["status", "stopped"]
        value = [2, 2]

        # 서비스 정지 시도
        if self.mysql.update("dbsafer3", "services", "no = %d" % (service_number), column, value) <0:
            return False

        return True

class Policy:
    '''
    dbsafer Policy control class

    정책 추가 사용 제거 수정 등을 행함
    '''
    def __init__(self):
        #TODO:conf File
        self.mysql = dbctrl.DBCtrl()
        conn = self.mysql.connect(host="10.77.162.11", port=3306, user="safeusr",
                                  passwd="dbsafer00", db="dbsafer3")
        self.mysql.setCursor(conn)

    def addPolicy(self,mode=1,**kwargs):
        '''
        정책 추가

        @param
            mode -  1. DB 접근제어
                    2. FTP 접근제어
                    3. TERMINAL 접근제어
                    4. DB 권한제어
                    5. FTP 권한제어
                    6. TERMINAL 권한제어
            kwargs - 컬럼, 값 (컬럼 = 값 의 형식)

        @return
            True - 성공
            False - 실패
        '''
        # no 는 현재 시간을 받아 대입
        id = time.time_ns()

        col = ["no"]
        values = [id]

        # 입력 정보 사항 컬럼 및 대응하는 값에 저장
        for key,value in kwargs.items():
            # 서비스를 적용하는 경우
            if key == "service":
                service = self.mysql.select("dbsafer3", "services", "name = '%s'" % (value), ["no"])
                if len(service) == 0:
                    return False
                value = ''.join(str(e) for e in service).replace('[','').replace(']','')

            # 접속 계정을 적용하는 경우
            elif key == "user":
                account_index = self.mysql.select("dbsafer3", "client_id", "id = '%s'" % (value), ["object_index"])
                if len(account_index) == 0:
                    return False
                col.append("id_object_index")
                values.append(''.join(str(e) for e in account_index).replace('[','').replace(']',''))

            col.append(key)
            values.append(value)
        table = ""

        if mode == 1:
            table = "policy_db_access"
        elif mode == 2:
            table = "policy_ftp_access"
        elif mode == 3:
            table = "policy_terminal_access"
        elif mode == 4:
            table = "policy_db_auth"
        elif mode == 5:
            table = "policy_ftp_auth"
        elif mode == 6:
            table = "policy_terminal_auth"
        else:
            return False

        if self.mysql.insert("dbsafer3", table, col, values) < 0:
            return False

        return True

    def modifyPolicy(self,name,mode = 1,**kwargs):
        '''
        정책 수정

        @param
            mode -  1. DB 접근제어
                    2. FTP 접근제어
                    3. TERMINAL 접근제어
                    4. DB 권한제어
                    5. FTP 권한제어
                    6. TERMINAL 권한제어
            kwargs -
        '''
        col = []
        values = []

        # 입력 정보 사항 컬럼 및 대응하는 값에 저장
        for key, value in kwargs.items():
            col.append(key)
            values.append(value)

        table = ""

        if mode == 1:
            table = "policy_db_access"
        elif mode == 2:
            table = "policy_ftp_access"
        elif mode == 3:
            table = "policy_terminal_access"
        elif mode == 4:
            table = "policy_db_auth"
        elif mode == 5:
            table = "policy_ftp_auth"
        elif mode == 6:
            table = "policy_terminal_auth"
        else:
            return False

        if self.mysql.update("dbsafer3", table, "name = '%s'" % (name), col, values) < 0:
            return False

        return True

    def deletePolicy(self,name,mode = 1):
        '''
        DB 접근 제어 정책 삭제

        @param
            mode -  1. DB 접근제어
                    2. FTP 접근제어
                    3. TERMINAL 접근제어
                    4. DB 권한제어
                    5. FTP 권한제어
                    6. TERMINAL 권한제어
            name - 정책 이름
        '''
        table = ""

        if mode == 1:
            table = "policy_db_access"
        elif mode == 2:
            table = "policy_ftp_access"
        elif mode == 3:
            table = "policy_shell_access"
        elif mode == 4:
            table = "policy_db_auth"
        elif mode == 5:
            table = "policy_ftp_access"
        elif mode == 6:
            table = "policy_shell_access"
        else:
            return False

        if self.mysql.delete("dbsafer3", table , "name = '%s'" % (name)) < 0:
            return False

        dbsaferudpsender.dbsaferUdpPacket()

        return True

    def usePolicy(self,service_name,mode = 1):
        '''
        정책 사용
        하나의 정책을 선택하여 사용, 나머지 정책은 미사용으로 변경

        @param
            service_name - 사용으로 변경하고자 하는 서비스 이름
            table - 적용 하고자하는 정책 테이블
        '''
        #TODO : 정책 변경시 DB 와 매니저는 바뀌는 것을 확인
        #TODO : UDP 패킷을 전송해도 정책이 적용되지 않는 현상 발견
        #TODO : 가만히 일정 시간을 놔두면 정책이 적용됨
        #TODO : 로그를 보니 UDP를 제대로 받지 못하였다는 식으로 로그가 찍히는 것을 확인
        #TODO : 조금 더 조사 후 수정 필요
        table = ""

        if mode == 1:
            table = "policy_db_access"
        elif mode == 2:
            table = "policy_ftp_access"
        elif mode == 3:
            table = "policy_shell_access"
        elif mode == 4:
            table = "policy_db_auth"
        elif mode == 5:
            table = "policy_ftp_access"
        elif mode == 6:
            table = "policy_shell_access"
        else:
            return False

        # 해당 정책 사용
        if self.mysql.update("dbsafer3", table, "name = '%s'" % (service_name), ["enabled"], [1]) < 0:
            return False
        # 해당 정책을 제외한 나머지 정책 미 사용
        if self.mysql.update("dbsafer3", table, "name != '%s'" % (service_name), ["enabled"], [0]) < 0:
            return False

        dbsaferudpsender.dbsaferUdpPacket()

        return True

    def getPolicyNumber(self, service_name, mode = 1):
        '''
        정책 number 확인

        @param
            service_name - 정책 이름을 확인 하고자하는 정책 서비스 이름
            table - 해당 서비스가 존재하는 테이블
        '''
        table = ""

        if mode == 1:
            table = "policy_db_access"
        elif mode == 2:
            table = "policy_ftp_access"
        elif mode == 3:
            table = "policy_shell_access"
        elif mode == 4:
            table = "policy_db_auth"
        elif mode == 5:
            table = "policy_ftp_access"
        elif mode == 6:
            table = "policy_shell_access"
        else:
            return False
        result = []
        result = self.mysql.select("dbsafer3",table,"name = '%s'"%(service_name),["no"])
        return result[0]

class DBSAFERLogger:
    '''
    A class that allows you to check DBSAFER's logs.

    DB, FTP, Terminal 관련 로그 확인
    '''
    def __init__(self):
        # TODO : conf File
        self.mysql = dbctrl.DBCtrl()
        conn = self.mysql.connect(host="10.77.162.11", port=3306, user="safeusr",
                                  passwd="dbsafer00", db="dbsafer3")
        self.mysql.setCursor(conn)

    def dbLogSearch(self):
        '''
        DB 정책 로그 조회

        @return
            로그 리스트
        '''
        log_list = []
        if DBSAFERLogger.dbAccessLogSearch(self) != -1:
            log_list.append(DBSAFERLogger.dbAccessLogSearch(self))
        if DBSAFERLogger.dbAuthLogSearch(self) != -1:
            log_list.append(DBSAFERLogger.dbAuthLogSearch(self))

        return log_list

    def ftpLogSearch(self):
        '''
        FTP 정책 로그 조회

        @return
            로그 리스트
        '''
        log_list = []
        if DBSAFERLogger.ftpAccessLogSearch(self) != -1:
            log_list.append(DBSAFERLogger.ftpAccessLogSearch(self))
        if DBSAFERLogger.ftpAuthLogSearch(self) != -1:
            log_list.append(DBSAFERLogger.ftpAuthLogSearch(self))

        return log_list

    def terminalLogSearch(self):
        '''
        Terminal 정책 로그 조회

        @return
            로그 리스트
        '''
        log_list = []
        if DBSAFERLogger.terminalAccessLogSearch(self) != -1:
            log_list.append(DBSAFERLogger.terminalAccessLogSearch(self))
        if DBSAFERLogger.terminalAuthLogSearch(self) != -1:
            log_list.append(DBSAFERLogger.terminalAuthLogSearch(self))

        return log_list

    def dbAccessLogSearch(self):
        '''
        DB 접근제어 관련 로그

        @return
            로그 리스트 반환
        '''
        log_list = self.mysql.select("dbsafer3","policy_db_access_history")

        return log_list

    def dbAuthLogSearch(self):
        '''
        DB 권한제어 관련 로그

        @return
            로그 리스트 반환
        '''
        log_list = self.mysql.select("dbsafer3","policy_db_auth_history")

        return log_list

    def ftpAccessLogSearch(self):
        '''
        FTP 접근제어 관련 로그

        @return
            로그 리스트 반환
        '''
        log_list = self.mysql.select("dbsafer3", "policy_ftp_access_history")

        return log_list

    def ftpAuthLogSearch(self):
        '''
        FTP 권한제어 관련 로그

        @return
            로그 리스트 반환
        '''
        log_list = self.mysql.select("dbsafer3", "policy_ftp_auth_history")

        return log_list

    def terminalAccessLogSearch(self):
        '''
        Terminal 접근제어 관련 로그

        @return
            로그 리스트 반환
        '''
        log_list = self.mysql.select("dbsafer3", "policy_shell_access_history")

        return log_list

    def terminalAuthLogSearch(self):
        '''
        Terminal 권한제어 관련 로그

        @return
            로그 리스트 반환
        '''
        log_list = self.mysql.select("dbsafer3", "policy_shell_auth_history")

        return log_list


if __name__ == '__main__':
    #service = Service()
    #service.deleteService(26)
    #service.insertService("mysql3",9,"10.77.162.11",3306,"10.77.162.11",4003)
    #service.updateService(27,"mymy",9,"10.77.162.11",3306,"10.77.162.11",4003)
    #service.stopService(27)
    #log_result = DBSAFERLogger()
    #print(log_result.dbLogSearch())
    policy = Policy()
    policy.usePolicy("new",mode=4)
    #policy = Policy()
    #policy.addDBAccessPolicy(name="1a222bcd",ip_begin="10.77.161.15",user="account",service="ora")
    #log = DBSAFERLogger()
    #print(log.dbAuthLogSearch())
    #print(log.dbAccessLogSearch())
    #print(log.dbLogSearch())






