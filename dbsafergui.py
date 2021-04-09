import winguicommon
import dbsaferguiutil

DEFAULTICONPATH = "C:\\Users\\pnpsecure\\Desktop\\icon\\"
MANAGERPATH = r"C:\Program Files\PNP SECURE\Enterprise Manager 7\Enterprise Manager.exe"

#TODO : 여러 가지 방향성을 조금 더 고민해 보아야 할 필요가 있다.
class Dbsafergui:
    def __init__(self):
        pass
 
    def start(self,path):
        '''
        DBSAFER Manger 시작

        @param
            path - 매니저 실행 파일 경로

        @return
            True - 성공
            False - 실패
        '''
        if dbsaferguiutil.runManager(path) == False:
            print("run 실패")
            return False

        return True

    def login(self):
        '''
        Manger login

        @return
            True - 성공
            False - 실패
       '''
        try:
            #todo: conf 파일 활용 여부 고려

            # 이미지 찾기를 이용하여 id 입력
            print(DEFAULTICONPATH+"log_in_id.png")
            cursor = winguicommon.findLocationPicture(DEFAULTICONPATH+"log_in_id.png")
            winguicommon.clickMouse(cursor)
            winguicommon.inputMsg("admin")

            # login PassWord 입력
            winguicommon.inputTab()
            winguicommon.inputMsg("admin007!")

            # login ip 입력
            winguicommon.inputTab()
            winguicommon.inputMsg("10.77.162.11")

            # Connect 클릭
            cursor = winguicommon.findLocationPicture(DEFAULTICONPATH + "log_in_connect.png")
            winguicommon.clickMouse(cursor)

            try:
                # 비밀 번호 바꾸라는 경고, 알림 등을 끌 때
                if dbsaferguiutil.closeAlarm() == False:
                    return False

                # 매니저 내용이 제대로 출력 되지 않은 경우
                if dbsaferguiutil.checkManagerContent() == False:
                    return False

                if dbsaferguiutil.initMangerLocation() == False:
                    return False

            except Exception as e:
                raise Exception("이미지 실패!!!")
        except Exception as e:
            print("이미지 실패!")
            return False

        return True

    def viewControlPolicy(self):
        '''
        정책 제어 화면 출력

        @return
            True - 성공
            False - 실패
        '''
        try:
            # 정책 제어 아이콘 찾아 클릭
            cursor = winguicommon.findLocationPicture(DEFAULTICONPATH+"control_policy.png")
            winguicommon.clickMouse(cursor)
        except Exception as e:
            return False

        return True

    def viewControlObject(self):
        '''
        객체 제어 화면 출력

        @return
            True - 성공
            False - 실패
        '''
        try:
            # 객체 제어 아이콘 찾아 클릭
            cursor = winguicommon.findLocationPicture(DEFAULTICONPATH + "control_object.png")
            winguicommon.clickMouse(cursor)
        except Exception as e:
            return False

        return True

    def viewMonitoring(self):
        '''
        모니터링 화면 출력

        @return
            True - 성공
            False - 실패
        '''
        try:
            # 모니터링 아이콘 찾아 클릭
            cursor = winguicommon.findLocationPicture(DEFAULTICONPATH + "monitor.png")
            winguicommon.clickMouse(cursor)
        except Exception as e:
            return False

        return True

    def viewLog(self):
        '''
        로그 조회 화면 출력

        @return
            True - 성공
            False - 실패
        '''
        try:
            # 로그 조회 아이콘 찾아 클릭
            cursor = winguicommon.findLocationPicture(DEFAULTICONPATH + "log.png")
            winguicommon.clickMouse(cursor)
        except Exception as e:
            return False

        return True

    def viewMaintenance(self):
        '''
        유지 보수 화면 출력

        @return
            True - 성공
            False - 실패
        '''
        try:
            # 유지 보수 아이콘 찾아 클릭
            cursor = winguicommon.findLocationPicture(DEFAULTICONPATH + "maintenance.png")
            winguicommon.clickMouse(cursor)
        except Exception as e:
            return False


        return True

    def viewSetting(self):
        '''
        설정 화면 출력

        @return
            True - 성공
            False - 실패
        '''
        try:
            # 설정 아이콘 찾아 클릭
            cursor = winguicommon.findLocationPicture(DEFAULTICONPATH + "setting.png")
            winguicommon.clickMouse(cursor)
        except Exception as e:
            return False

        return True

    def runTestCase(self):
        # 마우스 트레이서를 이용한 결과를 읽어옴
        # 결과를 똑같이 따라 가면서 CASE를 실행 시킴

if __name__ == '__main__':
    a = Dbsafergui()
    a.start(MANAGERPATH)
    a.login()
    a.viewControlPolicy()
    a.viewControlObject()
    a.viewMonitoring()
    a.viewSetting()
    a.viewLog()

# Default 값을 파일에 저장하여 기본적인 기능 테스트시에 Case를 제공(1번)
# 마우스 좌표값 파일 저장 (2번)
# 좌표 값 순서대로 클릭 하여 진행
# 창 크기, 위치를 절대적인 값을 움직여서 항상 객체가 있는곳은 좌표값이 일치함
# 정책 관리
    # DBMS
        # 접속 제어
            #(72,112)
            # (150,92)
            #(172,105)
        # 권한 제어
            # (72,112)
            # (150,92)
            # (198,120)
    # FTP
        # 접속 제어
            # (72,112)
            # (153,142)
            # (172,157)
        # 권한 제어
            # (72,112)
            # (153,142)
            # (172,168)
    # 터미널
        # 접속 제어
            # (72,112)
            # (180,188)
            # (182,202)
        # 권한 제어
            # (72,112)
            # (180,188)
            # (182,214)

# 객체 관리 (34,136)
    #서비스(184,93)
        #DB(177,103)
        #FTP(177,131)
        #TERMINAL(177,139)
    # 인스턴스 169 157
    # IP 주소 169 167
    # 접속 계정 169 184
    # 어플리케이션 162 207
    # 보안계정 162 225
    # 데이터마스킹 162 236
    # 테이블/컬럼 162 250
    # 정형 쿼리162 268
    # 시간 162 281
    # 명령어 162 296
# 모니터링 (49,177)
    #서비스 로그
        # 174 108
        # 174 118
        # 174 139
            #조회 1074 107
    #기타
        #관리자 192 170
        #시스템 192 182
        #경고 192 203
            #조회 515 142
# 로그조회 (45,200)

# 유지 보수(36,237)

# 동작 설정 (36,275)