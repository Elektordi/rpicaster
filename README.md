# rpicaster
Raspberry-PI based dynamic display solution

## Client

Usage:
`./client.py`

Dependencies:
`apt-get install python3 python3-pip libqt5gui5 libqt5webengine5 python3-pyqt5 python3-pyqt5.qtwebengine vlc`

Usage without desktop manager:
`apt-get install xinit`

`sudo xinit /bin/sh -c "sudo -u pi ./client.py"`

## Server

Usage:
`./app.py`
