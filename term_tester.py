#!/usr/bin/python
import time
from termctrl import *
from commonlib import *

CONF_FILE = 'conf/term_tester.conf'

def chk_config(conf):
    # 설정내용이 올바른지 확인
    pass    

def run_test(conf, server_list):
    # 현재 테스트 형식은?
    test_type = conf['Common']['test_type'].lower()
    if test_type in ('ssh','sftpup', 'sftpdown'):
        svc_type = 'ssh'
    elif test_type == 'telnet':
        svc_type = 'telnet'
    elif test_type in ('ftpup','ftpdown'):
        svc_type = 'ftp'
    else:
        print('Config Error')
        return -1
    
    test_func = {
        'ssh' : cmd_test,
        'telnet' : cmd_test,
        'ftpup' : ftp_test,
        'ftpdown' : ftp_test,
        'sftpup' : ftp_test,
        'sftpdown' : ftp_test
    }
    
    slist = []
    for sl in server_list:
        if sl[1].lower() == svc_type:
            slist.append(sl)
               
    procs = []
    q = mp.Queue()
    for i,svr in enumerate(slist):
        for pc in range(int(conf['Common']['session_count'])):
            proc = mp.Process(target=test_func[test_type], args=(conf, svr, (i,pc), q,))
            procs.append(proc)
            proc.start()
    print('proc cnt',len(procs))
    for proc in procs:
        proc.join()
    
    result = []
    while q.empty() == False:
        result.append(q.get(block=False, timeout=5))    
    return result

def CallTermCtrl(func):
    def wrapper(*args, **kwargs):
        term = TermCtrl()
        print(*args, **kwargs)
        ret = func(*args, **kwargs)
        term.close()
        del term
        return ret
    return wrapper

def test(param):
    print(param,'in testfunction')

def cmd_test(conf, svr, pc, q = None, stime=None):
    term = TermCtrl()
    #세션 지속 여부
    if conf['Common']['persist_session'].lower()=='true':
        #접속
        client = term.connect(svr[1], svr[2], svr[3], svr[4], svr[5])
        if type(client) == tl.Telnet:
            sh = client
        elif type(client) == pm.client.SSHClient:
            sh = client[1]
        else:
            print('Wrong type of client')
        #시간단위
        if conf['Common']['criteria'].lower() == 'time':
            while True:
                # 명령어 수행(runcmd or runonshell)
                ret = term.runcmdshell(sh, cmdlines)
                # 결과 검증(예상값 데이터가 필요함)
                
                # 현재시간 - 시작시간 >= TEST_TIME 이면 종료
                pass
        #횟수단위
        else:
            for i in range(conf['Common']['test_count']):
                #명령어 수행
                #결과 검증 
                pass
    # 단타 세션
    else:
        #시간단위
        if conf['Common']['criteria'].lower() == 'time':
            while True:
                #접속
                #명령어 수행
                #결과 검증
                pass
        #횟수단위
        else:
            for i in range(conf['Common']['test_count']):
                #접속
                #명령어 수행
                #결과 검증
                pass
    # 명령어 수행
    # 결과값 전달
    term.close()

def ftp_test(conf, svr, pc, q = None):
    term = TermCtrl()
    q.put(str(pc) + 'ftp')
    print('ftp')
    term.close()

if __name__ == '__main__':
    #설정파일 읽기
    conf = getfileconf(CONF_FILE)
    slist = getsvrlistcsv(conf['Common']['server_list_csv'])
    
    #설정 내용 체크
    chk_config(conf)
    
    # 테스트 실행
    result = run_test(conf, slist)
    print(result)
    # 서비스에 맞는 테스트 함수 딕셔너리

    
    # 결과 정리 및 출력
    #print(result)
