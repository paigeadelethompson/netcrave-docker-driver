import logging 
import traceback
import sys
from netcrave_docker_util.exception import unknown
from pathlib import Path

log = logging.getLogger(__name__)

async def swallow_async():
        try:
            await callback()
            return True
        except Exception as ex:
            exc_type, exc_value, exc_tb = sys.exc_info() 
            tb = traceback.TracebackException(exc_type, exc_value, exc_tb)
            if len(tb.stack) == 0:
                log.warn("this exception is a piece of shit {}".format(ex))
            else:
                stack = tb.stack[0]

                exc_type, exc_value, exc_traceback = sys.exc_info()
                _details = {
                    'filename': Path(stack.filename).name,
                    'lineno'  : stack.lineno,
                    'name'    : stack.name,
                    'type'    : tb.exc_type,
                    'message' : str(ex) }
                
                log.warn("""{file} {line} {name} {type} {message}""".format(
                        file = _details.get("filename"),
                        line = _details.get("lineno"),
                        name = _details.get("name"), 
                        type = _details.get("type"),
                        message = _details.get("message")))
            return False

def swallow(callback):
    try:
        callback()
        return True
    except Exception as ex:
        exc_type, exc_value, exc_tb = sys.exc_info() 
        tb = traceback.TracebackException(exc_type, exc_value, exc_tb)
        if len(tb.stack) == 0:
             log.warn("this exception is a piece of shit {}".format(ex))
        else:
            stack = tb.stack[0]

            exc_type, exc_value, exc_traceback = sys.exc_info()
            _details = {
                'filename': Path(stack.filename).name,
                'lineno'  : stack.lineno,
                'name'    : stack.name,
                'type'    : tb.exc_type,
                'message' : str(ex) }
            
            log.warn("""{file} {line} {name} {type} {message}""".format(
                    file = _details.get("filename"),
                    line = _details.get("lineno"),
                    name = _details.get("name"), 
                    type = _details.get("type"),
                    message = _details.get("message")))
        return False
