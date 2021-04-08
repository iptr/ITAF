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
            
            # 비밀 번호 바꾸라는 경고, 알림 등을 끌 때 사용
            try:
                if dbsaferguiutil.closeAlarm() == False:
                    return False

                cursor = winguicommon.findLocationPicture(DEFAULTICONPATH + "menu.png")
                winguicommon.clickMouse(cursor)

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


if __name__ == '__main__':
    a = Dbsafergui()
    a.start(MANAGERPATH)
    a.login()
    a.viewControlPolicy()
    a.viewControlObject()
    a.viewMonitoring()
    a.viewSetting()
    a.viewLog()
