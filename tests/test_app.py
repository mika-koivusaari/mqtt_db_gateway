from unittest import TestCase
from unittest.mock import patch

from mqtt_db_gateway import App


class TestApp(TestCase):
    def test_reload_program_config(self):
        self.fail()

    def test_terminate(self):
        self.fail()

    @patch('mqtt_db_gateway.grp')
    @patch('mqtt_db_gateway.ConfigParser')
    def test_readConfig_fileread(self,configparsermock,grpmock):
        app = App(
            cfg='cfg',
            pid='pid',
            nodaemon=True
        )

        instance = configparsermock.return_value

        grpmock.getgrnam.return_value(('name','passwd',1,'users'))

        app.readConfig('file.ini')

        instance.read.assert_called_with('file.ini')

    def test_program_cleanup(self):
        self.fail()

    def test_close_resources(self):
        self.fail()

    def test_createLogger(self):
        self.fail()

    def test_on_connect(self):
        self.fail()

    def test_on_message(self):
        self.fail()

    def test_exec_process(self):
        self.fail()

    def test_load_mqtt_input(self):
        self.fail()

    def test_load_rawid_sensorid(self):
        self.fail()

    def test_openConnections(self):
        self.fail()

    def test_run(self):
        self.fail()

    def test_config(self):
        self.fail()

    def test_config(self):
        self.fail()

    def test_pid(self):
        self.fail()

    def test_nodaemon(self):
        self.fail()

    def test_stop(self):
        self.fail()

    def test_reload(self):
        self.fail()

    def test_start(self):
        self.fail()
