import logging
import inspect
import taiflogger

log = taiflogger.Logger()
logger = log.getlogger()

# DEBUG 에 해당하는 로그 출력
def LOG_DEBUG(message):
    logger._log(level = logging.DEBUG, 
                msg = message, 
                args = (()), 
                stacklevel = len(inspect.stack()) - 1)

# INFO 에 해당하는 로그 출력
def LOG_INFO(message):
    logger._log(level = logging.INFO,
                msg = message,
                args = (()),
                stacklevel = len(inspect.stack()) - 1)

# WARNING 에 해당하는 로그 출력
def LOG_WARNING(message):
    logger._log(level = logging.WARNING,
                msg=message, 
                args=(()), 
                stacklevel=len(inspect.stack()) - 1)

# ERROR 에 해당하는 로그 출력
def LOG_ERROR(message):
    logger._log(level=logging.ERROR, 
                msg=message, 
                args=(()), 
                stacklevel=len(inspect.stack()) - 1)

# CRITICAL 에 해당하는 로그 출력
def LOG_CRITICAL(message):
    logger._log(level=logging.CRITICAL,
                msg=message,
                args=(()),
                stacklevel=len(inspect.stack())-1)

