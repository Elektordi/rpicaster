#!/usr/bin/env python3

import time
import requests

WEBHOOK = "https://discord.com/api/webhooks/111/xxxxx"
ALERT_DELAY = 600


def main():
    live_since = None
    while True:
        try:
            r = requests.get("http://127.0.0.1:5000/storage")
            live = r.json().get('live', False)
            if live_since is None and live:
                live_since = time.time()
                print("Live!")
            if not live_since is None:
                if not live:
                    live_since = None
                    print("None...")
                else:
                    if time.time() > live_since + ALERT_DELAY:
                        r = requests.post(WEBHOOK, json={"content": "ATTENTION: Live en ligne sur RpiCaster depuis plus de %d secondes!" % ALERT_DELAY})
                        live_since = time.time()
                        print("Alert!")
        except Exception as ex:
            print(ex)
        time.sleep(10)

if __name__ == '__main__':
    main()

