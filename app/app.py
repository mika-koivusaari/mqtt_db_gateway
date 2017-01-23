import grp
import sys
import logging
import re
import time

from configparser import ConfigParser
from configparser import NoOptionError
from configparser import NoSectionError

import paho.mqtt.client as mqtt
import sqlalchemy
from app import model
from sqlalchemy.orm import sessionmaker

from pep3143daemon import DaemonContext

class App:
    config = None
    logger = None
    loggerfh = None
    daemon = None
    mqttclient = None
    engine = None
    Session = None

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

    def reload_program_config(self, signum, frame):
        conf = self.readConfig(self._config_file)
        if conf is not None:
            self.config = conf
            self.close_resources()
            self.openConnections()
            self.createLogger()

    def terminate(self, signum, frame):
        self.logger.info("terminate")

    def program_cleanup(self, signum, frame):
        self.logger.info('Program cleanup')
        self.close_resources()
        raise SystemExit('Terminating on signal {0}'.format(signum))

    def readConfig(self, conf_file=None):
        config = ConfigParser()
        if conf_file is None:
            conf_file = 'mqtt_db_gateway.ini'
        config.read(conf_file)
        confData = {}
        # Mandatory configurations
        try:
            sqlalchemy = {}
            sqlalchemy['uri'] = config.get('sqlalchemy', 'uri')
            sqlalchemy['echo'] = config.getboolean('sqlalchemy', 'echo')
            sqlalchemy['pool_recycle'] = config.getint('sqlalchemy','pool_recycle')

            mqttbroker = {}
            mqttbroker['host'] = config.get('mqttbroker', 'host')
            mqttbroker['port'] = config.getint('mqttbroker', 'port')

            daemonData = {}
            groupname = config.get('daemon', 'group')
            daemonData['groupid'] = grp.getgrnam(groupname)[2]

        except NoSectionError:
            if self.daemon is not None and self.daemon.is_open:
                self.logger.error("Error in " + str(conf_file))
                return None
            else:
                print('Error in ' + conf_file)
                exit()

        # Optional configurations
        loggerData = {}
        try:
            try:
                loggerData['formatter'] = config.get('logger', 'formatter')
            except NoOptionError:
                loggerData['formatter'] = None
            try:
                loggerData['file'] = config.get('logger', 'file')
            except NoOptionError:
                loggerData['file'] = None
            try:
                loggerData['level'] = config.get('logger', 'level')
            except NoOptionError:
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


    def close_resources(self):
        if self.mqttclient is not None:
            self.mqttclient.close()
        if self.engine is not None:
            self.engine.close()

    def createLogger(self):
        if self.logger is not None and self.daemon is not None and self.daemon.is_open:
            self.logger.Debug("Create logger")
        else:
            print('Create logger')

        loggerConf = self.config['logger']
        print(loggerConf)
        if self.logger is None:
            self.logger = logging.getLogger('MQTT gateway')

        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s" if loggerConf["formatter"] is None else
            loggerConf["formatter"])
        if self.loggerfh is not None:
            self.loggerfh.close()
            self.logger.removeHandler(self.loggerfh)
        self.loggerfh = logging.FileHandler(
            "/var/log/mqttgateway/mqttgateway.log" if loggerConf["file"] is None else loggerConf["file"])
#        self.loggerfh = logging.FileHandler("/var/log/mqttgateway/mqttgateway.log")
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
        self.logger.setLevel(level.get(loggerConf["level"], logging.INFO))
        self.logger.debug('Logger created.')
        print('logger created.')

    #    def read_subscriptions_conf(self):

    # The callback for when the client receives a CONNACK response from the server.
    def on_connect(self, client, userdata, flags, rc):
        self.logger.debug('Connected to MQTT broker with result code ' + str(rc))
        # Subscribing in on_connect() means that if we lose the connection and
        # reconnect then subscriptions will be renewed.
        mqttinput = self.config['mqttinput']
        self.logger.debug(mqttinput)
        for key in mqttinput:
            input = mqttinput[key]
            client.subscribe(input.topic)
            self.logger.debug('Subscribed to ' + input.topic)

    # The callback for when a PUBLISH message is received from the server.
    def on_message(self, client, userdata, msg):
        from datetime import datetime
        from dateutil import tz
        self.logger.debug('Got message Topic: ' + msg.topic + ' Message: ' + str(msg.payload))
        mqttinput = self.config['mqttinput']
        for key in mqttinput:
            if mqtt.topic_matches_sub(key, msg.topic):
                try:
                    input = mqttinput[key]
                    m = re.match(input.topic_regexp, msg.topic)
                    rawid = m.group('rawid')
                    id = self.config['rawidsensorid'][rawid]
                    m = re.match(input.message_regexp, msg.payload.decode('UTF-8'))
                    try: #datetime is not mandatory
                        _datetime = m.group('datetime')
                    except IndexError:
                        _datetime = None
                    value = m.group('value')
                    if input.process_value is not None and input.process_value != "":
                        if input.process_value_type == input.PROCESS_TYPE_EXPRESSION:
                            value = eval(input.process_value, {"__builtins__": {}},
                                         {"value": int(value), "round": round})
                        elif input.process_value_type == input.PROCESS_TYPE_EXEC:
                            value = self.exec_process(input.process_value, value)
                    if input.process_time is not None and input.process_time != "":
                        if input.process_time_type == input.PROCESS_TYPE_EXPRESSION:
                            print(input.process_time)
                            _datetime = eval(input.process_time, None, {"value": _datetime, "round": round, "datetime": datetime, "tz": tz})
                        elif input.process_time_type == input.PROCESS_TYPE_EXEC:
                            _datetime = self.exec_process(input.process_time, datetime)
                    else: #no timestamp in input, use current time
                        _datetime = datetime.now()
                        self.logger.debug('rawid=' + rawid + ' id=' + str(id) + ' datetime=' + str(_datetime) + ' value=' + str(value))
                    if isinstance(value,(int,float)):
                        self.logger.debug('Value is number, save to data.')
                        data = model.Data(sensorid=id, time=_datetime, value=value)
                    else:
                        self.logger.debug('Value is text, save to datatext.')
                        data = model.DataText(sensorid=id, time=_datetime, text=value)
                    session = self.Session()
                    session.add(data)
                    session.commit()
                except KeyError:
                    self.logger.debug("rawid '" + rawid + "' not found.")

    #
    def exec_process(self, process, input):
        self.logger.debug("exec_process")
        self.logger.debug(input)
        self.logger.debug(process)
        # self=None
        input_value = input
        return_value = None
        arvo = "alku"
        self.logger.debug(locals())
        exec(process, globals(), locals())
        self.logger.debug(locals())
        self.logger.debug(return_value)
        self.logger.debug("arvo=" + str(arvo))
        return return_value

    def load_mqtt_input(self):
        self.logger.debug('load_mqtt_input')
        session = self.Session()
        mqttInput = {}
        for instance in session.query(model.MqttInput).all():
            self.logger.debug(instance)
            mqttInput[instance.topic] = instance
        self.config['mqttinput'] = mqttInput
        self.logger.debug('Loaded subscriptions')
        self.logger.debug(mqttInput)

    def load_rawid_sensorid(self):
        self.logger.debug('load_rawid_sensorid')
        session = self.Session()
        rawidsensorid = {}
        for instance in session.query(model.RawidSensorid).all():
            self.logger.debug(instance)
            rawidsensorid[instance.rawid] = instance.sensorid
        self.config['rawidsensorid'] = rawidsensorid
        self.logger.debug('Loaded rawid sensorid pairs')
        self.logger.debug(rawidsensorid)

    def openConnections(self):
        self.logger.debug("openConnections")

        #        try:
        self.logger.debug("Open DB connection")
        sqlalchemyConf = self.config['sqlalchemy']
        self.logger.debug("URI=" + sqlalchemyConf['uri'])
        self.logger.debug("Echo=" + str(sqlalchemyConf['echo']))
        self.logger.debug("Create engine")
        self.engine = sqlalchemy.create_engine(sqlalchemyConf['uri'], echo=sqlalchemyConf['echo'], pool_recycle=sqlalchemyConf['pool_recycle'])
        self.logger.debug("Connect")
        self.engine.connect()
        self.Session = sessionmaker(bind=self.engine)
        self.load_mqtt_input()
        self.load_rawid_sensorid()
        #        except Exception as ex:
        #            self.logger.error('Error opening DB: '+ str(ex))
        #            self.logger.error(ex)

        self.logger.debug("Open MQTT broker connection.")
        # connect
        self.mqttclient = mqtt.Client()
        self.mqttclient.on_connect = self.on_connect
        self.mqttclient.on_message = self.on_message

        brokerConf = self.config['mqttbroker']
        self.mqttclient.connect(brokerConf['host'], int(brokerConf['port']), 60)
        # NonBlocking call that processes network traffic, dispatches callbacks and
        # handles reconnecting.
        # Other loop*() functions are available that give a threaded interface and a
        # manual interface.
        self.mqttclient.loop_start()

    @property
    def config(self):
        return self._config

    @config.setter
    def config(self, value):
        'setting'
        self._config = value

    @property
    def config_file(self):
        return self._config_file

    @property
    def pid(self):
        return self._pid

    @property
    def nodaemon(self):
        return self._nodaemon
