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
    stime = time.time()
    for i,svr in enumerate(slist):
        for pc in range(int(conf['Common']['session_count'])):
            proc = mp.Process(target=test_func[test_type], args=(conf, svr, (i,pc), q, stime))
            procs.append(proc)
            proc.start()
    print('proc cnt',len(procs))
    for proc in procs:
        proc.join()
    
    result = []
    while q.empty() == False:
        result.append(q.get(block=False, timeout=5))    
    return result

def cmd_test(conf, svr, pc, q = None, stime=None):
    """[summary]

    Args:
        conf ([type]): [description]
        svr ([type]): [description]
        pc ([type]): [description]
        q ([type], optional): [description]. Defaults to None.
        stime ([type], optional): [description]. Defaults to None.
    """
    run_count = 0
    test_time = int(conf['Common']['test_time'])
    delay_time = int(conf['Common']['delay_time'])
    test_type = conf['Common']['test_type'].lower()
    criteria = conf['Common']['criteria'].lower()
    persist_session = conf['Common']['persist_session'].lower()
    repeat_count = int(conf['Common']['repeat_count'])
    ssh_cmd_func = conf['SSHConfig']['ssh_cmd_func'].lower()
    chk_verification = conf['Common']['chk_verification'].lower()
    
    f = open(conf['Input']['cmd_list_file'])
    reader = csv.reader(f)
    cmdlist = list(reader)
    f.close()
    cmdlines = []
    
    for row in cmdlist:
        if row[0].find('#') == -1:
            cmdlines.append(row[0])
    term = TermCtrl()
    #세션 지속하고 명령어만 반복
    if persist_session == 'true':
        #접속
        client = term.connect(svr[1], svr[2], svr[3], svr[4], svr[5])
        if type(client) == tl.Telnet:
            sh = client
        elif type(client) == pm.client.SSHClient:
            sh = client[0]
        elif type(client) == pm.channel.Channel:
            sh = client[1]
        else:
            print('Wrong type of client')
            
        while True:
            # 명령어 수행(runcmd or runonshell)
            if test_type == 'ssh' and ssh_cmd_func == 'runcmd':
                ret = term.runcmd(sh, cmdlines)
            else:
                ret = term.runcmdshell(sh, cmdlines)
            # 결과 검증
            if chk_verification == 'true':
                pass
            else:
                pass
            #테스트 종료 기준 (시간, 횟수)
            if criteria == 'time':
                if (time.time() - stime) >= test_time:
                    break
            else:
                run_count += 1
                if run_count > repeat_count:
                    break
            #딜레이
            time.sleep(delay_time)
        #결과 전달
        q.put(str(pc) + result)
        sh.close()     
    else:
        while True:
            # 접속
            client = term.connect(svr[1], svr[2], svr[3], svr[4], svr[5])
            if type(client) == tl.Telnet:
                sh = client
            elif type(client) == pm.client.SSHClient:
                sh = client[1]
            else:
                print('Wrong type of client')
            # 명령어 수행
            if test_type == 'ssh' and ssh_cmd_func == 'runcmd':
                ret = term.runcmd(sh, cmdlines)
            else:
                ret = term.runcmdshell(sh, cmdlines)
            # 결과 검증
            if chk_verification == 'true':
                pass
            else:
                pass
            #테스트 종료 기준 (시간, 횟수)
            if criteria == 'time':
                if (time.time() - stime) >= test_time:
                    break
            else:
                run_count += 1
                if run_count > repeat_count:
                    break
            #딜레이
            time.sleep(delay_time)
            sh.close()
        q.put(str(pc) + result)
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
