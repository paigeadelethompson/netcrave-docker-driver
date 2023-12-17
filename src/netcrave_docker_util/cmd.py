import io
import subprocess
import threading
import logging

def cmd(*args, **kwargs):
    logger = logging.getLogger(__name__)
    check = False
    def log_stream(pipe, logger):
        # by default stderr will be a binary stream
        # we wrap it into a text stream
        pipe = io.TextIOWrapper(pipe, encoding='utf-8', newline='')
        with pipe:
            for line in pipe:
                logger.info(line.rstrip('\n'))

    with subprocess.Popen(
            *args, bufsize=1, stderr=subprocess.PIPE, **kwargs) as proc:
        logger_thread = threading.Thread(
            target=log_stream, args=(proc.stderr, logger))
        logger_thread.start()
        proc.wait()
        logger_thread.join()
    if check is True:
        if proc.returncode != 0:
            raise subprocess.CalledProcessError(
                proc.returncode, proc.args,
                proc.stdout.read() if proc.stdout is not None else None)
    return proc
