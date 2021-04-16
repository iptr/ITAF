import os
import logging
import logging.config

LOG_CONF_PATH = 'conf/logging.conf'

class Logger:
    """
    TAIF Logger

    Checks if there is a configure file, reads the configuration file and performs logging basic settings
    make Logger instance -> run getlogger method
    """

    # 생성자
    def __init__(self):
        # logging.conf 파일의 유무를 판단
        if os.path.isfile(LOG_CONF_PATH) != True:
            logging.getLogger("root").critical("Can not Found configure file")


    # conf 파일을 읽어 로거를 반환
    def getlogger(self):
        # logging.conf 파일을 읽음
        fp = open(LOG_CONF_PATH, encoding='utf-8')
        logging.config.fileConfig(fp)
        # 읽어 드린 logging.conf 파일 중 로거 선택(default - root)
        logger = logging.getLogger()

        return logger

