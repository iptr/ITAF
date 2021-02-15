import os
import time
import socket as skt
import telnetlib as tl
import ftplib as fl
import paramiko as pm

from taiflogger import *
from dbctrl import *
from commonlib import *

class TermCtrl:
    """
    Telnet,FTP, SSH프로토콜을 사용하여 대상서버에서 작업하는 클래스
    대상서버 접속정보는 DB 또는 File에서 가져올 수 있다.

    Attr:
    server_list(DataFrame) : 대상서버 접속정보 및 client 객체
            name, svc_type(telnet, ftp, ssh), ip, port, userid, password
    conf(dic) : 설정정보
    lgr (Logger) : 로깅을 위한 인스턴스
    """
    lgr = None
    conf = None
    cols = None
    server_list = {}

    def __init__(self):
        self.lgr = Logger().getlogger("TermCtrl")
        self.conf = getfileconf(CONF_PATH)
        cols = self.conf['Tables']['server_list_cols'].split(',')
        self.cols=[]
        for col in cols:
            self.server_list[col.strip()] = []
            self.cols.append(col.strip())
        self.server_list['client'] = []
        self.cols.append('client')
        #self.setserverlist()
        
    def setserverlist(self):
        slist = getsvrlistcsv(self.conf['File']['server_list_file'])
        for row in slist:
            for i,col in enumerate(self.cols[:-1]):
                try:
                    self.server_list[col.strip()].append(row[i])
                except Exception:
                    print(i, col, row, self.cols, slist)
            self.server_list['client'].append('None')
            
    def connect(self, proto, host, port, user, passwd, timeout=5, ifc=None):
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
            except Exception as e:
                self.lgr.error(e)
                print('%s:%s'%(host,port),e)
                return -1
        elif proto == 'ftp':
            client = fl.FTP()
            try:
                client.connect(host, int(port), int(timeout),
                               source_address=sip)
                client.login(user, passwd)
            except Exception as e:
                self.lgr.error(e)
                return -2
        elif proto == 'ssh' or proto == 'sftp':
            sock = None
            if ifc != None:
                sock = skt.socket(skt.AF_INET, skt.SOCK_STREAM)
                sock.setsockopt(skt.SOL_SOCKET, skt.SO_BINDTODEVICE, ifc+'\0')
                sock.connect((host, int(port)))
            client = pm.SSHClient()
            client.set_missing_host_key_policy(pm.AutoAddPolicy())
            try:
                client.connect(host, port=int(port), username=user,
                               password=passwd, timeout=int(timeout),
                               allow_agent=False, sock=sock)
                sh = client.invoke_shell()
                sftp = pm.SFTPClient.from_transport(client.get_transport())
            except Exception as e:
                self.lgr.error(e)
                print(host,port,e)
                return -3
            return (client, sh, sftp)
        else:
            self.lgr.error('Wrong protocol : %s' % proto)
            return -4
        return client
    
    def connectlist(self, cno = None):
        """ 
        server_list 서버 목록의 일부 또는 전체 서버에 접속을 시도하고 
        server_list에 접속 객체를 갱신함

        Args:
            cno(None,list,int): server_list의 index, 
                                None = 전체
                                list = 일부 ex. [1,4]
                                int = 특정 서버
        """
        ci = self.server_list
        if cno == None:
            cno = range(len(self.server_list['name']))
        for rc in cno:
            if ci['client'][rc] not in ('', 'None', '-1'):
                continue
            else:
                ci['client'][rc] = self.connect(str(ci['svc_type'][rc]),
                                                str(ci['host'][rc]), 
                                                int(ci['port'][rc]), 
                                                str(ci['userid'][rc]), 
                                                str(ci['passwd'][rc]))

    def showclients(self):
        maxcolsize = [0 for col in self.cols]
        data = []
        for i in range(len(self.server_list['name'])):
            row = []
            for c, col in enumerate(self.cols):
                try:
                    if maxcolsize[c] < len(self.server_list[col][i]):
                        maxcolsize[c] = len(self.server_list[col][i])
                except Exception as e:
                    maxcolsize[c] = 32
                row.append(str(self.server_list[col][i]))
            data.append(row)
        
        row = ''
        for c,col in enumerate(self.cols):
            tmp = '{0:^%s}'%(maxcolsize[c]+4)
            row += tmp.format(col) 
        print(row)
        
        for line in data:
            row = ''
            for c, col in enumerate(self.cols):
                tmp = '{0:^%s}'%(maxcolsize[c]+4)
                row += tmp.format(line[c])
            print(row)

    def closeall(self):
        for i in range(len(self.server_list['name'])):
            c1 = self.server_list['client'][i] not in ['None','-1']
            if c1:
                try:
                    self.server_list['client'][i].close()
                except Exception as e:
                    self.lgr.error(e)
                self.server_list['client'][i] = -1

class CMDRunner():
    lgr = None
    def __init__(self):
        self.lgr = Logger().getlogger("CMDRunner")

    def runcmd(self, client, cmd, exresult=''):
        buf = ''
        if type(client) == tl.Telnet or type(client) == pm.channel.Channel:
            self.waitrecv(client)
        if type(client) == pm.client.SSHClient:
            try:
                stdin, stdout, stderr = client.exec_command(cmd)
            except Exception as e:
                self.lgr.error(e)
            buf = stdout.read() + stderr.read()
        elif type(client) == pm.channel.Channel:
            try:
                client.send(cmd+'\n')
                buf = self.waitrecv(client)
            except Exception as e:
                self.lgr.error(e)
        elif type(client) == tl.Telnet:
            try:
                client.write(cmd.encode() + b'\n')
                buf = self.waitrecv(client)
            except Exception as e:
                self.lgr.error(e)
        else:
            self.lgr.error('Wrong type client')
            return -1

        if type(buf) == str:
            pass
        else:
            buf = buf.decode()

        if buf.find(exresult) > -1:
            return (True, buf)
        else:
            return (False, buf)
            
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
        # when SSH on invoke shell Client
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


class FTRunner():
    lgr = None
    localcwd = None
    
    def __init__(self):
        self.lgr = Logger().getlogger('FTRunner')
        self.localcwd = os.getcwd()

    def getfile(self, client, dstpath, localpath=localcwd):
        '''
        dstpath(str) : 받아올 파일(절대 경로입력 필요)
        localpath(str) : 가져올 로컬 경로(절대 경로)
        '''
        if os.path.basename(localpath) == '':
            localfile = localpath + os.sep() + os.path.basename(dstpath)
        else:
            localfile = localpath
        # Client객체가 FTP인지 SFTP인지 체크한다
        if type(client) == fl.FTP:
            try:
                f = open(localfile,'wb')
                ftpcmd = 'RETR ' + os.path.abspath(dstpath)
                client.retrbinary(ftpcmd, f.write, blocksize=8192, rest=None)
                f.close()
            except Exception as e:
                print('DEBUG:', e, dstpath)
                return -1
        elif type(client) == pm.sftp_client.SFTPClient:
            try:
                client.get(dstpath, localpath)
            except Exception as e:
                print('DEBUG:', e)
                return -1
        else:
            self.lgr.error("Wrong type Client")
            return -2
        return 0
        
    def putfile(self, client, srcpath, dstpath):
        '''
        ftp 또는 ssh 클라이언트를 통해 원본경로의 내용을 대상경로로 업로드한다.
        :client: ssh client object
        :srcpath: source path to upload
        :dstpath: target path to upload
        '''
        if os.path.basename(dstpath) == '': 
            dstfile = dstpath + os.sep() + os.path.basename(srcpath)
        else:
            dstfile = dstpath
        # Client객체가 FTP인지 SFTP인지 체크한다
        if type(client) == fl.FTP:
            try:
                ftpcmd = 'STOR ' + os.path.abspath(dstfile)
                client.storbinary(ftpcmd, open(srcpath,'rb'), blocksize=8192, callback=None, rest=None)
            except Exception as e:
                print(e)
        elif type(client) == pm.sftp_client.SFTPClient:
            try:
                client.put(srcpath, dstfile)
            except Exception as e:
                print('DEBUG:', e)
                print(srcpath, dstfile)
                print(os.path.getsize(srcpath))
        else:
            self.lgr.error("Wrong type Client")

        # Check source path exists
        # Check destination path on target server exist
        # If directory does not exist, create directory
        

if __name__ == '__main__':
    pass
