from PySide6 import QtWidgets, QtGui, QtCore
from PySide6.QtWidgets import QFileDialog, QMessageBox, QSystemTrayIcon, QMenu
import sys
import os
import sqlite3
from pandian import init_db, import_data_file, export_checked_file, export_unchecked_file, export_all_file


def get_resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath('.')
    return os.path.join(base_path, relative_path)


class MainWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('固定资产盘点系统')
        self.resize(600, 420)
        init_db()
        self.init_ui()
        self.init_tray()

    def init_tray(self):
        icon_path = get_resource_path('icon.ico')
        icon = QtGui.QIcon(icon_path)
        
        if icon.isNull():
            pixmap = QtGui.QPixmap(32, 32)
            pixmap.fill(QtGui.QColor(33, 150, 243))
            painter = QtGui.QPainter(pixmap)
            painter.setPen(QtGui.QColor(255, 255, 255))
            painter.setFont(QtGui.QFont('Arial', 14, QtGui.QFont.Bold))
            painter.drawText(pixmap.rect(), QtCore.Qt.AlignCenter, 'P')
            painter.end()
            icon = QtGui.QIcon(pixmap)
        
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(icon)
        self.tray_icon.setToolTip('固定资产盘点系统')
        
        tray_menu = QMenu(self)
        show_action = tray_menu.addAction('显示窗口')
        show_action.triggered.connect(self.show_window)
        quit_action = tray_menu.addAction('退出')
        quit_action.triggered.connect(self.quit_app)
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self.on_tray_activated)
        
        if QSystemTrayIcon.isSystemTrayAvailable():
            self.tray_icon.show()

    def on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.Trigger or reason == QSystemTrayIcon.DoubleClick:
            self.show_window()

    def show_window(self):
        self.show()
        self.raise_()
        self.activateWindow()

    def quit_app(self):
        self.tray_icon.hide()
        QtWidgets.QApplication.quit()

    def closeEvent(self, event):
        event.ignore()
        self.hide()
        self.tray_icon.showMessage('固定资产盘点系统', '程序已最小化到托盘')

    def init_ui(self):
        layout = QtWidgets.QVBoxLayout()
        layout.setSpacing(10)

        self.setStyleSheet('''
            QWidget { background-color: white; color: #333; }
            QGroupBox { border: 1px solid #ccc; border-radius: 5px; padding: 10px; font-weight: bold; }
            QLabel { background-color: transparent; }
            QLineEdit { border: 1px solid #ccc; border-radius: 3px; padding: 5px; background-color: white; color: #333; }
            QPushButton { background-color: #f0f0f0; border: 1px solid #ccc; border-radius: 3px; padding: 5px 15px; color: #333; }
            QPushButton:hover { background-color: #e0e0e0; }
        ''')

        top_bar = QtWidgets.QHBoxLayout()
        btn_import = QtWidgets.QPushButton('导入数据')
        btn_import.setFixedSize(80, 28)
        btn_import.clicked.connect(self.handle_import)
        top_bar.addWidget(btn_import)
        top_bar.addStretch()
        layout.addLayout(top_bar)

        # Stats
        stats_group = QtWidgets.QGroupBox('盘点统计')
        sg_layout = QtWidgets.QHBoxLayout()

        total_layout = QtWidgets.QVBoxLayout()
        total_label = QtWidgets.QLabel('总固资数量')
        total_label.setAlignment(QtCore.Qt.AlignCenter)
        self.total_count = QtWidgets.QLabel('0')
        self.total_count.setAlignment(QtCore.Qt.AlignCenter)
        font = QtGui.QFont()
        font.setBold(True)
        font.setPointSize(24)
        self.total_count.setFont(font)
        total_layout.addWidget(total_label)
        total_layout.addWidget(self.total_count)
        sg_layout.addLayout(total_layout)

        checked_layout = QtWidgets.QVBoxLayout()
        checked_label = QtWidgets.QLabel('已盘点数量')
        checked_label.setAlignment(QtCore.Qt.AlignCenter)
        self.checked_count = QtWidgets.QLabel('0')
        self.checked_count.setAlignment(QtCore.Qt.AlignCenter)
        self.checked_count.setFont(font)
        self.checked_count.setStyleSheet('color: green;')
        checked_layout.addWidget(checked_label)
        checked_layout.addWidget(self.checked_count)
        sg_layout.addLayout(checked_layout)

        unchecked_layout = QtWidgets.QVBoxLayout()
        unchecked_label = QtWidgets.QLabel('待盘点数量')
        unchecked_label.setAlignment(QtCore.Qt.AlignCenter)
        self.unchecked_count = QtWidgets.QLabel('0')
        self.unchecked_count.setAlignment(QtCore.Qt.AlignCenter)
        self.unchecked_count.setFont(font)
        self.unchecked_count.setStyleSheet('color: red;')
        unchecked_layout.addWidget(unchecked_label)
        unchecked_layout.addWidget(self.unchecked_count)
        sg_layout.addLayout(unchecked_layout)

        stats_group.setLayout(sg_layout)
        layout.addWidget(stats_group)

        # Check
        check_group = QtWidgets.QGroupBox('资产盘点')
        cg_layout = QtWidgets.QGridLayout()
        cg_layout.setSpacing(10)

        cg_layout.addWidget(QtWidgets.QLabel('主资产编号：'), 0, 0)
        self.asset_id_edit = QtWidgets.QLineEdit()
        self.asset_id_edit.setFixedHeight(36)
        self.asset_id_edit.returnPressed.connect(self.handle_query)
        cg_layout.addWidget(self.asset_id_edit, 0, 1)
        btn_query = QtWidgets.QPushButton('查询')
        btn_query.setFixedHeight(36)
        btn_query.clicked.connect(self.handle_query)
        cg_layout.addWidget(btn_query, 0, 2)

        cg_layout.addWidget(QtWidgets.QLabel('资产名称：'), 1, 0)
        self.asset_name_lbl = QtWidgets.QLineEdit()
        self.asset_name_lbl.setReadOnly(True)
        self.asset_name_lbl.setFixedHeight(36)
        cg_layout.addWidget(self.asset_name_lbl, 1, 1, 1, 2)

        cg_layout.addWidget(QtWidgets.QLabel('责任人：'), 2, 0)
        self.owner_name_lbl = QtWidgets.QLineEdit()
        self.owner_name_lbl.setReadOnly(True)
        self.owner_name_lbl.setFixedHeight(36)
        cg_layout.addWidget(self.owner_name_lbl, 2, 1, 1, 2)

        cg_layout.addWidget(QtWidgets.QLabel('2025位置：'), 3, 0)
        self.loc2025_lbl = QtWidgets.QLineEdit()
        self.loc2025_lbl.setReadOnly(True)
        self.loc2025_lbl.setFixedHeight(36)
        cg_layout.addWidget(self.loc2025_lbl, 3, 1, 1, 2)

        cg_layout.addWidget(QtWidgets.QLabel('2026位置：'), 4, 0)
        self.loc2026_edit = QtWidgets.QLineEdit()
        self.loc2026_edit.setFixedHeight(36)
        cg_layout.addWidget(self.loc2026_edit, 4, 1)
        btn_save = QtWidgets.QPushButton('保存')
        btn_save.setFixedHeight(36)
        btn_save.clicked.connect(self.handle_save)
        cg_layout.addWidget(btn_save, 4, 2)

        check_group.setLayout(cg_layout)
        layout.addWidget(check_group)

        # Export
        export_group = QtWidgets.QGroupBox('报表导出')
        eg_layout = QtWidgets.QHBoxLayout()
        eg_layout.setSpacing(8)

        btn_checked = QtWidgets.QPushButton('已盘点资产')
        btn_checked.setFixedHeight(36)
        btn_checked.clicked.connect(self.export_checked)
        eg_layout.addWidget(btn_checked)

        btn_unchecked = QtWidgets.QPushButton('未盘点资产')
        btn_unchecked.setFixedHeight(36)
        btn_unchecked.clicked.connect(self.export_unchecked)
        eg_layout.addWidget(btn_unchecked)

        btn_all = QtWidgets.QPushButton('全量报表')
        btn_all.setFixedHeight(36)
        btn_all.clicked.connect(self.export_all)
        eg_layout.addWidget(btn_all)

        export_group.setLayout(eg_layout)
        layout.addWidget(export_group)

        self.setLayout(layout)
        self.update_stats()

    def update_stats(self):
        conn = sqlite3.connect('fixed_asset.db')
        c = conn.cursor()
        c.execute('SELECT COUNT(*) FROM assets')
        total = c.fetchone()[0]
        c.execute('SELECT COUNT(*) FROM assets WHERE is_checked = 1')
        checked = c.fetchone()[0]
        conn.close()
        self.total_count.setText(str(total))
        self.checked_count.setText(str(checked))
        self.unchecked_count.setText(str(total - checked))

    def handle_import(self):
        path, _ = QFileDialog.getOpenFileName(self, '选择Excel文件', filter='Excel Files (*.xlsx *.xls)')
        if not path:
            return
        ok = import_data_file(path)
        if ok:
            QMessageBox.information(self, '成功', '数据导入完成')
            self.update_stats()
        else:
            QMessageBox.critical(self, '错误', '导入失败')

    def handle_query(self):
        asset_id = self.asset_id_edit.text().strip()
        if not asset_id:
            QMessageBox.warning(self, '警告', '请输入主资产编号')
            return
        conn = sqlite3.connect('fixed_asset.db')
        c = conn.cursor()
        c.execute('SELECT asset_name, owner_name, location_2025, location_2026 FROM assets WHERE main_asset_id = ?', (asset_id,))
        r = c.fetchone()
        conn.close()
        if r:
            self.asset_name_lbl.setText(str(r[0] or ''))
            self.owner_name_lbl.setText(str(r[1] or ''))
            self.loc2025_lbl.setText(str(r[2] or ''))
            self.loc2026_edit.setText(str(r[3] or ''))
        else:
            QMessageBox.information(self, '提示', '未找到该资产')

    def handle_save(self):
        asset_id = self.asset_id_edit.text().strip()
        loc2026 = self.loc2026_edit.text().strip()
        if not asset_id:
            QMessageBox.warning(self, '警告', '请先查询资产')
            return
        if not loc2026:
            QMessageBox.warning(self, '警告', '请输入2026位置')
            return
        try:
            conn = sqlite3.connect('fixed_asset.db')
            c = conn.cursor()
            c.execute('UPDATE assets SET location_2026 = ?, is_checked = 1 WHERE main_asset_id = ?', (loc2026, asset_id))
            conn.commit()
            conn.close()
            QMessageBox.information(self, '成功', '保存成功')
            self.asset_id_edit.clear()
            self.asset_name_lbl.clear()
            self.owner_name_lbl.clear()
            self.loc2025_lbl.clear()
            self.loc2026_edit.clear()
            self.asset_id_edit.setFocus()
            self.update_stats()
        except Exception as e:
            QMessageBox.critical(self, '错误', str(e))

    def export_checked(self):
        path, _ = QFileDialog.getSaveFileName(self, '保存已盘点报表', '已盘点.xlsx', filter='Excel Files (*.xlsx)')
        if path:
            export_checked_file(path)
            QMessageBox.information(self, '成功', '已导出')

    def export_unchecked(self):
        path, _ = QFileDialog.getSaveFileName(self, '保存未盘点报表', '未盘点.xlsx', filter='Excel Files (*.xlsx)')
        if path:
            export_unchecked_file(path)
            QMessageBox.information(self, '成功', '已导出')

    def export_all(self):
        path, _ = QFileDialog.getSaveFileName(self, '保存全量报表', '全量.xlsx', filter='Excel Files (*.xlsx)')
        if path:
            export_all_file(path)
            QMessageBox.information(self, '成功', '已导出')


def main():
    app = QtWidgets.QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
