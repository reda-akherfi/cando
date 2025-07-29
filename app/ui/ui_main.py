from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton


class UiMainWindow:
    def setupUi(self, MainWindow):
        MainWindow.setWindowTitle("Cando")
        MainWindow.resize(800, 600)

        self.central_widget = QWidget()
        self.layout = QVBoxLayout(self.central_widget)

        # self.label = QLabel("Welcome to Cando")
        self.start_button = QPushButton("Start Timer")
        self.stop_button = QPushButton("Stop Timer")

        # self.layout.addWidget(self.label)
        self.layout.addWidget(self.start_button)
        self.layout.addWidget(self.stop_button)

        MainWindow.setCentralWidget(self.central_widget)
