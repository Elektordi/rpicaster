#!/usr/bin/env python3

import simple_websocket
import json
import time
import sys
import threading
from copy import copy
import os
import subprocess

from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtWebEngineWidgets import *

storage = {}
default_page = {"type":"status", "text":"RPiCaster display offline."}
cache = {"page": default_page}

VLC_COMMANDLINE = "cvlc --loop --aout=alsa --alsa-audio-device=default:CARD=vc4hdmi --fullscreen --no-osd"


class stream(threading.Thread):
    def __init__(self):
        self.ws = None
        super().__init__()

    def run(self):
        self.running = True
        while True:
            try:
                self.ws = simple_websocket.Client('ws://localhost:5000/stream', ping_interval=60)
                while True:
                    data = self.ws.receive()
                    data = json.loads(data)
                    storage.update(data)
                    print(storage)
                    cache['page'] = storage.get("page_%d"%(storage.get('page', 0)), default_page)
            except (KeyboardInterrupt):
                sys.exit()
            except (EOFError):
                self.ws.close()
            except Exception as ex:
                print(ex)

            if not self.running:
                return
            print("Reconnecting...")
            time.sleep(1)

    def stop(self):
        self.running = False
        if self.ws:
            self.ws.close()


class MainWindow(QMainWindow):
    def __init__(self, *args, **kwargs):
        super(MainWindow,self).__init__(*args, **kwargs)

        self.label_status = QLabel()
        self.label_status.setStyleSheet("color: grey;")
        self.label_status.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.label_status.setFont(QFont("Arial", 10))

        self.label_message = QLabel()
        self.label_message.setAlignment(Qt.AlignCenter)
        self.label_message.setFont(QFont("Arial", 64, QFont.Bold))
        self.label_message.setWordWrap(True)

        self.browser = QWebEngineView()
        self.browser_img = QWebEngineView()

        self.black = QWidget()
        self.layout = QStackedLayout()
        self.layout.addWidget(self.black)
        self.layout.addWidget(self.label_status)
        self.layout.addWidget(self.label_message)
        self.layout.addWidget(self.browser)
        self.layout.addWidget(self.browser_img)

        self.mainwidget = QWidget()
        self.mainwidget.setLayout(self.layout)
        self.setCentralWidget(self.mainwidget)

        self.last_url = ""
        self.last_url_img = ""
        self.player_process = None
        self.last_page = default_page
        self.content(self.last_page)

        self.setStyleSheet("background-color: black; color: white;")
        self.show()
        if "--fake-fullscreen" in sys.argv:
            self.setGeometry(0, 0, 1920, 1080)
        else:
            self.showFullScreen()

        self.stream = stream()
        self.stream.start()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.tick)
        self.timer.start(1000)

    def closeEvent(self,event):
        self.stream.stop()
        event.accept()

    def tick(self):
        if cache['page'] == self.last_page:
            return
        self.last_page = copy(cache['page'])
        self.content(self.last_page)

    def content(self, page):
        pagetype = page.get("type", "unknow")
        if pagetype == "status":
            text = page.get("text", '')
            self.label_status.setText(text)
            self.layout.setCurrentWidget(self.label_status)
        elif pagetype == "message":
            text = page.get("text", '')
            self.label_message.setText(text)
            self.layout.setCurrentWidget(self.label_message)
        elif pagetype == "image":
            url = page.get('url', 'about:blank')
            if url != self.last_url_img:
                self.last_url_img = url
                self.browser_img.setUrl(QUrl(url))
                # No need for cache, integrated in QWebEngineView chrome engine
            self.layout.setCurrentWidget(self.browser_img)
        elif pagetype == "web":
            url = page.get('url', 'about:blank')
            if url != self.last_url:
                self.last_url = url
                self.browser.setUrl(QUrl(url))
            self.layout.setCurrentWidget(self.browser)
        elif pagetype == "videostream":
            self.layout.setCurrentWidget(self.black)
            cmd = VLC_COMMANDLINE.split(" ") + [page.get('url', 'invalid:')]
            try:
                self.player_process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL)
            except OSError as ex:
                print("Failed to start player (%s). Exception: %s"%(cmd, ex))
        else:
            text = "Invalid page type: %s"%(pagetype)
            self.label_status.setText(text)
            self.layout.setCurrentWidget(self.label_status)

        if self.player_process is not None and not pagetype == "videostream":
            print("Killing player...")
            try:
                self.player_process.terminate()
            except OSError as ex:
                print("Failed to terminate player. Exception: %s"%(ex))
            self.player_process = None


def main():
    app = QApplication(sys.argv)
    cursor = QCursor(Qt.BlankCursor)
    app.setOverrideCursor(cursor)
    app.changeOverrideCursor(cursor)

    window = MainWindow()
    app.exec()


if __name__ == '__main__':
    main()


