import os

class Paths:
    def __init__(self, basedir, dest):
        self.basedir = basedir
        self.dest = dest

    def datadir(self, inst=None, year=None, date=None, filename=None):
        if filename:
            return os.path.join(self.basedir, inst, year, date, filename)
        elif date:
            return os.path.join(self.basedir, inst, year, date)
        elif year:
            return os.path.join(self.basedir, inst, year)
        elif inst:
            return os.path.join(self.basedir, inst)
        else:
            return self.basedir

    def labeldir(self, inst=None, year=None, date=None, filename=None):
        if filename:
            return os.path.join(self.basedir, inst, year, "pds4", date, filename)
        elif date:
            return os.path.join(self.basedir, inst, year, "pds4" ,date)
        elif year:
            return os.path.join(self.basedir, inst, year)
        elif inst:
            return os.path.join(self.basedir, inst)
        else:
            return self.basedir

    def destdir(self, collection_id, inst, year, date):
        return os.path.join(self.dest, collection_id, inst, year, date)
