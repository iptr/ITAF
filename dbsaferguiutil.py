import time
import winguicommon

def availableManager(window_list):
    '''
    매니저 창이 띄워 졌는지 확인

    @param
        list - 윈도우 리스트

    @return
        True - 성공
        False - 실패
    '''
    try:
        for i in range(len(window_list)):
            # EnterpriseManger 를 얻기위해 split
            comp = window_list[i].replace(" ","").split("[")

            # 구분자가 없는 경우
            if len(comp) != 2:
                continue

            # 구분자가 존재하며 매니저로 판별 되는 경우
            if comp[0] == "EnterpriseManager":
                return True
    except Exception as e:
        print(e)

    return False

def checkManagerContent():
    '''
    매니저의 내용이 제대로 출력 되었는지 확인

    @return
        True - 성공
        False - 실패
    '''
    # 최대 10초 시도
    for i in range(10):
        try:
            # 매니저에서 메뉴를 상징하는 객체가 존재하는지 확인
            winguicommon.findLocationPicture("C:\\Users\\pnpsecure\\Desktop\\icon\\menu.png")
            break
        except Exception as e:
            if i == 9:
                return False
            time.sleep(1)
            continue
    return True

def checkLogInWindow():
    '''
    DBSAFER 로그인 화면이 제대로 출력 되었는지 확인

    @return
        True - 성공
        False - 실패
    '''
    # 최대 10초 시도
    for i in range(10):
        try:
            # 매니저에서 로그인 객체가 존재하는지 확인
            winguicommon.findLocationPicture("C:\\Users\\pnpsecure\\Desktop\\icon\\log_in_id.png")
            break
        except Exception as e:
            if i == 9:
                return False

            time.sleep(1)
            continue

    return True

def runManager(path):
    '''
    매니저 실행

    @param
        path - 매니저 위치

    @return
        True - 성공
        False - 실패
    '''
    if winguicommon.runExe(path) == False:
        return False

    if checkLogInWindow() == False:
        return False

    return True

def closeAlarm(limit_time = 30):
    '''
    패스워드 변경, 공지 알림 체크 및 종료

    @param
        processName - 확인 하고자 하는 창 이름
        limit_time - 매니저가 실행 될 때 총 제한 시간

    @return
        True - 성공
        False - 실패
    '''
    start_time = int(time.time())
    # 매니저 사용 가능 할 때 까지 반복
    while availableManager(winguicommon.getWindowList()) != True:
        try:
            # 알림 창이 있는지 확인
            if winguicommon.checkTargetWindow("알림") == True:
                time.sleep(1)
                winguicommon.inputEsc()
                continue

            compare_time = int(time.time())

            # 지정한 최대 초 만큼 반복
            if compare_time - start_time > limit_time:
                return False

        except Exception as e:
            time.sleep(1)
            print("False!!")

    # 매니저의 내용이 올라왔는지 확인
    if checkManagerContent() == False:
        return False

    return True


def getMangerTitle(window_list):
    '''
    매니저 타이틀 취득

    @param
        window_list - 현재 띄워져 있는 창 리스트

    @return
        DBSAFER 매니저 타이틀
    '''
    index = -1
    try:
        for i in range(len(window_list)):
            # EnterpriseManger 를 얻기위해 split
            comp = window_list[i].replace(" ", "").split("[")

            # 구분자가 없는 경우
            if len(comp) != 2:
                continue

            # 구분자가 존재하며 매니저로 판별 되는 경우
            if comp[0] == "EnterpriseManager":
                index = i
                break

    except Exception as e:
        print(e)
        return ""

    if index == -1:
        return ""

    return window_list[index]


def initMangerLocation():
    '''
    Manager 구동 후 위치 및 크기 고정

    @return
        True - 성공
        False - 실패
    '''
    title = getMangerTitle(winguicommon.getWindowList())
    if winguicommon.resizeWindow(title) == False:
        return False

    if winguicommon.moveWindow(title) == False:
        return False

    print("완료 !")
    return True