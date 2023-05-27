import sys
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QPushButton,
    QMessageBox,
    QVBoxLayout,
    QWidget,
)
from PyQt5.QtGui import QFont
import subprocess
from scapy.all import *


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.setGeometry(400, 400, 400, 200)
        self.setWindowTitle("Cut-Thorough")
        font = QFont("Verdana", 12)

        button1 = QPushButton("동영상 허용")
        button1.clicked.connect(self.allow_videos)
        button1.setMinimumSize(150, 50)
        button1.setFont(font)
        button1.setStyleSheet(
            """
                QPushButton {
                    color: white;
                    background-color: #5cb85c;
                    border-style: outset;
                    border-width: 2px;
                    border-radius: 10px;
                    border-color: beige;
                    font: bold 14px;
                    padding: 6px;
                }
                QPushButton:pressed {
                    background-color: #3e8e41;
                    border-style: inset;
                }
            """
        )

        button2 = QPushButton("동영상 차단")
        button2.clicked.connect(self.block_videos)
        button2.setMinimumSize(150, 50)
        button2.setFont(font)
        button2.setStyleSheet(
            """
                QPushButton {
                    color: white;
                    background-color: #d9534f;
                    border-style: outset;
                    border-width: 2px;
                    border-radius: 10px;
                    border-color: beige;
                    font: bold 14px;
                    padding: 6px;
                }
                QPushButton:pressed {
                    background-color: #C9302C;
                    border-style: inset;
                }
            """
        )

        layout = QVBoxLayout()
        layout.addWidget(button1)
        layout.addWidget(button2)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.resize(self.layout().sizeHint())

    # HTTP 기반의 HLS/DASH 동영상 허용
    def allow_videos(self):
        cmd = 'sudo iptables -D INPUT -p tcp --dport 0:65535 -m string --string "GET /" --algo kmp -m string --string ".m3u8" --algo kmp -j DROP;sudo iptables -D INPUT -p tcp --dport 0:65535 -m string --string "GET /" --algo kmp -m string --string ".ts" --algo kmp -j DROP; sudo iptables -D INPUT -p tcp --dport 0:65535 -m string --string "GET /" --algo kmp -m string --string ".m4s" --algo kmp -j DROP; sudo iptables -D INPUT -p tcp --dport 0:65535 -m string --string "GET /" --algo kmp -m string --string ".mpd" --algo kmp -j DROP'
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            QMessageBox.information(
                self,
                "Success",
                "HTTP기반 HLS/DASH 프로토콜 동영상 허용 (지연과 트래픽에 주의하세요.)",
            )
        else:
            QMessageBox.warning(
                self,
                "Error",
                "동영상 허용에 실패했습니다; " + result.stderr,
            )

    # HTTP 기반의 HLS/DASH 동영상을 차단
    def block_videos(self):
        cmd = 'sudo iptables -A INPUT -p tcp —dport 0:65535 -m string —string "GET /" —algo kmp -m string —string ".m3u8" —algo kmp -j DROP;sudo iptables -A INPUT -p tcp —dport 0:65535 -m string —string "GET /" —algo kmp -m string —string ".ts" —algo kmp -j DROP; sudo iptables -A INPUT -p tcp —dport 0:65535 -m string —string "GET /" —algo kmp -m string —string ".m4s" —algo kmp -j DROP; sudo iptables -A INPUT -p tcp —dport 0:65535 -m string —string "GET /" —algo kmp -m string —string ".mpd" —algo kmp -j DROP'
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            QMessageBox.information(
                self,
                "Success",
                "HTTP기반의 HLS/DASH 프로토콜 동영상 차단 (관리자에게 문의하여 HTTPS로 동영상을 요청하세요.)",
            )
        else:
            QMessageBox.warning(
                self,
                "Error",
                "동영상 차단에 실패했습니다; " + result.stderr,
            )


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
