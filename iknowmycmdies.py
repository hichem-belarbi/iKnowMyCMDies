import sys
import os
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton,
    QLabel, QComboBox, QMessageBox, QListWidget, QDialog, QDialogButtonBox, QTextEdit,
    QScrollArea, QFrame, QSizePolicy
)
from PyQt5.QtCore import Qt, QSize, QRect
from PyQt5.QtGui import QFont, QIcon, QPixmap, QPainter, QColor, QLinearGradient
import subprocess

COMMAND_FILE = "commandes.txt"


CLOSE_ICON_PATH = "icons/close.png"
MINIMIZE_ICON_PATH = "icons/minimize.png"
TERMINAL_ICON_PATH = "icons/terminal.png"

def load_commands():
    commands = {}
    if not os.path.exists(COMMAND_FILE):
        return commands

    try:
        with open(COMMAND_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and ":" in line:
                    name, cmd_env = line.split(":", 1)
                    cmd, env = cmd_env.rsplit("|", 1)
                    commands[name.strip()] = {"command": cmd.strip(), "env": env.strip()}
    except Exception as e:
        print(f"Error while loading commands: {e}")
    return commands

def save_commands(commands):
    try:
        with open(COMMAND_FILE, "w", encoding="utf-8") as f:
            for name, data in commands.items():
                f.write(f"{name}:{data['command']}|{data['env']}\n")
    except Exception as e:
        print(f"Error while saving commands: {e}")

class TitleBar(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.setFixedHeight(100)
        self.layout = QHBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        
        # Title with icon
        self.title = QLabel("     IknowMyCMDies")
        self.title.setAlignment(Qt.AlignCenter)
        self.title.setStyleSheet("color: #569cd6; font-weight: bold;")
        
        # Control buttons
        self.btn_layout = QHBoxLayout()
        self.btn_layout.setSpacing(0)
        self.btn_layout.setContentsMargins(0, 0, 5, 0)
        
        self.min_btn = QPushButton()
        self.min_btn.setIcon(QIcon(MINIMIZE_ICON_PATH))
        self.min_btn.setFixedSize(40, 30)
        self.min_btn.clicked.connect(self.parent.showMinimized)
        
    
        self.close_btn = QPushButton()
        self.close_btn.setIcon(QIcon(CLOSE_ICON_PATH))
        self.close_btn.setFixedSize(40, 30)
        self.close_btn.clicked.connect(self.parent.close)
        
        self.btn_layout.addWidget(self.min_btn)
        self.btn_layout.addWidget(self.close_btn)
        
        self.layout.addWidget(self.title, stretch=1)
        self.layout.addLayout(self.btn_layout)
        
        self.setLayout(self.layout)
        self.setStyleSheet("""
            QWidget {
                background-color: #1a1a1a;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                border: 1px solid #569cd6;
                border-bottom: none;
            }
            QPushButton {
                background: transparent;
                border: none;
                padding: 0;
            }
            QPushButton:hover {
                background-color: #569cd6;
                border-radius: 4px;
            }
        """)

    def toggle_maximize(self):
        if self.parent.isMaximized():
            self.parent.showNormal()
        else:
            self.parent.showMaximized()

class AddCommandDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add a Command")
        self.setFixedSize(500, 300)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(15, 15, 15, 15)
        self.layout.setSpacing(10)
        
        # Command name
        name_label = QLabel("Name:")
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Ex: disable-bluetooth")
        
        # Shell command
        cmd_label = QLabel("Command:")
        self.cmd_input = QTextEdit()
        self.cmd_input.setPlaceholderText("Ex: Get-PnpDevice | Where-Object { $_.FriendlyName -like '*Bluetooth*' } | Disable-PnpDevice -Confirm:$false")
        self.cmd_input.setMaximumHeight(100)

        # Execution environment
        env_label = QLabel("Execute with:")
        self.env_combo = QComboBox()
        self.env_combo.addItems(["CMD", "PowerShell", "Bash"])

        # Buttons
        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)

        self.layout.addWidget(name_label)
        self.layout.addWidget(self.name_input)
        self.layout.addWidget(cmd_label)
        self.layout.addWidget(self.cmd_input)
        self.layout.addWidget(env_label)
        self.layout.addWidget(self.env_combo)
        self.layout.addWidget(self.buttons)

        self.setLayout(self.layout)
        self.apply_dark_theme()

    def apply_dark_theme(self):
        self.setStyleSheet("""
            QDialog {
                background-color: #252525;
                border: 1px solid #569cd6;
                border-radius: 5px;
            }
            QLabel {
                color: #569cd6;
            }
            QLineEdit, QTextEdit, QComboBox {
                background-color: #333;
                color: #fff;
                border: 1px solid #569cd6;
                border-radius: 3px;
                padding: 5px;
                selection-background-color: #569cd6;
            }
            QPushButton {
                background-color: #333;
                color: #569cd6;
                border: 1px solid #569cd6;
                border-radius: 3px;
                padding: 5px 10px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #569cd6;
                color: #fff;
            }
            QPushButton:pressed {
                background-color: #005f8c;
            }
        """)

    def get_command(self):
        return self.name_input.text().strip(), self.cmd_input.toPlainText().strip(), self.env_combo.currentText()

class DeleteCommandDialog(QDialog):
    def __init__(self, commands, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Delete Commands")
        self.setFixedSize(400, 400)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(15, 15, 15, 15)
        self.layout.setSpacing(10)

        self.list_widget = QListWidget()
        self.list_widget.addItems(commands.keys())
        self.list_widget.setSelectionMode(QListWidget.MultiSelection)
        
        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)

        self.layout.addWidget(QLabel("Select commands to delete:"))
        self.layout.addWidget(self.list_widget)
        self.layout.addWidget(self.buttons)

        self.setLayout(self.layout)
        self.apply_dark_theme()

    def apply_dark_theme(self):
        self.setStyleSheet("""
            QDialog {
                background-color: #252525;
                border: 1px solid #569cd6;
                border-radius: 5px;
            }
            QLabel {
                color: #569cd6;
            }
            QListWidget {
                background-color: #333;
                color: #fff;
                border: 1px solid #569cd6;
                border-radius: 3px;
                padding: 5px;
            }
            QListWidget::item {
                padding: 5px;
            }
            QListWidget::item:hover {
                background-color: #444;
            }
            QListWidget::item:selected {
                background-color: #569cd6;
                color: #fff;
            }
            QDialogButtonBox {
                button-layout: 1;
            }
            QPushButton {
                background-color: #333;
                color: #569cd6;
                border: 1px solid #569cd6;
                border-radius: 3px;
                padding: 5px 10px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #569cd6;
                color: #fff;
            }
            QPushButton:pressed {
                background-color: #005f8c;
            }
        """)

    def get_selected_commands(self):
        return [item.text() for item in self.list_widget.selectedItems()]

class CommandApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("IknowMyCMDies")
        self.setFixedSize(900, 700)
        self.setWindowFlags(Qt.FramelessWindowHint)  # Disable the native title bar
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.commands = load_commands()
        self.init_ui()

    def init_ui(self):
        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # Custom title bar
        self.title_bar = QWidget()
        self.title_bar.setFixedHeight(32)
        title_bar_layout = QHBoxLayout()
        title_bar_layout.setContentsMargins(5, 0, 5, 0)
        title_bar_layout.setSpacing(5)

        # Title
        title_label = QLabel("IknowMyCMDies")
        title_label.setStyleSheet("color: #569cd6; font-weight: bold; border: none;background-color: transparent;")
        title_bar_layout.addWidget(title_label, alignment=Qt.AlignLeft)

        # Minimize button
        minimize_btn = QPushButton("-")
        minimize_btn.setFixedSize(24, 24)
        minimize_btn.setStyleSheet("""
            QPushButton {
                background-color: #252525;
                color: #569cd6;
                border: 1px solid #569cd6;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #569cd6;
                color: #fff;
            }
        """)
        minimize_btn.clicked.connect(self.showMinimized)
        title_bar_layout.addWidget(minimize_btn, alignment=Qt.AlignRight)

        # Close button
        close_btn = QPushButton("x")
        close_btn.setFixedSize(24, 24)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #252525;
                color: #ff5f56;
                border: 1px solid #ff5f56;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #ff5f56;
                color: #fff;
            }
        """)
        close_btn.clicked.connect(self.close)
        title_bar_layout.addWidget(close_btn, alignment=Qt.AlignRight)

        self.title_bar.setLayout(title_bar_layout)
        self.title_bar.setStyleSheet("background-color: #1a1a1a; border-top-left-radius: 8px; border-top-right-radius: 8px;border: 1px solid #569cd6;border-bottom: none;")
        self.main_layout.addWidget(self.title_bar)

        # Main content
        self.content = QWidget()
        self.content.setObjectName("content")
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(20, 20, 20, 20)
        self.layout.setSpacing(15)

        # Title with icon
        title_layout = QHBoxLayout()
        title_layout.setAlignment(Qt.AlignCenter)
        
        terminal_icon = QLabel()
        terminal_icon.setPixmap(QPixmap(TERMINAL_ICON_PATH))
        
        title = QLabel("IknowMyCMDies")
        title.setStyleSheet("color: #569cd6; font-size: 24px; font-weight: bold;border: none;")
        
        title_layout.addWidget(terminal_icon)
        title_layout.addWidget(title, alignment=Qt.AlignCenter)
        self.layout.addLayout(title_layout)

        # Command selection
        combo_label = QLabel("Saved commands:")
        self.combo = QComboBox()
        self.combo.addItem("")  # Empty option
        self.combo.addItems(sorted(self.commands.keys()))
        self.combo.currentTextChanged.connect(self.update_input)  # Connect the combo box to update the input and set focus
        self.combo.setStyleSheet("""
            QComboBox {
                background-color: #252525;
                color: #fff;
                border: 1px solid #569cd6;
                border-radius: 4px;
                padding: 5px;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 24px;
                border-left-width: 1px;
                border-left-color: #569cd6;
                border-left-style: solid;
                border-top-right-radius: 4px;
                border-bottom-right-radius: 4px;
            }
            QComboBox::down-arrow {
                image: url(icons/arrow-down.png);  /* Add arrow-down icon */
                width: 16px;
                height: 16px;
            }
            QComboBox QAbstractItemView {
                background-color: #252525;
                color: #fff;
                border: 1px solid #569cd6;
                selection-background-color: #569cd6;
                selection-color: #fff;
            }
        """)
        self.layout.addWidget(combo_label)
        self.layout.addWidget(self.combo)

        # Separator or label for input
        input_label = QLabel("Command input:")
        input_label.setStyleSheet("color: #569cd6; font-size: 14px;")
        self.layout.addWidget(input_label)

        # Command input
        self.input_line = QLineEdit()
        self.input_line.setPlaceholderText("Enter the name of a command or select one from the list")
        self.layout.addWidget(self.input_line)

        # Result area with scrolling
        result_label = QLabel("Results:")
        self.result_area = QTextEdit()
        self.result_area.setReadOnly(True)
        self.result_area.setPlaceholderText("Execution results will be displayed here...")
        
        scroll = QScrollArea()
        scroll.setWidget(self.result_area)
        scroll.setWidgetResizable(True)
        self.layout.addWidget(result_label)
        self.layout.addWidget(scroll, stretch=1)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)

        self.execute_btn = QPushButton("Execute (Enter)")
        self.execute_btn.clicked.connect(self.execute_command)

        self.add_btn = QPushButton("Add")
        self.add_btn.clicked.connect(self.add_command)

        self.delete_btn = QPushButton("Delete")
        self.delete_btn.clicked.connect(self.delete_command)

        button_layout.addWidget(self.execute_btn)
        button_layout.addWidget(self.add_btn)
        button_layout.addWidget(self.delete_btn)

        # Connect Enter key to execute button after defining it
        self.input_line.returnPressed.connect(self.execute_btn.click)

        # Wrap button_layout in a QWidget
        button_widget = QWidget()
        button_widget.setLayout(button_layout)
        self.layout.addWidget(button_widget)

        self.content.setLayout(self.layout)
        self.main_layout.addWidget(self.content)
        self.setLayout(self.main_layout)

        self.apply_dark_theme()

    def apply_dark_theme(self):
        self.setStyleSheet("""
            #content {
                background-color: #1e1e1e;
                border-bottom-left-radius: 8px;
                border-bottom-right-radius: 8px;
                border: 1px solid #569cd6;
                border-top: none;
            }
            QLabel {
                color: #569cd6;
                font-size: 14px;
            }
            QLineEdit, QTextEdit, QComboBox {
                background-color: #252525;
                color: #fff;
                border: 1px solid #569cd6;
                border-radius: 4px;
                padding: 8px;
                selection-background-color: #569cd6;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 24px;
                border-left-width: 1px;
                border-left-color: #569cd6;
                border-left-style: solid;
                border-top-right-radius: 4px;
                border-bottom-right-radius: 4px;
            }
            QComboBox::down-arrow {
                image: url(none);
                width: 16px;
                height: 16px;
            }
            QComboBox QAbstractItemView {
                background-color: #252525;
                color: #fff;
                border: 1px solid #569cd6;
                selection-background-color: #569cd6;
                selection-color: #fff;
            }
            QPushButton {
                background-color: #252525;
                color: #569cd6;
                border: 1px solid #569cd6;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #569cd6;
                color: #fff;
            }
            QPushButton:pressed {
                background-color: #005f8c;
            }
            QScrollArea {
                border: none;
            }
            QTextEdit {
                background-color: #252525;
                color: #569cd6;
                border: 1px solid #569cd6;
                border-radius: 4px;
                padding: 10px;
            }
        """)

    def update_input(self, text):
        if text:
            self.input_line.setText(text)
            self.input_line.setFocus()  # Ensure the input line gains focus

    def execute_command(self):
        name = self.input_line.text().strip()
        if not name:
            self.result_area.setText("<span style='color: #ff5f56;'>Please enter or select a command.</span>")
            return

        if name not in self.commands:
            available_commands = "<br>".join(f"• <span style='color: #569cd6;'>{cmd}</span>" for cmd in self.commands.keys())
            self.result_area.setHtml(f"""
                <span style='color: #ff5f56;'>❌ Command '{name}' not found.</span>
                <br><br>
                <span style='color: #569cd6;'>Available commands:</span>
                <br>
                {available_commands}
            """)
            return

        command_data = self.commands[name]
        command = command_data["command"]
        env = command_data["env"]

        self.result_area.setHtml(f"""
            <span style='color: #569cd6;'>Executing command: </span><span style='color: #fff;'>{name}</span>
            <br><br>
            <span style='color: #569cd6;'>Command:</span>
            <div style='background-color: #252525; padding: 8px; border: 1px solid #569cd6;'>{command}</div>
            <br>
            <span style='color: #569cd6;'>Executed with:</span> <span style='color: #fff;'>{env}</span>
            <br><br>
            <span style='color: #569cd6;'>Result:</span>
        """)

        try:
            if env == "CMD":
                result = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT, universal_newlines=True)
            elif env == "PowerShell":
                result = subprocess.check_output(["powershell", "-Command", command], stderr=subprocess.STDOUT, universal_newlines=True)
            elif env == "Bash":
                result = subprocess.check_output(["bash", "-c", command], stderr=subprocess.STDOUT, universal_newlines=True)
            else:
                result = "Unknown environment."
            self.result_area.append(f"<pre style='color: #fff;'>{result}</pre>")
        except subprocess.CalledProcessError as e:
            self.result_area.append(f"<pre style='color: #ff5f56;'>{e.output}</pre>")

    def add_command(self):
        dialog = AddCommandDialog(self)
        if dialog.exec_():
            name, cmd, env = dialog.get_command()
            if name and cmd:
                self.commands[name] = {"command": cmd, "env": env}
                save_commands(self.commands)
                self.combo.clear()
                self.combo.addItem("")
                self.combo.addItems(sorted(self.commands.keys()))

    def delete_command(self):
        dialog = DeleteCommandDialog(self.commands, self)
        if dialog.exec_():
            selected = dialog.get_selected_commands()
            for name in selected:
                if name in self.commands:
                    del self.commands[name]
            save_commands(self.commands)
            self.combo.clear()
            self.combo.addItem("")
            self.combo.addItems(sorted(self.commands.keys()))

    def mousePressEvent(self, event):
        # Allow window movement via the custom title bar
        if event.button() == Qt.LeftButton:
            self.drag_pos = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and hasattr(self, 'drag_pos'):
            self.move(event.globalPos() - self.drag_pos)
            event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = CommandApp()
    window.show()
    sys.exit(app.exec_())
