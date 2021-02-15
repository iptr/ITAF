#!/usr/bin/python3
import time
import multiprocessing as mp
from ast import literal_eval
from termctrl import *
from commonlib import *

CONF_FILE = 'conf/term_tester.conf'

class ConfSet:
    svc_type = None
    test_type = None
    server_list_csv = None
    persist_session = None
    start_after_deploy = None
    measure_spec = None
    measure_spec_freq = None
    proc_count = None
    session_count = None
    criteria = None
    test_time = None
    repeat_count = None
    session_delay = None
    cmd_delay = None
    connect_timeout = None
    bind_interface = None
    cmd_list_file = None
    files_list_file = None
    ssh_auth_type = None
    ssh_key_file = None
    ssh_cmd_func = None
    
    def __init__(self, configfile):
        conf = getfileconf(configfile)
        self.test_type = conf['Common']['test_type'].lower()
        if self.test_type in ['ssh','sftp']:
            self.svc_type = 'ssh'
        elif self.test_type == 'telnet':
            self.svc_type = 'telnet'
        elif self.test_type == 'ftp':
            self.svc_type = 'ftp'
        else:
            print('Config Error')
            return -1
        self.server_list_csv = conf['Common']['server_list_csv']
        self.persist_session = conf['Common']['persist_session'].lower()
        self.start_after_deploy = conf['Common']['start_after_deploy'].lower()
        self.measure_spec = conf['Common']['measure_spec'].lower()
        self.measure_spec_freq = int(conf['Common']['measure_spec_freq'])
        self.proc_count = int(conf['Common']['proc_count'])
        self.sessiont_count = int(conf['Common']['session_count'])
        self.criteria = conf['Common']['criteria'].lower()
        self.test_time = int(conf['Common']['test_time'])
        self.repeat_count = int(conf['Common']['repeat_count'])
        self.session_delay = int(conf['Common']['session_delay'])
        self.cmd_delay = float(conf['Common']['cmd_delay'])
        self.connect_timeout = int(conf['Common']['connect_timeout'])       
        self.bind_interface = conf['Common']['bind_interface'].lower()
        self.cmd_list_file = conf['Input']['cmd_list_file']
        self.files_list_file = conf['Input']['files_list_file']
        self.ssh_auth_type = conf['SSHConfig']['ssh_auth_type'].lower()
        self.ssh_key_file = conf['SSHConfig']['ssh_key_file'].lower()
        self.ssh_cmd_func = conf['SSHConfig']['ssh_cmd_func'].lower()
        del conf


class DataSet:
    targetset = []
    dataset = []

    def __init__(self, slist, dataset):
        self.targetset = slist
        self.dataset = dataset
        
        del slist
        del dataset
        

def chk_config(conf):
    # 설정내용이 올바른지 확인
    pass

def prepare():
    conf = ConfSet(CONF_FILE)
    server_list = getsvrlistcsv(conf.server_list_csv)
    proc_cnt = conf.proc_count
    rptcnt = repeater(range(proc_cnt))
    slist = [[] for i in range(proc_cnt)]
    
    for sl in server_list:
        if sl[1].lower() == conf.svc_type:
            slist[next(rptcnt)].append(sl)
            
    dataset = []
    if conf.test_type in ('ssh', 'telnet'):
        cmdlist = getlistfromcsv(conf.cmd_list_file)
        for row in cmdlist:
            if row[0].find('#') == -1:
                dataset.append(row)
    else:
        fileslist = getlistfromcsv(conf.files_list_file)
        for row in fileslist:
            if row[0].find('#') == -1:
                dataset.append(row)
    dslist = []    
    for sl in slist:
        dslist.append(DataSet(conf, sl, dataset))
    return conf, dslist

def connect(term, conf, svr):
    temp = term.connect(svr[1], svr[2], svr[3], svr[4], svr[5],
                                        ifc = conf.bind_interface)
    if conf.test_type in ['ssh','telnet']:
        ret = dist_ftpcli(temp, conf.test_type)
    elif conf.test_type == ['sftp', 'ftp']:
        ret = dist_client(temp, conf.ssh_cmd_func)
    else:
        print('wrong test_type')
        return -1
    
def runcmd(runner, client, cmd):
    if len(cmd) < 2:
        ret = runner.runcmd(client, cmd[0], '')
    else:
        ret = runner.runcmd(client, cmd[0], cmd[1])
    # 결과 검증
    c1 = type(ret) == int
    c2 = type(ret) == tuple
    c3 = c2 and ret[0] == True
    c4 = c2 and ret[0] == False
    if c1 or c4:
        return -1
    else:
        return 0

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
    row += 'cmd_delay : %s\n'%conf['Common']['cmd_delay']
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

def run_test(conf, dslist):
    test_func = {
        'ssh' : cmd_test,
        'telnet' : cmd_test,
        'ftp' : ftp_test,
        'sftp' : ftp_test
    }

    # 기본 설정 출력 부분
    showbasicconf(conf, dslist)
    procs = []
    result = []
    # 부모 -> 자식 시그널용 공유메모리
    sig = mp.Value('d',0)
    # 자식 -> 부모 결과 전달용 큐
    rq = mp.Queue()
    stime = time.time()
    
    for psn, ds in enumerate(dslist):
        proc = mp.Process(target=test_func[conf.test_type], 
                          args=(conf, ds, psn, sig, rq,))
        procs.append(proc)
        proc.start()
    
    if conf.start_after_deploy == 'true':
        input('###### Press any key for starting... #####]')
    sig.value = 1
    '''
    # 측정 여부 확인해서 주기적으로 성능 측정
    if conf['Common']['measure_spec'].lower() == 'true':
        while sig.value = 1:
            tmpq = mp.Queue()
            tprocs = []
            tresult = []
            #ttds = DataSet(ds, dataset)
            #tconf.criteria = 'count'
            #tconf.sessiont_count = 1
            #tconf.repeat_count = len(dataset)
            #tconf.session_delay = 0
            tconf.cmd_delay = 0
            tproc = mp.Process(target=test_func[test_type], 
                               args=(ttds, -1, sig, tmpq,))
            tprocs.append(proc)
            tproc.start()
            tproc.join()
    
        while tmpq.empty() == False:
            tresult.append(tmpq.get(block=False, timeout = 5))
        print(tresult)
       ''' 
    # 자식프로세스로부터 결과값 받아오기
    while len(result) < conf.proc_count:
        while rq.empty() == False:
            result.append(rq.get(block=False, timeout=5))
    
    for proc in procs:
        proc.join()
    ftime = time.time()
    return result, (stime, ftime)

def cmd_test(conf, ds, psn, sig = None, rq = None):
    """[summary]

    Args:
        conf : Configuration instance 
        ds (TestDataSet): Test data Set instance 
        ps ([type]): Process sequence Number
        sig (Shared memory): signal from parant
        rq (pm.Queue): for sending result to parant 
    """
    term = TermCtrl()
    if ds.test_type in ['telnet', 'ssh'] :
        runner = CMDRunner()
    else:
        print('Wrong Test Type')
        return -1
        
    
    clients = []
    result = {
        # 프로세스 순서 번호
        'psn':psn,
        # 전체 결과 
        'result':None,
        # 대상 서버 개수
        'svrcnt':0,
        # 열었던 총 세션 개수
        'sescnt':0,
        # 명령어 개수
        'cmdcnt':0,
        # 실패 개수
        'failcnt':0,
        # 시작 시간
        'stime':0,
        # 종료 시간
        'ftime':0
    }
    # 데이터세트 리피터
    cmdrpt = repeater(ds.dataset)
    #세션 지속하고 명령어만 반복
    if conf.persist_session == 'true':
        # 세션 카운터
        scnt = 0
        result['stime'] = time.time()
        while True:
            # 접속
            for svr in ds.targetset:  
                client = connect(term, conf, svr)
                if client != -1:
                    result['sescnt'] += 1
                else:
                    result['result'] = -1
                    rq.put(result)
                    print(str(result), 'Error')
                    exit(-1)
                time.sleep(conf.session_delay)
                runner.waitrecv(client)
                clients.append(client)
            scnt += 1
            # 세션 카운트가 0인이면 무한 반복
            if conf.session_count > 0:
                if scnt > conf.session_count:
                    break
            else:
                if scnt % 100 == 0:
                    print('#%s proc : %s Sessions Connected'(psn,scnt))
        print('#%s proc : %s Sessions Connected'(psn,scnt))
        
        # 시작시그널이 올때까지 대기
        while True:
            if sig.value == 1:
                break
            elif sig.value == 0:
                time.sleep(1)
            else:
                return -1
            
        clirpt = repeater(clients)
        # 명령어 수행부
        while True:
            if runcmd(runner, next(clirpt), next(cmdrpt)) != 0:
                result['failcnt'] += 1

            #테스트 종료 기준 (시간, 횟수)
            if conf.criteria == 'time':
                if (time.time() - result['stime']) >= conf.test_time:
                    break
            else:
                if result['cmdcnt'] >= conf.repeat_count:
                    break
            #딜레이
            time.sleep(conf.cmd_delay)
        for client in clients:
            client.close()
    else:
        svrrpt = repeater(conf.targetset)
        while True:
            # 접속
            svr = next(svrrpt)
            client = connect(term, conf, svr)
            if client != -1:
                result['sescnt'] += 1
            else:
                result['result'] = -1
                rq.put(result)
                print(str(result), 'error')
                exit(-1)
            runner.waitrecv(client)
            
            # 명령어 수행
            if runcmd(runner, next(client), next(cmdrpt)) != 0:
                result['failcnt'] += 1
            
            #테스트 종료 기준 (시간, 횟수)
            if conf.criteria == 'time':
                if (time.time() - result['stime']) >= conf.test_time:
                    client.close()
                    break
            else:
                if result['cmdcnt'] >= conf.repeat_count:
                    client.close()
                    break
            time.sleep(conf.cmd_delay)
    result['ftime'] = time.time()
    rq.put(result)

def ftp_test(conf, ds, psn, sig = None, rq = None):    
    term = TermCtrl()
    if conf.test_type in ['ftp', 'sftp']:
        ftrun = FTRunner()
    else:
        print('Wrong Test Type')
        return -1
    
    filerpt = repeater(conf.dataset)
    result = {
        'sescnt':0,
        'cmdcnt':0,
        'failcnt':0,
        'stime':time.time(),
        'ftime':0
    }
    if conf.persist_session == 'true':
        #접속
        connect(term, conf, svr)
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
            hash = None
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
            time.sleep(cmd_delay)
        client.close()        
        #딜레이
    else:
        while True:
            temp = term.connect(svr[1], svr[2], svr[3], svr[4], svr[5],
                                ifc = bind_interface)
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
            if conf.criteria == 'time':
                if (time.time() - stime) >= conf.test_time:
                    client.close()
                    break
            else:
                if result['cmdcnt'] >= conf.repeat_count:
                    client.close()
                    break
            #딜레이
            time.sleep(conf.cmd_delay)
            client.close()
    result['ftime'] = time.time()
    q.put(result)

def cmd_measure(slist, rq):
    pass            
            
if __name__ == '__main__':
    # 테스트 준비
    conf, dslist = prepare()
    
    # 테스트 실행
    result = run_test(conf, dslist)
    
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
