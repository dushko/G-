import os

from g.core.db.database import Thumb


class DBThumbs(object):
    def getByHash(self, hash):
        raise NotImplementedError()
    def getByFilePath(self, path):
        raise NotImplementedError()
    def getById(self, id):
        raise NotImplementedError()

    def removeByHash(self, hash):
        raise NotImplementedError()
    def removeByFilePath(self, path):
        raise NotImplementedError()
    def removeById(self, id):
        raise NotImplementedError()


class DbThumbsFile(DBThumbs):
    def __init__(self, path):
        self.path = path

    def getByHash(self, thumbHash):
        subDir = thumbHash[:2]
        fname = os.path.join(self.path, subDir, thumbHash[2:])
        if os.path.exists(fname):
            with open(fname, 'rb') as f:
                data = f.readall()
                return Thumb(0, data)
        else:
            return None