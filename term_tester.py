#!/usr/bin/python
import time
import hashlib
import multiprocessing as mp
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
    
    cmdlines = []
    f = open(conf['Input']['cmd_list_file'])
    reader = csv.reader(f)
    cmdlist = list(reader)
    f.close()
    for row in cmdlist:
        if row[0].find('#') == -1:
            cmdlines.append(row)
    
    procs = []
    q = mp.Queue()
    stime = time.time()
    for i,svr in enumerate(slist):
        for pc in range(int(conf['Common']['session_count'])):
            proc = mp.Process(target=test_func[test_type], 
                              args=(conf, svr, cmdlines, (i,pc), q, stime))
            procs.append(proc)
            proc.start()
            time.sleep(1)
    print('proc cnt',len(procs))
    for proc in procs:
        proc.join()
    
    result = []
    while q.empty() == False:
        result.append(q.get(block=False, timeout=5))    
    return result

def cmd_test(conf, svr, cmdlines, pc, q = None, stime=None):
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
    
    term = TermCtrl()
    if test_type in ['telnet', 'ssh'] :
        runner = CMDRunner()
    else:
        print('Wrong Test Type')
        return -1
        
    #세션 지속하고 명령어만 반복
    sh = None
    result = []
    if persist_session == 'true':
        #접속
        client = term.connect(svr[1], svr[2], svr[3], svr[4], svr[5])
        if type(client) == tl.Telnet:
            sh = client
        elif type(client) == tuple and len(client) == 3:
            c1 = type(client[0]) == pm.client.SSHClient
            c2 = type(client[1]) == pm.channel.Channel
            c3 = ssh_cmd_func == 'runcmdshell'
            c4 = ssh_cmd_func == 'runcmd'
            if c1 and c2 and c4:
                sh = client[0]
            elif c1 and c2 and c3:
                sh = client[1]
            else:
                print('Wrong Type of client1')
                exit(-1)
        else:
            print('Wrong type of client2', client, type(client))
            exit(-2)
        print(type(sh), sh)
        runner.waitrecv(sh)
        cmdrpt = repeater(cmdlines)
        # 명령어 수행부
        while True:
            cmd = next(cmdrpt)
            ret = runner.runcmd(sh, cmd[0], cmd[1])
            # 결과 검증 OK
            c1 = type(ret) == int
            c2 = type(ret) == tuple
            c3 = c2 and ret[0] == True
            c4 = c2 and ret[0] == False
            if c1 or c4:
                result.append(False)
            else:
                result.append(True)
                
            #테스트 종료 기준 (시간, 횟수)
            if criteria == 'time':
                if (time.time() - stime) >= test_time:
                    break
            else:
                run_count += 1
                if run_count >= repeat_count:
                    break
            #딜레이
            time.sleep(delay_time)
        sh.close()     
    else:
        while True:
            # 접속
            client = term.connect(svr[1], svr[2], svr[3], svr[4], svr[5])
            if type(client) == tl.Telnet:
                sh = client
            elif type(client) == tuple and len(client) == 3:
                c1 = type(client[0]) == pm.client.SSHClient
                c2 = type(client[1]) == pm.channel.Channel
                c3 = ssh_cmd_func == 'runcmdshell'
                c4 = ssh_cmd_func == 'runcmd'
                if c1 and c2 and c4:
                    sh = client[0]
                elif c1 and c2 and c3:
                    sh = client[1]
                else:
                    print('Wrong Type of client1')
                    exit(-1)
            else:
                print('Wrong type of client2', client, type(client))
                exit(-2)
            # 명령어 수행
            ret = term.runcmd(sh, cmdlines)
            # 결과 검증
            c1 = type(ret) == int
            c2 = type(ret) == tuple
            c3 = c2 and ret[0] == True
            c4 = c2 and ret[0] == False
            if c1 or c4:
                result.append(False)
            else:
                result.append(True)
        
            #테스트 종료 기준 (시간, 횟수)
            if criteria == 'time':
                if (time.time() - stime) >= test_time:
                    sh.close()
                    break
            else:
                run_count += 1
                if run_count >= repeat_count:
                    sh.close()
                    break
            #딜레이
            time.sleep(delay_time)
    q.put(str(pc) + result)
    term.closeall()

def ftp_test(conf, svr, files, pc, q = None, stime=None):
    run_count = 0
    test_time = int(conf['Common']['test_time'])
    delay_time = int(conf['Common']['delay_time'])
    test_type = conf['Common']['test_type'].lower()
    criteria = conf['Common']['criteria'].lower()
    persist_session = conf['Common']['persist_session'].lower()
    repeat_count = int(conf['Common']['repeat_count'])
    ssh_cmd_func = conf['SSHConfig']['ssh_cmd_func'].lower()
    
    term = TermCtrl()
    if test_type in ['ftpup', 'ftpdown', 'sftpup', 'sftpdown']:
        ftrun = FTRunner()
    else:
        print('Wrong Test Type')
        return -1
    
    ftrunfunc = {
        'ftpup':ftrun.putfile,
        'sftpup':ftrun.putfile,
        'ftpdown':ftrun.getfile,
        'sftpdown':ftrun.getfile,        
    }
    
    result = []
    if persist_session == 'true':
        pass
        #접속
        temp = term.connect(svr[1], svr[2], svr[3], svr[4], svr[5])
        if test_type in ['sftpup', 'sftpdown']:
            client = temp[2]
        else:
            client = temp
        #업/다운 수행
        while True:
            ftrunfunc[test_type](client, files[0], files[1])
        #결과 검증
        #테스트 종료 기준
        #딜레이
    else:
        while True:
            pass
            # 접속
            # 업/다운 수행
            # 결과 검증
            # 테스트 종료 기준
            # 딜레이
    #결과 전달
            
            



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
