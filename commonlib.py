'''
Utility library
- Validation check...
'''
import re
import configparser

def chk_strlen(value, min, max):
    if min <= len(value) <= max:
        return True
    else:
        return False
    
def chk_valip(value, strtype):
    patt = re.compile("((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)")
    if patt.fullmatch(value):
        return True
    else:
        return False 
    
def chk_intsize(value, min=0, max=100000):
    if type(value) != str:
        return False
    if min <= value <= max:
        return True
    else:
        return False
    
def getconf(confgroup, location):
    
    pass


if __name__ == '__main__':
    pass
