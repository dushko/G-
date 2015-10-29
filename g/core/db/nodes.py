import gc
import os
import shutil
from subprocess import Popen, PIPE

from PyQt5.QtGui import QPixmap
from lxml.etree import Element

from g.tools import PhotoCmd


class FolderNode(object):
    """ A folder node containing photo nodes"""
    commentFile = "album.txt"

    def __init__(self, n):
        assert n.tag in ["folder", "db"]
        self.__node = n

    def __getName(self):
        return os.path.basename(self.__node.attrib["name"])
    name = property(__getName)

    def __getFile(self):
        return self.__node.attrib["name"]
    file = property(__getFile)

    def __getComment(self):
        ln = self.__node.xpath("c")
        if ln:
            return dec(ln[0].text)
        else:
            return ""
    comment = property(__getComment)

    def __getExpand(self):
        if "expand" in self.__node.attrib:
            return (self.__node.attrib["expand"] != "0")
        else:
            return True
    expand = property(__getExpand)

    def _getNode(self):  # special
        return self.__node

    def getParent(self):
        return FolderNode(self.__node.getparent())

    def getFolders(self):
        ln = [FolderNode(i) for i in self.__node.xpath("folder")]
        ln.sort(key=lambda x: x.name.lower())
        return ln

    def getPhotos(self):
        return self._select("photo")

    def getAllPhotos(self):
        return self._select("descendant::photo")

    def _select(self, xpath):
        """ 'xpath' should only target photo node """
        class PhotoNodes(list):
            def __init__(self, l, xpath):
                list.__init__(self, l)
                self.xpath = xpath

        ln = self.__node.xpath(xpath)
        ll = [PhotoNode(i) for i in ln]
        return PhotoNodes(ll, "//folder[@name='%s']/%s" %
                          (self.file, xpath))

    def setComment(self, t):
        assert type(t) == unicode
        file = os.path.join(self.file, FolderNode.commentFile)
        if t == "":  # if is the "kill comment"
            if os.path.isfile(file):  # if files exists, kill it
                try:
                    os.unlink(file)
                    return True
                except:
                    return False

            return True
        else:
            fid = open(file, "w")
            if fid:
                fid.write(t.encode("utf_8"))
                fid.close()
                self._updateInfo()
                return True
            else:
                return False

    def _updateInfo(self):
        ln = self.__node.xpath("c")
        assert len(ln) in [0, 1]
        if ln:
            nodeComment = ln[0]
        else:
            nodeComment = None

        comment = None
        file = os.path.join(self.file, FolderNode.commentFile)
        if os.path.isfile(file):
            fid = open(file, "r")
            if fid:
                comment = fid.read().decode("utf_8")
                fid.close()

        if comment:
            if nodeComment is None:
                nodeComment = Element("c")
                nodeComment.text = comment
                self.__node.append(nodeComment)
            else:
                nodeComment.text = comment
        else:
            if nodeComment is not None:
                self.__node.remove(nodeComment)

    def setExpand(self, bool):
        if bool:
            self.__node.attrib["expand"] = "1"
        else:
            self.__node.attrib["expand"] = "0"

    def rename(self, newname):
        assert type(newname) == str
        oldname = self.file
        newname = os.path.join(os.path.dirname(oldname), newname)
        if not (os.path.isdir(newname) or os.path.isfile(newname)):
            try:
                shutil.move(oldname, newname)
                moved = True
            except os.error as detail:
                raise Exception(detail)

            if moved:
                self.__node.attrib["name"] = newname

                ln = self.__node.xpath("descendant::folder")
                for i in ln:
                    i.attrib["name"] = newname + \
                        i.attrib["name"][len(oldname):]
                return True

        return False

    def createNewFolder(self, newname):
        assert type(newname) == unicode
        newname = os.path.join(self.file, newname)
        ll = [i for i in self.getFolders() if i.file == newname]
        if len(ll) == 1:
            # folder is already mapped in the db/xml
            # so no creation
            return False
        else:
            if not os.path.isfile(newname):
                # it's not a file

                if os.path.isdir(newname):
                    # but it's an existing folder
                    created = True
                else:
                    # this is a real new folder
                    # let's create it in the FS
                    try:
                        os.mkdir(newname)
                        created = True
                    except os.error as detail:
                        raise Exception(detail)

                if created:
                    #so map the folder to a db node
                    nodeDir = Element("folder", name=newname)
                    self.__node.append(nodeDir)
                    return FolderNode(nodeDir)
        return False

    def remove(self):
        """ delete ONLY node """
        self.__node.getparent().remove(self.__node)

    def delete(self):
        """ delete real folder and node """
        if os.path.isdir(self.file):
            try:
                shutil.rmtree(self.file)
                deleted = True
            except os.error as detail:
                raise Exception(detail)
        else:
            deleted = True

        if deleted:
            self.remove()
            return True

        return False

    def moveToFolder(self, nodeFolder):
        assert nodeFolder.__class__ == FolderNode
        oldname = self.file
        newname = os.path.join(nodeFolder.file, self.name)
        if not (os.path.isdir(newname) or os.path.isfile(newname)):
            try:
                shutil.move(oldname, newname)
                moved = True
            except os.error as detail:
                raise Exception(detail)

            if moved:
                self.__node.attrib["name"] = newname
                self.remove()
                nodeFolder.__node.append(self.__node)

                ln = self.__node.xpath("descendant::folder")
                for i in ln:
                    i.attrib["name"] = newname + \
                        i.attrib["name"][len(oldname):]
                return self
        return False


class PhotoNode(object):
    """
      Class PhotoNode
      to manipulate a node photo in the dom of album.xml.
    """
    def __init__(self, node):
        assert node.tag == "photo"
        self.__node = node
        self.pic = None

    def getParent(self):
        return FolderNode(self.__node.getparent())

    def getThumb(self):
        if self.pic is None:
            name = os.path.join(self.__getFolder(), self.name)
            self.pic = QPixmap(name).scaledToWidth(100)
        return self.pic

    def getPath(self):
        return os.path.join(self.__getFolder(), self.name)

    def getImage(self):
        file = self.file
        # XXX external call while pyexiv2 can't handle it
        extension = os.path.splitext(file)[1].lower()
        if extension == 'nef':
            data = Popen(["exiftool", "-b", "-JpgFromRaw",
                         "%s" % file], stdout=PIPE).communicate()[0]
            loader = gtk.gdk.PixbufLoader('jpeg')
            loader.write(data, len(data))
            im = loader.get_pixbuf()
            loader.close()
            return im
        else:
            return gtk.gdk.pixbuf_new_from_file(file)

    def moveToFolder(self, nodeFolder):
        assert nodeFolder.__class__ == FolderNode

        name = self.name
        while os.path.isfile(os.path.join(nodeFolder.file, name)):
            name = PhotoCmd.giveMeANewName(name)

        try:
            shutil.move(self.file, os.path.join(nodeFolder.file, name))
            moved = True
        except os.error as detail:
            raise Exception(detail)

        if moved:
            self.__node.attrib["name"] = name
            self.__node.getparent().remove(self.__node)
            nf = nodeFolder._getNode()
            nf.append(self.__node)
            return True

    def rotate(self, sens):
        assert sens in ["R", "L"]

        pc = PhotoCmd(self.file)
        pc.rotate(sens)
        self.updateInfo(pc)

    def transform(self, sens):
        assert sens in ["auto", "rotate90", "rotate180", "rotate270",
                        "flipHorizontal", "flipVertical", "transpose",
                        "transverse"]

        pc = PhotoCmd(self.file)
        pc.transform(sens)
        self.updateInfo(pc)

    def setComment(self, txt):
        assert type(txt) == str

        pc = PhotoCmd(self.file)
        if pc.addComment(txt):
            self.updateInfo(pc)

    def setRating(self, val):
        assert type(val) == int

        pc = PhotoCmd(self.file)
        if pc.addRating(val):  # always true
            self.updateInfo(pc)

    def addTag(self, tag):
        assert type(tag) == str

        pc = PhotoCmd(self.file)
        if pc.add(tag):
            self.updateInfo(pc)

    def addTags(self, tags):
        assert type(tags) == list

        pc = PhotoCmd(self.file)
        if pc.addTags(tags):
            self.updateInfo(pc)

    def delTag(self, tag):
        assert type(tag) == str

        pc = PhotoCmd(self.file)
        if pc.sub(tag):
            self.updateInfo(pc)

    def clearTags(self):
        pc = PhotoCmd(self.file)
        if pc.clear():
            self.updateInfo(pc)

    def rebuildThumbnail(self):
        pc = PhotoCmd(self.file)
        pc.rebuildExifTB()
        self.updateInfo(pc)

    def copyTo(self, path, resize=None, keepInfo=True, delTags=False,
               delCom=False):
        """ copy self to the path "path", and return its newfilename or none
            by default, it keeps IPTC/THUMB/EXIF, but it can be removed by
            setting keepInfo at False. In all case, new file keep its filedate
            system

            image can be resized/recompressed (preserving ratio) if resize
            (which is a tuple=(size, qual)) is provided:
                if size is a float : it's a percent of original
                if size is a int : it's the desired largest side
                qual : is the percent for the quality
        """
        assert type(path) == unicode, "photonod.copyTo() : path is not unicode"
        dest = os.path.join(path, self.name)

        while os.path.isfile(dest):
            dest = os.path.join(path,
                                PhotoCmd.giveMeANewName(
                                    os.path.basename(dest)))

        if resize:
            assert len(resize) == 2
            size, qual = resize
            assert type(size) in [int, float]

            pb = self.getImage()  # a gtk.PixBuf
            (wx, wy) = pb.get_width(), pb.get_height()

            # compute the new size -> wx/wy
            if type(size) == float:
                # size is a percent
                size = int(size * 100)
                wx = int(wx * size / 100)
                wy = int(wy * size / 100)

            else:
                # size is the largest side in pixels
                if wx > wy:
                    # format landscape
                    wx, wy = size, (size * wy) / wx
                else:
                    # format portrait
                    wx, wy = (size * wx) / wy, size

            # 3= best quality (gtk.gdk.INTERP_HYPER)
            pb = pb.scale_simple(wx, wy, 3)
            pb.save(dest, "jpeg", {"quality": str(int(qual))})

            if keepInfo:
                pc = PhotoCmd(self.file)
                pc.copyInfoTo(dest)
            del(pb)
            gc.collect()  # so it cleans pixbufs
        else:
            shutil.copy2(self.file, dest)
            if not keepInfo:
                # we must destroy info
                PhotoCmd(dest).destroyInfo()
        if keepInfo:
            if delCom:
                PhotoCmd(dest).addComment(u"")
            if delTags:
                PhotoCmd(dest).clear()

        return dest

    def getInfoFrom(self, copy):
        """ rewrite info from a 'copy' to the file (exif, iptc, ...)
            and rebuild thumb
            (used to ensure everything is back after a run in another program
             see plugin 'touch')
        """
        pc = PhotoCmd(copy)
        pc.copyInfoTo(self.file)

        #and update infos
        # generally, it's not necessary ... but if size had changed, jhead
        # correct automatically width/height exif, so we need to put back in db
        pc = PhotoCmd(self.file)
        self.updateInfo(pc)

    #~ def repair(self):
        #~ pc = PhotoCmd(self.file)
        #~ pc.repair()                 # kill exif tags ;-(
        # recreate "fake exif tags" with exifutils and thumbnails
        #~ pc.rebuildExifTB()
        #~ self.updateInfo(pc)

    def redate(self, w, d, h, m, s):
        pc = PhotoCmd(self.file)
        pc.redate(w, d, h, m, s)
        self.updateInfo(pc)
        self.updateName()

    def setDate(self, date):
        pc = PhotoCmd(self.file)
        pc.setDate(date)
        self.updateInfo(pc)
        self.updateName()

    def updateName(self):
        return True

    def updateInfo(self, pc):
        """ fill the node with REAL INFOS from "pc"(PhotoCmd)
            return the tags
        """
        assert pc.__class__ == PhotoCmd

        self.__node.clear()
        self.__node.attrib["name"] = os.path.basename(pc.file)
        self.__node.attrib["resolution"] = pc.resolution

        # NEW PhotoCmd (always a exifdate)
        self.__node.attrib["date"] = pc.exifdate
        if pc.isreal:
            self.__node.attrib["real"] = "yes"
        else:
            self.__node.attrib["real"] = "no"

        if pc.tags:
            for tag in pc.tags:
                nodeTag = Element("t")
                nodeTag.text = tag
                self.__node.append(nodeTag)
        if pc.comment:
            nodeComment = Element("c")
            try:
                nodeComment.text = char_utils.make_xml_string_legal(pc.comment)
            except ValueError as f:
                print("exception = %s" % f)
                print("nodeComment = %s" % nodeComment)
                print("pc.comment = %s" % pc.comment)
                raise
            self.__node.append(nodeComment)
        if pc.rating:
            nodeRating = Element("r")
            nodeRating.text = str(pc.rating)
            self.__node.append(nodeRating)

        return pc.tags

    def getInfo(self):
        """
        get real infos from photocmd
        """
        pc = PhotoCmd(self.file)
        info = {}
        info["tags"] = pc.tags
        info["comment"] = pc.comment
        info["exifdate"] = pc.exifdate
        info["rating"] = pc.rating  # huh, did i use that?
        info["filedate"] = pc.filedate
        info["resolution"] = pc.resolution
        info["readonly"] = pc.readonly
        info["filesize"] = os.stat(self.file)[6]

        return info

    def getThumbSize(self):
        """Get the size (width, height) of the thumbnail"""
        try:
            thumbnail = Img(thumb=self.file)
            return (thumbnail.width, thumbnail.height)
        except IOError:  # 404
            return (-1, -1)

    def delete(self):
        try:
            os.unlink(self.file)
            deleted = True
        except os.error as detail:
            raise Exception(detail)
            deleted = False

        if deleted:
            self.__node.getparent().remove(self.__node)
            return True

        return False

    def __getName(self):
        return self.__node.attrib["name"]
    name = property(__getName)

    def __getfolderName(self):
        return os.path.basename(self.folder)
    folderName = property(__getfolderName)

    def __getIsReadOnly(self):
        return not os.access(self.file, os.W_OK)
    isReadOnly = property(__getIsReadOnly)

    def __getTags(self):
        l = [dec(i.text) for i in self.__node.xpath("t")]
        l.sort()
        return l
    tags = property(__getTags)

    def __getComment(self):
        ln = self.__node.xpath("c")
        if ln:
            return dec(ln[0].text)
        else:
            return ""
    comment = property(__getComment)

    def __getRating(self):  # 0x4746 18246 IFD0 Exif.Image.Rating Short
            ln = self.__node.xpath("r")  # saved decimal like <r>5</r>
            if ln:
                return int(ln[0].text)
            else:
                return 0
    rating = property(__getRating)

    # if exif -> exifdate else filedate
    def __getDate(self):
        return self.__node.attrib["date"]
    date = property(__getDate)

    def __getResolution(self):
        return self.__node.attrib["resolution"]
    resolution = property(__getResolution)

    # if exifdate -> true else false
    def __getReal(self):
        return self.__node.attrib["real"]
    real = property(__getReal)

    def __getFolder(self):
        na = self.__node.getparent().attrib["name"]
        assert type(na) == str
        return na
    folder = property(__getFolder)

    def __getFile(self):
        return dec(os.path.join(self.__getFolder(), self.__getName()))
    file = property(__getFile)


class TagNode(object):
    """ """
    def __init__(self, n):
        assert n.tag == "tag"
        self.__node = n

    def __getName(self):
        return dec(self.__node.text)
    name = property(__getName)

    def __getKey(self):
        return dec(self.__node.get("key"))

    def __setKey(self, v):
        self.__node.set("key", v)
    key = property(__getKey, __setKey)

    def remove(self):
        self.__node.getparent().remove(self.__node)

    def moveToCatg(self, c):
        assert type(c) == CatgNode
        self.remove()
        c._appendToCatg(self.__node)


class CatgNode(object):
    """ """
    def __init__(self, n):
        assert n.tag == "tags"
        self.__node = n

    def __getName(self):
        if "name" in self.__node.attrib:
            return dec(self.__node.attrib["name"])
        else:
            return u"Tags"
    name = property(__getName)

    def __getExpand(self):
        if "expand" in self.__node.attrib:
            return (self.__node.attrib["expand"] != "0")
        else:
            return True
    expand = property(__getExpand)

    def getTags(self):
        l = [TagNode(i) for i in self.__node.xpath("tag")]
        l.sort(cmp=lambda x, y: cmp(x.name, y.name))
        return l

    def getCatgs(self):
        return [CatgNode(i) for i in self.__node.xpath("tags")]

    def getAllTags(self):
        l = self.getTags()
        for i in self.getCatgs():
            l.extend(i.getAllTags())
        l.sort(cmp=lambda x, y: cmp(x.name, y.name))
        return l

    def addTag(self, t):
        assert type(t) == str

        if self.isUnique("tag", t):
            n = Element("tag")
            n.text = t
            self.__node.append(n)
            return TagNode(n)

    def rename(self, newName):
        self.__node.attrib["name"] = newName

    def remove(self):
        self.__node.getparent().remove(self.__node)

    def moveToCatg(self, c):
        self.remove()
        c._appendToCatg(self.__node)

    def _appendToCatg(self, element):
        self.__node.append(element)

    def addCatg(self, t):
        assert type(t) == str

        if self.isUnique("tags", t):
            n = Element("tags", name=t)
            self.__node.append(n)
            return CatgNode(n)

    def setExpand(self, bool):
        if bool:
            self.__node.attrib["expand"] = "1"
        else:
            self.__node.attrib["expand"] = "0"

    def isUnique(self, type, name):
        if type == "tag":
            ln = [dec(i.text) for i in self.__node.xpath("//tag")]
        else:
            ln = [CatgNode(i).name for i in self.__node.xpath("//tags")]
        return name not in ln