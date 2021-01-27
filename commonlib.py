'''
Utility library
- Validation check...
- Read configuration
'''
import re
import csv
import configparser as cp

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
    temp = list(reader)
    f.close()
    return temp

def add_row_to_df(df, rows):
    """append rows to dataframe

    Args:
        df (DataFrame) : Original DataFrame
        rows (list) : Records to append
    """
    
    


if __name__ == '__main__':
    pass
