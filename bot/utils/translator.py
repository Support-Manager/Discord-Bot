from bot import enums


class Translator(dict):
    def __init__(self, translations: dict, language: enums.Language):
        self.language = language.value
        super().__init__(**translations)

    def translate(self, key: str):
        return self[key][self.language]
