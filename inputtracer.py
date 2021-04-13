import os.path
import sys

from pynput.keyboard import Listener as KeyboardListener
from pynput.keyboard import Key
from pynput.mouse import Listener as MouseListener
import keyboard
from multiprocessing import Process
import psutil

global_x = ""
global_y = ""
global_path = ""

class InputTracer:
    def __init__(self,path):
        self.path=path
        global global_path
        global_path = path

    def initPatternFile(self):
        '''
        마우스 클릭 패턴 저장 파일 초기화

        @return
            True - 성공
            False - 실패
        '''
        try:
            fp = open(self.path,"w")
            fp.close()
        except Exception as e:
            return False

        return True

    def on_click(x,y,button,pressed):
        '''
        클릭 하였을 때 마우스 이벤트 지점 확인 및 파일 저장

        @return
            click 이벤트가 끝났을 때 False 반환
        '''
        global global_path
        global global_x
        global global_y

        fp = open(global_path, "a+")

        # 마우스를 눌렸을 때
        if pressed == True:
            global_x = str(x)
            global_y = str(y)
        # 마우스를 뗄 때
        else:
            # 위치가 변경 된 것을 확인(드래그)
            if global_x != str(x) or global_y != str(y):
                fp.write("Button.drag"+":"+global_x+","+global_y+":"+str(x)+","+str(y)+ "\n")
                print("Button.drag" + ":" + global_x + "," + global_y + ":" + str(x) + "," + str(y) + "\n")
                fp.close()
            # 위치 변경 안 되었 을 때(일반 클릭)
            else:
                fp.write(str(button) + ":" + global_x + "," + global_y + "\n")
                print(str(button) + ":" + global_x + "," + global_y + "\n")
                fp.close()
            global_x = ""
            global_y = ""

            return False

    def on_press(key):
        '''
        키보드 입력 감지

        @param
            key - 입력한 키

        @return
            종료 시 False 반환
        '''
        global global_path

        if os.path.isfile(global_path) == False:
            return False

        fp = open(global_path,'a+')
        # 입력한 키를 파일에 저장
        fp.write("keyboard"+":"+str(key)+"\n")
        print("keyboard" + ":" + str(key) + "\n")
        fp.close()

        return False

    def keyboardTracer(self):
        '''
        마우스 커서, 키보드 이벤트 확인

        @return
            True - 성공
            False - 실패
        '''
        try:
            # 키보드의 esc 를 눌려 리스너 종료
            while keyboard.is_pressed("esc") == 0:
                with KeyboardListener(on_press=InputTracer.on_press) as listener:
                    listener.join()

        except Exception as e:
            print(e)

        return False

    def mouseTracer(self,proc):
        '''
        마우스 커서 이벤트 확인

        @return
            True - 성공
            False - 실패
        '''
        try:
            # 키보드 리스너의 프로세스가 살아 있을 때 까지 반복
            while psutil.pid_exists(proc):
                with MouseListener(on_click=InputTracer.on_click) as listener:
                    listener.join()

        except Exception as e:
            print(e)

        return False

    def tracer(self):
        '''
        키보드, 마우스 리스너를 동시에 사용하기 위한 멀티 프로세스
        두개의 리스너를 동시에 실행

        '''
        procs = []

        keyboard_proc = Process(target=InputTracer.keyboardTracer,args=(self,))
        procs.append(keyboard_proc)
        keyboard_proc.start()

        mouse_proc = Process(target=InputTracer.mouseTracer, args=(self,keyboard_proc.pid))
        procs.append(mouse_proc)
        mouse_proc.start()

        for proc in procs:
            proc.join()

if __name__ == '__main__':
    a = InputTracer("target.txt")
    a.initPatternFile()
    a.tracer()
