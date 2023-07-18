#!/usr/bin/env python3

from flask import Flask, request
from flask_sock import Sock, ConnectionClosed
import json

app = Flask(__name__)
sock = Sock(app)

app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 3600*24
app.config['SOCK_SERVER_OPTIONS'] = {'ping_interval': 60}

storage = {}
clients = []


def broadcast(data):
    print("=> %r"%(data))
    for c in clients:
        try:
            c.send(json.dumps(data))
        except ConnectionClosed:
            print("Client disconnected: %s:%d"%(c.remote_addr, c.remote_port))
            clients.remove(c)


@sock.route('/stream')
def ws_stream(ws):
    ws.remote_addr, ws.remote_port = ws.sock.getpeername()
    print("Client connected: %s:%d"%(ws.remote_addr, ws.remote_port))
    clients.append(ws)
    try:
        ws.send(json.dumps(storage))
        while True:
            data = ws.receive()
            # TODO
    except ConnectionClosed:
        print("Client disconnected: %s:%d"%(ws.remote_addr, ws.remote_port))
        clients.remove(ws)


@app.route("/play")
def route_play():
    page = int(request.args.get('page'))
    storage["page"] = page
    broadcast({"page": page})
    return "OK"


@app.route("/storage")
def route_storage():
    return json.dumps(storage)


@app.route("/golive")
def route_golive():
    if not storage.get('rtmp'):
        return "NOT LIVE (RTMP)"
    storage['live'] = True
    storage['page'] = int(storage.get('interrupt_live_page'))
    broadcast({"page": storage['page']})
    return "OK"


@app.route("/endlive")
def route_endlive():
    if not storage.get('rtmp'):
        return "NOT LIVE (RTMP)"
    if storage.get('page') != int(storage.get('interrupt_live_page')):
        return "NOT LIVE (PAGE)"
    storage['live'] = False
    storage['page'] = storage.get('interrupt_end_page')
    broadcast({"page": storage['page']})
    return "OK"


@app.route("/reload")
def route_reload():
    with open("storage.json", "rt") as f:
        data = json.loads(f.read())
    storage.update(data)
    if not storage.get('page'):
        storage['page'] = int(storage.get('default_page', 0))
    broadcast(data)
    return "OK"


@app.route("/srs_callback", methods=["POST"])
def route_srs():
    data = request.get_json()
    print("Got SRS callback: %s"%(data))
    if data.get('app') != 'live' or data.get('stream') != 'livestream':
        print("Invalid app/stream.")
        return "1"
    if data.get('action') == 'on_publish':
        storage['rtmp'] = True
        if storage.get('interrupt_rtmp_page'):
            storage['live'] = True
            storage['page'] = int(storage.get('interrupt_rtmp_page'))
            broadcast({"page": storage['page']})
    elif data.get('action') == 'on_unpublish':
        storage['rtmp'] = False
        if storage.get('interrupt_end_page'):
            storage['live'] = False
            storage['page'] = int(storage.get('interrupt_end_page'))
            broadcast({"page": storage['page']})
    return "0"  # 0 = OK


@app.route("/")
def route_index():
    return "<p>RpiCaster</p>"


route_reload()

if __name__ == '__main__':
    app.run(debug=True)

