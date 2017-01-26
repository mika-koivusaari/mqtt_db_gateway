#!/usr/bin/python
# -*- coding: utf-8 -*-
import argparse

from app.app import App
from app.daemon import Daemon

def main():
    parser = argparse.ArgumentParser(description="MQTT DB gateway")

    parser.add_argument('method', choices=['start', 'stop', 'reload'])

    parser.add_argument("--cfg", dest="cfg", action="store",
                        default="/etc/mqtt_db_gateway/mqtt_db_gateway.ini",
                        help="Full path to configuration")

    parser.add_argument("--pid", dest="pid", action="store",
                        default="/var/run/mqtt_db_gateway/mqtt_db_gateway.pid",
                        help="Full path to PID file")

    parser.add_argument("--nodaemon", dest="nodaemon", action="store_true",
                        help="Do not daemonize, run in foreground")

    parsed_args = parser.parse_args()

    if parsed_args.method == 'stop':
        Daemon.stop(parsed_args.pid)

    elif parsed_args.method == 'start':
        app = App(
            cfg=parsed_args.cfg,
            pid=parsed_args.pid,
            nodaemon=parsed_args.nodaemon
        )
        Daemon.start(app)

    elif parsed_args.method == 'reload':
        Daemon.reload(parsed_args.pid)


if __name__ == "__main__":
    main()
