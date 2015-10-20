from gi.repository import Gtk
from gi.repository import GdkPixbuf

class MainWindow:
    def __init__(self, treeDb):
        self.treeDb = treeDb


        builder = Gtk.Builder()
        builder.add_from_file("data/MainWindow.glade")
        window = builder.get_object('MainWindow')


        self.albumTree = builder.get_object('albumTree')

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

        store = Gtk.TreeStore(GdkPixbuf.Pixbuf, str)
        self._fillStore(store, self.treeDb.tree, folderIcon)
        self.albumTree.set_model(store)

        rendererName = Gtk.CellRendererText()
        rendererIcon = Gtk.CellRendererPixbuf()

        columnIcon = Gtk.TreeViewColumn('Icon', rendererIcon)
        columnIcon.add_attribute(rendererIcon, 'pixbuf', 0)
        columnName = Gtk.TreeViewColumn("Name", rendererName, text=1)

        self.albumTree.append_column(columnIcon)
        self.albumTree.append_column(columnName)


