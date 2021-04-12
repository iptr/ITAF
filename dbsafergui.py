import winguicommon
import dbsaferguiutil
import commonlib

DEFAULTICONPATH = "C:\\Users\\pnpsecure\\Desktop\\icon\\"
MANAGERPATH = r"C:\Program Files\PNP SECURE\Enterprise Manager 7\Enterprise Manager.exe"
CONFIGPATH = "conf/dbsaferGUI.conf"
LEFT = 1
RIGHT = 2
DRAG = 3

class Dbsafergui:
    def __init__(self):
        conf = commonlib.readConfFile(CONFIGPATH)
        self.id = conf['id']
        self.passwd = conf['password']
        self.ip = conf['ip']

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
            # 이미지 찾기를 이용하여 id 입력
            print(DEFAULTICONPATH+"log_in_id.png")
            cursor = winguicommon.findLocationPicture(DEFAULTICONPATH+"log_in_id.png")
            winguicommon.clickMouse(cursor)
            winguicommon.inputMsg(self.id)

            # login PassWord 입력
            winguicommon.inputTab()
            winguicommon.inputMsg(self.passwd)

            # login ip 입력
            winguicommon.inputTab()
            winguicommon.inputMsg(self.ip)

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

                # 초기 매니저 위치 및 크기 변경
                if dbsaferguiutil.initMangerLocation() == False:
                    return False

            except Exception as e:
                raise Exception("이미지 실패!!!")
        except Exception as e:
            print("이미지 실패!")
            return False

        return True

    def runTestCase(self,pattern_file_path):
        '''
        기존에 등록되어 있는 테스트 케이스 실행

        @param
            pattern_file_path - 패턴 파일 경로

        @return
            True - 성공
            False - 실패
        '''
        # 마우스 트레이서를 이용한 결과를 읽어옴
        pattern_list = commonlib.getSplitNewLineList(pattern_file_path)

        if len(pattern_list) == 0:
            return False

        # 패턴에 맞추어 마우스 컨트롤
        for i in range(len(pattern_list)):
            # 마우스 패턴 파싱
            result = Dbsafergui.parseMousePattern(self,pattern_list[i])
            if len(result) == 0:
                return False

            # 파싱 된 결과를 토대로 마우스 액션 시작
            if Dbsafergui.runMouseAction(self,result) == False:
                return False

        return True

    def runMouseAction(self,result,x=0,y=0):
        '''
        마우스 정보를 받아 액션을 취함

        @param
            action - 마우스 액션
            x - 드래그시 x 좌표
            y - 드래그시 y 좌표

        @return
            True - 성공
            False - 실패
        '''
        try:
            # 마우스 좌 클릭
            if result["action"] == LEFT:
                winguicommon.clickMouse((result["x"],result["y"]))
            # 마우스 우 클릭
            elif result["action"] == RIGHT:
                winguicommon.clickMouse((result["x"],result["y"]),button="right")
            # 드래그
            elif result["action"] == DRAG:
                winguicommon.moveCursor((result["x"],result["y"]))
                winguicommon.drag((result["move_x"],result["move_y"]))
            else:
                raise Exception("액션 잘못 입력")

        except Exception as e:
            print("마우스 액션 실패!")
            return False

        return True

    def parseMousePattern(self,text):
        '''
        마우스 좌,우 클릭 및 좌표 값 확인

        @param
            text - 마우스 패턴

        @return
            마우스 좌,우 클릭 및 좌표 값
        '''
        result = {}

        try:
            x = 0
            y = 0
            move_x = 0
            move_y = 0
            # 패턴 파일의 내용 중 마우스 버튼에 대한 부분 획득
            action_list = str(text).split(":")

            # x,y 좌표 획득
            existing_location = action_list[1].split(",")

            # 드래그 일 경우
            if len(action_list) == 3:
                action = DRAG
                changed_location = action_list[2].split(",")
                # 기존 마우스 포인터 위치 저장
                x = existing_location[0]
                y = existing_location[1]
                # 바꾼 마우스 포인터 위치 저장
                move_x = changed_location[0]
                move_y = changed_location[1]
            # 마우스 좌클릭 일 때
            elif action_list[0].find("Button.left") != -1:
                action = LEFT
                x = existing_location[0]
                y = existing_location[1]
            # 마우스 우클릭 일 때
            elif action_list[0].find("Button.right") != -1:
                action = RIGHT
                x = existing_location[0]
                y = existing_location[1]
            else:
                action = 0

            result = {"action":action,"x":x,"y":y,"move_x":move_x,"move_y":move_y}

        except Exception as e:
            #todo:logging
            pass

        return result

if __name__ == '__main__':
    a = Dbsafergui()
    #a.start(MANAGERPATH)
    #a.login()
    a.runTestCase("target.txt")