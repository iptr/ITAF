'''
Utility library
- Validation check...
- Read configuration
'''
import re
import csv
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


def getsvrlistcsv(fname):
    f = open(fname)
    reader = csv.reader(f)
    org = list(reader)
    f.close()
    cols=['name','svc_type','host','port','userid','passwd']
    temp = []
    for row in org:
        if len(row) != len(cols) :
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

def add_row_to_df(df, rows):
    """append rows to dataframe

    Args:
        df (DataFrame) : Original DataFrame
        rows (list) : Records to append
    """
    
    


if __name__ == '__main__':
    pass
