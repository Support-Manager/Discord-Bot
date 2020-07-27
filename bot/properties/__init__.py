from .config import Config
from .defaults import Defaults
import os

CONFIG = Config()

path = os.path.dirname(os.path.abspath(__file__))

CONFIG.from_json_file(path + '/config.json')
try:
    CONFIG.from_json_file(path + '/../instance/secrets.json')
except:
    pass
