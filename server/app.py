#!/usr/bin/env python3

from flask import Flask, request
from flask_sock import Sock, ConnectionClosed
import json

app = Flask(__name__)
sock = Sock(app)

storage = {}
clients = []


def update_storage(key, value):
    storage[key] = value
    for c in clients:
        c.send(json.dumps({key: value}))


def reload_storage(data):
    storage.update(data)
    for c in clients:
        c.send(json.dumps(storage))


@sock.route('/stream')
def ws_stream(ws):
    clients.append(ws)
    try:
        ws.send(json.dumps(storage))
        while True:
            data = ws.receive()
            # TODO
    except ConnectionClosed:
        clients.remove(ws)


@app.route("/play")
def route_play():
    page = int(request.args.get('page'))
    update_storage("page", page)
    return "OK"


@app.route("/reload")
def route_reload():
    with open("storage.json", "rt") as f:
        data = json.loads(f.read())
    reload_storage(data)
    return "OK"


@app.route("/")
def route_index():
    return "<p>RpiCaster</p>"


route_reload()

if __name__ == '__main__':
    app.run(debug=True)

