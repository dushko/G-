from gi.repository import Gtk, Gdk
from gi.repository import GdkPixbuf

import g.db
from g.gui.gtk.listview import ListView

class MainWindow:
    def __init__(self, treeDb : g.db.TreeDB, tagDb : g.db.DBTags):
        self.treeDb = treeDb
        self.tagDb = tagDb

        builder = Gtk.Builder()
        builder.add_from_file("data/MainWindow.glade")

        window = builder.get_object('MainWindow')

        self.thumbsView = ListView()

        self.treeAlbums = builder.get_object('treeAlbums')
        self.treeTags = builder.get_object('treeTags')
        self.subMainPane = builder.get_object('subMainPane')
        self.subMainPane.pack1(self.thumbsView, True, True)

        self.leftStack = builder.get_object('leftStack')


        self.toolAlbumsEventBox = builder.get_object('toolAlbumsEventBox')
        self.toolAlbumsFrame = builder.get_object('toolAlbumsFrame')
        self.toolAlbumsLabel = builder.get_object('labelAlbums')
        self.toolAlbumsIcon = builder.get_object('iconAlbums')

        # self.toolTagsEventBox = builder.get_object('toolTagsEventBox')
        # self.toolTagsFrame = builder.get_object('toolTagsFrame')

        self.toolAlbumsEventBox.connect('button-press-event', self.onToolAlbumsPress)

        self.iconTags = builder.get_object('iconTags')
        self.labelTags = builder.get_object('labelTags')

        window.connect('delete-event', Gtk.main_quit)
        window.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)
        window.show()
        self.initGui()

        Gtk.main()

    def onToolAlbumsPress(self, widget : Gtk.Widget, event, *data):

        if self.toolAlbumsLabel.is_visible():
            self.toolAlbumsLabel.set_visible(False)
            self.toolAlbumsFrame.set_shadow_type(Gtk.ShadowType.NONE)
            self.leftStack.set_visible(False)
        else:
            self.toolAlbumsLabel.set_visible(True)
            self.toolAlbumsFrame.set_shadow_type(Gtk.ShadowType.ETCHED_IN)
            self.leftStack.set_visible(True)
            n = self.leftStack.page_num(self.treeAlbums)
            self.leftStack.set_current_page(n)
            self.leftStack.set_visible(True)


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

    def updateTreeWidget(self, widget : Gtk.TreeView, tree : g.db.Tree, icon : GdkPixbuf.Pixbuf):
        def fillStore(st : Gtk.TreeStore, treeStruct, ico : GdkPixbuf.Pixbuf):
            def helper(storeIter, tr):
                it = st.append(storeIter, [ico, tr.name])
                for child in tr.children:
                    helper(it, child)

            helper(None, treeStruct)

        store = Gtk.TreeStore(GdkPixbuf.Pixbuf, str)
        fillStore(store, tree, icon)
        widget.set_model(store)

        rendererName = Gtk.CellRendererText()
        rendererIcon = Gtk.CellRendererPixbuf()

        columnIcon = Gtk.TreeViewColumn('Icon', rendererIcon)
        columnIcon.add_attribute(rendererIcon, 'pixbuf', 0)
        columnName = Gtk.TreeViewColumn('Name', rendererName, text=1)

        widget.append_column(columnIcon)
        widget.append_column(columnName)
