'''
Utility library
- Validation check...
- Read configuration
'''
import re
import os
import csv
import hashlib
import base64
import configparser as cp
from struct import pack
from struct import unpack
from ipaddress import IPv4Address
from dbctrl import *

CONF_PATH = 'conf/taif.conf'

def chk_strlen(value, min, max):
    '''
    문자열 길이 체크
    '''
    if min <= len(value) <= max:
        return True
    else:
        return False
    
def chk_valip(value):
    '''
    IP주소 문자열에 대한 Vaildation Check
    '''
    patt = re.compile("((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)")
    
    if patt.fullmatch(value):
        return True
    else:
        return False 
    
def chk_intsize(value, min=0, max=100000):
    '''
    value값에 대해서 min~max 사이의 정수일 경우 True 
    정수가 아니거나 범위를 초과할 경우 False
    '''
    try:
        value = int(value)
    except Exception as e:
        return False

    if min <= value <= max:
        return True
    else:
        return False
    
def get_file_conf(conf_file, section=None, option=None):
    '''
    파일로부터 설정을 가져오는 함수
    '''
    config = cp.ConfigParser()
    try:
        config.read(conf_file, encoding='UTF-8')
    except Exception as e:
        print('get_file_conf() error : ' + e)
    sections = []
    if section == None:
        sections = config.sections()
    elif type(section) == list:
        sections = section
    elif type(section) == str:
        sections.append(section)
    else:
        return -1
    
    if option == None:
        conf = {}
        for sec in sections:
            try:
                conf[sec] = {}
            except:
                print(conf, sec)
            for opt in config.items(sec):
                conf[sec][opt[0]] = opt[1]
        return conf
    else:
        return config.get(section, option)
            
def get_db_conf(dbname, table, option=None):
    '''
    DB로부터 설정을 가져오는 함수
    [To do] @ jycho
    '''
    pass

def del_comment(datalist):
    '''
    datalist에 #가 포함된 라인만 제거 후 리스트로 리턴
    '''
    ret = []
    for line in datalist:
        if type(line) == list and len(line) > 0:
            line[0] = line[0].replace('\r','')
            if line[0].strip('\t ')[0] != '#':
                ret.append(line)
    return ret

def get_list_from_csv(fname):
    '''
    csv 파일로부터 내용들을 받아 리스트로 반환
    '''
    # 파일 존재 여부 확인
    if os.path.isfile(fname) == False:
        return -1
        
    # 파일 오픈시 예외발생
    try:
        f = open(fname, encoding='utf-8')
    except Exception as e:
        print('get_list_from_csv() Error : ' + e)
        return -2
    
    reader = csv.reader(f)
    tmp = list(reader)
    f.close()
    ret = del_comment(tmp)
    return ret

def get_list_from_txt(fname):
    '''
    일반 Text파일을 읽어 리스트로 리턴
    리스트 식별자는 개행문자
    '''
    # 경로의 파일이 존재하는지 확인
    if os.path.isfile(fname) == False:
        return -1
    
    # 파일 오픈시 예외 발생 확인
    try:
        f = open(fname, 'r', encoding='utf-8')
        lines = f.readlines()
        f.close()
    except Exception as e:
        print("get_list_from_txt() Error : %s"%e)
        return -1
    
    # 주석 라인 제거
    return del_comment(lines)

def get_server_list_csv(fname):
    '''
    서버목록 CSV 파일에서 List 추출
    '''
    org = get_list_from_csv(fname)
    cols = ['name','svc_type','host','port','userid','passwd','svcnum']
    lines = []

    for row in org:
        #if len(row) < len(cols) :
        #    continue
        if row[1].lower() not in ['ssh','telnet','ftp','sftp']:
            continue
        if not chk_valip(row[2]):
            continue
        if not chk_intsize(row[3], 1, 65534):
            continue
        lines.append(row) 
    return lines

def get_server_list_db():
    '''
    NIY(Not Implemented Yet)
    db로부터 서버 목록을 가져와 list로 반환한다.
    '''
    conf = get_file_conf(CONF_PATH)
    columns = conf['Tables']['server_list_cols'].split(',')
    result = []
    
    if conf['Common']['cfgtype'].lower() != 'db':
        return result

    dbc = DBCtrl()
    if dbc.connect() == -1:
        return -1
    
    slist = dbc.select(conf['DB']['db'],
                        conf['Tables']['server_list_tbl'],
                        cols=columns)
    dbc.close()
    
    for i, row in enumerate(slist):
        temp = []
        for j, col in enumerate(columns):
            temp.append(row[j])
        result.append(temp)

    return result

def get_remote_file_list(self, path, client=None):
        '''
        NIY(Not Implemented Yet)
        원격지에 파일 목록을 가져와 리스트로 반환한다.
        :param path: 디렉토리 경로
        :param client: ssh client object
        '''
        flist = []
        if client != None:
            cmd = "file `find %s`|grep -v directory" % path
            ret = self.run_cmd(client, cmd)
            if len(ret['stdout'][0]) > 0:
                for line in ret['stdout'][0]:
                    flist.append(line.strip(':')[0])
        else:
            for dpath, dnames, fnames in os.walk(path):
                for fn in fnames:
                    flist.append(dpath + os.sep + fn)
        return flist


def get_local_path(self, path):
    '''
    NIY(Not Implemented Yet)
    path가 존재하는지 파일인지 디렉토리인지 확인하고 디렉토리일경우 디렉토리 하위의 모든 파일들을 리턴한다.
    path의 파일명에 와일드카드(*,?)가 존재할경우 다수의 파일목록을 리턴한다.
    '''
    flist = []
    dname = os.path.dirname(path)
    bname = os.path.basename(path)
    # Check whether the path is a directory
    if os.path.isdir(path):
        flist = self.get_fileslist(path)
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
                    flist += self.get_fileslist(tmppath)
                elif os.path.isfile(tmppath):
                    flist.append(tmppath)
                else:
                    pass
        return flist
    return flist

def rotator(values):
    '''
    Values(list)의 값을 무한히 로테이션 시켜주는 기능
    rotater로 객체 생성 후 next(객체명)으로 뽑아냄
    ex) 
    rt = rotator([1,2,3,4,5])
    next(rt)
    '''
    i = 0
    while True:
        yield values[i]
        i += 1
        if i >= len(values):
            i = 0
            
def get_hash(buf, algorithm='sha256'):
    hash = hashlib.new(algorithm)
    if type(buf) == bytes:
        hash.update(buf)
    else:
        hash.update(buf.encode())
    return hash.hexdigest()

def get_hash_bytes(buf, algorithm='sha256'):
    hash = hashlib.new(algorithm)
    if type(buf) == str:
        hash.update(buf.encode())
    else:
        hash.update(buf)
    return hash.digest()

def encode_b64(text):
    """
    Text를 Base64로 인코딩
    """
    return base64.b64encode(text)
    
def get_file_hash(fname):
    '''
    파일로부터 해쉬값을 뽑아 str 형태로 리턴함
    '''
    try:
        f = open(fname,'rb')
        hash = get_hash(f.read())
        f.close()
    except Exception as e:
        print(e)
        return -1
    return hash

def tuple_to_str_list(data):
    '''
    튜플형태의 값을 리스트로 리턴함
    '''
    ret = []
    for line in data:
        ret.append(line[0])
        
def line_to_csv_str(line):
    '''
    line을 csv형태의 string으로 변환함
    line (list) : CSV 형태로 변경할 list
    return : str + '\n'
    '''
    return str(line).strip("[]\'").replace('\'', '').replace(' ','') + '\n'

def print_matrix(contents:list, header=None, padding=1):
    '''
    2중 리스트(테이블)를 입력 받아 정리된 테이블형태로 출력한다.
    '''
    result = []
    sizelist = [0 for _ in contents[0]]
    
    if header == list:
        contents.insert(0,header)

    # 각 컬럼의 최대 크기 측정
    for row in contents:
        for i,col in enumerate(row):
            if sizelist[i] < len(col):
                sizelist[i] = len(col)
    
    # 컬럼 사이즈대로 출력하기
    for row in contents:
        line = ''
        for i, csz in enumerate(sizelist):
            temp = '{0:^%s}'%(csz+(padding*2))
            line += temp.format(row[i])
        print(line)
    return result

def usToB(number:int):
    """정수를 Unsigned Short(2byte)의 
    Big endian Binary Byte로 리턴함

    Args:
        number (int): 바꿀 정수

    Returns:
        bytes : 2byte크기의 Binary bytes
    """
    return pack('>H',int(number))

def ipToB(ipaddr:str):
    """IP주소 -> Big endian Binary bytes 변경

    Args:
        ipaddr (str): 문자로된 IP주소

    Returns:
        bytes: 문자열 바이너리 바이트
    """
    return IPv4Address(ipaddr).packed
    
def longToB(num:int):
    """Unsigned long to Big endian Binary Bytes로 변경

    Args:
        bytes (str): 4bytes Binary
    """
    return pack('>I',int(num))

if __name__ == '__main__':
    pass

def byteToNum(bytestr:bytes, sign=False):
    if len(bytestr) == 1:
        format = '>B'
    elif len(bytestr) == 2:
        format = '>H'
    elif len(bytestr) == 4:
        format = '>I'
    elif len(bytestr) == 8:
        format = '>Q'
    else:
        return 0
    if sign:
        format.lower()
    return int(unpack(format, bytestr)[0])