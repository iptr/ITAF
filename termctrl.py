import os
import time
import re
import csv
import telnetlib as tl
import ftplib as fl
import paramiko as pm
import pandas as pd
import multiprocessing as mp

from taiflogger import *
from dbctrl import *
from commonlib import *

CONF_PATH = 'conf/taif.conf'


class TermCtrl:
    """
    Telnet,FTP, SSH프로토콜을 사용하여 대상서버에서 작업하는 클래스
    대상서버 접속정보는 DB 또는 File에서 가져올 수 있다.

    Attr:
    cinf(DataFrame) : 대상서버 접속정보 및 client 객체
            name, svc_type(telnet, ftp, ssh), ip, port, userid, password
    lgr (Logger) : 로깅을 위한 인스턴스
    """
    
    cinf = None
    lgr = None

    def __init__(self):
        '''
        Configuration import priority : DB -> File
        '''
        self.lgr = Logger().getlogger("TermCtrl")
        self.configure()

    # GetConf함수로 바꾸고 어디에서 어떤 내용의 설정들을 
    # 가져올지 파라매터를 받아서 수행하도록하는게 좋을듯
    def configure(self):
        # 기본 설정 불러오기
        try:
            jf = open(CONF_PATH)
            conf = json.load(jf)
            jf.close()
        except Exception as e:
            self.lgr.error(e)
            raise e
        # 데이터 프레임 생성
        columns = conf['CFGDB']['TSVR_TBL']['COLS']
        self.cinf = pd.DataFrame()
        for col in columns:
            self.cinf[col] = []
        self.cinf['client'] = []

        # 설정을 DB에서 가져오기일 경우
        if conf['CFGLTYPE'].lower() == 'db':
            dbc = DBCtrl()
            if dbc.connect() != -1:
                coninfo = dbc.select(conf['CFGDB']['DB'],
                                     conf['CFGDB']['TSVR_TBL']['NAME'],
                                     cols=columns)
                dbc.close()
                for i, row in enumerate(coninfo):
                    temp = {}
                    for j, col in enumerate(columns):
                        temp[col] = row[j]
                    self.cinf.loc[i] = temp
            else:
                self.lgr.error("DB connection error")
                return -1
        # 설정을 File에서 가져오기일 경우
        elif conf['CFGTYPE'].lower() == 'FILE':
            f = open(conf['SERVER_LIST_PATH'])
            slist = csv.reader(f)
            f.close()
            for row in slist:
                if len(row) != len(columns) :
                    continue
                if row[1].upper() not in ['SSH','TEL','FTP']:
                    continue
                if not chk_valip(row[2]):
                    continue
                if not chk_intsize(row[3],1,65534):
                    continue
                self.cinf.append(pd.Series(row, index=self.cinf.columns)
                                ,ignore_index=True)
        #설정이 잘못되었을 경우
        else:
            self.lgr.error("Wrong \"%s\" in %s"%CONF_PATH)
            return -1
        self.cinf = self.cinf.astype({'port': int})
    
    def add_server_list(self, name, proto, host, port, userid, passwd,
                        client=None):
        self.cinf['name'].append(name)
        self.cinf['svc_type'].append(proto)
        self.cinf['host'].append(host)
        self.cinf['port'].append(int(port))
        self.cinf['userid'].append(userid)
        self.cinf['passwd'].append(passwd)
        self.cinf['client'].append(client)
           
    def connect(self, proto, host, port, user, passwd, sname=None,
                timeout=5):
        """ SSH, Telnet, FTP 접속 후 서버리스트(cinf)에 추가하고
            해당 접속 객체를 리턴함

        Args:
            proto (str): Protocol 'SSH','Tel','FTP'
            host (str): host ip
            port (int or str): port
            user (str): user id
            passwd (str): passwd

        Returns:
            client(obj) : connected session object
        """
        # 이름을 입력받지 못할 경우
        if sname == None:
            sname = proto + '_' + host + ':' + port
        
        # 기존 cinf에 해당 서버 및 포트가 있는 경우 그냥 접속만 해야되는데...
        exist_index = None
        for i in range(len(self.cinf)):
            if self.cinf['host'] == host and self.cinf['port'] == port:
                exist_index = i
        
        proto = proto.lower()
        client = None
        if proto in ('telnet','tel'):
            client = tl.Telnet()
            try:
                client.open(host, int(port), int(timeout))
                client.read_until('Username:')
                client.write(user + '\n')
                client.read_until('Password:')
                client.write(passwd + '\n')
            except Exception as e:
                self.lgr.error(e)
                client = None
        elif proto == 'ftp':
            client = fl.FTP()
            try:
                client = client.connect(host, int(port), int(timeout))
                client.login(user, passwd)
            except Exception as e:
                self.lgr.error(e)
                client = None
        elif proto == 'ssh' or proto == 'sftp':
            client = pm.SSHClient()
            client.set_missing_host_key_policy(pm.AutoAddPolicy())
            try:
                client.connect(host, port=int(port), username=user,
                               password=passwd, timeout=int(timeout))
            except Exception as e:
                self.lgr.error(e)
                client = None
        else:
            self.lgr.error('Wrong protocol : %s' % proto)
            return -1
        if exist_index == None:
            self.add_server_list(sname, proto, host, port, user, passwd,
                                 client)
        else:
            self.cinf['client'][exist_index] = client

    def connectlist(self, cno = None):
        """ 
        cinf 서버 목록의 일부 또는 전체 서버에 접속을 시도하고 
        cinf에 접속 객체를 갱신함

        Args:
            cno(None,list,int): cinf의 index, 
                                None = 전체
                                list = 일부 ex. [1,4]
                                int = 특정 서버
        """
        ci = self.cinf
        if cno == None:
            cno = range(len(self.cinf.index))
        for rc in cno:
            print(rc)
            if ci['client'][rc] != None:
                continue
            else:
                ci['client'][rc] = self.connect(str(ci['host'][rc]), 
                                                int(ci['port'][rc]), 
                                                str(ci['userid'][rc]), 
                                                str(ci['passwd'][rc]))
                print(ci['client'][rc])

    def showclients(self):
        print(self.cinf)

    def runcmd(self, client, cmd):
        '''
        단일 명령어 실행. 
        :param client : paramko SSH Client object 
        :param cmd [str or list] : Command to run on the client
        :return: dictionary of stdin, stdout, stderr
        '''
        dict_ret = {'cmd': cmd, 'stdout': [], 'stderr': []}
        if type(client) == pm.client.SSHClient:
            pass
        elif int(client) < len(self.cinf['client']) > 0:
            client = self.cinf['client'][int(client)]
        else:
            self.lgr.error('there is no %s client' % client)
            return -1

        if type(cmd) == str:
            try:
                stdin, stdout, stderr = client.exec_command(cmd)
            except Exception as e:
                self.lgr.error(e)
                return -1
            dict_ret['stdout'].append(stdout.readlines())
            dict_ret['stderr'].append(stderr.readlines())
        elif type(cmd) == list:
            for line in enumerate(cmd):
                try:
                    stdin, stdout, stderr = client.exec_command(line)
                except Exception as e:
                    self.lgr.error(e)
                    dict_ret['stdout'].append(None)
                    dict_ret['stderr'].append(None)
                    continue
                dict_ret['stdout'].append(stdout.readlines())
                dict_ret['stderr'].append(stderr.readlines())
        else:
            self.lgr.error('wrong type cmd parameter')
            return -1
        return dict_ret

    def runonshell(self, client, cmdlines):
        """세션을 유지한 쉘에서 명령어를 수행함

        Args:
            client ([obj]): 접속 클라이언트
            cmdlines ([list]): 수행할 명령어 리스트

        Returns:
            [dict]: 명령어 및 수행된 결과값에 대한 딕셔너리
        """
        sh = client.invoke_shell()
        dict_ret = {'cmd': cmdlines, 'recv': []}
        for cmd in cmdlines:
            sh.send(cmd)
            buf = ''
            cnt = 0
            while True:
                if sh.recv_ready():
                    buf += sh.recv(4096).decode('ascii')
                else:
                    if buf == '':
                        cnt += 1
                        time.sleep(0.1)
                        if cnt > 10:
                            cnt = -1
                            break
                        else:
                            continue
                    else:
                        break
            if cnt == -1:
                dict_ret['recv'].append('')
            else:
                dict_ret['recv'].append(re.split('\n|\r', buf))
        sh.close()
        return dict_ret

    def isrmtfile(self, client, path):
        """대상서버에 path가 존재하는지 확인
        사용하지 말것

        Args:
            client ([type]): [description]
            path ([type]): [description]

        Returns:
            [type]: [description]
        """
        cmd = "if test -f %s;then echo \"file\";" % path
        cmd += "elif test -d %s;then echo \"directory\";fi" % path
        dict_ret = self.runcmd(client, cmd)
        if dict_ret['stdout'][0] == 'file':
            return 1
        elif dict_ret['stdout'][0] == 'directory':
            return 2
        else:
            return -1

    def getfileslist(self, path, client=None):
        '''
        path에 해당되는 디렉토리내 모든 파일 및 디렉토리 목록을 리턴한다.
        client를 입력받을 경우 원격지의 path에 대해서 수행한다.
        :param path: 디렉토리 경로
        :param client: ssh client object
        '''
        
        flist = []
        if client != None:
            cmd = "file `find %s`|grep -v directory" % path
            ret = self.runcmd(client, cmd)
            if len(ret['stdout'][0]) > 0:
                for line in ret['stdout'][0]:
                    flist.append(line.strip(':')[0])
        else:
            for dpath, dnames, fnames in os.walk(path):
                for fn in fnames:
                    flist.append(dpath + os.sep + fn)
        return flist

    def getlocalpath(self, path):
        '''
        path가 존재하는지 파일인지 디렉토리인지 확인하고 디렉토리일경우 디렉토리 하위의 모든 파일들을 리턴한다.
        path의 파일명에 와일드카드(*,?)가 존재할경우 다수의 파일목록을 리턴한다.
        '''
        flist = []
        dname = os.path.dirname(path)
        bname = os.path.basename(path)
        # Check whether the path is a directory
        if os.path.isdir(path):
            flist = self.getfileslist(path)
            return flist

        # whether path is a file
        if os.path.isfile(path):
            flist.append(path)
            return flist

        # check the path includes wild cards and get files as the pattern
        if re.search("\*|\?", bname) != None:
            if re.fullmatch('\*+', bname):
                patt = re.compile('\S*')
            elif re.fullmatch('\?+', bname) != None:
                patt = re.compile(bname.replace('?', '.'))
            else:
                patt = '^' + \
                    bname.replace('.', '\.').replace(
                        '?', '.').replace('*', '\S*') + '$'
                patt = re.compile(patt)

            try:
                dlist = os.listdir(dname)
            except:
                self.lgr.error("%s directory does Not exist")
                return flist

            for fn in dlist:
                if re.fullmatch(patt, fn) != None:
                    tmppath = dname + os.sep + fn
                    if os.path.isdir(tmppath):
                        flist += self.getfileslist(tmppath)
                    elif os.path.isfile(tmppath):
                        flist.append(tmppath)
                    else:
                        pass
            return flist
        return flist

    def put(self, client, srcpath, dstpath):
        '''
        ftp 또는 ssh 클라이언트를 통해 원본경로의 내용을 대상경로로 업로드한다.
        :client: ssh client object
        :srcpath: source path to upload
        :dstpath: target path to upload
        '''
        sftp = pm.SFTPClient.from_transport(client.get_transport())
        srcbase = os.path.basename(srcpath)
        srcfiles = self.getlocalpath(srcpath)

        # Check source path exists
        if srcfiles == []:
            self.lgr.error('param srcpath Not exists')
            return -1

        # Check destination path on target server exist
        # If directory does not exist, create directory
        isrmt = self.isrmtfile(client, dstpath)
        if self.isrmtfile(client, dstpath) != 2:
            sftp.mkdir(dstpath)

        for path in srcfiles:
            sftp.put(dstpath + os.sep + path.replace(srcbase, ''))
        sftp.close()

    def get(self, client, dstpath):
        # TODO(jycho) : implement get function
        # Create SFTPClient
        sftp = pm.SFTPClient.from_transport(client.get_transport())
        dstfiles = []
        # Check Dstpath

        # get directory or files
        pass

    def close(self, idx):
        client = self.cinf['client'][idx]
        if client != -1 or pd.isna(client) == False:
            try:
                client.close()
            except Exception as e:
                self.lgr.error(e)
                return -1
            self.cinf['client'][idx] == -1
        else:
            return 0


if __name__ == '__main__':
    pass
