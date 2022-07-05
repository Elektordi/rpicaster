#!/usr/bin/env python3

import simple_websocket
import json
import time
import sys

storage = {}

def main():
    while True:
        try:
            ws = simple_websocket.Client('ws://localhost:5000/stream')
            while True:
                data = ws.receive()
                data = json.loads(data)
                storage.update(data)
                print(storage)
        except (KeyboardInterrupt):
            ws.close()
            sys.exit()
        except (EOFError):
            ws.close()
        except (simple_websocket.ConnectionClosed, ConnectionRefusedError):
            pass

        print("Reconnecting...")
        time.sleep(1)

if __name__ == '__main__':
    main()


