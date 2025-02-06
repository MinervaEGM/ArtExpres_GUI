import logging
import os
from datetime import datetime

def init_config(absolute_project_directory):
    logging.basicConfig(filename = absolute_project_directory + "/debug_info.log", format = '%(asctime)s %(message)s', filemode = 'a') #%(levelname)s
    logger = logging.getLogger()
    logger.setLevel(logging.WARNING)
    return logger

def write_to_log(absolute_project_directory,info, item):
    date = datetime.now().strftime("%Y/%m/%d")
    time = datetime.now().strftime("%H:%M:%S")
    try:
        with open(absolute_project_directory + '/data/application_info.csv', 'a') as file:
            line = date + ',' + time + ',' + info + ',' + str(item) + ',\n'
            file.write(line)
    except FileNotFoundError as e:
        logger.warning(e)
    except Exception as e:
        logger.warning(e)