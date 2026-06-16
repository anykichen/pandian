from PySide6 import QtWidgets, QtGui, QtCore
from PySide6.QtWidgets import QFileDialog, QMessageBox, QSystemTrayIcon, QMenu
import sys
import sqlite3
import os
from pandian import init_db, import_data_file, export_checked_file, export_unchecked_file, export_all_file


class MainWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('固定资产盘点系统')
        self.setFixedSize(700, 480)
        self.setStyleSheet("""
            QWidget {
                font-family: 'Microsoft YaHei', 'PingFang SC', sans-serif;
                font-size: 14px;
            }
            QGroupBox {
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                padding: 15px;
                margin-top: 10px;
                font-weight: bold;
                color: #333;
                background-color: #fafafa;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 8px;
                color: #666;
            }
            QPushButton {
                background-color: #4a90d9;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #357abd;
            }
            QPushButton:pressed {
                background-color: #2d6bb3;
            }
            QLineEdit {
                border: 1px solid #ccc;
                border-radius: 4px;
                padding: 6px 10px;
                background-color: white;
            }
            QLineEdit:focus {
                border-color: #4a90d9;
                outline: none;
            }
            QLabel {
                color: #555;
            }
        """)
        init_db()
        self.init_ui()
        self.init_tray()

    def init_tray(self):
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QtGui.QIcon('icon.ico'))
        self.tray_icon.setToolTip('固定资产盘点系统')

        tray_menu = QMenu()
        show_action = tray_menu.addAction('显示窗口')
        show_action.triggered.connect(self.show_window)
        quit_action = tray_menu.addAction('退出')
        quit_action.triggered.connect(self.quit_app)
        self.tray_icon.setContextMenu(tray_menu)

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
        event.ignore()
        self.hide()
        self.tray_icon.showMessage('固定资产盘点系统', '程序已最小化到托盘，点击托盘图标可重新显示')

    def init_ui(self):
        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Stats section
        stats_group = QtWidgets.QGroupBox('盘点统计')
        sg_layout = QtWidgets.QHBoxLayout()
        sg_layout.setSpacing(20)

        # Total assets
        total_widget = QtWidgets.QWidget()
        total_widget.setStyleSheet("""
            QWidget {
                background-color: #ffffff;
                border-radius: 10px;
                padding: 15px 25px;
                border: 1px solid #e0e0e0;
            }
        """)
        total_layout = QtWidgets.QVBoxLayout(total_widget)
        total_label = QtWidgets.QLabel('总固资数量')
        total_label.setAlignment(QtCore.Qt.AlignCenter)
        total_label.setStyleSheet('font-size: 13px; color: #888;')
        self.total_count_lbl = QtWidgets.QLabel('0')
        self.total_count_lbl.setAlignment(QtCore.Qt.AlignCenter)
        self.total_count_lbl.setStyleSheet('font-weight: bold; font-size: 32px; color: #333333;')
        total_layout.addWidget(total_label)
        total_layout.addWidget(self.total_count_lbl)
        sg_layout.addWidget(total_widget)

        # Checked assets
        checked_widget = QtWidgets.QWidget()
        checked_widget.setStyleSheet("""
            QWidget {
                background-color: #e8f5e9;
                border-radius: 10px;
                padding: 15px 25px;
                border: 1px solid #c8e6c9;
            }
        """)
        checked_layout = QtWidgets.QVBoxLayout(checked_widget)
        checked_label = QtWidgets.QLabel('已盘点数量')
        checked_label.setAlignment(QtCore.Qt.AlignCenter)
        checked_label.setStyleSheet('font-size: 13px; color: #66bb6a;')
        self.checked_count_lbl = QtWidgets.QLabel('0')
        self.checked_count_lbl.setAlignment(QtCore.Qt.AlignCenter)
        self.checked_count_lbl.setStyleSheet('font-weight: bold; font-size: 32px; color: #2e7d32;')
        checked_layout.addWidget(checked_label)
        checked_layout.addWidget(self.checked_count_lbl)
        sg_layout.addWidget(checked_widget)

        # Unchecked assets
        unchecked_widget = QtWidgets.QWidget()
        unchecked_widget.setStyleSheet("""
            QWidget {
                background-color: #ffebee;
                border-radius: 10px;
                padding: 15px 25px;
                border: 1px solid #ffcdd2;
            }
        """)
        unchecked_layout = QtWidgets.QVBoxLayout(unchecked_widget)
        unchecked_label = QtWidgets.QLabel('待盘点数量')
        unchecked_label.setAlignment(QtCore.Qt.AlignCenter)
        unchecked_label.setStyleSheet('font-size: 13px; color: #ef5350;')
        self.unchecked_count_lbl = QtWidgets.QLabel('0')
        self.unchecked_count_lbl.setAlignment(QtCore.Qt.AlignCenter)
        self.unchecked_count_lbl.setStyleSheet('font-weight: bold; font-size: 32px; color: #c62828;')
        unchecked_layout.addWidget(unchecked_label)
        unchecked_layout.addWidget(self.unchecked_count_lbl)
        sg_layout.addWidget(unchecked_widget)

        stats_group.setLayout(sg_layout)
        layout.addWidget(stats_group)

        # Import section
        import_group = QtWidgets.QGroupBox('数据导入')
        ig_layout = QtWidgets.QHBoxLayout()
        ig_layout.setContentsMargins(10, 5, 10, 5)
        btn_import = QtWidgets.QPushButton('选择Excel文件并导入')
        btn_import.setFixedHeight(36)
        btn_import.setStyleSheet("""
            QPushButton {
                background-color: #5c6bc0;
                font-size: 15px;
                padding: 10px 30px;
            }
            QPushButton:hover {
                background-color: #3949ab;
            }
        """)
        btn_import.clicked.connect(self.handle_import)
        ig_layout.addWidget(btn_import)
        import_group.setLayout(ig_layout)
        layout.addWidget(import_group)

        # Check section
        check_group = QtWidgets.QGroupBox('资产盘点')
        cg_layout = QtWidgets.QGridLayout()
        cg_layout.setSpacing(10)
        cg_layout.setContentsMargins(10, 10, 10, 10)

        cg_layout.addWidget(QtWidgets.QLabel('主资产编号：'), 0, 0)
        self.asset_id_edit = QtWidgets.QLineEdit()
        self.asset_id_edit.returnPressed.connect(self.handle_query)
        self.asset_id_edit.setPlaceholderText('请输入主资产编号')
        cg_layout.addWidget(self.asset_id_edit, 0, 1)
        btn_query = QtWidgets.QPushButton('查询')
        btn_query.setFixedHeight(30)
        btn_query.clicked.connect(self.handle_query)
        cg_layout.addWidget(btn_query, 0, 2)

        cg_layout.addWidget(QtWidgets.QLabel('资产名称：'), 1, 0)
        self.asset_name_lbl = QtWidgets.QLineEdit()
        self.asset_name_lbl.setReadOnly(True)
        self.asset_name_lbl.setStyleSheet('background-color: #f5f5f5; color: #333;')
        cg_layout.addWidget(self.asset_name_lbl, 1, 1, 1, 2)

        cg_layout.addWidget(QtWidgets.QLabel('责任人：'), 2, 0)
        self.owner_name_lbl = QtWidgets.QLineEdit()
        self.owner_name_lbl.setReadOnly(True)
        self.owner_name_lbl.setStyleSheet('background-color: #f5f5f5; color: #333;')
        cg_layout.addWidget(self.owner_name_lbl, 2, 1, 1, 2)

        cg_layout.addWidget(QtWidgets.QLabel('2025位置：'), 3, 0)
        self.loc2025_lbl = QtWidgets.QLineEdit()
        self.loc2025_lbl.setReadOnly(True)
        self.loc2025_lbl.setStyleSheet('background-color: #f5f5f5; color: #333;')
        cg_layout.addWidget(self.loc2025_lbl, 3, 1, 1, 2)

        cg_layout.addWidget(QtWidgets.QLabel('2026位置：'), 4, 0)
        self.loc2026_edit = QtWidgets.QLineEdit()
        self.loc2026_edit.setPlaceholderText('请输入2026年盘点位置')
        cg_layout.addWidget(self.loc2026_edit, 4, 1)
        btn_save = QtWidgets.QPushButton('保存')
        btn_save.setFixedHeight(30)
        btn_save.setStyleSheet("""
            QPushButton {
                background-color: #43a047;
            }
            QPushButton:hover {
                background-color: #2e7d32;
            }
        """)
        btn_save.clicked.connect(self.handle_save)
        cg_layout.addWidget(btn_save, 4, 2)

        check_group.setLayout(cg_layout)
        layout.addWidget(check_group)

        # Report section
        report_group = QtWidgets.QGroupBox('报表导出')
        rg_layout = QtWidgets.QHBoxLayout()
        rg_layout.setSpacing(15)
        rg_layout.setContentsMargins(10, 5, 10, 5)

        btn_export_checked = QtWidgets.QPushButton('已盘点资产')
        btn_export_checked.setFixedHeight(32)
        btn_export_checked.clicked.connect(self.export_checked)
        rg_layout.addWidget(btn_export_checked)

        btn_export_unchecked = QtWidgets.QPushButton('未盘点资产')
        btn_export_unchecked.setFixedHeight(32)
        btn_export_unchecked.clicked.connect(self.export_unchecked)
        rg_layout.addWidget(btn_export_unchecked)

        btn_export_all = QtWidgets.QPushButton('全量报表')
        btn_export_all.setFixedHeight(32)
        btn_export_all.clicked.connect(self.export_all)
        rg_layout.addWidget(btn_export_all)

        report_group.setLayout(rg_layout)
        layout.addWidget(report_group)

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
        self.total_count_lbl.setText(str(total))
        self.checked_count_lbl.setText(str(checked))
        self.unchecked_count_lbl.setText(str(total - checked))

    def handle_import(self):
        path, _ = QFileDialog.getOpenFileName(self, '选择固定资产Excel文件', filter='Excel Files (*.xlsx *.xls)')
        if not path:
            return
        ok = import_data_file(path)
        if ok:
            QMessageBox.information(self, '成功', '数据导入完成')
            self.update_stats()
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
            self.asset_id_edit.clear()
            self.asset_name_lbl.clear()
            self.owner_name_lbl.clear()
            self.loc2025_lbl.clear()
            self.loc2026_edit.clear()
            self.asset_id_edit.setFocus()
            self.update_stats()
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
