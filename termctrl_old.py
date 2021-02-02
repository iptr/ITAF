import os
import time
import re
import telnetlib as tl
import ftplib as fl
import paramiko as pm
import pandas as pd

from taiflogger import *
from dbctrl import *
from commonlib import *

class TermCtrl:
    """
    Telnet,FTP, SSH프로토콜을 사용하여 대상서버에서 작업하는 클래스
    대상서버 접속정보는 DB 또는 File에서 가져올 수 있다.

    Attr:
    cinf(DataFrame) : 대상서버 접속정보 및 client 객체
            name, svc_type(telnet, ftp, ssh), ip, port, userid, password
    conf(dic) : 설정정보
    lgr (Logger) : 로깅을 위한 인스턴스
    """
    lgr = None
    conf = None
    cinf = None

    def __init__(self):
        self.lgr = Logger().getlogger("TermCtrl")
        self.configure()

    def configure(self):
        # 기본 설정 불러오기
        self.conf = getfileconf(CONF_PATH)
        conf = self.conf
        # 데이터 프레임 생성
        columns = conf['Tables']['server_list_cols'].split(',')
        self.cinf = pd.DataFrame()
        for col in columns:
            self.cinf[col.strip()] = []
        self.cinf['client'] = []
        
    def getserverlist(self):
        # 설정을 DB에서 가져오기일 경우
        conf = self.conf
        if conf['Common']['cfgtype'].lower() == 'db':
            result = getsvrlistdb()
            if result != -1:
                self.lgr.error('DB Connection failed')
            else:
                for row in result:
                    row.append('')
                    self.cinf.loc[len(self.cinf)] = row
            
        # 설정을 File에서 가져오기일 경우
        elif conf['Common']['cfgtype'].lower() == 'file':
            slist = getsvrlistcsv(conf['File']['server_list_file'])
            for row in slist:
                row.append('')
                self.cinf.loc[len(self.cinf)] = row
        #설정이 잘못되었을 경우
        else:
            self.lgr.error("\"%s\" in %s is Wrong Type"%(conf['Common']['cfgtype'],CONF_PATH))
            return -1
        self.cinf = self.cinf.astype({'port': int})

    def waitrecv(self, client, waitcount=3, decoding=False):
        """ Waiting for receiving the result of telnet command 

        Args:
            client (telnetlib.Telnet): telnet client object
            waitcount (int) : Seconds of waiting          
            decoding (bool) : whether make return data decoded or not
        Returns:
            received data (bytestring or str)
        """
        readcount=0
        preread=0
        readwait=0
        buf=b''
        # when SSH Client
        if type(client) == pm.channel.Channel:
            while True:
                if client.recv_ready():
                    buf += client.recv(65535)
                    readcount += 1
                else:
                    if preread < readcount :
                        preread = readcount
                        readwait = 0
                    else:
                        if readwait > waitcount:
                            break
                    readwait += 1
                    time.sleep(0.1)
            # when Telnet Client
        elif type(client) == tl.Telnet:
            while True:
                tmp = client.read_eager()
                if tmp != b'':
                    buf += tmp
                    readcount += 1
                else:
                    if preread < readcount :
                        preread = readcount
                        readwait = 0
                    else:
                        if readwait > waitcount:
                            break
                    readwait += 1
                    time.sleep(0.1)
        else:
            self.lgr.error('client type error')
            return -1
                
        if decoding:
            return buf.decode()
        else:
            return buf                

    def connect(self, proto, host, port, user, passwd, timeout=5):
        """ SSH, Telnet, FTP 접속 후 해당 접속 객체를 리턴함

        Args:
            proto (str): Protocol 'SSH','TELNET','FTP'
            host (str): host ip
            port (int or str): port
            user (str): user id
            passwd (str): passwd

        Returns:
            client(obj) : connected session object
        """
        proto = proto.lower()
        client = None
        if proto == 'telnet':
            client = tl.Telnet()
            try:
                client.open(host, int(port), int(timeout))
                client.read_until(b'login:')
                client.write(user.encode() + b'\n')
                client.read_until(b'Password:')
                client.write(passwd.encode() + b'\n')
                self.waitrecv(client)
            except Exception as e:
                self.lgr.error(e)
                return -1
        elif proto == 'ftp':
            client = fl.FTP()
            try:
                client.connect(host, int(port), int(timeout))
                client.login(user, passwd)
            except Exception as e:
                self.lgr.error(e)
                return -1
        elif proto == 'ssh' or proto == 'sftp':
            client = pm.SSHClient()
            client.set_missing_host_key_policy(pm.AutoAddPolicy())
            try:
                client.connect(host, port=int(port), username=user,
                               password=passwd, timeout=int(timeout))
                sh = client.invoke_shell()
                self.waitrecv(sh)
                sftp = pm.SFTPClient.from_transport(client.get_transport())
            except Exception as e:
                self.lgr.error(e)
                return -1
            return (client, sh, sftp)
        else:
            self.lgr.error('Wrong protocol : %s' % proto)
            return -1
        return client
    
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
            cno = range(len(self.cinf))
        for rc in cno:
            if ci['client'][rc] not in ('', None, -1):
                continue
            else:
                ci['client'][rc] = self.connect(str(ci['svc_type'][rc]),
                                                str(ci['host'][rc]), 
                                                int(ci['port'][rc]), 
                                                str(ci['userid'][rc]), 
                                                str(ci['passwd'][rc]))

    def showclients(self):
        print(self.cinf)

    def runcmd(self, client, cmd):
        '''
        단일 명령어 실행. for only SSH
        :param client : paramko SSH Client object 
        :param cmd [str or list] : Command to run on the client
        :return: dictionary of stdin, stdout, stderr
        '''
        dict_ret = {'cmd': cmd, 'stdout': [], 'stderr': []}
        if type(client) != pm.client.SSHClient:
            self.lgr.error('Wrong Client This function is\
                           only for SSH' % client)
            return -1
        elif type(client) == pm.client.SSHClient:
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
    
    def runcmdshell(self, client, cmdlines):
        """세션을 유지한 쉘에서 명령어를 수행함

        Args:
            client (obj): 접속 클라이언트 또는 invokeshell 객체
            cmdlines (list): 수행할 명령어 리스트

        Returns:
            dict_ret: 명령어 및 수행된 결과값에 대한 딕셔너리
        """
        dict_ret = {'cmd': cmdlines, 'recv':[]}
        for cmd in cmdlines:
            buf = self.waitrecv(client)
            if type(client) == tl.Telnet:
                client.write(cmd.encode() + b'\n')
            elif type(client) == pm.channel.Channel:
                client.send(cmd + '\n')
            else:
                self.lgr.error('Client is not available')
                return -1
            buf = self.waitrecv(client)
            if buf == '':
                dict_ret['recv'].append('')
            else:
                #dict_ret['recv'].append(re.split('\n|\r\n', buf))
                dict_ret['recv'].append(buf)
        return dict_ret
        

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
        # Client객체가 FTP인지 SFTP인지 체크한다
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
        # client가 SSH면 SFTP 채널 오픈
        sftp = pm.SFTPClient.from_transport(client.get_transport())
        dstfiles = []
        
        # Check Dstpath

        # get directory or files
        pass

    def closeall(self):
        for i in range(len(self.cinf)):
            c1 = self.cinf['client'][i] != -1
            c2 = pd.isna(self.cinf['client'][i]) == False
            if c1 or c2:
                try:
                    self.cinf['client'][i].close()
                except Exception as e:
                    self.lgr.error(e)
                self.cinf['client'][i] = -1


if __name__ == '__main__':
    pass
