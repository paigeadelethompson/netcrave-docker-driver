import logging 
log = logging.getLogger(__name__)

def swallow(callback):
    try:
        callback()
        return True
    except Exception as ex:
        log.warn("swollowed error {ex} swollowed error".format(ex = ex))
        return False
