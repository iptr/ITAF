import asyncio
import json
import platform as pf
# Libs for Implementation of daemon
import grp
import signal
import logmacro
import argparse
from commonlib import *

'''
TCP5025 port listen
taif_agent로 부터 접속을 받아 서버목록을 관리함
가상 사용자 테스트 세트를 받아 taif_agent에 전달
taif_agent로부터 해당 서버의 가용 상태를 관리
테스트 준비 상태 수집
테스트 실행 명령 전달
테스트 결과 수집
수집된 결과 정리 및 리포트 작성
'''

'''
터미널 명령어 리스트
- help : 사용방법 출력
- show
    - tester : 테스터 목록 출력
    - test_suites : 모든 테스트 스위트 출력
    - test_cases : 모든 테스트 케이스 출력
    - services : 모든 서비스 출력
    - agent_server : Agent 설치된 서버 목록
- add
    - tester : 테스터 추가
    - service : 서비스 추가
    - test_suite : 테스트 스위트 추가
- remove
    - tester : 테스터 삭제
    - service : 서비스 삭제
    - test_suite : 테스트 스위트 삭제
- modify
    - tester : 테스터 수정
    - service : 서비스 수정
    - test_suite : 테스트 스위트 수정
- run
    - test_suite : 테스트 스위트 실행
- winagt : Windows GUI 기능 명령
    - kbd : 키보드 관련 명령
    - mouse : 마우스 관련 명령
    - capture : 화면 캡쳐
    - oscmd : os 명령어 실행
- perfagt : 부하테스트 관련 명령
    - prepare : 슈터들에 데이터들을 전달하여 준비시킴
    - run : 슈터들에 테스트 시작 요청
    - suspend : 슈터들에 테스트 중단 요청
    - resume : 슈터들에 테스트 재개 요청
    - cleanup : 슈터들을 초기화 시킴
'''

'''
taif_manager -> taif_agent 데이터 구조(json)
key : value
cmd : command
param : Parameter
- Command List
    - win_kbd : key value or key value list
    - win_move_mouse : coordinate of cursor to move
    - win_click : action type(right, left, click, double click)
    - win_script : a set of keyboard and mouse actions
    - set_shooter : a dataset file for performance test
    - run_shooter : shooter's ID or None(all)
    - suspend_shooter : shooter's ID or None(all)
    - resume_shooter : shooter's ID or None(all)
    - cleanup_shooter : shooter's ID or None(all)
    - get_shooter_status : shooter's ID or None(all)
'''

class CommandSet:
    '''
    taif_manager -> taif_agent 데이터 구조(json)
    key : value
    cmd : command
    param : Parameter
    - Command List
        - win_kbd : key value or key value list
        - win_move_mouse : coordinate of cursor to move
        - win_click : action type(right, left, click, double click)
        - win_script : a set of keyboard and mouse actions
        - set_shooter : a dataset file for performance test
        - run_shooter : shooter's ID or None(all)
        - suspend_shooter : shooter's ID or None(all)
        - resume_shooter : shooter's ID or None(all)
        - cleanup_shooter : shooter's ID or None(all)
        - get_shooter_status : shooter's ID or None(all)
    '''
    def set(self, cmd, param):
        self.cmd = cmd
        self.param = param

class ResultData:
    '''
    수행한 명령어
    명령 수행 결과
    '''
    def set(self, cmd=None, result=None):
        self.cmd = cmd
        self.result = result

# 관리 서비스 목록 클래스
class ServiceList:
    '''
    taif_manager에서 관리하는 서버목록
    '''
    header = ['Server Name',
              'Protocol',
              'IP',
              'Port',
              'UserID',
              'Passwd',
              'Status',
              'Agent']
    services = []
    def add(self, sname:str, proto:str, 
            ip:str, port:int, user:str, 
            passwd:str, status:str=None, 
            agt_inst:bool=None):
        var_names = locals()
        line = []
        for vn in var_names[1:]:
            line.append(eval(vn))
        self.services.append(line)
    
    def remove():
        pass
    
    def show(self, sname = None):
        if sname == None:
            print_matrix(self.services, self.header)
        else:
            is_found = False
            for line in self.services:
                if line[0] == sname:
                    print_matrix(line, self.header)
                    is_found = True
            if is_found == False:
                print("There is no Server")
        return None

# 부하 테스트 데이터 세트 클래스
class PerfDataSet:
    '''
    테스트 설정 정보
    가상 사용자 정보
        가상 사용자 식별자
        세션 개수
        보안 계정명
        세션 IP
    타겟 서버 정보
        서비스 이름
        서비스 타입
        IP
        Port
        접속계정
        패스워드
        DBSFER 서비스 번호
    입력 데이터 세트
        데이터 타입 : 명령어 또는 전송파일
        명령어일 경우
            명령어, 예상결과, 다음 명령어 수행 사이 딜레이
        전송파일일 경우
            파일명, 원본경로, 원격경로, 받을경로, 해쉬값, 딜레이
    '''
    

# 테스트 준비 상태 수집

# 테스트 실행 명령 전송

# 테스트 결과 수집


# 수집된 결과 및 리포트 작성


# 데몬 클래스
class TaifServer:
    '''
    데몬 형태로 실행 가능하도록 하는 클래스
    열려있는 모든 File descriptor를 닫는다.
    현재 작업 디렉토리를 변경한다
    파일 생성시 마스크를 재설정한다
    백그라운드로 실행된다
    프로세스 그룹에서 분리한다
    터미널의 I/O 시그널을 무시한다
    제어 터미널과 분리한다
    다음과 같은 상황을 올바르게 다룰수 있다
        System V init 프로세스에 의해 시작된다.
        SIGTERM 시그널에 의해 종료된다
        자식 프로세스는 SIGCLD 시그널을 발생시킨다
        
    IPC를 어떻게 구현하지?
    아... 모르겠다 그냥 TCP 포트 통신으로 하자...
    TCP 5025로 붙어서 명령어 떤지고... 결과 받는식으로 가보자
    
    '''
    async def handler(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        while True:
            # 클라이언트가 보낸 내용을 받기
            data = await reader.read(1024)
            # 받은 내용을 출력하고,
            # 가공한 내용을 다시 내보내기
            peername = writer.get_extra_info('peername')
            print(f"[S] received: {len(data)} bytes from {peername}")
            mes = data.decode()
            print(f"[S] message: {mes}")
            #res = mes.upper()[::-1]
            res = mes.upper()
            writer.write(res.encode())
            await writer.drain()

    async def start_server(self):
        # 서버를 생성하고 실행
        server = await asyncio.start_server(self.handler, host="0.0.0.0", port=5025)
        async with server:
            # serve_forever()를 호출해야 클라이언트와 연결을 수락합니다.
            await server.serve_forever()


    def start_taif_server():
        ts = TaifServer()
        asyncio.run(ts.start_server())

if __name__ == '__main__':
    if 'Linux' != pf.system():
        print('This Program can be run on Linux')
        exit(-1)
        
    
        
    # 시작 - 5025포트 리스닝하는 데몬 프로세스 생성
    
    
    pass