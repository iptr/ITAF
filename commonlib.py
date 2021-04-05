'''
Utility library
- Validation check...
- Read configuration
'''
import re
import os
import csv
import hashlib
import configparser as cp
from dbctrl import *

CONF_PATH = 'conf/taif.conf'

def chk_strlen(value, min, max):
    if min <= len(value) <= max:
        return True
    else:
        return False
    
def chk_valip(value):
    patt = re.compile("((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)")
    if patt.fullmatch(value):
        return True
    else:
        return False 
    
def chk_intsize(value, min=0, max=100000):
    try:
        value = int(value)
    except Exception as e:
        return False
    if min <= value <= max:
        return True
    else:
        return False
    
def getfileconf(conf_file, section=None, option=None):
    config = cp.ConfigParser()
    config.read(conf_file, encoding='UTF-8')
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
            
def getdbconf(dbname, table, option=None):
    pass

def delcomment(datalist):
    ret = []
    for line in datalist:
        if type(line) == list:
            if line[0].find('#') > -1:
                pass
            else:
                ret.append(line)
        else:
            if -1 < str(line).find('#') < 4:
                pass
            else:
                ret.append(line)
    return ret

def getlistfromcsv(fname):
    f = open(fname)
    reader = csv.reader(f)
    tmp = list(reader)
    f.close()
    ret = delcomment(tmp)
    return ret

def getlistfromtxt(fname):
    f = open(fname)
    lines = f.readlines()
    f.close()
    ret = []
    ret = delcomment(lines)
    return ret

def getsvrlistcsv(fname):
    org = getlistfromcsv(fname)
    cols=['name','svc_type','host','port','userid','passwd']

    temp = []
    for row in org:
        if len(row) < len(cols) :
            continue
        if 4 > row[0].find('#') > -1:
            continue
        if row[1].upper() not in ['SSH','TELNET','FTP']:
            continue
        if not chk_valip(row[2]):
            continue
        if not chk_intsize(row[3], 1, 65534):
            continue
        temp.append(row) 
    return temp

def getsvrlistdb():
    conf = getfileconf(CONF_PATH)
    columns = conf['Tables']['server_list_cols'].split(',')
    if conf['Common']['cfgtype'].lower() == 'db':
            dbc = DBCtrl()
            if dbc.connect() != -1:
                slist = dbc.select(conf['DB']['db'],
                                     conf['Tables']['server_list_tbl'],
                                     cols=columns)
                dbc.close()
                result = []
                for i, row in enumerate(slist):
                    temp = []
                    for j, col in enumerate(columns):
                        temp.append(row[j])
                    result.append(temp)
                return result
            else:
                return -1
#수정 필요
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

# 수정 필요
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

def repeater(values):
    i = 0
    while True:
        yield values[i]
        i += 1
        if i >= len(values):
            i = 0
            
def gethash(buf):
    result = hashlib.sha256(buf.encode())
    return result.hexdigest()

def getfilehash(fname):
    f = open(fname,'rb')
    hash = gethash(f.read())
    f.close()
    return hash

def tupletostrlist(data):
    ret = []
    for line in data:
        ret.append(line[0])

def removeHashTag(text):
    '''
    # 문자를 제거

    @param
        text - # 문자를 제거 하고자하는 문자열

    @return
        # 문자가 제거된 문자열
    '''
    removeResult = str(text)

    return removeResult.replace("#","")

def removeLineFeed(text):
    '''
    LineFeed 문자를 제거

    @param
        text - LineFeed를 제거 하고자하는 문자열

    @return
        LineFeed 문자가 제거된 문자열
    '''

    removeResult = str(text)

    return removeResult.replace("\n","")

def splitEqual(text):
    '''
    = 기준으로 문자열 분리

    @param
        text - 분리 하고자 하는 문자열

    @return
        = 기준 상위 문자열 - key
        = 기준 하위 문자열 - value
    '''
    text = str(text)
    if text.find("=") == -1:
        return ""
    else:
        result = text.replace(" ","").split("=")

        return result

def readFileLines(path):
    '''
    파일의 내용 읽기

    @param
        path - 파일 경로

    @return
        파일 내용
    '''
    if os.path.isfile(path) == False:
        return ""

    fp = open(path,"r")
    result = fp.readlines()

    return result

def readFileLine(path):
    '''
    파일의 내용 한줄 읽기

    @param
        path - 파일 경로

    @return
        한줄의 파일 내용
    '''
    if os.path.isfile(path) == False:
        return ""

    fp = open(path,"r")
    result = fp.readline()

    return result

def readDCConfFile(path):
    '''
    DC Config 파일 read

    @param
        path - conf 파일이 저장된 위치

    @return
        설정값
    '''

    fp = open(path,"r")

    readLine = fp.readline()
    result = []

    while readLine:
        if isComment(readLine) != 1:
            if isComment(readLine) == 2:
                readLine = splitHashTag(readLine)

            readLine = removeLineFeed(readLine)
            split_result = splitEqual(readLine)
            if len(split_result) != 0:
                result.append(split_result)
        else:
            pass

        readLine = fp.readline()

    return dict(result)

def isComment(content):
    '''
    주석 여부 확인

    @parma
        content - 주석 여부 확인 수행하는 문장

    @return
        0 -> noComment
        1 -> isComment
        2 -> content + comment
    '''
    if len(content) == 0:
        return 0

    string_to_ascii = [ord(c) for c in content]

    # 시작부터 주석처리가 되어 있는 경우
    if(string_to_ascii[0] == 35):
        return 1

    # statement 뒤에 주석 처리가 되어 있는 경우
    for i in range(len(string_to_ascii)):
        if(i > 0):
            if(string_to_ascii[i] == 35):
                return 2

    return 0

def splitHashTag(text):
    '''
    # 기준으로 문자열 분리

    @param
        text - 분리 하고자 하는 문자열

    @return
        # 기준 상위의 있는 문자열
    '''
    text = str(text)
    if text.find("#") == -1:
        return ""
    else:
        result = text.replace(" ", "").split("#")

        # 주석 처리가 되어 있지 않은 부분 반환
        return result[0]

def adjustLength(original_list,comparision_target):
    '''
    비교 대상의 리스트 길이 조정

    @param
        original_list - 비교 기준인 리스트
        comparision_target - 비교가 되는 리스트

    @return
        길이 차이 만큼 0이 추가된 comparision_target 반환
    '''
    if len(original_list) != len(comparision_target):
        diff = len(original_list) - len(comparision_target)
        if diff > 0:
            for i in range(diff):
                comparision_target.append(0)
        else:
            pass

    return comparision_target

if __name__ == '__main__':
    pass
