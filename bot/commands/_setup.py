import json

bot = None

with open('commands/config.json', 'r', encoding='utf-8') as c:
    config = json.load(c)
