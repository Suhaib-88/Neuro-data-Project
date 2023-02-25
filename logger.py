import logging
import os
from datetime import datetime

def absoluteFilePaths(directory):
    for dirpath,_,filenames in os.walk(directory):
        yield os.path.abspath(dirpath)


def absoluteFilePaths(directory):
    for dirpath,_,filenames in os.walk(directory):
        yield os.path.abspath(dirpath)

LOG_FILE = f"{datetime.now().strftime('%m_%d_%Y_%H_%M_%S')}.log"

logs_path = os.path.join(next(absoluteFilePaths("logs")), LOG_FILE)

if not os.path.exists(logs_path):
    os.makedirs(logs_path)

LOG_FILE_PATH = os.path.join(logs_path, LOG_FILE)

logging.basicConfig(
    filename=LOG_FILE_PATH,
    format="[ %(asctime)s ] %(lineno)d %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)