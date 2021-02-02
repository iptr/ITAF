import os
import time
import re
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
        self.setserverlist()
        
    def setserverlist(self):
        cols = self.conf['Tables']['server_list_cols'].split(',')
        self.cols=[]
        for col in cols:
            self.server_list[col.strip()] = []
            self.cols.append(col.strip())
        self.server_list['client'] = []
        self.cols.append('client')
        slist = getsvrlistcsv(self.conf['File']['server_list_file'])
        for row in slist:
            for i,col in enumerate(cols):
                self.server_list[col.strip()].append(row[i])
            self.server_list['client'].append('None')
            
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
            except Exception as e:
                self.lgr.error(e)
                print(e)
                return -1
        elif proto == 'ftp':
            client = fl.FTP()
            try:
                client.connect(host, int(port), int(timeout))
                client.login(user, passwd)
            except Exception as e:
                self.lgr.error(e)
                return -2
        elif proto == 'ssh' or proto == 'sftp':
            client = pm.SSHClient()
            client.set_missing_host_key_policy(pm.AutoAddPolicy())
            try:
                client.connect(host, port=int(port), username=user,
                               password=passwd, timeout=int(timeout),
                               allow_agent=False)
                sh = client.invoke_shell()
                sftp = pm.SFTPClient.from_transport(client.get_transport())
            except Exception as e:
                self.lgr.error(e)
                print(e)
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

    def runcmd(self, client, cmdlist):
        result = {'cmd': cmdlist, 'recv': [], 'stderr': []}
        buf = ''
        
        if type(client) == pm.client.SSHClient or type(client) == pm.channel.Channel:
            self.waitrecv(client)
        for cmd in cmdlist:
            if type(client) == pm.client.SSHClient:
                try:
                    stdin, stdout, stderr = client.exec_command(cmd)
                except Exception as e:
                    self.lgr.error(e)
                result['recv'].append(stdout.readlines())
                result['stderr'].append(stderr.readlines())
            elif type(client) == pm.channel.Channel:
                try:
                    client.send(cmd+'\n')
                    buf = self.waitrecv(client)
                except Exception as e:
                    self.lgr.error(e)
                if buf == '':
                    result['recv'].append('')
                    result['stderr'].append(None)
                else:
                    result['recv'].append(buf)
                    result['stderr'].append(None)
            elif type(client) == tl.Telnet:
                try:
                    client.write(cmd.encode() + b'\n')
                    buf = self.waitrecv(client)
                except Exception as e:
                    self.lgr.error(e)
                if buf == '':
                    result['recv'].append('')
                    result['stderr'].append(None)
                else:
                    result['recv'].append(buf)
                    result['stderr'].append(None)
            else:
                self.lgr.error('Wrong type client')
                return -1
        return result
            
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
    def __init__(self):
        self.lgr = Logger().getlogger('FTRunner')

    def getfile(self, client, dstpath, localpath='.'):
        # Client객체가 FTP인지 SFTP인지 체크한다
        if client == fl.FTP:
            f = open(localpath,'wb')
            client.retrbinary(dstpath, f.write, blocksize=8192, rest=None)
            f.close()
        elif client == pm.SFTPClient:
            client.get(dstpath, localpath)
        else:
            self.lgr.error("Wrong type Client")
        
    
    def putfile(self, client, srcpath, dstpath):
        '''
        ftp 또는 ssh 클라이언트를 통해 원본경로의 내용을 대상경로로 업로드한다.
        :client: ssh client object
        :srcpath: source path to upload
        :dstpath: target path to upload
        '''
        # Client객체가 FTP인지 SFTP인지 체크한다
        if client == fl.FTP:
            client.storbinary(dstpath, open(srcpath,'rb'), blocksize=8192, callback=None, rest=None)
        elif client == pm.SFTPClient:
            client.put(srcpath, dstpath)
        else:
            self.lgr.error("Wrong type Client")
        pass
        # Client객체가 FTP인지 SFTP인지 체크한다
        sftp = pm.SFTPClient.from_transport(client.get_transport())
        srcbase = os.path.basename(srcpath)
        srcfiles = self.getlocalpath(srcpath)

        # Check source path exists
        # Check destination path on target server exist
        # If directory does not exist, create directory
        

if __name__ == '__main__':
    pass
