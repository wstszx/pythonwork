import sys
import json
from datetime import datetime
from pathlib import Path
from PySide6.QtGui import QCursor, QTextCursor,QIntValidator
from PySide6.QtCore import Qt, Signal, QObject, QTimer,QItemSelectionModel,QTime
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QDialog, QTableWidget, QTableWidgetItem,
    QPushButton, QVBoxLayout, QHBoxLayout, QMenu, QLineEdit, QLabel,
    QHeaderView, QAbstractItemView, QComboBox, QFormLayout, QFileDialog, QTextEdit,QTimeEdit
)

class Logger(QObject):
    log_signal = Signal(str)

    def __init__(self):
        super().__init__()
        self.logs = []
        self.log_signal.connect(self.handle_log)

    def handle_log(self, message):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        self.logs.append(log_entry)
        print(log_entry)

logger = Logger()

def format_dr_time(minutes):
    """将分钟数转换为HH:mm格式"""
    hours = minutes // 60
    mins = minutes % 60
    return f"{hours:02d}:{mins:02d}"


class AccountInfo:
    def __init__(self, name, password="", group="默认组", races_completed=0, dr_time=0, 
                 sixteen_code="", secondary_email="", account_type="游戏号",
                 dr_level="1", coins=0, green_points=0, status="空闲中", executed_action="休息"):
        self.name = name
        self.password = password
        self.group = group
        self.races_completed = races_completed
        self.dr_time = dr_time
        self.sixteen_code = sixteen_code
        self.secondary_email = secondary_email
        self.account_type = account_type
        self.dr_level = dr_level
        self.coins = coins
        self.green_points = green_points
        self.status = status
        self.executed_action = executed_action

    def to_dict(self):
        return {
            "name": self.name,
            "password": self.password,
            "group": self.group,
            "races_completed": self.races_completed,
            "dr_time": self.dr_time,
            "sixteen_code": self.sixteen_code,
            "secondary_email": self.secondary_email,
            "account_type": self.account_type,
            "dr_level": self.dr_level,
            "coins": self.coins,
            "green_points": self.green_points,
            "status": self.status,
            "executed_action": self.executed_action
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            name=data["name"],
            password=data.get("password", ""),
            group=data.get("group", "默认组"),
            races_completed=data.get("races_completed", 0),
            dr_time=data.get("dr_time", 0),
            sixteen_code=data.get("sixteen_code", ""),
            secondary_email=data.get("secondary_email", ""),
            account_type=data.get("account_type", "游戏号"),
            dr_level=data.get("dr_level", "1"),
            coins=data.get("coins", 0),
            green_points=data.get("green_points", 0),
            status=data.get("status", "空闲中"),
            executed_action=data.get("executed_action", "休息")
        )

class AccountManagerWindow(QMainWindow):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.setWindowTitle("账号管理")
        self.setMinimumSize(900, 600)

        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "账号名称", "密码", "编组", "sqb场次",
            "dr时间", "16位码", "辅助邮箱", "账号类别"
        ])
        self.table.setSelectionMode(QAbstractItemView.ExtendedSelection) #多选
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)#选整行
        self.table.horizontalHeader().setStretchLastSection(True)#伸缩
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)#不可直接编辑

        self.add_btn = QPushButton("添加账号")
        self.import_btn = QPushButton("导入账号")
        self.edit_btn = QPushButton("编辑账号")
        self.delete_btn = QPushButton("删除账号")

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.add_btn)
        button_layout.addWidget(self.import_btn) 
        button_layout.addWidget(self.edit_btn)
        button_layout.addWidget(self.delete_btn)

        container = QWidget()
        main_layout = QVBoxLayout()
        main_layout.addWidget(self.table)
        main_layout.addLayout(button_layout)
        container.setLayout(main_layout)
        self.setCentralWidget(container)

        self.add_btn.clicked.connect(self.add_account)
        self.import_btn.clicked.connect(self.import_account)
        self.edit_btn.clicked.connect(self.edit_account)
        self.delete_btn.clicked.connect(self.delete_account)

        self.load_accounts()


    def load_accounts(self):
        self.table.setRowCount(len(self.main_window.accounts))
        for row, account in enumerate(self.main_window.accounts):
            self.table.setItem(row, 0, QTableWidgetItem(account.name))
            self.table.setItem(row, 1, QTableWidgetItem(account.password))
            self.table.setItem(row, 2, QTableWidgetItem(account.group))
            self.table.setItem(row, 3, QTableWidgetItem(str(account.races_completed)))
            self.table.setItem(row, 4, QTableWidgetItem(format_dr_time(account.dr_time)))
            self.table.setItem(row, 5, QTableWidgetItem(account.sixteen_code))
            self.table.setItem(row, 6, QTableWidgetItem(account.secondary_email))
            self.table.setItem(row, 7, QTableWidgetItem(account.account_type))

    def import_account(self):
        """导入账号功能实现"""
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getOpenFileName(
            self, "导入账号", "", "Text Files (*.txt)", options=options)
        if not file_path:
            return

        success_count = 0
        error_count = 0
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue

                    # 分割字段（支持空格和制表符）
                    parts = line.replace('\t', ' ').split()
                    if len(parts) < 8:
                        logger.log_signal.emit(f"第{line_num}行：字段不足，需要9个字段")
                        error_count += 1
                        continue

                    try:
                        # 解析字段
                        name = parts[0]
                        password = parts[1]
                        group = parts[2]
                        races_completed = int(parts[3])
                        
                        # 处理时间格式（支持HH:mm或分钟数）
                        time_str = parts[4]
                        if ':' in time_str:
                            hours, mins = map(int, time_str.split(':'))
                            dr_time = hours * 60 + mins
                        else:
                            dr_time = int(time_str)
                            
                        sixteen_code = parts[5]
                        secondary_email = parts[6]
                        account_type = parts[7]
                        

                        # 验证数据有效性
                        valid_types = ["游戏号", "会员号", "游玩号"]
                        valid_actions = ["休息", "UT操作"]
                        if account_type not in valid_types:
                            raise ValueError(f"无效账号类型: {account_type}")

                        # 检查重复
                        if any(acc.name == name for acc in self.main_window.accounts):
                            logger.log_signal.emit(f"第{line_num}行：账号 {name} 已存在")
                            error_count += 1
                            continue

                        # 创建账号对象
                        new_account = AccountInfo(
                            name=name,
                            password=password,
                            group=group,
                            races_completed=races_completed,
                            dr_time=dr_time,
                            sixteen_code=sixteen_code,
                            secondary_email=secondary_email,
                            account_type=account_type
                        )
                        self.main_window.accounts.append(new_account)
                        success_count += 1

                    except Exception as e:
                        logger.log_signal.emit(f"第{line_num}行：错误 - {str(e)}")
                        error_count += 1

            # 刷新界面
            self.load_accounts()
            self.main_window.refresh_table()
            self.main_window.update_group_filter()
            logger.log_signal.emit(f"导入完成：成功 {success_count} 条，失败 {error_count} 条")

        except Exception as e:
            logger.log_signal.emit(f"文件读取失败：{str(e)}")

    def add_account(self):
        dialog = AccountEditDialog(
            groups=self.main_window.get_existing_groups(),
            parent=self
        )
        if dialog.exec():
            # 接收所有9个返回值
            (name, password, group, races_completed, dr_time, sixteen_code,
            secondary_email, account_type, action) = dialog.get_data()
            
            if not name:
                logger.log_signal.emit("账号名称不能为空！")
                return
            if any(acc.name == name for acc in self.main_window.accounts):
                logger.log_signal.emit("账号名称已存在！")
                return
            
            new_account = AccountInfo(
                name=name,
                password=password,
                group=group,
                races_completed=races_completed,
                dr_time=dr_time,
                sixteen_code=sixteen_code,
                secondary_email=secondary_email,
                account_type=account_type,
                executed_action=action  # 设置执行操作
            )
            self.main_window.accounts.append(new_account)
            self.load_accounts()
            self.main_window.refresh_table()
            logger.log_signal.emit(f"已添加账号：{name}")
        self.main_window.update_group_filter()

    def edit_account(self):
        selected = self.table.currentRow()
        if selected >= 0:
            account = self.main_window.accounts[selected]
            dialog = AccountEditDialog(
                account=account,
                groups=self.main_window.get_existing_groups(),
                parent=self
            )
            if dialog.exec():
                # 接收所有9个返回值
                (name, password, group, races_completed, dr_time, sixteen_code,
                secondary_email, account_type, action) = dialog.get_data()
                
                # 验证名称唯一性
                if name != account.name and any(acc.name == name for acc in self.main_window.accounts):
                    logger.log_signal.emit("账号名称已存在！")
                    return
                
                # 更新所有字段
                account.name = name
                account.password = password
                account.group = group
                account.races_completed = races_completed
                account.dr_time = dr_time
                account.sixteen_code = sixteen_code
                account.secondary_email = secondary_email
                account.account_type = account_type
                account.executed_action = action  # 更新执行操作
                
                self.load_accounts()
                self.main_window.refresh_table()
                logger.log_signal.emit(f"已更新账号：{name}")
                self.main_window.update_group_filter()
    def delete_account(self):
        selected = self.table.currentRow()
        if selected >= 0:
            account = self.main_window.accounts.pop(selected)
            self.load_accounts()
            self.main_window.refresh_table()
            logger.log_signal.emit(f"已删除账号：{account.name}")
                
class AccountEditDialog(QDialog):
    def __init__(self, account=None, groups=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("编辑账号" if account else "添加账号")

        self.name_input = QLineEdit()
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.action_input = QComboBox()
        self.action_input.addItems(["休息", "UT操作"])
        self.group_input = QComboBox()
        self.group_input.setEditable(True)
        self.group_input.addItems(groups if groups else ["默认组"])
        self.races_input = QLineEdit()
        self.races_input.setValidator(QIntValidator(0, 9999))
        # 修改为时间编辑控件
        self.dr_time_input = QTimeEdit()
        self.dr_time_input.setDisplayFormat("HH:mm")
        self.dr_time_input.setTime(QTime(0, 0))  # 默认时间
        self.sixteen_code_input = QLineEdit()
        self.secondary_email_input = QLineEdit()
        self.account_type_input = QComboBox()
        self.account_type_input.addItems(["游戏号", "会员号", "游玩号"])



        
        # 如果编辑现有账号，填充所有字段
        if account:
            self.races_input.setText(str(account.races_completed))
            # 转换分钟数为QTime对象
            hours = account.dr_time // 60
            minutes = account.dr_time % 60
            self.dr_time_input.setTime(QTime(hours, minutes))

            self.sixteen_code_input.setText(account.sixteen_code)
            self.secondary_email_input.setText(account.secondary_email)
            self.account_type_input.setCurrentText(account.account_type)
            self.action_input.setCurrentText(account.executed_action)  # 设置执行操作
            self.name_input.setText(account.name)
            self.password_input.setText(account.password)
            self.action_input.setCurrentText(account.executed_action)
            self.group_input.setCurrentText(account.group)

        form = QFormLayout()
        form.addRow("账号名称:", self.name_input)
        form.addRow("密码:", self.password_input)
        form.addRow("执行操作:", self.action_input)
        form.addRow("编组:", self.group_input)
        form.addRow("sqb场次:", self.races_input)
        form.addRow("dr时间:", self.dr_time_input)
        form.addRow("16位码:", self.sixteen_code_input)
        form.addRow("辅助邮箱:", self.secondary_email_input)
        form.addRow("账号类别:", self.account_type_input)
        self.submit_btn = QPushButton("确认")
        form.addRow(self.submit_btn)

        self.setLayout(form)
        self.submit_btn.clicked.connect(self.accept)

    def get_data(self):
        races = int(self.races_input.text()) if self.races_input.text() else 0
        # 获取时间并转换为分钟数
        time = self.dr_time_input.time()
        dr_time = time.hour() * 60 + time.minute()
    
        return (
            self.name_input.text(),
            self.password_input.text(),
            self.group_input.currentText(),
            int(self.races_input.text()) if self.races_input.text() else 0,
            dr_time,  # 使用转换后的分钟数
            self.sixteen_code_input.text(),
            self.secondary_email_input.text(),
            self.account_type_input.currentText(),
            self.action_input.currentText()  # 新增执行操作
        )

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.accounts = []
        self.data_file = Path("account_data.json")
        self.updating_selection = False  # 新增标志变量
        self.updating_checkboxes = False  # 新增标志变量
        self.init_ui()
        self.load_data()
        self.update_group_filter()  # 初始化时更新编组列表

    def init_ui(self):
        self.setWindowTitle("账号管理器")
        self.setMinimumSize(1000, 720)

        # 新增编组筛选控件
        self.group_filter = QComboBox()
        self.group_filter.setEditable(True)
        self.group_filter.addItem("所有组别")
        self.group_filter.currentTextChanged.connect(self.refresh_table)

        self.manager_btn = QPushButton("账号管理")
        self.export_btn = QPushButton("导出数据")
        self.batch_btn = QPushButton("批量操作")

        control_layout = QHBoxLayout()
        control_layout.addWidget(QLabel("编组筛选:"))
        control_layout.addWidget(self.group_filter)
        control_layout.addWidget(self.manager_btn)
        control_layout.addWidget(self.export_btn)
        control_layout.addWidget(self.batch_btn)
        control_layout.addStretch()
        self.table = QTableWidget()
        # 添加这行代码隐藏垂直表头（行索引）
        self.table.verticalHeader().setVisible(False)

        self.table.setColumnCount(10)
        self.table.setHorizontalHeaderLabels([
            "选择", "账号名称", "DR时间", "DR等级", "sqb场次",
            "金币", "绿点", "状态", "执行的操作", "编组"
        ])

        header = self.table.horizontalHeader()
        header.setMinimumSectionSize(40)
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        for col in range(1, 9):
            header.setSectionResizeMode(col, QHeaderView.Interactive)
        header.setSectionResizeMode(9, QHeaderView.Stretch)

        self.table.setSelectionMode(QAbstractItemView.ExtendedSelection) 

        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)

        self.table.itemSelectionChanged.connect(self.update_checkboxes_from_selection)
        self.table.itemChanged.connect(self.update_selection_from_checkboxes)


        # 日志显示区域
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setMinimumHeight(120)
        logger.log_signal.connect(self.append_log)

        main_layout = QVBoxLayout()
        main_layout.addLayout(control_layout)
        main_layout.addWidget(self.table, 1)
        main_layout.addWidget(QLabel("运行日志:"))
        main_layout.addWidget(self.log_output)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

        self.manager_btn.clicked.connect(self.show_manager_window)
        self.export_btn.clicked.connect(self.export_data)
        self.batch_btn.clicked.connect(self.show_batch_menu)

    def append_log(self, message):
        self.log_output.append(message)
        cursor = self.log_output.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.log_output.setTextCursor(cursor)

    # 新增的两个同步方法
    def update_checkboxes_from_selection(self):
        """同步选择状态到复选框"""
        if self.updating_checkboxes:
            return
        self.updating_checkboxes = True
        
        selected_rows = set(index.row() for index in self.table.selectedIndexes())
        
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item:
                new_state = Qt.Checked if row in selected_rows else Qt.Unchecked
                if item.checkState() != new_state:
                    item.setCheckState(new_state)
        
        self.updating_checkboxes = False

    def update_selection_from_checkboxes(self, item):
        """同步复选框到选择状态"""
        if self.updating_selection or item.column() != 0:
            return
        self.updating_selection = True
        
        row = item.row()
        selection_model = self.table.selectionModel()
        
        if item.checkState() == Qt.Checked:
            selection_model.select(
                self.table.model().index(row, 0),
                QItemSelectionModel.Select | QItemSelectionModel.Rows
            )
        else:
            selection_model.select(
                self.table.model().index(row, 0),
                QItemSelectionModel.Deselect | QItemSelectionModel.Rows
            )
        
        self.updating_selection = False
    def refresh_table(self):
        selected_group = self.group_filter.currentText()
        self.table.setRowCount(0)
        
        # 根据选定组别过滤账户
        if selected_group == "所有组别":
            filtered_accounts = self.accounts
        else:
            filtered_accounts = [acc for acc in self.accounts if acc.group == selected_group]
        
        # 遍历过滤后的账户列表填充表格
        for row, acc in enumerate(filtered_accounts):
            def create_item(text, checkable=False):
                item = QTableWidgetItem(str(text))
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                if checkable:
                    item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
                    item.setCheckState(Qt.Unchecked)
                return item

            self.table.insertRow(row)
            self.table.setItem(row, 0, create_item("", checkable=True))
            self.table.setItem(row, 1, create_item(acc.name))
            self.table.setItem(row, 2, create_item(format_dr_time(acc.dr_time)))
            self.table.setItem(row, 3, create_item(acc.dr_level))
            self.table.setItem(row, 4, create_item(acc.races_completed))
            self.table.setItem(row, 5, create_item(acc.coins))
            self.table.setItem(row, 6, create_item(acc.green_points))
            
            status_item = create_item(acc.status)
            status_color = Qt.green if acc.status == "空闲中" else Qt.red
            status_item.setForeground(status_color)
            self.table.setItem(row, 7, status_item)
            
            self.table.setItem(row, 8, create_item(acc.executed_action))
            self.table.setItem(row, 9, create_item(acc.group))

    def get_selected_accounts(self):
        selected = []
        for row in range(self.table.rowCount()):
            if self.table.item(row, 0).checkState() == Qt.Checked:
                selected.append(self.accounts[row])
        return selected

    def show_batch_menu(self):
        menu = QMenu()
        batch_export = menu.addAction("批量导出")
        batch_execute = menu.addAction("批量执行")
        action = menu.exec(QCursor.pos())

        if action == batch_export:
            self.batch_export()
        elif action == batch_execute:
            self.batch_execute()

    def batch_export(self):
        selected = self.get_selected_accounts()
        if not selected:
            logger.log_signal.emit("请先选择要导出的账号")
            return

        options = QFileDialog.Options()
        path, _ = QFileDialog.getSaveFileName(
            self, "批量导出", "batch_export.json", "JSON Files (*.json)", options=options)
        if path:
            try:
                with open(path, "w", encoding="utf-8") as f:
                    json.dump([acc.to_dict() for acc in selected], f, indent=2)
                logger.log_signal.emit(f"成功导出 {len(selected)} 个账号")
            except Exception as e:
                logger.log_signal.emit(f"导出失败: {str(e)}")

    def batch_execute(self):
        selected = self.get_selected_accounts()
        if not selected:
            logger.log_signal.emit("请先选择要执行的账号")
            return

        logger.log_signal.emit(f"开始批量执行 {len(selected)} 个账号...")
        for acc in selected:
            self.execute_script(acc)

    def load_data(self):
        if self.data_file.exists():
            try:
                with open(self.data_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.accounts = [AccountInfo.from_dict(item) for item in data]
                    self.update_group_filter()  # 加载数据后更新编组列表
                    self.refresh_table()
                    logger.log_signal.emit("数据加载成功")
            except Exception as e:
                logger.log_signal.emit(f"数据加载失败: {str(e)}")

    def save_data(self):
        data = [acc.to_dict() for acc in self.accounts]
        try:
            with open(self.data_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.log_signal.emit("数据保存成功")
        except Exception as e:
            logger.log_signal.emit(f"数据保存失败: {str(e)}")

    def show_context_menu(self, pos):
        menu = QMenu()
        export_action = menu.addAction("导出账号")
        execute_action = menu.addAction("执行脚本")

        selected = self.table.rowAt(pos.y())
        if selected >= 0:
            account = self.accounts[selected]
            action = menu.exec(self.table.viewport().mapToGlobal(pos))
            if action == export_action:
                self.export_account(account)
            elif action == execute_action:
                self.execute_script(account)

    def export_account(self, account):
        options = QFileDialog.Options()
        path, _ = QFileDialog.getSaveFileName(
            self, "导出账号", f"{account.name}.json", "JSON Files (*.json)", options=options)
        if path:
            try:
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(account.to_dict(), f, indent=2)
                logger.log_signal.emit(f"账号 {account.name} 导出成功")
            except Exception as e:
                logger.log_signal.emit(f"导出失败: {str(e)}")

    def export_data(self):
        options = QFileDialog.Options()
        path, _ = QFileDialog.getSaveFileName(
            self, "导出数据", "accounts.txt", "Text Files (*.txt)", options=options)
        
        if path:
            try:
                with open(path, "w", encoding="utf-8") as f:
                    for acc in self.accounts:
                        f.write("\t".join([
                            acc.name,
                            acc.password,
                            str(acc.dr_time),
                            acc.dr_level,
                            str(acc.races_completed),
                            str(acc.coins),
                            str(acc.green_points),
                            acc.status,
                            acc.executed_action,
                            acc.group
                        ]) + "\n")
                logger.log_signal.emit("数据导出成功（TXT格式）")
            except Exception as e:
                logger.log_signal.emit(f"导出失败: {str(e)}")

    def execute_script(self, account):
        account.status = "运行中"
        self.refresh_table()
        
        if account.executed_action == "UT操作":
            logger.log_signal.emit(f"开始执行 {account.name} 的UT操作...")
            QTimer.singleShot(2000, lambda: self.finish_script(account, "UT操作完成"))
        elif account.executed_action == "休息":
            logger.log_signal.emit(f"{account.name} 进入休息状态...")
            QTimer.singleShot(2000, lambda: self.finish_script(account, "休息完成"))

    def finish_script(self, account, result):
        account.status = "空闲中"
        account.executed_action = f"最后操作：{result}"
        self.refresh_table()
        logger.log_signal.emit(f"{account.name} 操作完成: {result}")

    def show_manager_window(self):
        self.manager_window = AccountManagerWindow(self)
        self.manager_window.show()

    def closeEvent(self, event):
        self.save_data()
        super().closeEvent(event)

    def update_group_filter(self):
        """更新编组筛选下拉列表，包含所有非空编组"""
        current_text = self.group_filter.currentText()
        groups = {acc.group for acc in self.accounts if acc.group.strip()}  # 过滤空编组
        groups = sorted(groups) if groups else ["默认组"]
        
        self.group_filter.blockSignals(True)
        self.group_filter.clear()
        self.group_filter.addItem("所有组别")
        self.group_filter.addItems(groups)
        
        # 保持当前选择状态（如果存在）
        if current_text in groups or current_text == "所有组别":
            self.group_filter.setCurrentText(current_text)
        self.group_filter.blockSignals(False)

    def get_existing_groups(self):
        return list({acc.group for acc in self.accounts})
    





if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())