import sys

from PyQt5.QtGui import QIcon
from PyQt5.uic import loadUi
from PyQt5.QtWidgets import QApplication, QMainWindow, QTreeWidgetItem, QTreeWidget
from g.gui.qt.gsidetoolbar import GSideToolbar
from g.gui.qt.thumbview import ThumbView
from g.core.tree import Tree


class SideBarButton:
    def __init__(self, name, buttonId, icon):
        assert type(buttonId) == int;
        assert type(name) == str

        self.id = buttonId
        self.name = name
        self.icon = icon


class MainWindow(QMainWindow):
    def __init__(self, *args, parent=None):
        super(MainWindow, self).__init__()

        self.dbPhotos = args[0]
        ''' :type DbPhotos'''
        self.dbTags = args[2]

        loadUi('data/mainwindow.ui', self)

        leftToolbarButtons = [SideBarButton('Albums', 1, 'image'),
                SideBarButton('Tags', 2, 'image')]
        rightToolbarButtons = [SideBarButton('Properties', 1, 'image'),
                SideBarButton('Metadata', 2, 'image')]
        self.leftSideToolbar = GSideToolbar(leftToolbarButtons)
        self.leftSideToolbar.selectionChanged.connect(self.onLeftSideToolChange)
        self.rightSideToolbar = GSideToolbar(rightToolbarButtons)

        self.centralLayout.insertWidget(-1, self.rightSideToolbar)
        self.centralLayout.insertWidget(0, self.leftSideToolbar)


        self.thumbView = ThumbView()
        self.splitterThumbs.addWidget(self.thumbView)

        self.stackLeftActivateAlbums()
        albumsTreeData = self.dbPhotos.getAlbumTree()

        self.treeAlbums.headerItem().setText(0, 'Albums')
        self.fillTreeWidget(self.treeAlbums, albumsTreeData)


    def setAlbumsTree(self):
        pass

    def stackLeftActivateAlbums(self):
        self.stackLeft.setCurrentWidget(self.treeAlbums)

    def stackLeftActivateTags(self):
        self.stackLeft.setCurrentWidget(self.treeTags)

    def fillTreeWidget(self, widget : QTreeWidget, tree : Tree):
        def helper(t : Tree, parent):
            item = QTreeWidgetItem()
            item.setText(0, t.name)
            item.setIcon(0, QIcon('data/gfx/folder.png'))
            if type(parent) == QTreeWidget:
                parent.insertTopLevelItem(0, item)
            else:
                parent.addChild(item)
            for ch in t.children:
                helper(ch, item)

        widget.setColumnCount(1)
        helper(tree, widget)

    def onLeftSideToolChange(self, buttonId):
        if buttonId == 'Albums':
            print('Albums!!')
            items = [i for i in range(100)]
            self.thumbView.setItems(items)
        else:
            print('Button clicked: ', buttonId)

    @staticmethod
    def start(*args):
        app = QApplication(sys.argv)

        w = MainWindow(*args)
        w.show()

        sys.exit(app.exec_())
