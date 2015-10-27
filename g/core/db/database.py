# -*- coding: utf-8 -*-

##
##    Copyright (C) 2005 manatlan manatlan[at]gmail(dot)com
##
## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published
## by the Free Software Foundation; version 2 only.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
import os
import os.path
import stat

from lxml.etree import Element, ElementTree

from g.core.db.nodes import CatgNode
from g.core.tree import Tree


def walktree(top=".", depthfirst=True):
    try:
        names = os.listdir(top)
    except WindowsError:  # protected dirs in win
        names = []

    if not depthfirst:
        yield top, names
    for name in names:
        try:
            st = os.lstat(os.path.join(top, name))
        except os.error:
            continue
        if stat.S_ISDIR(st.st_mode) and not name.startswith("."):
            for (newtop, children) in walktree(os.path.join(top, name),
                                               depthfirst):
                yield newtop, children
    if depthfirst:
        yield top, names


class ImportError(Exception):
    def __init__(self, txt, file):
        self.txt = txt
        self.file = file
        Exception.__init__(self, txt)


# =============================================================================
class DBTags:
    """ Class to manage tags tree """
    def __init__(self, file):
        if os.path.isfile(file):
            self.root = ElementTree(file=file).getroot()
        else:
            self.root = Element("tags")
        self.file = file

    def getTagsTree(self, rootTag=None):
        """
        Returns hierarchical representation of tags from given root node.

        :param rootTag: root of tree to build
        :return: Tree struct with all tags
        """
        root = None
        if rootTag is None:
            root = self.root
        else:
            raise NotImplemented('getTagsTree from subtag not supported')

        def builder(node, tree):
            for tagNode in node.getchildren():
                if tagNode.tag == 'tag':
                    treeChild = tree.addChild(tagNode.get('name'))
                    builder(tagNode, treeChild)

        resultTree = Tree('root')
        builder(root, resultTree)

        return resultTree

    def save(self):
        fid = open(self.file, "w")
        fid.write("""<?xml version="1.0" encoding="UTF-8"?>""")
        ElementTree(self.root).write(fid, encoding="utf-8", prett_print=True)
        fid.close()

    def getRootTag(self):
        return CatgNode(self.root)

    def updateImportedTags(self, importedTags):
        assert type(importedTags) == list

        r = self.getRootTag()
        existingTags = [i.name for i in r.getAllTags()]

        # compare existing and imported tags -> newTags
        newTags = []
        for tag in importedTags:
            if tag not in existingTags:
                newTags.append(tag)

        if newTags:
            # create a category imported
            nom = u"Imported Tags"
            while 1:
                nc = r.addCatg(nom)
                if nc is not None:
                    break
                else:
                    nom += u"!"

            for tag in newTags:
                ret = nc.addTag(tag)
                assert ret is not None, "tag '%s' couldn't be added" % tag

        return len(newTags)


class TreeDB(object):
    def __init__(self, db, filter=None):
        self.__filter = filter
        self.db = db
        self.tree = None
        self.folderNames = []

        self.init()

    def init(self):
        root = self.db.getRootFolder()
        path = []
        self.zapfill(root, path)

    def zapfill(self, node, attach):
        """
        same as fill, but zap the beginning of the useless tree, and
        branch to fill
        """
        if node is not None:
            folders = node.getFolders()
            photos = node.getPhotos()
            # zap the useless folders
            if len(folders) == 1 and len(photos) == 0:
                attach.append(node.name)
                return self.zapfill(folders[0], attach)
            else:
                if self.tree is None:
                    rootPath = '/'.join(attach)
                    tree = Tree(rootPath)
                    self.tree = tree.addChild(node.name)

                return self.fill(node, self.tree)

    def fill(self, node, tree):
        """
        rebuild treestore from the nodefolder 'node' to the iter 'attach'
        """
        folders = node.getFolders()

        if node is not None:
            for f in folders:
                ch = tree.addChild(f.name)
                self.fill(f, ch)

    # # new version, with recursive process, to avoid bug (see below)
    def find(self, node):
        """ return the 'iter' of the node in the model or None """
        a = self.get_iter_root()
        while a:
            r = self.ffind(a, node)
            if r:
                return r
            a = self.iter_next(a)

    def ffind(self, it, node):
        nnode = self.get(it)

        if nnode and nnode.file == node.file:
            return it
        else:
            ic = self.iter_children(it)
            while ic:
                f = self.ffind(ic, node)
                if f:
                    return f
                else:
                    ic = self.iter_next(ic)


    def get(self, it):
        """ get the 'node' of the iter 'it' """
        node = self.get_value(it, 2)
        return node


class Thumb(object):
    def __init__(self, thumbId : int, data : bytearray):
        self.id = thumbId
        self.data = data

    @staticmethod
    def fromImageFile(path):
        pass


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
