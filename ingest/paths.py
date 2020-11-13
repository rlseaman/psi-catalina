import os
import itertools

class Paths:
    def __init__(self, basedir, dest):
        self.basedir = basedir
        self.dest = dest

    def datadir(self, inst=None, year=None, date=None, filename=None):
        return self._buildpath((self.basedir, inst, year, date, filename))

    def labeldir(self, inst=None, year=None, date=None, filename=None):
        subdir = "other" if date else None
        return self._buildpath((self.basedir, inst, year, subdir, date, filename))
        
    def destdir(self, collection_id, inst=None, year=None, date=None):
        return self._buildpath((self.dest, collection_id, inst, year, date))

    def _buildpath(self, elements):
        return os.path.join(*self._filledElements(elements))

    def _filledElements(self, elements):
        elementList = list(elements)
        if any(itertools.dropwhile(lambda x: x, elementList)):
            raise Exception("Gaps detected in path:", elementList)
        return list(itertools.takewhile(lambda x: x, elementList))

if __name__ == '__main__':
    p = Paths("base", "dest")
    print(p.datadir("I52"))
    print(p.datadir("I52", "2020"))
    print(p.datadir("I52", "2020", "20Aug01"))
    print(p.datadir("I52", "2020", "20Aug01", "test.fit"))

    print(p.labeldir("I52"))
    print(p.labeldir("I52", "2020"))
    print(p.labeldir("I52", "2020", "20Aug01"))
    print(p.labeldir("I52", "2020", "20Aug01", "test.fit"))

    print(p.destdir("data","I52", "2020", "20Aug01"))