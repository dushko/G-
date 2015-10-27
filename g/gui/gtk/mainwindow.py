from gi.repository import GdkPixbuf
from gi.repository import Gtk, Gdk

import g.core.db.database
import g.core.db.dbphotos
from g.gui.gtk.gtoolbar import GToolBar, GToolButton
from g.gui.gtk.listview import ListView


class MainWindow:
    def __init__(self, treeDb : g.core.db.database.TreeDB, photoDb : g.core.db.dbphotos.DbPhotos, tagDb : g.core.db.database.DBTags):
        self.treeDb = treeDb
        self.tagDb = tagDb
        self.photoDb = photoDb

        builder = Gtk.Builder()
        builder.add_from_file("data/MainWindow.glade")

        window = builder.get_object('MainWindow')

        self.thumbsView = ListView()

        self.treeAlbumsLayout = builder.get_object('treeAlbumsLayout')
        self.treeTagsLayout = builder.get_object('treeTagsLayout')
        self.treeAlbums = builder.get_object('treeAlbums')
        self.treeTags = builder.get_object('treeTags')
        self.mainPane = builder.get_object('mainPane')
        self.subMainPane = builder.get_object('subMainPane')
        self.subMainPane.pack1(self.thumbsView, True, False)
        self.thumbsView.show()
        self.thumbsView.get_resize_mode()
        self.thumbsView.grab_focus()


        self.leftStack = builder.get_object('leftStack')
        self.leftStack.set_visible(False)

        self.iconTags = builder.get_object('iconTags')
        self.labelTags = builder.get_object('labelTags')
        self.mainBoxLayout = builder.get_object('mainBoxLayout')


        buttons = [GToolButton('properties', 'Properties', 'image'),
                GToolButton('metadata', 'Metadata', 'battery'),
                GToolButton('geolocation', 'Geolocation', 'dialog-information')]
        leftToolbarButtons = [GToolButton('albums', 'Albums', 'image'),
                GToolButton('tags', 'Tags', 'accessories-text-editor')]

        self.rightToolBar = GToolBar(buttons)
        self.leftToolBar = GToolBar(leftToolbarButtons)

        self.mainBoxLayout.pack_start(self.rightToolBar, False, False, 0)
        self.mainBoxLayout.pack_start(self.leftToolBar, False, False, 0)
        self.mainBoxLayout.reorder_child(self.leftToolBar, 0)
        self.mainBoxLayout.reorder_child(self.mainPane, 1)
        self.mainBoxLayout.reorder_child(self.rightToolBar, 2)
        self.leftToolBar.connect('selection-changed', self.onLeftToolBarChanged)
        self.rightToolBar.connect('selection-changed', self.onRightToolBarChanged)

        self.treeAlbums.connect('row-activated', self.onAlbumRowActivation)

        window.connect('delete-event', Gtk.main_quit)
        window.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)
        window.show()
        self.initGui()
        Gtk.main()

    def onAlbumRowActivation(self, widget : Gtk.TreeView, p1, column : Gtk.TreeViewColumn):
        treeSelection = widget.get_selection()
        model, iter0 = treeSelection.get_selected()
        albumPath = model.get_value(iter0, 2)
        photos = self.photoDb.getPhotosByPath(albumPath)
        self.thumbsView.set_photos(photos)

    def onRightToolBarChanged(self, _, buttonId):
        print('Right toolbar changed ', buttonId)

    def onLeftToolBarChanged(self, _, buttonId):
        if buttonId is not None:
            self.leftStack.set_visible(True)
            if buttonId == 'albums':
                n = self.leftStack.page_num(self.treeAlbumsLayout)
                self.leftStack.set_current_page(n)
            elif buttonId == 'tags':
                n = self.leftStack.page_num(self.treeTagsLayout)
                self.leftStack.set_current_page(n)
        else:
            self.leftStack.set_visible(False)

    def _fillStore(self, store : Gtk.TreeStore, tree, icon : GdkPixbuf.Pixbuf):
        def helper(storeIter, tr):
            it = store.append(storeIter, [icon, tr.name])
            for child in tr.children:
                helper(it, child)

        helper(None, tree)

    def initGui(self):
        folderIcon = GdkPixbuf.Pixbuf.new_from_file('data/img/folder.png')

        self.updateTreeWidget(self.treeAlbums, self.treeDb.tree, folderIcon)
        self.updateTreeWidget(self.treeTags, self.tagDb.getTagsTree(), folderIcon)

    def updateTreeWidget(self, widget : Gtk.TreeView, tree : g.core.db.database.Tree, icon : GdkPixbuf.Pixbuf):
        def fillStore(st : Gtk.TreeStore, treeStruct, ico : GdkPixbuf.Pixbuf):
            def helper(storeIter, tr):
                p = tr.getFullPath()
                it = st.append(storeIter, [ico, tr.name, p])
                for child in tr.children:
                    helper(it, child)

            helper(None, treeStruct)

        store = Gtk.TreeStore(GdkPixbuf.Pixbuf, str, str)
        fillStore(store, tree, icon)
        widget.set_model(store)

        rendererName = Gtk.CellRendererText()
        rendererIcon = Gtk.CellRendererPixbuf()

        columnIcon = Gtk.TreeViewColumn('Icon', rendererIcon)
        columnIcon.add_attribute(rendererIcon, 'pixbuf', 0)
        columnName = Gtk.TreeViewColumn('Name', rendererName, text=1)

        widget.append_column(columnIcon)
        widget.append_column(columnName)

    @staticmethod
    def start(dbPhotos, dbAlbums, dbTags):
        mw = MainWindow(dbAlbums, dbPhotos, dbTags)
