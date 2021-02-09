#!/usr/bin/python
import time
import hashlib
import multiprocessing as mp
from ast import literal_eval
from termctrl import *
from commonlib import *

CONF_FILE = 'conf/term_tester.conf'

def chk_config(conf):
    # 설정내용이 올바른지 확인
    pass

def dist_ftpcli(client, test_type):
    if type(client) == int:
        return -1
    elif type(client) == tuple and test_type.lower() == 'sftp':
        return client[2]
    elif type(client) == fl.FTP and test_type.lower() == 'ftp':
        return client
    else:
        return -1

def dist_client(client, ssh_cmd_func):
    c1 = type(client) == tl.Telnet
    c2 = type(client) == tuple and len(client) == 3
    c5 = ssh_cmd_func == 'runcmdshell'
    c6 = ssh_cmd_func == 'runcmd'
    if c1:
        return client
    elif c2:
        c3 = type(client[0]) == pm.client.SSHClient
        c4 = type(client[1]) == pm.channel.Channel
        if c3 and c4 and c6:
            return client[0]
        elif c3 and c4 and c5:
            return client[1]
        else:
            print('Wrong Type of client')
            return -1
    else:
        print('Wrong type of client2', client, type(client))
        return -1

def showbasicconf(conf, tsc, cmdcnt):
    row = '\n[Test Configuration]\n'
    row += 'Test Type : %s \n'%conf['Common']['test_type']
    row += 'Test Criteria : %s\n'%conf['Common']['criteria']
    if conf['Common']['criteria'].lower() == 'time':
        row += 'Test Time : %s\n'%conf['Common']['test_time']
    elif conf['Common']['criteria'].lower() == 'count':
        row += 'Repeat Count : %s\n'%conf['Common']['repeat_count']
    else:
        print('Wrong Configuration : CRITERIA')
        exit(-1)
    row += 'Delay_time : %s\n'%conf['Common']['delay_time']
    row += 'CMD(File) Set Count : %s\n'%cmdcnt
    row += 'Total Server Count : %s \n'%tsc
    row += 'Session Count per a server : %s\n'%conf['Common']['session_count']
    row += 'Total Session Count : %s \n'%(tsc*int(conf['Common']['session_count']))
    row += 'Persist Session : %s\n'%conf['Common']['persist_session']
    row += '\n[Test Started : Session information]'
    print(row)

def showresult(totses, totcnt, totfail, stime, ftime):
    '''
    Total Sesssions:
    Total Command(Files) Count:
    Start Time :
    Finish Time :
    Test Running Time :
    '''
    row = '\n[Test Result]\n'
    row += 'Total Sesssions: %s\n'%totses
    row += 'Total Command(Files) Count: %s\n'%totcnt
    row += 'Total Failure Count: %s\n'%totfail
    try:
        row += 'Total Success Rate: %.2f%%\n'%(100-((totfail/totcnt)*100))
    except Exception as e:
        row += 'Total Success Rate: 0%\n'
    row += 'Start Time : %s\n'%time.strftime('%c', time.localtime(stime))
    row += 'Finish Time : %s\n'%time.strftime('%c', time.localtime(ftime))
    row += 'Running Time : %.2fS\n'%(ftime - stime)
    print(row)

def run_test(conf, server_list):
    test_type = conf['Common']['test_type'].lower()
    if test_type in ['ssh','sftp']:
        svc_type = 'ssh'
    elif test_type == 'telnet':
        svc_type = 'telnet'
    elif test_type == 'ftp':
        svc_type = 'ftp'
    else:
        print('Config Error')
        return -1
    
    test_func = {
        'ssh' : cmd_test,
        'telnet' : cmd_test,
        'ftp' : ftp_test,
        'sftp' : ftp_test
    }
    
    slist = []
    for sl in server_list:
        if sl[1].lower() == svc_type:
            slist.append(sl)
    
    inputdata = []
    if test_type in ('ssh', 'telnet'):
        cmdlist = getlistfromcsv(conf['Input']['cmd_list_file'])
        for row in cmdlist:
            if row[0].find('#') == -1:
                inputdata.append(row)
    else:
        fileslist = getlistfromcsv(conf['Input']['files_list_file'])
        for row in fileslist:
            if row[0].find('#') == -1:
                inputdata.append(row)

    showbasicconf(conf, len(slist), len(inputdata))
    procs = []
    q = mp.Queue()
    stime = time.time()
    for i,svr in enumerate(slist):
        for pc in range(int(conf['Common']['session_count'])):
            proc = mp.Process(target=test_func[test_type], 
                              args=(conf, svr, inputdata, (i,pc), q, stime))
            procs.append(proc)
            proc.start()
            print("%s %s %s:%s #%s"%(svr[0],svr[1],svr[2],svr[3],pc))
    
    for proc in procs:
        proc.join()
    ftime = time.time()
    result = []
    while q.empty() == False:
        result.append(q.get(block=False, timeout=5))    
    return result, (stime, ftime)

def cmd_test(conf, svr, cmdlines, pc, q = None, stime=None):
    """[summary]

    Args:
        conf ([type]): [description]
        svr ([type]): [description]
        pc ([type]): [description]
        q ([type], optional): [description]. Defaults to None.
        stime ([type], optional): [description]. Defaults to None.
    """
    test_time = int(conf['Common']['test_time'])
    delay_time = float(conf['Common']['delay_time'])
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
    result = {
        'sescnt':0,
        'cmdcnt':0,
        'failcnt':0,
        'stime':time.time(),
        'ftime':0
    }
    cmdrpt = repeater(cmdlines)
    if persist_session == 'true':
        #접속
        client = term.connect(svr[1], svr[2], svr[3], svr[4], svr[5])
        sh = dist_client(client, ssh_cmd_func)
        if type(sh) != int and sh != -1:
            result['sescnt'] += 1
        else:
            q.put(str(pc) + str(result))
            exit(-1)
        runner.waitrecv(sh)
        
        # 명령어 수행부
        while True:
            cmd = next(cmdrpt)
            if len(cmd) < 2:
                ret = runner.runcmd(sh, cmd[0], '')
            else:
                ret = runner.runcmd(sh, cmd[0], cmd[1])
            result['cmdcnt'] += 1
            # 결과 검증
            c1 = type(ret) == int
            c2 = type(ret) == tuple
            c3 = c2 and ret[0] == True
            c4 = c2 and ret[0] == False
            if c1 or c4:
                result['failcnt'] += 1

            #테스트 종료 기준 (시간, 횟수)
            if criteria == 'time':
                if (time.time() - stime) >= test_time:
                    break
            else:
                if result['cmdcnt'] >= repeat_count:
                    break
            #딜레이
            time.sleep(delay_time)
        sh.close()     
    else:
        while True:
            # 접속
            client = term.connect(svr[1], svr[2], svr[3], svr[4], svr[5])
            sh = dist_client(client, ssh_cmd_func)
            if type(sh) != int and sh != -1:
                result['sescnt'] += 1
            else:
                break
            runner.waitrecv(sh)
            # 명령어 수행
            cmd = next(cmdrpt)
            if len(cmd) < 2:
                ret = runner.runcmd(sh, cmd[0], '')
            else:
                ret = runner.runcmd(sh, cmd[0], cmd[1])
            result['cmdcnt'] += 1
            # 결과 검증
            c1 = type(ret) == int
            c2 = type(ret) == tuple
            c3 = c2 and ret[0] == True
            c4 = c2 and ret[0] == False
            if c1 or c4:
                result['failcnt'] += 1
                #result.append(True)
            
            #테스트 종료 기준 (시간, 횟수)
            if criteria == 'time':
                if (time.time() - stime) >= test_time:
                    sh.close()
                    break
            else:
                if result['cmdcnt'] >= repeat_count:
                    sh.close()
                    break
            #딜레이
            time.sleep(delay_time)
    result['ftime'] = time.time()
    buf = str(svr[1]) + ';' + str(svr[2])+ ':' + str(svr[3]) + ';' 
    buf += str(pc) + ';' + str(result) + ';' 
    buf += str(result['cmdcnt']/(result['ftime'] - result['stime']))
    q.put(buf)

def ftp_test(conf, svr, files, pc, q = None, stime=None):
    test_time = int(conf['Common']['test_time'])
    delay_time = int(conf['Common']['delay_time'])
    test_type = conf['Common']['test_type'].lower()
    criteria = conf['Common']['criteria'].lower()
    persist_session = conf['Common']['persist_session'].lower()
    repeat_count = int(conf['Common']['repeat_count'])
    jobid = str(pc[0]) + str(pc[1])
    
    term = TermCtrl()
    if test_type in ['ftp', 'sftp']:
        ftrun = FTRunner()
    else:
        print('Wrong Test Type')
        return -1
    
    filerpt = repeater(files)
    result = {
        'sescnt':0,
        'cmdcnt':0,
        'failcnt':0,
        'stime':time.time(),
        'ftime':0
    }
    if persist_session == 'true':
        #접속
        temp = term.connect(svr[1], svr[2], svr[3], svr[4], svr[5])
        client = dist_ftpcli(temp, test_type)
        if client == -1:
            return -1
        else:
            result['sescnt'] += 1

        #업/다운 수행
        while True:
            row = next(filerpt)
            upload = row[1] + os.sep + row[0]
            remote = row[2] + os.sep + row[0] + '-' + jobid
            download = row[3] + os.sep + row[0] + '-' + jobid
            putret = ftrun.putfile(client, upload, remote)
            getret = ftrun.getfile(client, remote, download)
            result['cmdcnt'] += 2 
            #결과 검증1
            c1 = putret not in [0,None] or getret not in [0,None]
            if c1:
                r1 = False
            else:
                r1 = True
            #결과 검증2
            try:
                hash = getfilehash(download)
            except Exception as e:
                print(e)
            if hash == row[4]:
                r2 = True
            else:
                r2 = False
            if r1 == False or r2 == False:
                result['failcnt'] += 2
            #테스트 종료 기준
            if criteria == 'time':
                if (time.time() - stime) >= test_time:
                    break
            else:
                if result['cmdcnt'] >= repeat_count:
                    break
            #딜레이
            time.sleep(delay_time)
        client.close()        
        #딜레이
    else:
        while True:
            temp = term.connect(svr[1], svr[2], svr[3], svr[4], svr[5])
            client = dist_ftpcli(temp, test_type)
            if client == -1:
                return -1
            else:
                result['sescnt'] += 1
            row = next(filerpt)
            upload = row[1] + os.sep + row[0]
            remote = row[2] + os.sep + row[0] + '-' + jobid
            download = row[3] + os.sep + row[0] + '-' + jobid           
            putret = ftrun.putfile(client, upload, remote)
            getret = ftrun.getfile(client, remote, download)
            result['cmdcnt'] += 1
            #결과 검증1
            c1 = putret not in [0,None] or getret not in [0,None]
            if c1:
                r1 = False
            else:
                r1 = True
            #결과 검증2
            hash = getfilehash(download)
            if hash == row[4]:
                r2 = True
            else:
                r2 = False
            if r1 == False or r2 == False:
	            result['failcnt'] += 2
            #테스트 종료 기준
            if criteria == 'time':
                if (time.time() - stime) >= test_time:
                    client.close()
                    break
            else:
                if result['cmdcnt'] >= repeat_count:
                    client.close()
                    break
            #딜레이
            time.sleep(delay_time)
            client.close()
    result['ftime'] = time.time()
    buf = str(svr[1]) + ';' + str(svr[2])+ ':' + str(svr[3]) + ';' 
    buf += str(pc) + ';' + str(result) + ';' 
    buf += str(result['cmdcnt']/(result['ftime'] - result['stime']))
    q.put(buf)
            
            
if __name__ == '__main__':
    #설정파일 읽기
    conf = getfileconf(CONF_FILE)
    slist = getsvrlistcsv(conf['Common']['server_list_csv'])
    
    #설정 내용 체크
    chk_config(conf)
    
    stime = time.time()
    # 테스트 실행
    result = run_test(conf, slist)
    # 결과 출력
    totses = 0
    totcnt = 0
    totfail = 0
    print('\n[Session Result]')
    header = '{0:^8}'.format('SType')
    header += '{0:^23}'.format('IP : Port')
    header += '{0:^10}'.format('Sess ID')
    header += '{0:^10}'.format('CMDCNT')
    header += '{0:^10}'.format('FailCNT')
    header += '{0:^10}'.format('STime')
    header += '{0:^10}'.format('FTime')
    header += '{0:^10}'.format('TPS')
    print(header)
    for row in result[0]:
        tmpd = literal_eval(row.split(';')[3])
        totses += int(tmpd['sescnt'])
        totcnt += int(tmpd['cmdcnt'])
        totfail += int(tmpd['failcnt'])
        tmp = '{0:^8}'.format(row.split(';')[0])
        tmp += '{0:^23}'.format(row.split(';')[1])
        tmp += '{0:^10}'.format(row.split(';')[2])
        tmp += '{0:^10}'.format(str(tmpd['cmdcnt']))
        tmp += '{0:^10}'.format(str(tmpd['failcnt']))
        tmp += '{0:^10}'.format(time.strftime('%X',time.localtime(int(tmpd['stime']))))
        tmp += '{0:^10}'.format(time.strftime('%X',time.localtime(int(tmpd['ftime']))))
        tmp += '{0:^10}'.format('%.2f'%float(row.split(';')[4]))
        print(tmp)
    showresult(totses, totcnt, totfail, result[1][0], result[1][1])
