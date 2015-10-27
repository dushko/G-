import os

from lxml.etree import ElementTree, Element

from g.common import cd2d
from g.core.db.database import TreeDB, walktree
from g.core.db.nodes import FolderNode, PhotoNode, PhotoNode
from g.tools import PhotoCmd, supportedFormats


class DBPhotos:
    normalizeName = False
    autorotAtImport = False

    def __init__(self, file):
        if os.path.isfile(file):
            self.root = ElementTree(file=file).getroot()
        else:
            print('Cannot opet file %s', file)
            self.root = Element("db")
        self.file = file

    def getPhotosByPath(self, path):
        path = os.path.normpath(path)

        node = self.root.xpath('//folder[@name="%s"]' % (path, ))
        photos = node[0].xpath('photo')
        photoNodes = [PhotoNode(p) for p in photos]
        return photoNodes

    def getAlbumTree(self, rootAlbum=None):
        if rootAlbum is None:
            dbTree = TreeDB(self)
            return dbTree.tree
        else:
            raise NotImplemented('getAlbumTree not implemented for subalbums')

    @staticmethod
    def setNormalizeName(v):
        assert v in (True, False)
        DBPhotos.normalizeName = v

    @staticmethod
    def setNormalizeNameFormat( v):
        assert isinstance(v, str)
        PhotoCmd.setNormalizeNameFormat(v)

    @staticmethod
    def setAutorotAtImport(v):
        assert v in (True, False)
        DBPhotos.autorotAtImport = v

    def add(self, path, tags={}):
        assert type(path) == str
        assert os.path.isdir(path)

        path = os.path.normpath(path)
        importErrors = {}
        ln = self.root.xpath('//folder[@name="%s"]' % path)
        assert len(ln) <= 1
        if ln:
            nodeFolder = ln[0]
            filesInBasket = [i.file for i in self.getBasket(nodeFolder)]
            nodeFolder.getparent().remove(nodeFolder)
        else:
            filesInBasket = []

        files = []
        for (basepath, children) in walktree(path, False):
            dir = basepath
            try:
                nodeDir = self.root.xpath(u"""//folder[@name="%s"]""" % dir)[0]
            except:
                nodeDir = None

            if nodeDir is None:
                rep = []
                while True:
                    rep.append(dir)
                    dir, n = os.path.split(dir)
                    if not n:
                        break
                rep.reverse()

                node = self.root
                for r in rep:
                    try:
                        nodeDir = node.xpath(u"""folder[@name="%s"]""" % r)[0]
                    except:
                        nodeDir = Element("folder", name=r)
                        node.append(nodeDir)

                        FolderNode(nodeDir)._updateInfo()  # read comments

                    node = nodeDir
                nodeDir = node

            for child in children:
                if child.split('.')[-1].lower() in supportedFormats:
                    file = os.path.join(basepath, child)
                    if os.path.isfile(file):
                        files.append((file, nodeDir))

        yield len(files)   # first yield is the total number of files

        i = 0
        for (file, nodeDir) in files:
            yield i
            i += 1
            m = self.__addPhoto(nodeDir, file, tags, filesInBasket)
            if m:
                importErrors[file] = m

        ln = self.root.xpath(u"""//folder[@name="%s"]""" % path)
        if ln:
            yield FolderNode(ln[0])
        else:
            yield None
        if len(importErrors) > 0:
            k = importErrors.keys()
            k.sort()
            msgs = []
            for f in k:
                msgs.append('"%s" adding file: "%s"' % (importErrors[f], f))
            print('JBrout import errors: '.join(msgs))

    def __addPhoto(self, nodeDir, file, tags, filesInBasket):
        assert type(file) == str

        newNode = Element("photo")
        nodeDir.append(newNode)

        node = PhotoNode(newNode)
        if file in filesInBasket:
            node.addToBasket()

        try:
            iii = PhotoCmd(file,
                           needAutoRename=DBPhotos.normalizeName,
                           needAutoRotation=DBPhotos.autorotAtImport,
                           )
            if iii.exifdate == "":
                # exif is not present, and photocmd can't reach
                # to recreate minimal exif tags (because it's readonly ?)
                # we can't continue to import this photo
                raise Exception(
                    "Exif couldn't be set in this picture (readonly?)")
        except Exception as m:
            # remove the bad node
            nodeDir.remove(newNode)

            return m
        else:
            importedTags = node.updateInfo(iii)
            for i in importedTags:
                tags[i] = i  # feed the dict of tags

            return None

    def getRootFolder(self):
        if len(self.root) > 0:
            return FolderNode(self.root[0])

    def redoIPTC(self):
        """ refresh IPTC in file and db """
        ln = self.root.xpath(u"""//photo[t]""")
        for i in ln:
            p = PhotoNode(i)
            print(p.name)
            pc = PhotoCmd(p.file)
            pc.__maj()              # rewrite iptc in file
            p.updateInfo(pc)      # rewrite iptc in db.xml

    def getMinMaxDates(self):
        """ return a tuple of the (min, max) of photo dates
            or none if no photos
        """
        ln = self.root.xpath("//photo")
        if ln:
            ma = 11111111111111
            mi = 99999999999999
            for i in ln:
                a = int(i.attrib["date"])
                ma = max(a, ma)
                mi = min(a, mi)
            return cd2d(str(mi)), cd2d(str(ma))

    def select(self, xpath, fromNode=None):
        ln = self.root.xpath(xpath)
        if ln:
            return [PhotoNode(i) for i in ln]
        else:
            return []

    def query(self, xpath):
        ln = self.root.xpath(xpath)
        return ln

    def toXml(self):
        """ for tests only """
        from io import StringIO
        fid = StringIO()
        fid.write("""<?xml version="1.0" encoding="UTF-8"?>""")
        ElementTree(self.root).write(fid, encoding="utf-8")
        return fid.getvalue()

    def save(self):
        """ save the db, and a basket.txt file """
        fid = open(self.file, "wb")
        fid.write(b"""<?xml version="1.0" encoding="UTF-8"?>""")
        ElementTree(self.root).write(fid)
        fid.close()