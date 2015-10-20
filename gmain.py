import os

from g import db

def gg():
    print('gg')
    for i in range(10):
        yield i

def f():
    dbFile = 'config/db.xml'
    dbase = db.DBPhotos(dbFile)

    treeDb = db.TreeDB(dbase)

def gui():
    dbFile = 'config/db.xml'
    dbase = db.DBPhotos(dbFile)
    treeDb = db.TreeDB(dbase)

    import g.gui.gtk.mainwindow as mw
    w = mw.MainWindow(treeDb)


if __name__ == '__main__':
    #f()
    gui()