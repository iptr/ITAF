#!/usr/bin/python
from termctrl import *
from commonlib import *

CONF_FILE = 'conf/term_tester.conf'

def chk_config(conf):
    # 설정내용이 올바른지 확인
    pass

def run_test(client, conf):
    test_type = conf['Common']['test_type'].lower()
    if test_type == 'telnet':
        pass
    elif test_type == 'ssh':
        pass
    elif test_type == 'ftpup':
        pass
    elif test_type == 'ftpdown':
        pass
    elif test_type == 'sftpup':
        pass
    elif test_type == 'sftpdown':
        pass
    else:
        pass

def telnet_test(client, conf):
    print('telnet')
    pass

def ftp_test(client, conf):
    print('ftp')
    pass

def ftpup_test(client, conf):
    print('ftpup')
    pass

def ftpdown_test(client, conf):
    print('ftpdown')
    pass

def ssh_test(client, conf):
    print('ssh')
    pass

def sftpup_test(client, conf):
    print('sftpup')
    pass

def sftpdown_test(client, conf):
    print('sftpdown')
    pass
    

if __name__ == '__main__':
    #설정파일 읽기
    conf = getfileconf(CONF_FILE)
    slist = getsvrlistcsv(conf['Common']['server_list_csv'])
    
    #설정 내용 체크
    chk_config(conf)
    
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
        exit(-1)
    
    # 서버 리스트 가져와서 서비스에 맞는 서비스만 저장하고 세션 접속
    term = TermCtrl()
    for line in slist:
        if line[1].lower() == svc_type:
            term.connect(line[1], line[2], line[3],
                         line[4], line[5], line[0])

    print(term.cinf)
    
    # 서비스에 맞는 테스트 실행
    test_func = {
        'telnet':telnet_test,
        'ftpup':ftpup_test,
        'ftpdown':ftpdown_test,
        'ssh':ssh_test,
        'sftpup':sftpup_test,
        'sftpdown':sftpdown_test
    }
    ret = test_func[test_type](slist, conf)
    
    # 결과 정리 및 출력
    
