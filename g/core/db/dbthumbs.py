import os, sqlite3

from PIL import Image

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

    def add(self, path : str):
        pass

class DbThumbsSqlite(DBThumbs):
    def __init__(self, base):
        self.base = base
        self.cur = None
        self.conn = None

        self.__openBase()

    def __openBase(self):
        self.conn = sqlite3.connect(self.base)

        self.cur = self.conn.cursor()
        self.cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='thumbnails'")
        if self.cur.fetchone() is None:
            self.cur.execute("CREATE TABLE thumbnails("
                    "path STRING,"
                    "thumbnail BLOB,"
                    "PRIMARY KEY(path))")

    def getByFilePath(self, thumbPath):
        self.cur.execute("SELECT thumbnail FROM thumbnails WHERE path=?", (thumbPath,))
        thumb = self.cur.fetchone()
        if thumb:
            return thumb[0]
        else:
            return None

    def addByFilePath(self, thumbPath, thumbnail):
        self.cur.execute("SELECT path FROM thumbnails WHERE path=?", (thumbPath,))
        if self.cur.fetchone():
            self.cur.execute("UPDATE thumbnails SET thumbnail=? WHERE path=?",
                    (thumbnail, thumbPath))
        else:
            self.cur.execute("INSERT INTO thumbnails(path, thumbnail) VALUES(?, ?)",
                    (thumbPath, thumbnail))

        self.conn.commit()

if __name__ == '__main__':
    db = DbThumbsSqlite('thumbs.db')
    size = (256, 256)
    d = '/media/data/ph/marn2'
    paths = os.listdir('/media/data/ph/marn2')
    paths = [os.path.join(d, p) for p in paths]
    for p in paths:
        print(p)
        thumb = g.core.db.thumbreader.getThumb(p, size)
        db.addByFilePath(p, thumb)

        retr = db.getByFilePath(p)