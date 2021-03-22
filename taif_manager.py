import socket as skt
import json

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
class CommandSet:
    '''
    taif_manager에서 taif_agent로 보낼때 데이터 형식
    '''
    def set(self, cmd, param):
        self.cmd = cmd
        self.param = param

# 서버 목록 클래스


# 부하 테스트 데이터 세트 클래스


# Agent로부터 접속요청 받을 리스너


# 테스트 준비 상태 수집

# 테스트 실행 명령 전송

# 테스트 결과 수집


# 수집된 결과 및 리포트 작성



if __name__ == '__main__':
    # 시작 - 5025포트 리스닝하는 데몬 프로세스 생성
    
    
    pass