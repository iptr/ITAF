import argparse
import socket
from threading import Thread
import platform

if platform.system() == "Windows":
    import winguicommon

def ignoreComment():
    pass

def getCommand():
    # test Code
    return "abc".encode()

def proceedMsg(client_sock,addr,fp):
    '''
    명령을 입력 받고 agent에 전달 후 응답 기록
    '''
    while True:
        try:
            command = getCommand()

            client_sock.sendall(command)

            data = client_sock.recv(4096)

            if not data:
                break

            if len(data) < 256:
                print(data)

            fp.write(data.decode())

        except Exception as e:
            print("ERROR!!!!!")
            break


def setServer(host,port):
    '''
    agent 와 통신
    '''

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((host, port))
    server_socket.listen()

    fp = open("file_write_test.txt",'w')

    client_socket,addr = server_socket.accept()
    sock_thread = Thread(target=proceedMsg,args=(client_socket,addr,fp,),daemon=True)
    sock_thread.start()

    sock_thread.join()

    fp.close()

class ShowAction(argparse.Action):
    # Custom Action Class
    # todo : self.option 삭제, if 문 내 비교는 option_string 으로 교체
    def __init__(self, option_strings, nargs=None, **kwargs):
        self.option = option_strings
        super(ShowAction,self).__init__(option_strings=option_strings,nargs=nargs, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        # 호출 시 옵션 확인 및 출력
        if ''.join(self.option) == "--showTester":
            ShowAction.showTester(self)
        if ''.join(self.option) == "--showTestSuites":
            ShowAction.showSuite(self)
        if ''.join(self.option) == "--showServices":
            ShowAction.showTestCases(self)
        if ''.join(self.option) == "--showTestCases":
            ShowAction.showServices(self)
        if ''.join(self.option) == "--showAgentServer":
            ShowAction.showAgentServer(self)

    def showTester(self):
        print("show!")
    def showSuite(self):
        print("show2!")
    def showTestCases(self):
        print("show!")
    def showServices(self):
        print("show!")
    def showAgentServer(self):
        print("Agent!!")

class AddAction(argparse.Action):
    def __init__(self, option_strings, nargs=None, **kwargs):
        self.option = option_strings
        super(AddAction,self).__init__(option_strings=option_strings,nargs=nargs, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        if ''.join(self.option) == "--addTester":
            AddAction.addTester(self)
        if ''.join(self.option) == "--addService":
            AddAction.addService(self)
        if ''.join(self.option) == "--addTestSuite":
            AddAction.addTestSuite(self)

    def addTester(self):
        print("RT")

    def addService(self):
        print("RS")

    def addTestSuite(self):
        print("RTS")

class RemoveAction(argparse.Action):
    def __init__(self, option_strings, nargs=None, **kwargs):
        self.option = option_strings
        super(RemoveAction,self).__init__(option_strings=option_strings,nargs=nargs, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        if ''.join(self.option) == "--removeTester":
            RemoveAction.removeTester(self)
        if ''.join(self.option) == "--removeService":
            RemoveAction.removeService(self)
        if ''.join(self.option) == "--removeTestSuite":
            RemoveAction.removeTestSuite(self)

    def removeTester(self):
        print("RT")
    def removeService(self):
        print("RS")
    def removeTestSuite(self):
        print("RTS")

class ModifyAction(argparse.Action):
    def __init__(self, option_strings, nargs=None, **kwargs):
        self.option = option_strings
        super(ModifyAction,self).__init__(option_strings=option_strings,nargs=nargs, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        if ''.join(self.option) == "--modifyTester":
            ModifyAction.modifyTester(self)
        if ''.join(self.option) == "--modifyService":
            ModifyAction.modifyService(self)
        if ''.join(self.option) == "--modifyTestSuite":
            ModifyAction.modifyTestSuite(self)

    def modifyTester(self):
        print("mdTester")
    def modifyService(self):
        print("mdService")
    def modifyTestSuite(self):
        print("mdTS")

class WinAction(argparse.Action):
    def __init__(self, option_strings, nargs=None, **kwargs):
        self.option = option_strings
        super(WinAction,self).__init__(option_strings=option_strings,nargs=nargs, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        pass

    def keyboard(command):
        if winguicommon.inputMsg(command) == False:
            return False

        return True

    def moveMouse(pos):
        if winguicommon.moveCursor(pos) == False:
            return False

        return True

    def clickMouse(pos,click=1,interval=1,button="left",double=0):
        if winguicommon.clickMouse(pos,click,interval,button,double) == False:
            return False

        return True

    def capture(path,start_x=0,start_y=0,x=0,y=0):
        if winguicommon.runCapture(start_x,start_y,x,y,path) == False:
            return False

        return True

    def runCommand(command,path=""):
        result = winguicommon.runWindowCommand(command)

        if len(path) == 0:
            print(result)
        else:
            fp = open(path,'a')
            fp.write("---------\n")
            fp.write("%s command result:\n"%(command))
            fp.write(result+"\n")
            fp.write("---------\n")

        return result

class Overloader(argparse.Action):
    def __init__(self, option_strings, nargs=None, **kwargs):
        self.option = option_strings
        super(Overloader, self).__init__(option_strings=option_strings,nargs=nargs, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        pass

    def prepare():
        print("prepare")

    def suspend():
        print("suspend")

    def resume():
        print("resume!")

    def cleanUp():
        print("clean")

    def run():
        print("run")

class RunAction(argparse.Action):
    def __init__(self, option_strings, nargs=None, **kwargs):
        self.option = option_strings
        super(RunAction,self).__init__(option_strings=option_strings,nargs=nargs, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        if ''.join(self.option) == "--runTestSuite":
            RunAction.runTestSuite(self,values)

    def runTestSuite(self,info):
        account = info[0]
        file_name = info[1]

        setServer(host = '127.0.0.1',port = 5025)
        print("show!")




if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog="manager",usage='%(prog)s [options]')

    #parser.add_argument('integers', metavar='N', type=int, nargs='+',
    #                    help='an integer for the accumulator')
    #parser.add_argument('--sum', dest='accumulate', action='store_const',
    #                    const=sum, default=max,
    #                    help='sum the integers (default: find the max)')

    parser.add_argument('--showTester', action=ShowAction,help="테스터 목록을 출력 해준다.\n사용법:--showTester",nargs=0)
    parser.add_argument('--showTestCases', action=ShowAction,help="테스트 케이스 목록을 출력 해준다.\n사용법:--showTestCases",nargs=0)
    parser.add_argument('--showTestSuites', action=ShowAction,help="테스트 스위트 목록을 출력 해준다.\n사용법:--showTestSuite",nargs=0)
    parser.add_argument('--showServices', action=ShowAction,help="서비스 목록을 출력 해준다.\n사용법:--showServices",nargs=0)
    parser.add_argument('--showAgentServer', action=ShowAction,help="에이전트 서버 목록을 출력 해준다.\n사용법:--showAgentServer",nargs=0)

    parser.add_argument('--addTester',action=AddAction)
    parser.add_argument('--addService',action=AddAction)
    parser.add_argument('--addTestSuite',action=AddAction)

    parser.add_argument('--removeTester',action=RemoveAction)
    parser.add_argument('--removeService',action=RemoveAction)
    parser.add_argument('--removeTestSuite',action=RemoveAction)

    parser.add_argument('--modifyTester',action=ModifyAction)
    parser.add_argument('--modifyService',action=ModifyAction)
    parser.add_argument('--modifyTestSuite',action=ModifyAction)

    parser.add_argument('--runTestSuite',action=RunAction,nargs=3)

    parser.add_argument('--perfagtPrepare',action=Overloader)
    parser.add_argument('--perfagtRun',action=Overloader)
    parser.add_argument('--perfagtSuspend',action=Overloader)
    parser.add_argument('--perfagtResume',action=Overloader)
    parser.add_argument('--perfagtCleanup',action=Overloader)

    if platform.system() == "Windows":
        parser.add_argument('--winagtKeyboard', action=WinAction,nargs= 1,help="키보드 입력을 할 수 있게 함\n usage:--winagtKeyboard [command]")
        parser.add_argument('--winagtMouseMove', action=WinAction,nargs= 1,help="마우스를 해당 x,y 좌표로 옮김\n usage:--winagtMouseMove [pos] \n pos=(x,y)")
        parser.add_argument('--winagtMouseClick', action=WinAction,nargs= 5,help="해당 x,y 좌표를 클릭함\n usage:--winagtMouseClick [pos] [click] [interval] [button] [double]\n pos=(x,y) \n click = 클릭 할 횟수 \n interval = 간격 \n buttotn = [left | right] \n double = 더블클릭 여부")
        parser.add_argument('--winagtCapture', action=WinAction,nargs= 5,help="키보드 입력을 할 수 있게 함\n usage:--winagtCapture [path] [start_x] [start_y] [x] [y]\n path=캡쳐 저장 위치")
        parser.add_argument('--winagtOscmd', action=WinAction,nargs= 2,help="윈도우 명령어를 사용 가능 하게 함\n usage:--winagtOscmd [command] [path]\n path = 결과 저장 할 파일")

    args = parser.parse_args()
    #print(args)
    #print(args)
    #print(args.accumulate(args.integers))

    #setServer()
