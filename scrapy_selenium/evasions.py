from os import listdir
from os.path import isfile, join


class EvasionMeasureFactory(object):

    @staticmethod
    def from_directory():
        evasions = []
        dir_path = "evasions/"
        for filename in listdir(dir_path):
            filepath = join(dir_path, filename)
            if isfile(filepath):
                with open(filepath, 'r') as jsfile:
                    javascript = jsfile.read()
                evasions.append(EvasionMeasureFactory(name=filename, javascript=javascript))
        return evasions

    def __init__(self, name, javascript):
        self.name = name
        self.javascript = javascript
