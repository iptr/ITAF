from pynput import mouse
import keyboard

global_x = ""
global_y = ""
global_path = ""

class MouseTracer:
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
                fp.write("drag"+":"+global_x+","+global_y+":"+str(x)+","+str(y)+ "\n")
                fp.close()
            # 위치 변경 안 되었 을 때(일반 클릭)
            else:
                fp.write(str(button) + ":" + global_x + "," + global_y + "\n")
                fp.close()
            global_x = ""
            global_y = ""
            return False

    def mouseTracer(self):
        '''
        마우스 커서 확인 (클릭 이벤트 확인)

        @return
            True - 성공
            False - 실패
        '''
        try:
            # 키보드의 c 를 눌려 리스너 종료
            while keyboard.is_pressed("c") == 0:
                with mouse.Listener(on_click=MouseTracer.on_click) as listener:
                    listener.join()
        except Exception as e:
            print(e)
            return False

        return True

if __name__ == '__main__':
    a = MouseTracer("target.txt")
    a.mouseTracer()
