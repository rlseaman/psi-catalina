import os
import itertools

class Paths:
    '''
    A helper class that determines where data files and labels are stored. This
    provides multiple ways to get at each data file and label file, and
    accounts for the fact that the data and labels are delivered in separate locations.
    '''
    def __init__(self, basedir, dest, bundle_id, schemadir):
        self.basedir = basedir
        self.dest = dest
        self.bundle_id = bundle_id
        self.schemadir = schemadir

    def datadir(self, inst=None, year=None, date=None, filename=None):
        '''
        Returns the data directory
        '''
        return self._buildpath((self.basedir, inst, year, date, filename))

    def labeldir(self, inst=None, year=None, date=None, filename=None):
        '''
        Returns the label file directory
        '''
        subdir = "other/pds4" if date else None
        return self._buildpath((self.basedir, inst, year, subdir, date, filename))

    def destdir(self, collection_id, inst=None, year=None, subDir=None, date=None, failed=False):
        '''
        Returns the destination directory
        '''
        if failed:
            return self._buildpath((self.dest, "failed", collection_id, inst, year, None, date))
        else:
            return self._buildpath((self.dest, self.bundle_id, collection_id, inst, year, subDir, date))

    def productDestDir(self, p, failed=False):
        return self.destdir(p.collection_id(), p.inst, p.year, p.date, failed)        

    def validationDataDir(self, p, failed=False):
        return self.destdir(None, p.inst, p.year, None, p.date, failed)        

    def validationLabelDir(self, p, failed=False):
        return self.destdir(None, p.inst, p.year, "other/pds4", p.date, failed)        

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