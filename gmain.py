import g.core.db.dbphotos
from g.core.db import database
from g.core.db.dbthumbs import DbThumbsSqlite

interface = 'qt'

def gui():
    if interface == 'qt':
        import g.gui.qt.mainwindow as mw
    elif interface == 'gtk':
        import g.gui.gtk.mainwindow as mw


    dbPhotos = g.core.db.dbphotos.DbPhotos('config/db.xml')
    dbTags = database.DBTags('config/tags.xml')
    dbAlbums = database.TreeDB(dbPhotos)
    dbThumbs = DbThumbsSqlite('thumbs.db')

    mw.MainWindow.start(dbPhotos, dbAlbums, dbTags, dbThumbs)


if __name__ == '__main__':
    gui()