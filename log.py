import logging
import datetime


def setup_logging(log_file_name):
    file_level = logging.INFO
    console_level = logging.INFO
    log_file_name = '%s_%s.log' % (log_file_name,datetime.datetime.now().strftime('%Y-%m-%d-%H%M%S%f'))
    formatter = logging.Formatter('%(asctime)s: %(levelname)s: %(message)s')
    logger = logging.getLogger(__name__)
    logger.setLevel(min(file_level,console_level))

    ch = logging.StreamHandler()
    ch.setLevel(console_level)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    fh = logging.FileHandler(log_file_name,mode = 'a')
    fh.setLevel(file_level)
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    return logger