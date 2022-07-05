#!/usr/bin/env python3

import simple_websocket
import json
import time
import sys
import threading

from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtWebEngineWidgets import *

storage = {}


class stream(threading.Thread):
    def __init__(self):
        self.ws = None
        super().__init__()

    def run(self):
        self.running = True
        while True:
            try:
                self.ws = simple_websocket.Client('ws://localhost:5000/stream')
                while True:
                    data = self.ws.receive()
                    data = json.loads(data)
                    storage.update(data)
                    print(storage)
            except (KeyboardInterrupt):
                sys.exit()
            except (EOFError):
                self.ws.close()
            except (simple_websocket.ConnectionClosed, ConnectionRefusedError):
                pass

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

        self.browser = QWebEngineView()
        self.last_url = "about:blank"
        self.browser.setUrl(QUrl(self.last_url))

        self.setCentralWidget(self.browser)

        self.show()
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
        url = storage.get("page_%d"%(storage['page']), {}).get("url")
        if not url:
            return
        if url == self.last_url:
            return
        self.last_url = url
        self.browser.setUrl(QUrl(url))


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    app.exec()


if __name__ == '__main__':
    main()


