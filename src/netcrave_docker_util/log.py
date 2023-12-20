import logging
import os
import datetime


def configure_logger_for_module(name):
    module_logger = logging.getLogger(name)
    module_logger.setLevel(
        logging.INFO if not os.environ.get('DEBUG') else logging.DEBUG)
    main_logger = logging.getLogger('__main__')
    main_logger.setLevel(logging.INFO if not os.environ.get(
        'DEBUG') else logging.DEBUG)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)

    try:
        import colorlog

        stream_formatter = colorlog.ColoredFormatter(
            '%(log_color)s%(asctime)s %(levelname)s %(green)s%(module)s %(cyan)s%(funcName)s %(white)s%(message)s',
            "%H:%M:%S",
            log_colors={
                'DEBUG': 'blue',
                'INFO': 'green',
                'WARNING': 'yellow',
                'ERROR': 'red',
                'CRITICAL': 'bold_red',
                'EXCEPTION': 'bold_red',
            })
    except ImportError:
        stream_formatter = logging.Formatter(
            '%(levelname)s %(module)s %(funcName)s %(message)s')
    console_handler.setFormatter(stream_formatter)

    package_timestamp = datetime.datetime.now().strftime('%Y%m%dT%H%M%S')
    if os.path.isdir('logs'):
        file_handler = logging.FileHandler(
            os.path.join(
                'logs',
                '{}_{}.log'.format(
                    name,
                    package_timestamp)),
            mode='a')
        file_handler.setLevel(
            logging.INFO if not os.environ.get('DEBUG') else logging.DEBUG)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s %(module)s %(name)s %(message)s'))
        module_logger.addHandler(file_handler)
        main_logger.addHandler(file_handler)

    module_logger.addHandler(console_handler)
    main_logger.addHandler(console_handler)

    return module_logger, main_logger, console_handler
