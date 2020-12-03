import os
import logging
import logging.config
import logging.handlers
import socket
import json


class Logger:
	hostname = socket.gethostname()
	conf = None

	def __init__(self) :
		f = open("conf/logger.conf",'r')
		self.conf = json.load(f)
		f.close()
		logdir = os.path.dirname(self.conf['handlers']['filelog']['filename'])
		if not os.path.isdir(logdir):
			os.mkdir(logdir)
		logging.config.dictConfig(self.conf)
		intlogger = logging.getLogger("Logger Class")
		intlogger.debug("Logger instance Created")


	def getlogger(self, logger_name):
		logger = logging.getLogger(logger_name)
		logger.debug(logger_name + " created")
		#fileHandler = logging.FileHandler(self.__log_file_name)
		#streamHandler = logging.StreamHandler()
		#fileHandler.setFormatter(self.__formatter)
		#streamHandler.setFormatter(self.__formatter)
		#logger.addHandler(fileHandler)
		#logger.addHandler(streamHandler)
		#logger.setLevel(log_level)
		return logger