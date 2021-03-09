#!/usr/bin/python3
import time
import copy
import random
import multiprocessing as mp
from termctrl import *
from dbctrl import *
from commonlib import *

CONF_FILE = 'conf/term_tester.conf'

class ConfSet:
    def __init__(self, configfile):
        STR_TRUE = 'true'
        conf = get_file_conf(configfile)
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
        self.use_nat_identity = conf['DBSAFER']['use_nat_identity'].lower() == STR_TRUE
        self.dbsafer_cert_id_csv = conf['DBSAFER']['dbsafer_cert_id_csv']
        self.dbsafer_gw = conf['DBSAFER']['dbsafer_gw']
        self.dbsafer_log = conf['DBSAFER']['dbsafer_log']
        tmp = conf['DBSAFER']['dynamic_port']
        if -1 < tmp.find('~'):
            self.dynamic_port = list(range(int(tmp.split('~')[0]), int(tmp.split('~')[1])))
        else:
            self.dynamic_port = [int(tmp)]
        self.dbsafer_dbid = conf['DBSAFER']['dbsafer_dbid']
        self.dbsafer_dbpw = conf['DBSAFER']['dbsafer_dbpw']
        self.chk_svcnum = conf['DBSAFER']['chk_svcnum'].lower() == STR_TRUE 
        self.server_list_csv = conf['Input']['server_list_csv']
        self.persist_session = conf['Common']['persist_session'].lower() == STR_TRUE
        self.start_after_deploy = conf['Common']['start_after_deploy'].lower() == STR_TRUE
        self.measure = conf['Common']['measure'].lower() == STR_TRUE
        self.measure_delay = int(conf['Common']['measure_delay'])
        self.proc_count = int(conf['Common']['proc_count'])
        self.proc_delay = float(conf['Common']['proc_delay'])
        self.session_count = int(conf['Common']['session_count'])
        self.criteria = conf['Common']['criteria'].lower()
        self.test_time = int(conf['Common']['test_time'])
        self.repeat_count = int(conf['Common']['repeat_count'])
        self.session_delay = float(conf['Common']['session_delay'])
        self.cmd_delay = float(conf['Common']['cmd_delay'])
        self.connect_timeout = int(conf['Common']['connect_timeout'])       
        self.bind_interface = conf['Common']['bind_interface'].lower()
        self.cmd_list_csv = conf['Input']['cmd_list_csv']
        self.files_list_csv = conf['Input']['files_list_csv']
        self.ssh_auth_type = conf['SSHConfig']['ssh_auth_type'].lower() == STR_TRUE
        self.ssh_key_file = conf['SSHConfig']['ssh_key_file']
        self.ssh_invoke_sh = conf['SSHConfig']['ssh_invoke_sh'].lower() == STR_TRUE
        del conf

class DataSet:
    '''
    Data Set for CMD(Command)/FT(File Transfer) test
    CMD Set Cols : Command / Expected Result / Delay Time(sec)
    FT Set Cols: Filename / Source Path / Remote Path / Local Path
            File hash / Delay time(sec)
    '''
    dataset = []

    def __init__(self, dataset):
        self.dataset = dataset
        del dataset

class ServerSet:
    '''
    Server list set for Test
    Cols : Server name / Protocol Type / IP Address / Port
    / UserID / Password / DBSAFER Service Number
    '''
    svr_list = []
    sess_cnt = 0  

    def __init__(self, server_list, sess_cnt):
        self.svr_list = server_list
        self.sess_cnt = sess_cnt
        del server_list
        del sess_cnt

class Result:
    psn = None
    svrcnt = 0
    totses = 0
    sesok = 0
    sesfail = 0
    totcmd = 0
    cmdok = 0
    cmdfail = 0
    stime = 0
    ftime = 0
   
def chk_config(conf):
    # NIY(Not Implemented Yet)
    # 설정내용이 올바른지 확인
    pass

def prepare():
    """
    테스트 준비 과정
    Returns : conf, avail_svrlist, svr_set_list ,DataSet(dataset), cert_id_list
    """
    avail_svrlist = [] 
    conf = ConfSet(CONF_FILE)

    # 세션 개수가 0일경우 65535로 세션개수 변경
    if 0 == conf.session_count:
        conf.session_count = 65535

    # 대상서버 목록 가져오기
    server_list = get_server_list_csv(conf.server_list_csv)
    if server_list == -1 or len(server_list) < 1:
        print('Error : get_server_list_csv()',server_list, conf.server_list_csv)
        return -1

    # 사용자 식별 사용여부에 따라 DBSAFER서버리스트 가져오기
    if True == conf.use_nat_identity:
        avail_svrlist, cert_id_list = set_nat_identity(conf, server_list)
    else:
        # 파일 서버 목록에서 서비스 테스트 타입과 동일한 서비스 타입의 서비스만 추림
        for sl in server_list:
            if sl[1].lower() == conf.svc_type:
                avail_svrlist.append(sl)
        cert_id_list = None

    # 프로세스별 서버리스트 및 세션개수 정리
    totses = len(avail_svrlist) * conf.session_count
    svrcnt = len(avail_svrlist)

    # 서버개수 * 세션개수보다 프로세스 개수가 클 경우
    if conf.proc_count > svrcnt:
        # 프로세스 개수 줄임
        if conf.proc_count > totses:
            conf.proc_count = totses
        # 세션을 서버 단위로 나눔
        avail_svrlist *= int(conf.proc_count / svrcnt)
        avail_svrlist += avail_svrlist[0:int(conf.proc_count % svrcnt)]
        # 서버단위 세션 개수를 프로세스에 나누어 담았다면
        sflag = True
    else:
        sflag = False

    svr_set_list = [ServerSet([],0) for i in range(conf.proc_count)]
    cntrt = rotator(range(conf.proc_count))
    
    for svr in avail_svrlist:
        svr_set_list[next(cntrt)].svr_list.append(svr)

    # 프로세스별 세션 개수 입력
    for i in range(conf.proc_count):
        if sflag:
            svr_set_list[i].sess_cnt = int(totses / conf.proc_count)
            if i < int(totses % conf.proc_count):
                svr_set_list[i].sess_cnt += int(totses / conf.proc_count)
        else:
            svr_set_list[i].sess_cnt = conf.session_count * len(svr_set_list[i].svr_list)

    # 명령어와 예상결과값 또는 파일명 및 파일 해쉬값 같은 테스트 필요 데이터세트 설정
    dataset = []
    if conf.test_type in ('ssh', 'telnet'):
        cmdlist = get_list_from_csv(conf.cmd_list_csv)
    else:
        cmdlist = get_list_from_csv(conf.files_list_csv)
    
    # 샵 주석 제거된 리스트
    dataset = del_comment(cmdlist)
    
    return conf, avail_svrlist, svr_set_list ,DataSet(dataset), cert_id_list

def set_nat_identity(conf, server_list):
    '''
    사용자 식별 기능을 사용하기 위한 프로시저
    prepare() 과정에서 사용되며 서버 리스트와 보안계정 목록을 리턴함
    '''
    SSH_CODE = 4
    SFTP_CODE = 22
    MYSQL_PORT = 3306
    avail_svrlist = []
    # Cert ID 목록 가져오기
    cert_id_list = get_list_from_csv(conf.dbsafer_cert_id_csv)
    
    if 'ssh' == conf.test_type:
        test_type = SSH_CODE
    elif 'sftp' == conf.test_type:
        test_type = SFTP_CODE
    else:
        test_type = -1
        return -1

    dbc = DBCtrl()
    dbc.connect(host = conf.dbsafer_log,
                port = MYSQL_PORT,
                user = conf.dbsafer_dbid,
                passwd = conf.dbsafer_dbpw,
                db='dbsafer3')
    
    if conf.chk_svcnum:
        svc_sel_qry = 'select no from \
                   dbsafer3.services where type=\"%s\"\
                   and destip=\"%s\" and destport=\"%s\"'

        print("Waiting for getting service number from the DBSAFER")

        for sl in server_list:
            dbc.cur.execute(svc_sel_qry%(test_type, sl[2], sl[3]))
            for dbsvc in dbc.cur.fetchall():
                #서버리스트 마지막 컬럼에 서비스 번호 입력
                sl[6] = dbsvc[0]
                avail_svrlist.append(sl)
        
        # server_list.csv파일에 서비스번호 추가
        lines = get_server_list_csv(conf.server_list_csv)
        f = open(conf.server_list_csv + '.withDBSSVCNUM','w')
        for line in lines:
            chk_flag = False
            for sl in avail_svrlist:
                if sl[2] == line[2] and \
                sl[3] == line[3] and \
                sl[1] == line[1]:
                    print("DEBUG : ",sl)
                    try:
                        f.write(str(sl).strip("[]\'").replace('\'', '').replace(' ','') + '\n')
                    except Exception as e:
                        print(e,sl)
                    chk_flag = True
                    break
            if False == chk_flag:
                f.write(str(line).strip("[]\'").replace('\'', '').replace(' ','') + '\n')
        f.close()
    else:
        for sl in server_list:

            avail_svrlist.append(sl)
        pass

    
    # dbsafer_ldap_list의 보안계정들에 대한 login 전부 1로 변경쿼리
    login_updt_qry = 'update dbsafer3.dbsafer_ldap_list '
    login_updt_qry += 'set login=1 where sno=\"%s\"'
    ldapip_updt_qry = 'update dbsafer3.dbsafer_ldap_list '
    ldapip_updt_qry += 'set ipaddr=\"%s\" where sno=\"%s\"'
    
    # oms_access에 해당 IP가 없을때 Insert할 쿼리
    oms_sel_qry = 'select ip, unikey from dbsafer3.oms_access'
    oms_ins_qry = 'insert into dbsafer3.oms_access'
    oms_ins_qry += '(ip,mac_addr,env_ip,lan_count,nat_version,'
    oms_ins_qry += 'computer_name,cpu_info,mem_info,sno,login,'
    oms_ins_qry += 'gw_ip,login_access,unikey) values('
    oms_ins_qry += ('\"%s\",'*12) + '\"%s\")'
    dummymac = '00:00:00:00:00:00'
    dummyipv6 = '0000::0000:0000:0000:0000%64,'
    nowt = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))
    hash = get_hash('TrollkingTester')
    omsiplist = []
    
    # oms_access 테이블 select 쿼리
    dbc.cur.execute(oms_sel_qry)
    
    for line in dbc.cur.fetchall():
        omsiplist.append(list(line))
        
    for cert_id in cert_id_list:
        add_oms_flag = True
        
        # dbsafer_ldap_list의 로그인 컬럼 업데이트
        dbc.cur.execute(login_updt_qry%cert_id[0])
        
        # dbsafer_ldap_list의 ipaddr 컬럼 업데이트
        dbc.cur.execute(ldapip_updt_qry%(cert_id[1],cert_id[0]))
        
        for line in omsiplist:
            # line : oms_access ip, unikey list 
            if line[0] == cert_id[1] and line[1] == hash:
                add_oms_flag = False
                break
            else:
                add_oms_flag = True
        
        # oms_access에 레코드 추가하기
        if add_oms_flag == True:
            values = (cert_id[1], dummymac, dummyipv6+cert_id[1], 1,
                    '9.9.99.9T', 'TrollkingsTester',
                    'AMD rather than Intel!', '8192GB',cert_id[0],
                    1, conf.dbsafer_gw, nowt, hash)
            dbc.cur.execute(oms_ins_qry%values)
            
    dbc.db.commit()
    
    return avail_svrlist, cert_id_list

def connect(term, conf, svr, use_nat_id=False, cert_id=None, dyport=None):
    '''
    테스트 수행에서 서비스에 접속하는 프로시저
    '''
    if True == use_nat_id and cert_id != None and dyport != None:
        natidpkt = NATIDPKT()
        natidpkt.set(svcnum = svr[6],
                    tgip = svr[2],
                    tgport = int(svr[3]),
                    cert_id = cert_id[0],
                    gwip = conf.dbsafer_gw,
                    gwport = dyport,
                    loip = cert_id[1]
                    )
        
        temp = term.connect(svr[1], conf.dbsafer_gw, dyport, 
                            svr[4],svr[5], ifc = conf.bind_interface,
                            usenatid = True, natidpkt = natidpkt)
    else:
        temp = term.connect(svr[1], svr[2], svr[3], svr[4], svr[5],
                            ifc = conf.bind_interface,
                            usenatid = False,
                            natidpkt = None)
    
    ret = dist_client(temp, conf)
    
    return ret
    
def runcmd(runner, client, cmdlines):
    '''
    테스트 수행에서 명령어 수행 프로시저
    '''
    result = [0,0]
    for cmdline in cmdlines:
        if len(cmdline) < 2:
            ret = runner.runcmd(client, cmdline[0], '')
        else:
            ret = runner.runcmd(client, cmdline[0], cmdline[1])
        # 결과 검증
        c1 = int == type(ret)
        c2 = tuple == type(ret)
        c3 = True == c2 and ret[0] 
        c4 = False == c2 and ret[0] 
        if c1 or c4:
            result[1] += 1
        else:
            result[0] += 1
    return result

def runft(runner, client, dataset, sessid=''):
    '''
    테스트 수행에서 파일전송 프로시저
    '''
    result = [0,0]
    FNAME = 0; SRCPATH = 1; RMTPATH = 2; LOCPATH = 3; HASH = 4
    for row in dataset:
        upload = row[SRCPATH] + os.sep + row[FNAME]
        remote = row[RMTPATH] + os.sep + row[FNAME] + '-' + sessid
        download = row[LOCPATH] + os.sep + row[FNAME] + '-' + sessid
        putret = runner.putfile(client, upload, remote)
        getret = runner.getfile(client, remote, download)

        #결과 검증1
        r1 = False
        r2 = False
        c1 = -1 < putret and -1 < getret
        if c1:
            r1 = True
        
        #결과 검증2
        hash = None
        try:
            hash = get_file_hash(download)
        except Exception as e:
            print(e)
        
        if hash == row[HASH]:
            r2 = True
       
        if True == r1 and True == r2:
            result[0] += 2
        else:
            result[1] += 2

    return result
    
def measure_session(svr_list, dataset, signal):
    '''
    테스트 중간에 세션을 생성하고 명령어/파일 전송 시간을 측정
    '''
    EXPIRE_CNT = 300
    GET_QUEUE_TIMEOUT = 5
    # 측정 여부 확인해서 주기적으로 성능 측정
    tq = mp.Queue()
    tconf = ConfSet(CONF_FILE)
    tconf.persist_session = True
    tconf.proc_count = 1
    tconf.session_count = 1
    tconf.criteria = 'count'
    tconf.repeat_count = len(dataset.dataset)
    tconf.session_delay = 0
    tconf.cmd_delay = 0
    timeoutcnt = 0
    
    while True:
        if 2 == signal.value :
            break
        tprocs = []
        tresult = []
        for i,sl in enumerate(svr_list):
            tresult.append([sl[0],sl[1],str(sl[2]+':'+sl[3]), 0])
            svr_set = ServerSet([sl], 1)
            proc = mp.Process(target=tester, 
                            args=(tconf, svr_set, dataset, i, signal, tq))
            proc.start()
            tprocs.append(proc)

        for proc in tprocs:
            proc.join()

        while False == tq.empty():
            tmp = tq.get(block=False, timeout=GET_QUEUE_TIMEOUT)
            if dict == type(tmp):
                tresult[int(tmp['psn'])][3] = float(tmp['ftime']) - float(tmp['stime'])
                timeoutcnt = 0
        
        for tr in tresult:
            print(tr)
        print('\n')
        time.sleep(tconf.measure_delay)
        
        timeoutcnt += 1
        if timeoutcnt >= EXPIRE_CNT:
            break

def dist_client(client, conf):
    '''
    [To do] dist_client와 ftpcli와 합쳐서 구현 어짜피 동일한 내용이므로...
    '''
    if int == type(client):
        return -1

    if fl.FTP == type(client) and 'ftp' == conf.test_type:
        return client

    if tl.Telnet == type(client) and 'telnet' == conf.test_type:
        return client
    
    if type(client) == tuple and 2 == len(client):
        c1 = type(client[0]) == pm.client.SSHClient
        c2 = type(client[1]) == pm.channel.Channel
        c3 = type(client[1]) == pm.SFTPClient
        c4 = 'ssh' == conf.test_type
        c5 = 'sftp' == conf.test_type
        if c1 and c4 and conf.ssh_invoke_sh == False:
            return client[0]
        if c2 and c4 and conf.ssh_invoke_sh == True:
            return client[1]
        if c3 and c5:
            return client[1]
    return -1

def show_basic_conf(conf, svr_set_list, dataset):
    '''
    기본 설정을 출력함
    '''
    scnt = 0
    row2 = '\n'+'{0:^25}'.format('[ Test Processes ]') + '\n\n'
    header = '{0:<15}'.format('Server Name')
    header += '{0:^8}'.format('SVC')
    header += '{0:^20}'.format('IP Address:Port')
    for i, ss in enumerate(svr_set_list):
        row2 += 'Test Process #%s ( %s Sessions )\n'%(i,ss.sess_cnt)
        row2 += header + '\n'
        for sl in ss.svr_list:
            scnt += 1 
            row = '{0:^15}'.format(sl[0])
            row += '{0:^8}'.format(sl[1])
            row += '{0:^20}'.format(sl[2]+':'+sl[3])
            row2 += row + '\n'
        row2 += '\n'
    row1 = '\n' + '{0:^30}'.format('[Test Configuration]') + '\n\n'
    for mv in dir(conf):
        if mv.startswith('_') == False:
            row1 += mv.upper() + ' : ' + str(eval('conf.%s'%mv)) + '\n'
    row1 += 'Process Count : %s \n'%conf.proc_count
    row1 += 'Server Count : %s \n'%scnt
    row1 += 'Total Session Count (Will be Created) : %s \n'%(scnt*conf.session_count)
    print(row1)
    print(row2)

def show_result(result):
    '''
    테스트 결과를 출력함
    '''
    totsvr = 0
    totses = 0
    totsesok = 0
    totsesfail = 0
    totcmd = 0
    totcmdok = 0
    totcmdfail = 0
    stime = result[1][0]
    ftime = result[1][1]

    print('\n\n[ Processes Result ]\n')
    header = '{0:^5}'.format('PSN')
    header += '{0:^5}'.format('SVR')
    header += '{0:^5}'.format('CMD')
    header += '{0:^6}'.format('Fail')
    header += '{0:^10}'.format('STime')
    header += '{0:^10}'.format('FTime')
    header += '{0:^10}'.format('Runtime')
    header += '{0:^10}'.format('TPS')
    print(header)

    for line in result[0]:
        totsvr += int(line.svrcnt)
        totses += int(line.totses)
        totsesok += int(line.sesok)
        totsesfail += int(line.sesfail)
        totcmd += int(line.totcmd)
        totcmdok += int(line.cmdok)
        totcmdfail += int(line.cmdfail)
        tmp = '{0:^5}'.format(line.psn)
        tmp += '{0:^5}'.format(line.svrcnt)
        tmp += '{0:^5}'.format(line.cmdok)
        tmp += '{0:^6}'.format(line.cmdfail)
        tmp += '{0:^10}'.format(time.strftime('%X',time.localtime(line.stime)))
        tmp += '{0:^10}'.format(time.strftime('%X',time.localtime(line.ftime)))
        tmp += '{0:^10.2f}'.format(line.ftime - line.stime)
        tmp += '{0:^10.2f}'.format(line.cmdok/(line.ftime-line.stime))
        print(tmp)
            
    row = '\n\n[ Total Result ]\n\n'
    row += "Total Sesssions : %s\n"%totses
    row += "Total Success Session Count : %s\n"%totsesok
    row += "Total Failure Session Count : %s\n"%totsesfail
    row += "Total Command Count : %s\n"%totcmd
    row += "Total Success Command Count : %s\n"%totcmdok
    row += "Total Failure Command Count : %s\n"%totcmdfail
    try:
        row += 'Total Sesssion Success Rate : %.2f%%\n'%((totsesok/totses)*100)
    except Exception as e:
        row += 'Total Session Success Rate : 0%\n'
    try:
        row += 'Total Command Success Rate : %.2f%%\n'%((totcmdok/totcmd)*100)
    except Exception as e:
        row += 'Total Success Rate : 0%\n'    
    row += 'Start Time : %s\n'%time.strftime('%Y-%m-%d %H:%M:%S', 
                                              time.localtime(stime))
    row += 'Finish Time : %s\n'%time.strftime('%Y-%m-%d %H:%M:%S', 
                                              time.localtime(ftime))
    row += 'Running Time : %.2fS\n'%(ftime - stime)
    print(row)

def run_test(conf, svr_list, svr_set_list, dataset, cert_id_list=None):
    # 기본 설정 출력 부분
    show_basic_conf(conf, svr_set_list, dataset)
    procs = []
    result = []
    # 부모 -> 자식 시그널용 공유메모리 
    # 0: 초기 정지 상태, 1: 시작, 2:종료
    signal = mp.Value('d',0)
    # 자식 -> 부모 결과 전달용 큐
    rq = mp.Queue()
    stime = time.time()
    tmpconf = copy.deepcopy(conf)
    dyport_rotator = rotator(conf.dynamic_port)
    for psn, sl in enumerate(svr_set_list):
        tmpconf.dynamic_port = [next(dyport_rotator)]
        proc = mp.Process(target=tester, 
                          args=(tmpconf, sl, dataset, psn, signal, rq, cert_id_list))
        procs.append(proc)
        proc.start()
        time.sleep(conf.proc_delay)
    
    # 세션 접속 기다리기
    conndone = 0
    timer = 0
    while conndone < conf.proc_count:
        while rq.empty() == False:
            timer = time.time()
            buf = rq.get(block=False, timeout=5)
            if type(buf) == tuple:
                if 'CD' == buf[1]:
                    print('Proc #%s : %s Sessions Connected'%(buf[0],buf[2]))
                    conndone +=1
        curtime = time.time()
        if (curtime - timer) > 30 and timer != 0:
            break

    if True == conf.start_after_deploy:
        input('\n\n###### Press any key for starting... ######')
    signal.value = 1

    #중간에 세션 명령어 소요시간 측정
    if True == conf.measure:
        proc = mp.Process(target=measure_session,
                          args=(random.choice(svr_list), 
                          dataset, signal))
        proc.start()
        procs.append(proc)
    
    # 자식프로세스로부터 결과값 받아오기
    while len(result) < conf.proc_count:
        while rq.empty() == False:
            buf = rq.get(block=False, timeout=5)
            if Result == type(buf):
                result.append(buf)
    
    signal.value = 2
    for proc in procs:
        proc.join()
    ftime = time.time()
    return result, (stime, ftime)

def tester(conf, svr_set, dataset, psn, signal = None, rq = None, cert_id_list=None):
    '''
    테스트 프로세스 구현부
    '''
    if len(svr_set.svr_list) == 0:
        print('Server set not exist')
        return 0
    term = TermCtrl()
    if conf.test_type in ['telnet', 'ssh']:
        runner = CMDRunner()
    elif conf.test_type in ['ftp', 'sftp']:
        runner = FTRunner()
    else:
        print('Wrong Test Type')
        return -1

    r = Result()
    r.psn = psn
    r.svrcnt = len(svr_set.svr_list)
    clients = []
    if True == conf.use_nat_identity and cert_id_list != None:
        cert_id_rotator = rotator(cert_id_list)
        dyport_rotator = rotator(conf.dynamic_port)

    #세션 지속하고 명령어만 반복
    r.stime = time.time()
    if True == conf.persist_session:
        # 접속
        print("Proc #%s : Start Connecting"%(psn))
        for sc in range(int(svr_set.sess_cnt/len(svr_set.svr_list))):
            for svr in svr_set.svr_list:
                if True == conf.use_nat_identity and cert_id_list != None:
                    cert_id = next(cert_id_rotator)
                    dyport = next(dyport_rotator)
                else:
                    cert_id = None
                    dyport = None
                client = connect(term, conf, svr, 
                                 use_nat_id = conf.use_nat_identity,
                                 cert_id = cert_id,
                                 dyport = dyport)
                r.totses += 1
                if client != -1:
                    r.sesok += 1
                else:
                    r.sesfail += 1
                    continue
                time.sleep(conf.session_delay)
                c1 = 'telnet' == conf.test_type
                c2 = 'ssh' == conf.test_type
                c3 = True == conf.ssh_invoke_sh 
                if c1 or (c2 and c3) :
                    runner.waitrecv(client)
                clients.append(client)
                time.sleep(conf.session_delay)
        rq.put((psn,'CD',len(clients)))

        # 시작시그널이 올때까지 대기
        print("Proc #%s : Waiting for Start signal"%psn)
        while True:
            if 0 == signal.value:
                time.sleep(0.5)
            elif 1 == signal.value:
                break
            elif 2 == signal.value:
                return 0
            else:
                return -1
        
        print("Proc #%s : CMD/FT Start"%psn)
        # 명령어/파일전송 수행부
        while True:
            for i, client in enumerate(clients):
                if conf.test_type in ['telnet', 'ssh']:
                    ret = runcmd(runner, client, dataset.dataset)
                elif conf.test_type in ['ftp', 'sftp']:
                    ret = runft(runner, client, dataset.dataset, sessid=str(psn)+str(i))
                else:
                    pass
                r.cmdok += ret[0]
                r.cmdfail += ret[1]
                r.totcmd += ret[0] + ret[1]
                
            #테스트 종료 기준 (시간, 횟수)
            if 'time' == conf.criteria:
                if (time.time() - r.stime) >= conf.test_time:
                    break
            else:
                if int(r.totcmd/len(dataset.dataset)) >= (conf.repeat_count * len(clients)):
                    break
            #딜레이
            time.sleep(conf.cmd_delay)
        for client in clients:
            client.close()
    else:
        svrrt = rotator(svr_set.svr_list)
        while True:
            # 접속
            svr = next(svrrt)
            if True == conf.use_nat_identity and cert_id_list != None:
                cert_id = next(cert_id_rotator)
            else:
                cert_id = None
            client = connect(term, conf, svr, 
                             use_nat_id = conf.use_nat_identity,
                             cert_id = cert_id)
            r.totses += 1
            if client != -1:
                r.sesok += 1
            else:
                r.sesfail += 1
                continue
            runner.waitrecv(client)
            
            # 명령어/파일 전송 수행
            if conf.test_type in ['telnet', 'ssh']:
                ret = runcmd(runner, client, dataset.dataset)
            elif conf.test_type in ['ftp', 'sftp']:
                ret = runft(runner, client, dataset.dataset, sessid=str(psn))
            else:
                pass
            r.cmdok += ret[0]
            r.cmdfail += ret[1]
            r.totcmd += ret[0] + ret[1]
            
            #테스트 종료 기준 (시간, 횟수)
            if 'time' == conf.criteria:
                if (time.time() - r.stime) >= conf.test_time:
                    break
            else:
                if int(r.totcmd/len(dataset.dataset)) >= (conf.repeat_count * len(clients)):
                    break
            time.sleep(conf.cmd_delay)
            client.close()
    r.ftime = time.time()
    rq.put(r)


if __name__ == '__main__':
    # 테스트 준비
    conf, svr_list, svr_set_list, dataset, cert_id_list = prepare()
    
    # 테스트 실행
    result = run_test(conf, svr_list, svr_set_list, dataset, cert_id_list)

    # 결과 출력
    show_result(result)