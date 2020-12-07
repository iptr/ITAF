import os
import logging
import logging.config
import logging.handlers
import json


class Logger:
	"""
	ITAF Logger
	make Logger instance -> run getlogger method
	"""
	
	def __init__(self) :
		f = open("conf/logger.conf",'r')
		conf = json.load(f)
		f.close()
		logdir = os.path.dirname(conf['handlers']['filelog']['filename'])
		if not os.path.isdir(logdir):
			os.mkdir(logdir)
		logging.config.dictConfig(conf)
		intlogger = logging.getLogger("ITAF_Logger")
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
