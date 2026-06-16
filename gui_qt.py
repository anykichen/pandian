from PySide6 import QtWidgets, QtGui
from PySide6.QtWidgets import QFileDialog, QMessageBox, QSystemTrayIcon, QMenu
import sys
import sqlite3
import os
from pandian import init_db, import_data_file, export_checked_file, export_unchecked_file, export_all_file


class MainWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('固定资产盘点系统')
        self.setFixedSize(700, 420)
        self.init_ui()
        self.init_tray()
        init_db()

    def init_tray(self):
        # 创建托盘图标
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QtGui.QIcon('icon.ico'))
        self.tray_icon.setToolTip('固定资产盘点系统')

        # 托盘菜单
        tray_menu = QMenu()
        show_action = tray_menu.addAction('显示窗口')
        show_action.triggered.connect(self.show_window)
        quit_action = tray_menu.addAction('退出')
        quit_action.triggered.connect(self.quit_app)
        self.tray_icon.setContextMenu(tray_menu)

        # 点击托盘图标显示窗口
        self.tray_icon.activated.connect(self.on_tray_activated)
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
        # 关闭窗口时最小化到托盘
        event.ignore()
        self.hide()
        self.tray_icon.showMessage('固定资产盘点系统', '程序已最小化到托盘，点击托盘图标可重新显示')

    def init_ui(self):
        layout = QtWidgets.QVBoxLayout()

        # Import section
        import_group = QtWidgets.QGroupBox('1. 固定资产数据导入')
        ig_layout = QtWidgets.QHBoxLayout()
        btn_import = QtWidgets.QPushButton('选择Excel文件并导入')
        btn_import.clicked.connect(self.handle_import)
        ig_layout.addWidget(btn_import)
        import_group.setLayout(ig_layout)
        layout.addWidget(import_group)

        # Check section
        check_group = QtWidgets.QGroupBox('2. 资产盘点操作')
        cg_layout = QtWidgets.QGridLayout()
        cg_layout.addWidget(QtWidgets.QLabel('主资产编号：'), 0, 0)
        self.asset_id_edit = QtWidgets.QLineEdit()
        self.asset_id_edit.returnPressed.connect(self.handle_query)
        cg_layout.addWidget(self.asset_id_edit, 0, 1)
        btn_query = QtWidgets.QPushButton('查询资产')
        btn_query.clicked.connect(self.handle_query)
        cg_layout.addWidget(btn_query, 0, 2)

        cg_layout.addWidget(QtWidgets.QLabel('资产名称：'), 1, 0)
        self.asset_name_lbl = QtWidgets.QLineEdit(); self.asset_name_lbl.setReadOnly(True)
        cg_layout.addWidget(self.asset_name_lbl, 1, 1, 1, 2)

        cg_layout.addWidget(QtWidgets.QLabel('姓名：'), 2, 0)
        self.owner_name_lbl = QtWidgets.QLineEdit(); self.owner_name_lbl.setReadOnly(True)
        cg_layout.addWidget(self.owner_name_lbl, 2, 1, 1, 2)

        cg_layout.addWidget(QtWidgets.QLabel('2025位置：'), 3, 0)
        self.loc2025_lbl = QtWidgets.QLineEdit(); self.loc2025_lbl.setReadOnly(True)
        cg_layout.addWidget(self.loc2025_lbl, 3, 1, 1, 2)

        cg_layout.addWidget(QtWidgets.QLabel('2026位置：'), 4, 0)
        self.loc2026_edit = QtWidgets.QLineEdit()
        cg_layout.addWidget(self.loc2026_edit, 4, 1)
        btn_save = QtWidgets.QPushButton('保存盘点结果')
        btn_save.clicked.connect(self.handle_save)
        cg_layout.addWidget(btn_save, 4, 2)

        check_group.setLayout(cg_layout)
        layout.addWidget(check_group)

        # Report section
        report_group = QtWidgets.QGroupBox('3. 盘点报表生成')
        rg_layout = QtWidgets.QHBoxLayout()
        btn_export_checked = QtWidgets.QPushButton('导出已盘点资产报表')
        btn_export_checked.clicked.connect(self.export_checked)
        rg_layout.addWidget(btn_export_checked)
        btn_export_unchecked = QtWidgets.QPushButton('导出未盘点资产报表')
        btn_export_unchecked.clicked.connect(self.export_unchecked)
        rg_layout.addWidget(btn_export_unchecked)
        btn_export_all = QtWidgets.QPushButton('导出全量盘点报表')
        btn_export_all.clicked.connect(self.export_all)
        rg_layout.addWidget(btn_export_all)
        report_group.setLayout(rg_layout)
        layout.addWidget(report_group)

        self.setLayout(layout)

    def handle_import(self):
        path, _ = QFileDialog.getOpenFileName(self, '选择固定资产Excel文件', filter='Excel Files (*.xlsx *.xls)')
        if not path:
            return
        ok = import_data_file(path)
        if ok:
            QMessageBox.information(self, '成功', '数据导入完成')
        else:
            QMessageBox.critical(self, '错误', '导入失败，查看终端输出')

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
            QMessageBox.information(self, '提示', '未找到该主资产编号对应的资产')

    def handle_save(self):
        asset_id = self.asset_id_edit.text().strip()
        loc2026 = self.loc2026_edit.text().strip()
        if not asset_id:
            QMessageBox.warning(self, '警告', '请先查询资产信息')
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
            QMessageBox.information(self, '成功', '盘点结果已保存')
            # 清空并聚焦
            self.asset_id_edit.clear()
            self.asset_name_lbl.clear()
            self.owner_name_lbl.clear()
            self.loc2025_lbl.clear()
            self.loc2026_edit.clear()
            self.asset_id_edit.setFocus()
        except Exception as e:
            QMessageBox.critical(self, '错误', f'保存失败：{e}')

    def export_checked(self):
        path, _ = QFileDialog.getSaveFileName(self, '保存已盘点报表', '已盘点资产报表.xlsx', filter='Excel Files (*.xlsx)')
        if path:
            export_checked_file(path)
            QMessageBox.information(self, '成功', f'已导出到：{path}')

    def export_unchecked(self):
        path, _ = QFileDialog.getSaveFileName(self, '保存未盘点报表', '未盘点资产报表.xlsx', filter='Excel Files (*.xlsx)')
        if path:
            export_unchecked_file(path)
            QMessageBox.information(self, '成功', f'已导出到：{path}')

    def export_all(self):
        path, _ = QFileDialog.getSaveFileName(self, '保存全量报表', '全量资产盘点报表.xlsx', filter='Excel Files (*.xlsx)')
        if path:
            export_all_file(path)
            QMessageBox.information(self, '成功', f'已导出到：{path}')


def main():
    app = QtWidgets.QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
