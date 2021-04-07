import winguicommon

DEFAULTICONPATH = "icon/"
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
        if winguicommon.runExe(path) == False:
            return False
        try:
            # 디바이스 변경 허용 '예' 클릭
            cursor = winguicommon.findLocationPicture(DEFAULTICONPATH+"yes.png")
            winguicommon.clickMouse(cursor)
        except Exception as e:
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
            # 이미지 찾기를 이용하여 ip 입력
            cursor = winguicommon.findLocationPicture(DEFAULTICONPATH+"log_in_ip.png")
            winguicommon.clickMouse(cursor)
            winguicommon.inputMsg("10.77.161.167")

            # login ID 입력
            winguicommon.inputTab()
            winguicommon.inputMsg("heyboy")

            # login PassWord 입력
            winguicommon.inputTab()
            winguicommon.inputMsg("dbsafer00")

            # Connect 클릭
            cursor = winguicommon.findLocationPicture(DEFAULTICONPATH + "log_in_connect.png")
            winguicommon.clickMouse(cursor)

            # 비밀 번호 바꾸라는 경고, 알림 등을 끌 때 사용
            # TODO : 좌표값을 얻지 않고도 무조건 해당 알림을 종료 할 수 있는 방법을 찾자
            # TODO : new window 가 발생 했을 때 이벤트를 감지 할 수 있는거 찾아 보자
                # 1. esc 를 2번 누른다.
                    # 문제점: 해당 화면(알림)이 언제 뜰지 모른다.
                # 2. 이미지를 찾아 간다.
                    # 비밀 번호 바꾸라는 경고가 뜨는경우 안 뜨는 경우를 구분해야 한다.
                # 3. 좌표값을 찾아 간다.
                    # 매니저 위치, 크기가 일정하다는 가정이 필요
            winguicommon.inputEsc()
            winguicommon.inputEsc()

        except Exception as e:
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


if __name__ == '__main__':
    a = Dbsafergui()
    # a.login()
    a.viewControlPolicy()
    a.viewControlObject()
    a.viewMonitoring()
    a.viewSetting()
    a.viewLog()
