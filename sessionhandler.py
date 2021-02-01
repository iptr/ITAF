import sys

from . import taiflogger
from . import dbctrl
from .commonlib import *

class SessionHandler:
    lgr = None
    conf = None
    server_list = {}
    
    def __init__(self):
        self.lgr = Logger().getlogger('SessionHandler')
        self.configure()
        
    def configure(self):
        # 기본 설정 불러오기
        self.conf = getfileconf(CONF_PATH)
        conf = self.conf
        # 클라이언트 정보 딕셔너리 생성
        cols = conf['Tables']['server_list_cols'].split(',')
        for col in cols:
            self.server_list[col.strip()] = []
        self.server_list['client'] = []
        
    def getserverlist(self):
        # 설정을 DB에서 가져오기일 경우
        conf = self.conf
        cols = conf['Tables']['server_list_cols'].split(',')
        if conf['Common']['cfgtype'].lower() == 'db':
            result = getsvrlistdb()
            if result != -1:
                self.lgr.error('DB Connection failed')
            else:
                for row in result:
                    for i, col in enumerate(cols):
                        self.server_list[col.strip()].append(row[i])
                        self.server_list['client'].append('')
            
        # 설정을 File에서 가져오기일 경우
        elif conf['Common']['cfgtype'].lower() == 'file':
            slist = getsvrlistcsv(conf['File']['server_list_file'])
            for row in slist:
                for i, col in enumerate(cols):
                    self.server_list[col.strip()].append(row[i])
                    self.server_list['client'].append('')
        #설정이 잘못되었을 경우
        else:
            self.lgr.error("\"%s\" in %s is Wrong Type"%(conf['Common']['cfgtype'],CONF_PATH))
            return -1
        
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
        sl = self.server_list
        if cno == None:
            cno = range(len(self.server_list))
        for rc in cno:
            if sl['client'][rc] not in ('', None, -1):
                continue
            else:
                sl['client'][rc] = self.connect(str(sl['svc_type'][rc]),
                                                str(sl['host'][rc]), 
                                                int(sl['port'][rc]), 
                                                str(sl['userid'][rc]), 
                                                str(sl['passwd'][rc]))

    def showclients(self):
        header = ''
        conf = self.conf
        cols = conf['Tables']['server_list_cols'].split(',')
        colsize = []
        data = []
        for r in range(len(self.server_list['name'])):
            row = ''
            for c, col in enumerate(cols):
                row += self.server_list[col.strip()][r].strip() + '  '
            data.append(row)
            
        for c, col in enumerate(cols):
            strlen = 0
            for i in range(self.server_list[col]):
                data[c].append(self.server_list[col][i])
                if strlen < self.server_list[col][i]:
                    strlen = self.server_list[col][i]
            colsize.append(strlen)
        
        for i, col in enumerate(cols):
            temp = '{0:^%s}'%colsize[i]
            header += temp.format(col.strip()) + '  '
        header += '\n'
        
        print(header)
        for d in data:
            print(d)
        
if __name__ == '__main__':
    pass