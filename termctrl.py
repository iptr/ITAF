import os
import time
from struct import pack
from ipaddress import IPv4Address
import socket as skt
import telnetlib as tl
import ftplib as fl
import paramiko as pm
from taiflogger import *
from dbctrl import *
from commonlib import *

class NATIDPKT:
    idcode = b'NATIDENTITY'
    pktver = pack('>H',1)
    totlen = pack('>H',0)
    encrypt = pack('>B',0)
    svctype = pack('>I',4)
    rdplog = pack('>I',0)
    svcnum = pack('>I',0)
    localip = b''
    localport = b''
    targetip = b''
    targetport = b''
    gwip = IPv4Address('0.0.0.0').packed
    gwport = pack('>H',0)
    certidlen = pack('>H',9)  
    certid = b'trollking'
    proglen = pack('>H',11)
    progname = b'trolltester'
    assistkeylen = pack('>H',0)
    assistkey = b''
    proghashlen = pack('>H',0)
    proghash = b''
    webassist = pack('>I',0)
    ostype = pack('>H',0)
    msgtunnel = pack('>H',0)
    payload = b''

    def __init__(self):
        pass

    def set(self, svcnum=b'', tgip=b'', tgport=b'', gwip=b'', 
            gwport=b'', certid=b'', loip=b'', loport=b''):
        # 필수정보 교체: 대상서비스번호, 대상IP, port, 로컬IP, 로컬port, dbsIP, dbsport, 
        #               보안계정)
        if loip != b'':
            self.localip = IPv4Address(loip).packed
        if loport != b'':
            self.localport = pack('>H',loport)
        if svcnum != b'':
            self.svcnum = pack('>I',int(svcnum))
        if tgip != b'':
            self.targetip = IPv4Address(tgip).packed 
        if tgport != b'':
            self.targetport = pack('>H',int(tgport))
        if gwip != b'':
            self.gwip = IPv4Address(gwip).packed
        if gwport != b'':
            self.gwport = pack('>H',int(gwport))
        if certid != b'':
            try:
                self.certid = certid.encode()
            except Exception as e:
                print('debug : %s, %s'%(e,certid))
    # 보안계정 길이 계산
        self.certidlen = pack('>H',len(self.certid))

        # 전체 길이 계산(encrypt ~ 끝까지)
        payload = self.encrypt + self.svctype + self.rdplog + self.svcnum
        payload += self.localip + self.localport + self.targetip + self.targetport
        payload += self.gwip + self.gwport + self.certidlen + self.certid
        payload += self.proglen + self.progname + self.assistkeylen + self.assistkey
        payload += self.proghashlen + self.proghash + self.webassist + self.ostype + self.msgtunnel
        self.totlen = pack('>H', len(payload))
        self.payload = self.idcode + self.pktver + self.totlen + payload

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
            
    def connect(self, proto, host, port, user, passwd, timeout=5, ifc=None, 
                usenatid=False, natidpkt=None):
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
                sock.setsockopt(skt.SOL_SOCKET, skt.SO_BINDTODEVICE, (ifc+'\0').encode('utf8'))
                try:
                    sock.connect((host, int(port)))
                except Exception as e:
                    print(e, host+':'+str(port))
                    return -3
                if usenatid == True and natidpkt != None:
                    sktname = sock.getsockname()
                    natidpkt.set(loip=sktname[0], loport=sktname[1])
                    sock.send(natidpkt.payload)
            client = pm.SSHClient()
            client.set_missing_host_key_policy(pm.AutoAddPolicy())
            try:
                client.connect(host, port=int(port), username=user,
                               password=passwd, timeout=int(timeout),
                               allow_agent=False, sock=sock,
                               banner_timeout=30, auth_timeout=30)
                sh = client.invoke_shell()
                sftp = pm.SFTPClient.from_transport(client.get_transport())
            except Exception as e:
                self.lgr.error(e)
                return -4
            return (client, sh, sftp)
        else:
            self.lgr.error('Wrong protocol : %s' % proto)
            return -5
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
                return -1
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
            self.lgr.error('client type error: %s'%client)
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
                print('DEBUG1:', e, dstpath)
                return -1
        elif type(client) == pm.sftp_client.SFTPClient:
            try:
                client.get(dstpath, localpath)
            except Exception as e:
                print('DEBUG2:', e, dstpath, localpath)
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
                return -1
        elif type(client) == pm.sftp_client.SFTPClient:
            try:
                client.put(srcpath, dstfile)
            except Exception as e:
                print('DEBUG:', e)
                return -2
        else:
            self.lgr.error("Wrong type Client")
        return 0
        # Check source path exists
        # Check destination path on target server exist
        # If directory does not exist, create directory
        

if __name__ == '__main__':
    pass
