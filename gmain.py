import g.core.db.dbphoto
from g.core.db import database

interface = 'qt'

def gui():
    if interface == 'qt':
        import g.gui.qt.mainwindow as mw
    elif interface == 'gtk':
        import g.gui.gtk.mainwindow as mw


    dbPhotos = g.core.db.dbphoto.DBPhotos('config/db.xml')
    dbTags = database.DBTags('config/tags.xml')
    dbAlbums = database.TreeDB(dbPhotos)

    mw.MainWindow.start(dbPhotos, dbAlbums, dbTags)


if __name__ == '__main__':
    gui()