#!/usr/bin/env python

import sys
from dotmap import DotMap

from PyQt5.QtWidgets import QApplication, QLabel, QFrame, QMainWindow, QPushButton, QAction, QMessageBox
import PyQt5.QtWidgets as QW
import PyQt5.QtGui as QG
from PyQt5.QtCore import Qt

from generate import AsmodeusGenerate

class AsmoGUI():

    def __init__(self):
        self.app = QApplication(sys.argv)

        self.frame = QFrame()
        self.mainWindow = MainWindow()
        self.mainWindow.setCentralWidget(self.frame)

        self.mainWindow.showMaximized()

        self.app.exec_()

    
class WindowGenerate(QW.QDialog):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowTitle('Generate meteoroids')


        layout = QW.QHBoxLayout()
        self.countLabel = QLabel('Count:')
        self.countLabel.setAlignment(Qt.AlignLeft)
        layout.addWidget(self.countLabel)
        self.count = QW.QSpinBox()
        self.count.setMinimum(0)
        self.count.setMaximum(1000000)
        layout.addWidget(self.count)
        
        self.setLayout(layout)

        combo = QW.QComboBox(self)
        combo.addItem('Uniform')
        combo.addItem('Pareto')
        combo.move(50, 50)

        self.buttons = QW.QDialogButtonBox(QW.QDialogButtonBox.Ok | QW.QDialogButtonBox.Cancel, Qt.Horizontal, self)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)

        #self.resize(1000, 1000)

class MainWindow(QMainWindow):
    version = '0.0.1'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowTitle('Asmodeus GUI')


        self.buildMenu({
            'Program': {
                'About': {
                    'connect': self.showAbout,
                },
                'Quit': {
                    'shortcut': 'Ctrl+Q',
                    'connect': self.close,
                },
            },
            'Dataset': {
                'New': {
                    'shortcut': 'Ctrl+N',
                    'connect': self.showNewDataset,
                },
                'Load': {
                    'shortcut': 'Ctrl+O',
                    'connect': self.loadDataset,
                },
                'Save': {
                    'shortcut': 'Ctrl+S',
                    'connect': self.saveDataset,
                },
            }
        })

        self.windowGenerate = WindowGenerate()

    def buildMenu(self, menuDict):
        self.menu = self.menuBar()

        menuMap = DotMap(menuDict)

        for menu, items in menuMap.items():
            new = self.menu.addMenu(menu)
            for item, properties in items.items():
                button = QAction(QG.QIcon('exit24.png'), item, self)
                button.setStatusTip(item)
                if 'connect' in properties:
                    button.triggered.connect(properties.connect)
                if 'shortcut' in properties:
                    button.setShortcut(properties.shortcut)

                new.addAction(button)

    def loadDataset(self):
        pass

    def saveDataset(self):
        pass

    def showAbout(self):
        message = QMessageBox()
        message.setIcon(QMessageBox.Information)
        message.setText(f"Asmodeus GUI, version {self.version}")
        message.setInformativeText("Just learning")
        message.setWindowTitle("About")
        message.setStandardButtons(QMessageBox.Ok)
        message.exec_()

    def showNewDataset(self):
        self.windowGenerate.show()

gui = AsmoGUI()
