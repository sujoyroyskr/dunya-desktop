import os
import platform
import json

from PyQt4 import QtGui, QtCore

from dunyadesktop_app.utilities import database
from progressbar import ProgressBar

if platform.system() == 'Linux':
    FONT_SIZE = 9
else:
    FONT_SIZE = 12

CSS_PATH = os.path.join(os.path.dirname(__file__), '..', 'ui_files', 'css',
                        'tableview.css')

DOCS_PATH = os.path.join(os.path.dirname(__file__), '..', 'cultures',
                         'documents')


DUNYA_ICON = os.path.join(os.path.dirname(__file__), '..', 'ui_files',
                          'icons', 'dunya.svg')
CHECK_ICON = os.path.join(os.path.dirname(__file__), '..', 'ui_files',
                          'icons', 'tick-inside-circle.svg')


class TableView(QtGui.QTableView):
    def __init__(self, *__args):
        QtGui.QTableView.__init__(self, *__args)

        # setting the table for no edit and row selection
        self.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
        self.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        #self.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
        self.setMouseTracking(True)
        self.horizontalHeader().setStretchLastSection(True)
        font = QtGui.QFont()
        font.setPointSize(13)
        self.horizontalHeader().setFont(font)

        # hiding the vertical headers
        self.verticalHeader().hide()

        # arranging the artist column for being multi-line
        self.setWordWrap(True)
        self.setTextElideMode(QtCore.Qt.ElideMiddle)

        self._last_index = QtCore.QPersistentModelIndex()
        self.viewport().installEventFilter(self)

        self._set_css()
        self._set_font()

    def _set_font(self):
        font = QtGui.QFont()
        font.setPointSize(FONT_SIZE)
        self.setFont(font)

    def _set_css(self):
        with open(CSS_PATH) as f:
            css = f.read()
        self.setStyleSheet(css)


class TableViewResults(TableView):
    """Table view widget of query results."""
    def __init__(self, parent=None):
        TableView.__init__(self)
        self.setSortingEnabled(True)
        self.setDragDropMode(QtGui.QAbstractItemView.DragOnly)

        self.horizontal_header = self.horizontalHeader()
        self._set_horizontal_header()

        self.menu = QtGui.QMenu(self)
        self._set_menu()
        self.add_maincoll = QtGui.QAction("Add to main collection", self)

        self.setColumnWidth(0, 10)

        self.open_dunya = QtGui.QAction("Open on Player", self)
        self.open_dunya.setIcon(QtGui.QIcon(DUNYA_ICON))

        self.menu.addAction(self.add_maincoll)
        self.menu.addAction(self.open_dunya)

    def _set_menu(self):
        self.add_maincoll = QtGui.QAction("Add to main collection", self)

        self.menu.addSeparator()

        self.open_dunya = QtGui.QAction("Open on Player", self)
        self.open_dunya.setIcon(QtGui.QIcon(DUNYA_ICON))

    def _set_horizontal_header(self):
        self.horizontal_header.setStretchLastSection(True)
        self.horizontal_header.hide()
        self.horizontal_header.setResizeMode(QtGui.QHeaderView.Fixed)

    def contextMenuEvent(self, event):
        """Pops up the context menu when the right button is clicked."""
        if self.selectionModel().selection().indexes():
            for index in self.selectionModel().selection().indexes():
                row, column = index.row(), index.column()
        self.index = index
        self.menu.popup(QtGui.QCursor.pos())

    def get_selected_rows(self):
        selected_rows = []
        for item in self.selectionModel().selectedRows():
            if item.row() not in selected_rows:
                selected_rows.append(item)
        return selected_rows


class TableWidget(QtGui.QTableWidget, TableView):
    added_new_doc = QtCore.pyqtSignal(list)

    def __init__(self):
        QtGui.QTableWidget.__init__(self)
        TableView.__init__(self)
        self.setDragDropMode(QtGui.QAbstractItemView.DropOnly)
        self.setAcceptDrops(True)
        self.setDragDropOverwriteMode(False)

        self._set_columns()
        self.setDisabled(True)

        self.recordings = []
        self.indexes = {}
        self.coll = ''

    def _set_columns(self):
        self.setColumnCount(2)
        self.setHorizontalHeaderLabels(['Status', 'Title'])
        self.horizontalHeader().setResizeMode(QtGui.QHeaderView.Fixed)

    def dropMimeData(self, p_int, p_int_1, QMimeData, Qt_DropAction):
        self.last_drop_row = p_int
        return True

    def dropEvent(self, event):
        # The QTableWidget from which selected rows will be moved
        sender = event.source()

        # Default dropEvent method fires dropMimeData with appropriate
        # parameters (we're interested in the row index).
        super(QtGui.QTableWidget, self).dropEvent(event)
        # Now we know where to insert selected row(s)
        drop_row = self.last_drop_row
        selected_rows = sender.get_selected_rows()

        selected_rows_index = [item.row() for item in selected_rows]

        # if sender == receiver (self), after creating new empty rows selected
        # rows might change their locations
        sel_rows_offsets = [0 if self != sender or srow < drop_row
                            else len(selected_rows_index) for srow in
                            selected_rows_index]
        selected_rows_index = [row + offset for row, offset
                               in zip(selected_rows_index, sel_rows_offsets)]

        # copy content of selected rows into empty ones
        docs = []
        conn, c = database.connect()
        for i, srow in enumerate(selected_rows):
            source_index = sender.model().mapToSource(srow)
            if database.add_doc_to_coll(
                    conn, c, self.recordings[source_index.row()], self.coll):

                item = sender.model().sourceModel().item(selected_rows_index[i], 1)
                if item:
                    source = QtGui.QTableWidgetItem(item.text())
                    self.insertRow(drop_row + i)
                    self.setItem(drop_row + i, 1, source)
                    docs.append(self.recordings[source_index.row()])
                    self.indexes[self.recordings[source_index.row()]] = drop_row + i
        if docs:
            self.added_new_doc.emit(docs)
        event.accept()

    def create_table(self, coll):
        # first cleans the table, sets the columns and enables the widget
        self.setRowCount(0)

        self._set_columns()
        self.setEnabled(True)

        for i, item in enumerate(coll):
            set_check = False
            path = os.path.join(DOCS_PATH, item,
                                'audioanalysis--metadata.json')
            try:
                metadata = json.load(open(path))
                cell = QtGui.QTableWidgetItem(metadata['title'])
                set_check = True
            except IOError:
                print("Needs to be downloaded {0}".format(item))
                cell = QtGui.QTableWidgetItem(item)
            self.insertRow(self.rowCount())
            self.setItem(i, 1, cell)
            self.setColumnWidth(0, 60)
            if set_check:
                self.set_checked(self.rowCount()-1)

    def set_progress_bar(self, status):
        docid = status.docid
        step = status.step
        n_progress = status.n_progress

        progress_bar = self.cellWidget(self.indexes[docid], 0)
        if not progress_bar:
            self.setCellWidget(self.indexes[docid], 0, ProgressBar(self))
            progress_bar = self.cellWidget(self.indexes[docid], 0)

        if not step == n_progress:
            progress_bar.update_progress_bar(step, n_progress)
        else:
            print('checked')
            self.set_checked(self.indexes[docid])

    def set_checked(self, raw):
        item = QtGui.QLabel()
        item.setAlignment(QtCore.Qt.AlignCenter)
        icon = QtGui.QPixmap(CHECK_ICON).scaled(20, 20,
                                                QtCore.Qt.KeepAspectRatio,
                                                QtCore.Qt.SmoothTransformation)
        item.setPixmap(icon)
        self.setCellWidget(raw, 0, item)
