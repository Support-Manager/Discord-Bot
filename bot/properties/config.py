import json


class Config(dict):
    def __init__(self, **kwargs):
        super(dict, self).__init__(**kwargs)

    def from_json_file(self, path):
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.update(**data)
