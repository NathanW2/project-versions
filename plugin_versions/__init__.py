#-----------------------------------------------------------
# Copyright (C) 2015 Martin Dobias
#-----------------------------------------------------------
# Licensed under the terms of GNU GPL 2
# 
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#---------------------------------------------------------------------

import os
import bz2
from PyQt4.QtGui import *
from PyQt4.QtCore import *

import sqlite3

from qgis.core import QgsProject, QgsMessageLog

def classFactory(iface):
    return MinimalPlugin(iface)


def db():
    _db = sqlite3.connect(r"C:\temp\projects.sqlite")
    cur = _db.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS projects (
            name TEXT,
            "save_date" datetime,
            filepath TEXT,
            xml BLOB,
            tag TEXT
        );
    """)
    _db.commit()
    return _db


def save_project(tag=None):

    QgsMessageLog.logMessage("Save projects")
    _db = db()
    filepath = QgsProject.instance().fileName()
    name = os.path.basename(filepath)
    with open(filepath) as f:
        data = f.read()
        data = sqlite3.Binary(bz2.compress(data))
        cur = _db.cursor()
        if not tag:
            tag = ""
        values = (name, filepath, data, tag)
        sql = u"""
            INSERT INTO projects (name, save_date, filepath, xml, tag)
        VALUES(?, CURRENT_TIMESTAMP, ?, ?, ?)
        """
        cur.execute(sql, values)
        _db.commit()


def get_version_xml(name, date):
    sql = "SELECT xml FROM projects WHERE name = ? and save_date = ?";
    rows = db().cursor().execute(sql, (name, date))
    return rows.fetchone()[0]

def current_project():
    filepath = QgsProject.instance().fileName()
    name = os.path.basename(filepath)
    return name

def get_versions(name):
    sql = "SELECT save_date, tag FROM projects WHERE name = ? ORDER BY save_date DESC";
    rows = db().cursor().execute(sql, (name, ))
    return rows


class UIVersions(QDockWidget):
    versionSelected = pyqtSignal(str)

    def __init__(self, parent=None):
        super(UIVersions, self).__init__(parent)
        self.projectList = QListWidget()
        self.setWidget(self.projectList)
        self.projectList.itemClicked.connect(self.updateFromItem)

    def updateFromItem(self, item):
        date = item.data(Qt.UserRole)
        self.versionSelected.emit(date)

    def loadVersions(self, versions):
        self.projectList.clear()
        for version in versions:
            date = version[0]
            tag = version[1]
            if tag:
                name = "{0} ({1})".format(tag, date)
            else:
                name = "{0}".format(date)
            item = QListWidgetItem()
            item.setText(name)
            item.setData(Qt.UserRole, date)
            self.projectList.addItem(item)


class MinimalPlugin:
    def __init__(self, iface):
        self.iface = iface
        self.connect()

    def initGui(self):
        self.menu = QMenu("Project Versions")
        self.projectVersionsAction = QAction("Versions", None, triggered=self.show_versions)
        self.projectSnapshotAction = QAction("Create Snapshot", None, triggered=self.create_tag)
        self.menu.addAction(self.projectSnapshotAction)
        self.menu.addAction(self.projectVersionsAction)
        before = self.iface.fileMenu().actions()[4]
        self.iface.fileMenu().insertMenu(before, self.menu)

        self.dock = UIVersions()
        self.dock.versionSelected.connect(self.loadProject)
        self.iface.addDockWidget(Qt.RightDockWidgetArea, self.dock)
        self.dock.hide()

    def connect(self):
        QgsMessageLog.logMessage("Connected to save_project")
        QgsProject.instance().projectSaved.connect(save_project)
        QgsProject.instance().projectSaved.connect(self.reloadVersions)

    def disconnect(self):
        QgsMessageLog.logMessage("Disconnected to save_project")
        QgsProject.instance().projectSaved.disconnect(save_project)
        QgsProject.instance().projectSaved.disconnect(self.reloadVersions)

    def create_tag(self):
        text, accepted = QInputDialog.getText(self.iface.mainWindow(), "Snapshot Name", "Enter name of the snapshot")
        if not accepted:
            return
        self.disconnect()
        self.iface.actionSaveProject().trigger()
        save_project(text)
        self.reloadVersions()
        self.connect()

    def unload(self):
        QgsProject.instance().projectSaved.disconnect(save_project)

    def reloadVersions(self):
        name = current_project()
        rows = get_versions(name)
        self.dock.loadVersions(rows)

    def show_versions(self):
        self.reloadVersions()
        self.dock.show()

    def loadProject(self, date):
        name = current_project()
        xml = get_version_xml(name, date)
        filepath = QgsProject.instance().fileName()
        data = bz2.decompress(xml)
        with open(filepath, "w+") as f:
            f.write(data)

        self.iface.addProject(filepath)
