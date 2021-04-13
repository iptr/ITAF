import subprocess
import pyscreenshot
import pyautogui
import time
import win32api
from win32 import win32gui
from pynput.keyboard import Key, Controller


def runWindowCommand(command=""):
    '''
    cmd 명령어 실행 결과 확인

    @param
        command - cmd 명령어

    @return
        명령 실행 결과
    '''
    result = ""
    try:
        # 커맨드 명령 실행
        result = subprocess.call(command,shell=True)
    except Exception as e:
        #todo:logging
        print(e)
        return ""

    return result
def runCapture(start_x = 0, start_y = 0, x = 640, y=480,path=""):
    '''
    화면 캡쳐 실행 및 저장

    @param
        start_x - x 시작 좌표
        start_y - y 시작 좌표
        x - x 좌표
        y - y 좌표

    @return
        True - 성공
        False - 실패
    '''
    try:
        # 각 좌표를 기준으로 캡쳐 실행
        img = pyscreenshot.grab(bbox=(start_x,start_y,x,y))
        # 캡쳐본 지정된 경로에 저장
        img.save(path)
    except Exception as e:
        #todo:logging
        print(e)
        return False

    return True

def runExe(path=""):
    '''
    외부 실행 프로그램 실행

    @param
        path - 외부 실행 프로그램 경로

    @return
        True - 성공
        False - 실패
    '''
    try:
        # 지정된 경로에 있는 응용 프로그램 실행
        win32api.ShellExecute(0,'open',path,'','',1)
        time.sleep(5)
    except Exception as e:
        #todo:logging
        print(e)
        return False

    return True

def getCursor():
    '''
    현재 커서 위치 반환

    @return
        현재 커서 위치
    '''
    pos = ()
    try:
        pos = pyautogui.position()
    except Exception as e:
        return pos

    return pos

def getMonitorSize():
    '''
    현재 모니터 해상도 확인

    @return
        해상도
    '''
    size = 0

    try:
        size = pyautogui.size()
    except Exception as e:
        return -1

    return size

def moveCursor(pos):
    '''
    절대적인 위치로 커서 이동

    @param
        pos - x,y 좌표

    @return
        True - 성공
        False - 실패
    '''
    try:
        pyautogui.FAILSAFE = False
        pyautogui.moveTo(pos)
    except Exception as e:
        #todo:logging
        return False

    return True

def clickMouse(pos=(),click=1,interval=1,button="left",double=0):
    '''
    마우스 클릭

    @param
        pos - x,y 좌표
        click - 원하는 클릭 횟수
        interval - 클릭 간격
        button - 마우스 버튼(좌클릭 - left, 우클릭 - right)
        double - 더블 클릭 여부

    @return
        True - 성공
        False - 실패
    '''
    try:
        if len(pos) == 0:
            pyautogui.click()
        else:
            pyautogui.FAILSAFE = False
            if double == 0:
                # 클릭
                pyautogui.click(pos,clicks=click,interval=interval,button=button)
            elif double == 1:
                pyautogui.doubleClick(pos,button=button)
            else:
                raise Exception("클릭 실패!")
    except Exception as e:
        return False

    return True

def changeMouseRelativePositon(pos):
    '''
    마우스 포인터 상대적으로 이동

    @param
        pos - x,y 좌표

    @return
        True - 성공
        False - 실패
    '''
    try:
        pyautogui.moveRel(pos)
    except Exception as e:
        return False

    return True

def drag(pos,persistence=1,button="left",relative=0):
    '''
    원하는 영역 드래그

    @param
        pos - x,y 좌표
        persistence - 지속 시간
        button - 마우스 버튼
        relative - 상대적 좌표값 사용 여부

    @return
        True - 성공
        False - 실패
    '''
    try:
        # 절대 좌표를 사용 하는 경우
        if relative == 0:
            pyautogui.dragTo(pos,duration=persistence,button=button)
        # 상대 좌표를 사용 하는 경우
        elif relative == 1:
            pyautogui.dragRel(pos,duration=persistence,button=button)
        else:
            raise Exception("드래그 실패!")
    except Exception as e:
        return False

    return True

def inputMsg(message=""):
    '''
    응용 프로그램에 입력값 전달

    @param
        message - 입력값

    @return
        True - 성공
        False - 실패
    '''
    try:
        # 해당 문자를 입력
        pyautogui.typewrite(message)
    except Exception as e:
        return False

    return True

def upDownOneKey(charactor):
    '''
    하나의 키만 입력

    @param
        charactor - 입력하고자하는 문자

    @return
        True - 성공
        False - 실패
    '''
    if len(charactor) != 1:
        return False

    try:
        # 해당 문자를 누름
        pyautogui.keyDown(charactor)
        # 키보드 자판을 누른 후 뗌
        pyautogui.keyUp(charactor)
    except Exception as e:
        return False

    return True

def keyboardAction(key):
    '''
    Key 를 이용하여 키보드 액션을 취함

    @param
        key - 키보드 액션 키

    @return
        True - 성공 , 무시하고 진행
        False - 실패
    '''
    try:
        keyboard = Controller()
        if len(key) == 0:
            return True

        # 타입이 Key 인 경우
        if key.find("Key.") != -1:
            key = Key[key.split(".")[1]]
        # escape 문자 무시
        elif key.find("\\") != -1:
            return True

        keyboard.press(key)
        keyboard.release(key)

    except Exception as e:
        return False

    return True

def findLocationPicture(path):
    '''
    사진을 이용하여 해당 사진의 내용이 존재하는 좌표 값을 반환

    @param
        path - 사진 경로

    @return
        해당 좌표값 반환
    '''
    picture_center = ()
    try:
        # 사진의 내용이 존재하는 좌표값 확인
        picture = pyautogui.locateOnScreen(path)
        # 좌표 값의 가운데를 클릭
        picture_center=pyautogui.center(picture)
    except Exception as e:
        print(e)
        return picture_center

    return picture_center

def closeCurrentWindow():
    '''
    현재 창 닫기

    @return
        True - 성공
        False - 실패
    '''
    try:
        # alt + F4 종료 커맨드 실행
        pyautogui.hotkey('alt','f4')
    except Exception as e:
        return False

    return True

def inputTab():
    '''
    키보드의 tab을 입력

    @return
        True - 성공
        False - 실패
    '''
    try:
        # tab 입력
        pyautogui.press('tab')
    except Exception as e:
        return False

    return True

def inputEsc():
    '''
    키보드의 ESC를 입력

    @return
        True - 성공
        False - 실패
    '''
    try:
        # esc 입력
        pyautogui.press('esc')
    except Exception as e:
        return False

    return True

def getWindowList():
    '''
    현재 띄워져 있는 window 리스트 확인

    @return
        output - 윈도우 타이틀 리스트
    '''
    def callback(hwnd, hwnd_list: list):
        # 창의 타이틀 확인
        title = win32gui.GetWindowText(hwnd)
        # 사용 가능한 창의 정보 리스트에 저장
        if win32gui.IsWindowEnabled(hwnd) and win32gui.IsWindowVisible(hwnd) and title:
            hwnd_list.append(title)
        return True
    output = []
    win32gui.EnumWindows(callback, output)
    return output

def checkTargetWindow(processName=""):
    '''
    찾고자 하는 창의 유무 확인

    @param
        processName - 찾고자 하는 창의 이름

    @return
        True - 존재
        False - 존재하지 않음
    '''
    handler_list = []
    try:
        # 현재 윈도우 종류 확인
        handler_list = getWindowList()
        # 찾고자 하는 윈도우가 있는지 확인
        if handler_list.count(processName) != 0:
            return True
        else:
            return False
    except Exception as e:
        return False

def resizeWindow(title = "",x_size=600,y_size=800):
    '''
    창 크기 바꾸기

    @param
        title - 크기를 바꾸고자 하는 창의 타이틀
        x_size - 가로 크기
        y_size - 세로 크기

    @return
        True - 성공
        False - 실패
    '''
    try:
        # 해당 타이틀에 해당하는 객체 선택
        win = pyautogui.getWindowsWithTitle(title)[0]
        # 해당 객체 크기 변경
        win.resize(x_size,y_size)
    except Exception as e:
        print("size 실패!!")
        return False

    return True

def moveWindow(title = "",x_pos = 0, y_pos = 0):
    '''
    창 위치 옮기기

    @param
        title - 옮기고자 하는 창의 타이틀
        x_pos - x 좌표
        y_pos - y 좌표

    @return
        True - 성공
        False - 실패
    '''
    try:
        # 해당 타이틀에 해당하는 객체 선택
        win = pyautogui.getWindowsWithTitle(title)[0]
        # 해당 객체 이동
        win.moveTo(x_pos,y_pos)
    except Exception as e:
        print("size 실패!!")
        return False

    return True

if __name__ == '__main__':
    pass
