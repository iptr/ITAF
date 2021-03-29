import asyncio

'''
데몬 상태로 수행 기능
    윈도우일 경우와 리눅스일경우 두가지 경우에 대한 처리
    실행되면 taif_manager로 접속 시도
    접속되면 명령 대기 상태가 됨
    명령이 들어오면 수행하고 결과를 리턴함
    다시 명령 대기 상태가 됨
'''

class ResultData:
    '''
    수행한 명령어
    명령 수행 결과
    '''
    def set(self, cmd=None, result=None):
        self.cmd = cmd
        self.result = result

class Connector:
    pass

class AgentDM:
    pass

class Shooter:
    pass

class WinGUICtrl:
    pass
    

if __name__ == '__main__':
    pass