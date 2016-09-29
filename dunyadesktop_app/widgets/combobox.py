from __future__ import absolute_import
from __future__ import print_function
import os
import platform

from PyQt4 import QtGui, QtCore

from .filteringdialog import FilteringDialog

if platform.system() == 'Linux':
    BUTTON_POS = 9
    FONT_SIZE = 9
    CSS_PATH = os.path.join(os.path.dirname(__file__), '..', 'ui_files', 'css',
                            'combobox.css')
else:
    CSS_PATH = os.path.join(os.path.dirname(__file__), '..', 'ui_files', 'css',
                            'combobox_mac.css')
    BUTTON_POS = 18
    FONT_SIZE = 11

ICON_PATH_CANCEL = os.path.join(os.path.dirname(__file__), '..', 'ui_files',
                                'icons', 'cancel-music.svg')

CSS_BUTTON = '''QToolButton {border: 0px;
                             padding: 0px;}
                QToolButton:hover{background-color: #c7dde0;
                                  border-radius: 5px;}'''

class ComboBox(QtGui.QComboBox):
    def __init__(self, parent):
        QtGui.QComboBox.__init__(self, parent)
        self.setEditable(True)
        self.setInsertPolicy(QtGui.QComboBox.NoInsert)

        if platform.system() == 'Linux':
            self.setFixedHeight(23)

        self._set_css()

        self.cancel_button = QtGui.QToolButton(self)
        self.cancel_button.setStyleSheet(CSS_BUTTON)
        self.cancel_button.setIcon(QtGui.QIcon(ICON_PATH_CANCEL))
        self.cancel_button.setVisible(False)

        # signals
        self.currentIndexChanged.connect(self.change_lineedit_status)
        self.cancel_button.clicked.connect(self.reset_attribute_selection)
        self.lineEdit().textEdited.connect(lambda:
                                           self.cancel_button.setVisible(True))
        self.lineEdit().editingFinished.connect(self.check_lineedit_status)
        self.dialog_filtering = FilteringDialog()
        self.dialog_filtering.ok_button_clicked.connect(
            lambda: self.set_selection(self.dialog_filtering.selection))

    def _set_css(self):
        with open(CSS_PATH) as f:
            css = f.read()
        self.setStyleSheet(css)

    def resizeEvent(self, QResizeEvent):
        button_size = self.cancel_button.sizeHint()
        frame_width = self.lineEdit().style().pixelMetric(
                                            QtGui.QStyle.PM_DefaultFrameWidth)
        self.cancel_button.move(
                self.rect().right()-BUTTON_POS*frame_width-button_size.width(),
                        (self.rect().bottom()-button_size.height() + 1) / 2)
        super(ComboBox, self).resizeEvent(QResizeEvent)

    def wheelEvent(self, QWheelEvent):
        pass

    def mousePressEvent(self, QMouseEvent):
        self.dialog_filtering.attribute = self.attribute
        self.dialog_filtering.setWindowTitle("")
        self.dialog_filtering.filtering_model.add_items(self.attribute)
        self.dialog_filtering.move(QMouseEvent.globalPos().x(),
                                   QMouseEvent.globalPos().y())
        self.dialog_filtering.exec_()

    def set_placeholder_text(self, text):
        font = QtGui.QFont()
        font.setPointSize(FONT_SIZE)

        self.lineEdit().setPlaceholderText(text)
        self.lineEdit().setFont(font)

    def add_items(self, attribute):
        self.attribute = attribute
        for att in self.attribute:
            self.addItem(att['name'])
        self.setCurrentIndex(-1)

    def get_attribute_id(self):
        index = self.currentIndex()
        if index is not -1:
            try:
                return self.attribute[index]['uuid']
            except:
                return self.attribute[index]['mbid']
        else:
            return ''

    def set_selection(self, index):
        try:
            index_row = index.row()
        except:
            index_row = index
        self.setCurrentIndex(index_row)
        self.lineEdit().setText(self.attribute[index_row]['name'])
        self.cancel_button.setVisible(True)

    def reset_attribute_selection(self):
        self.lineEdit().setText('')
        self.setCurrentIndex(-1)
        self.cancel_button.setVisible(False)

    def change_lineedit_status(self):
        if self.currentIndex() is not -1:
            self.lineEdit().setReadOnly(True)
            self.change_background("#F3F4E3;")
        else:
            self.lineEdit().setReadOnly(False)
            self.change_background()

    def change_background(self, color=''):
        self.lineEdit().setStyleSheet("background-color: {0};".format(color))

    def check_lineedit_status(self):
        if str(self.lineEdit().text().toUtf8()) == '':
            self.cancel_button.setVisible(False)
