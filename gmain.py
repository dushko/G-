from g import db


interface = 'qt'

def gui():
    if interface == 'qt':
        import g.gui.qt.mainwindow as mw
    elif interface == 'gtk':
        import g.gui.gtk.mainwindow as mw


    dbPhotos = db.DBPhotos('config/db.xml')
    dbTags = db.DBTags('config/tags.xml')
    dbAlbums = db.TreeDB(dbPhotos)

    mw.MainWindow.start(dbPhotos, dbAlbums, dbTags)


if __name__ == '__main__':
    gui()