import commonlib
import winguicommon
import time
import win32gui
import os
class Rdp:
    def __init__(self):
        pass
    def available(self,window_list):
        '''
        원격 데스크톱 연결이 제대로 되었는가 확인

        @param
            window_list - 현재 윈도우 객체

        @return
            True - 성공
            False - 실패
        '''
        try:
            for i in range(len(window_list)):
                comp = window_list[i].split(".")
                if len(comp) != 4:
                    continue
                comp = window_list[i].replace(" ",'').split(":")
                if comp[1] == "원격 데스크톱 연결":
                    return True
        except Exception as e:
            return False
        return False
    def start(self):
        '''
        RDP 시작

        @return
            True - 성공
            False - 실패
        '''
        if winguicommon.runcom() ==False:
            return False
        time.sleep(1)

        if winguicommon.inputMsg("mstsc") == False:
            return False

        winguicommon.keyboardAction("Key.enter")
        return True

    def run(self):
        '''
        Manger login

        @return
            True - 성공
            False - 실패
       '''
        try:
            server = ["192.168.105.69","192.168.105.69","192.168.105.69"]
            server2 = ["dbsafer00))","dbsafer00))","dbsafer00))"]
            i = 0
            j = 0
            for i in range(len(server)):
                Rdp.start(self)
                for _ in range(10):
                    if winguicommon.getWindowList().count("원격 데스크톱 연결") != 0:
                        break
                    time.sleep(1)
                winguicommon.inputMsg(server[i])
                winguicommon.keyboardAction("Key.enter")
                # 10초 반복
                for j in range(10):
                    # window 보안 나오면 나감
                    if winguicommon.getWindowList().count("Windows 보안") != 0:
                        break
                    # n 키 누름
                    winguicommon.upDownOneKey('n')
                    time.sleep(1)
                
                if j > 9:
                    return False
                
                time.sleep(1)
                winguicommon.inputMsg(server2[i])
                winguicommon.keyboardAction("Key.enter")
                for _ in range(5):
                    winguicommon.upDownOneKey('y')            
                    time.sleep(1)        
                time.sleep(2.5)
                #winguicommon.closeCurrentWindow()
                winguicommon.clickMouse((771,19))
                winguicommon.keyboardAction("Key.enter")

                #0,0 으로 이동
                #winguicommon.moveWindow()
                # 크기 재 설정
                #winguicommon.resizeWindow()


        except Exception as e:
            return False

        return True

if __name__ == '__main__':
    a = Rdp()
    a.run()