from gi.repository import Gtk
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

        self.albumTree = builder.get_object('albumTree')
        self.tagTree = builder.get_object('tagTree')
        ''' :type : Gtk.Paned '''
        self.mainPane = builder.get_object('mainPane')
        self.mainPane.pack2(self.thumbsView, True, True)

        window.show_all()
        self.initGui()

        Gtk.main()

    def _fillStore(self, store : Gtk.TreeStore, tree, icon : GdkPixbuf.Pixbuf):
        def helper(iter, tr):
            it = store.append(iter, [icon, tr.name])
            for child in tr.children:
                helper(it, child)

        helper(None, tree)

    def initGui(self):
        folderIcon = GdkPixbuf.Pixbuf.new_from_file('data/img/folder.png')

        self.updateTreeWidget(self.albumTree, self.treeDb.tree, folderIcon)
        self.updateTreeWidget(self.tagTree, self.tagDb.getTagsTree(), folderIcon)

    def updateTreeWidget(self, widget : Gtk.TreeView, tree : g.db.Tree, icon : GdkPixbuf.Pixbuf):
        store = Gtk.TreeStore(GdkPixbuf.Pixbuf, str)
        self._fillStore(store, tree, icon)
        widget.set_model(store)

        rendererName = Gtk.CellRendererText()
        rendererIcon = Gtk.CellRendererPixbuf()

        columnIcon = Gtk.TreeViewColumn('Icon', rendererIcon)
        columnIcon.add_attribute(rendererIcon, 'pixbuf', 0)
        columnName = Gtk.TreeViewColumn('Name', rendererName, text=1)

        widget.append_column(columnIcon)
        widget.append_column(columnName)
