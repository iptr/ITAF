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
    ret = delcomment(tmp)
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
    

if __name__ == '__main__':
    pass
