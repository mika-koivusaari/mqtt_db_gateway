from unittest import TestCase
from unittest import main
from unittest.mock import patch
from unittest.mock import DEFAULT

from configparser import NoSectionError
from configparser import NoOptionError

from app.app import App


class TestApp(TestCase):
#    def test_reload_program_config(self):
#        self.fail()

#    def test_terminate(self):
#        self.fail()

    @patch('app.app.grp')
    @patch('app.app.ConfigParser')
    def test_readConfig_fileread_givenname(self,configparsermock,grpmock):
        app = App(
            cfg='cfg',
            pid='pid',
            nodaemon=True
        )

        instance = configparsermock.return_value

        grpmock.getgrnam.return_value(('name','passwd',1,'users'))

        app.readConfig('file.ini')

        instance.read.assert_called_with('file.ini')

    @patch('app.app.grp')
    @patch('app.app.ConfigParser')
    def test_readConfig_fileread_noname(self, configparsermock, grpmock):
        app = App(
            cfg='cfg',
            pid='pid',
            nodaemon=True
        )

        instance = configparsermock.return_value

        grpmock.getgrnam.return_value(('name', 'passwd', 1, 'users'))

        app.readConfig(None)

        instance.read.assert_called_with('mqtt_db_gateway.ini')

    @patch('app.app.grp')
    @patch('app.app.ConfigParser')
    def test_readConfig_mandatorysection_nodaemon(self, configparsermock, grpmock):
        app = App(
            cfg='cfg',
            pid='pid',
            nodaemon=True
        )

        instance = configparsermock.return_value

        grpmock.getgrnam.return_value(('name', 'passwd', 1, 'users'))

        def get_side_effect(section,key):
            if section == 'sqlalchemy' and key == 'uri':
                raise NoSectionError('Mandatory config test')
            else:
                return DEFAULT

        instance.get.side_effect = get_side_effect
        self.assertRaises(SystemExit, app.readConfig,None)

    @patch('app.app.App.logger')
    @patch('app.app.DaemonContext')
    @patch('app.app.grp')
    @patch('app.app.ConfigParser')
    def test_readConfig_mandatorysection_daemon(self, configparsermock, grpmock, daemonmock, loggermock):
        app = App(
            cfg='cfg',
            pid='pid',
            nodaemon=False
        )

        daemonmock.is_open.return_value = True
        app.daemon=daemonmock

        instance = configparsermock.return_value

        grpmock.getgrnam.return_value(('name', 'passwd', 1, 'users'))

        def get_side_effect(section, key):
            if section == 'sqlalchemy' and key == 'uri':
                raise NoSectionError('Mandatory config test')
            else:
                return DEFAULT

        instance.get.side_effect = get_side_effect
        self.assertIsNone(app.readConfig(conf_file=None))

    @patch('app.app.App.mqttclient')
    @patch('app.app.App.engine')
    def test_program_cleanup_all(self,enginemock,mqttclientmock):
        app = App(
            cfg='cfg',
            pid='pid',
            nodaemon=False
        )

        app.engine = enginemock
        app.mqttclient = mqttclientmock

        app.close_resources()

        mqttclientmock.close.assert_called_with()
        enginemock.close.assert_called_with()

    @patch('app.app.App.engine')
    def test_program_cleanup_engine(self, enginemock):
        app = App(
            cfg='cfg',
            pid='pid',
            nodaemon=False
        )

        app.engine = enginemock

        app.close_resources()

        enginemock.close.assert_called_with()

    @patch('app.app.App.mqttclient')
    def test_program_cleanup_mqtt(self, mqttclientmock):
        app = App(
            cfg='cfg',
            pid='pid',
            nodaemon=False
        )

        app.mqttclient = mqttclientmock

        app.close_resources()

        mqttclientmock.close.assert_called_with()

#    def test_createLogger(self):
#        self.fail()

#    def test_on_connect(self):
#        self.fail()

#    def test_on_message(self):
#        self.fail()

#    def test_exec_process(self):
#        self.fail()

#    def test_load_mqtt_input(self):
#        self.fail()

#    def test_load_rawid_sensorid(self):
#        self.fail()

#    def test_openConnections(self):
#        self.fail()

#    def test_run(self):
#        self.fail()

#    def test_config(self):
#        self.fail()

#    def test_config(self):
#        self.fail()

#    def test_pid(self):
#        self.fail()

#    def test_nodaemon(self):
#        self.fail()

#    def test_stop(self):
#        self.fail()

#    def test_reload(self):
#        self.fail()

#    def test_start(self):
#        self.fail()

if __name__ == '__main__':
    main()
