from PyQt5.QtWidgets import QWidget, QPushButton, QVBoxLayout, QButtonGroup
from PyQt5.QtCore import pyqtSignal


class GSideToolbar(QWidget):
    selectionChanged = pyqtSignal(str)

    def __init__(self, buttons):
        super().__init__()

        self.selectedId = None

        self.mainLayout = QVBoxLayout(self)
        self.buttonGroup = QButtonGroup()
        self.buttons = {}

        for button in buttons:
            b = QPushButton(button.name)
            self.buttonGroup.addButton(b)
            self.buttonGroup.setId(b, button.id)
            self.buttons[button.id] = b
            self.mainLayout.addWidget(b)

        self.buttonGroup.buttonClicked.connect(self.buttonClicked)

        self.mainLayout.addStretch()

    def buttonState(self, state):
        pass

    def buttonClicked(self, button : QPushButton):
        buttonId = self.buttonGroup.id(button)
        buttonName = self.buttons[buttonId].text()
        self.selectionChanged.emit(buttonName)

    @staticmethod
    def createButton(text, icon):
        pass

