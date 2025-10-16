import sys
# 使用 PySide6
from PySide6.QtWidgets import QApplication, QMainWindow, QLabel, QPushButton

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("My First Qt App in VSCode")
        self.setFixedSize(300, 200)
        
        # 创建一个标签和一个按钮
        self.label = QLabel("Hello, World!", self)
        self.label.move(50, 50)
        
        self.button = QPushButton("Click Me", self)
        self.button.move(50, 80)
        self.button.clicked.connect(self.on_button_clicked) # 连接信号和槽
    
    def on_button_clicked(self):
        self.label.setText("Button Clicked!")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())