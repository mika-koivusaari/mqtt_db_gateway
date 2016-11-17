#!/usr/bin/python
import logging
import time
import re
import argparse
import sys
import os
import signal
import grp
from configparser import SafeConfigParser
from configparser import NoSectionError
from configparser import NoOptionError

import paho.mqtt.client as mqtt
from pep3143daemon import DaemonContext, PidFile
import sqlalchemy
from sqlalchemy.orm import sessionmaker

import model

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
        app = App(
            cfg=parsed_args.cfg,
            pid=parsed_args.pid,
            nodaemon=parsed_args.nodaemon
        )
        app.stop()

    elif parsed_args.method == 'start':
        app = App(
            cfg=parsed_args.cfg,
            pid=parsed_args.pid,
            nodaemon=parsed_args.nodaemon
        )
        app.start()

    elif parsed_args.method == 'reload':
        app = App(
                cfg=parsed_args.cfg,
                pid=parsed_args.pid,
                nodaemon=parsed_args.nodaemon
        )
        app.reload()

class App:

    config = None
    logger = None
    loggerfh = None
    daemon = None
    mqttclient = None
    engine = None
    Session = None

    def reload_program_config(self,signum, frame):
        conf=self.readConfig(self._config_file)
        if conf is not None:
            self.config=conf
            self.close_resources()
            self.openConnections()
            self.createLogger()

    def terminate(self,signum, frame):
        self.logger.info("terminate")

    def readConfig(self,conf_file=None):
        config = SafeConfigParser()
        if (conf_file is None):
            conf_file = 'mqtt_db_gateway.ini'
        config.read(conf_file)
        confData = {}
        #Mandatory configurations
        try:
            sqlalchemy = {}
            sqlalchemy['uri'] = config.get('sqlalchemy','uri')
            sqlalchemy['echo'] = config.getboolean('sqlalchemy','echo')

            mqttbroker = {}
            mqttbroker['host'] = config.get('mqttbroker', 'host')
            mqttbroker['port'] = config.getint('mqttbroker', 'port')

            daemonData = {}
            groupname = config.get('daemon', 'group')
            daemonData['groupid'] = grp.getgrnam(groupname)[2]


        except NoSectionError:
            if self.daemon is not None and self.daemon.is_open:
                self.logger.error("Error in "+str(conf_file))
                return None
            else:
                print ('Error in '+conf_file)
                exit()

        #Optional configurations
        loggerData = {}
        try:
            try:
                loggerData['formatter'] = config.get('logger', 'formatter')
            except  NoOptionError:
                loggerData['formatter'] = None
            try:
                loggerData['file'] = config.get('logger', 'file')
            except  NoOptionError:
                loggerData['file'] = None
            try:
                loggerData['level'] = config.get('logger', 'level')
            except  NoOptionError:
                loggerData['level'] = None
        except NoSectionError:
            loggerData['formatter'] = None
            loggerData['file'] = None
            loggerData['level'] = None

        confData['mqttbroker'] = mqttbroker
        confData['logger'] = loggerData
        confData['daemon'] = daemonData
        confData['sqlalchemy'] = sqlalchemy

        if self.daemon is not None and self.daemon.is_open:
            self.logger.info("Config loaded from " + str(conf_file))
        else:
            print("Config loaded from " + str(conf_file))
        return confData

    def __init__(self, cfg, pid, nodaemon):
        self._config_file = cfg
        self._pid = pid
        self._nodaemon = nodaemon

    def program_cleanup(self,signum, frame):
        self.logger.info('Program cleanup')
        self.close_resources()
        raise SystemExit('Terminating on signal {0}'.format(signum))

    def close_resources(self):
        if self.mqttclient is not None:
            self.mqttclient.close()
        if self.engine is not None:
            self.engine.close()
        
#        if self.db is not None:
#            self.cursor.close(
#
#            )
#            self.db.close()
#        if self.ser is not None:
#            self.ser.close()

    def createLogger(self):
        if self.logger is not None and self.daemon is not None and self.daemon.is_open:
            self.logger.Debug("Create logger")
        else:
            print ('Create logger')

        loggerConf = self.config['logger']
        if self.logger is None:
            self.logger = logging.getLogger('MQTT gateway')

        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s" if loggerConf["formatter"]==None else loggerConf["formatter"])
        if self.loggerfh is not None:
            self.loggerfh.close()
            self.logger.removeHandler(self.loggerfh)
        self.loggerfh = logging.FileHandler("/var/log/mqttgateway/mqttgateway.log" if loggerConf["file"]==None else loggerConf["file"])
        self.loggerfh.setFormatter(formatter)
        self.logger.addHandler(self.loggerfh)
        level = {
            "CRITICAL": logging.CRITICAL,
            "ERROR": logging.ERROR,
            "WARNING": logging.WARNING,
            "INFO": logging.INFO,
            "DEBUG": logging.DEBUG,
            "NOTSET": logging.NOTSET
        }
        self.logger.setLevel(level.get(loggerConf["level"],logging.INFO))
        self.logger.debug('Logger created.')

#    def read_subscriptions_conf(self):


    # The callback for when the client receives a CONNACK response from the server.
    def on_connect(self, client, userdata, flags, rc):
        self.logger.debug('Connected to MQTT broker with result code '+str(rc))
        # Subscribing in on_connect() means that if we lose the connection and
        # reconnect then subscriptions will be renewed.
        mqttinput = self.config['mqttinput']
        self.logger.debug(mqttinput)
        for key in  mqttinput:
            input = mqttinput[key]
            client.subscribe(input.topic)
            self.logger.debug('Subscribed to '+input.topic)

    # The callback for when a PUBLISH message is received from the server.
    def on_message(self, client, userdata, msg):
        self.logger.debug('Got message Topic: '+ msg.topic+' Message: '+str(msg.payload))
#        self.logger.debug('Topic is for subcscribe '+userdata)

    def load_mqtt_input(self):
        self.logger.debug('load_mqtt_input')
        session = self.Session()
        mqttInput = {}
        for instance in session.query(model.Mqtt_input).all():
            self.logger.debug(instance)
            mqttInput[instance.topic]=instance
        self.config['mqttinput'] = mqttInput
        self.logger.debug('Loaded subscriptions')
        self.logger.debug(mqttInput)

    def openConnections(self):
        self.logger.debug("openConnections")

#        try:
        self.logger.debug("Open DB connection")
        sqlalchemyConf = self.config['sqlalchemy']
        self.logger.debug("URI="+sqlalchemyConf['uri'])
        self.logger.debug("Echo="+str(sqlalchemyConf['echo']))
        self.logger.debug("Create engine")
        self.engine = sqlalchemy.create_engine(sqlalchemyConf['uri'], echo=sqlalchemyConf['echo'])
        self.logger.debug("Connect")
        self.engine.connect()
        self.Session = sessionmaker(bind=self.engine)
        self.load_mqtt_input()
#        except Exception as ex:
#            self.logger.error('Error opening DB: '+ str(ex))
#            self.logger.error(ex)

        self.logger.debug("Open MQTT broker connection.")
        # connect
        self.mqttclient = mqtt.Client()
        self.mqttclient.on_connect = self.on_connect
        self.mqttclient.on_message = self.on_message

        brokerConf = self.config['mqttbroker']
        self.mqttclient.connect(brokerConf['host'],int(brokerConf['port']), 60)
        # NonBlocking call that processes network traffic, dispatches callbacks and
        # handles reconnecting.
        # Other loop*() functions are available that give a threaded interface and a
        # manual interface.
        self.mqttclient.loop_start()


    def run(self):
        self.openConnections()
        self.logger.debug("Run")

        self.logger.debug("Start")
        while True:
            try:
                time.sleep(59)

                self.logger.debug("loop")

            except:
                self.logger.error(sys.exc_info()[0])
                self.logger.error(sys.exc_info()[1])
                self.logger.error(sys.exc_info()[2])
                raise

    @property
    def config(self):
        return self._config

    @config.setter
    def config(self, value):
        'setting'
        self._config = value

    @property
    def pid(self):
        return self._pid


    @property
    def nodaemon(self):
        return self._nodaemon


    def stop(self):
        try:
            pid = open(self.pid).readline()
        except IOError:
            print("Daemon already gone, or pidfile was deleted manually")
            sys.exit(1)
        print("terminating Daemon with Pid: {0}".format(pid))
        os.kill(int(pid), signal.SIGTERM)
        sys.stdout.write("Waiting...")
        while os.path.isfile(self.pid):
            sys.stdout.write(".")
            sys.stdout.flush()
            time.sleep(0.5)
        print("Gone")

    def reload(self):
        try:
            pid = open(self.pid).readline()
        except IOError:
            print("Daemon not running, or pidfile was deleted manually")
            sys.exit(1)
        print("Sending SIGUSR1 to Daemon with Pid: {0}".format(pid))
        os.kill(int(pid), signal.SIGUSR1)
        sys.stdout.write("Ok")

    def start(self):
        self.config=self.readConfig(self._config_file)
        self.daemon = DaemonContext(pidfile=PidFile(self.pid)
                                   ,signal_map={signal.SIGTERM: self.program_cleanup,
                                                signal.SIGHUP: self.terminate,
                                                signal.SIGUSR1: self.reload_program_config}
#                                   ,files_preserve=(sys.stdout)
                                   ,stdout=open("/tmp/daemon_stdout.log",'w')
                                   ,stderr=open("/tmp/daemon_stderr.log",'w')
                                   ,gid=self.config["daemon"]["groupid"])
        print ("daemon created")
        if self.nodaemon:
            print("no daemon")
            self.daemon.detach_process = False
        else:
            self.daemon.detach_process = True
        try:
            print("before daemon")
            self.daemon.open()
            print ("after daemon")
            self.createLogger()
            self.logger.debug('After open')
            self.run()
        except:
            print ("Unexpected error:", sys.exc_info()[0])
            raise



if __name__ == "__main__":
  main()
