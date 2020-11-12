import logging
import logging.handlers

class Logger:
	def __init__(self, log_file_name=LOG_FILE_NAME, is_file_output=True, is_stream_output=True) :
		self.__hostname = socket.gethostname()
		self.__log_file_name = log_file_name
		self.__formatter = logging.Formatter('[%(asctime)s]'
										+ '[%(levelname)s]'
										+ '[' + self.__hostname + ']'
										+ '[%(name)s]'
										+ '[%(funcName)s]'
										+ ' %(message)s')

	def getlogger(self, logger_name, log_level):
		logger = logging.getLogger(logger_name)
		fileHandler = logging.FileHandler(self.__log_file_name)
		streamHandler = logging.StreamHandler()
		fileHandler.setFormatter(self.__formatter)
		streamHandler.setFormatter(self.__formatter)
		logger.addHandler(fileHandler)
		logger.addHandler(streamHandler)
		logger.setLevel(log_level)
		return logger