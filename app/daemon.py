from pep3143daemon import DaemonContext, PidFile
import signal
import os
import sys
import time

class Daemon:

    def stop(self, pidfile):
        try:
            pid = open(pidfile).readline()
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


    def reload(self, pidfile):
        try:
            pid = open(pidfile).readline()
        except IOError:
            print("Daemon not running, or pidfile was deleted manually")
            sys.exit(1)
        print("Sending SIGUSR1 to Daemon with Pid: {0}".format(pid))
        os.kill(int(pid), signal.SIGUSR1)
        sys.stdout.write("Ok")

    def start(app):
        app.config = app.readConfig(app.config_file)
        app.daemon = DaemonContext(pidfile=PidFile(app.pid)
                                   , signal_map={signal.SIGTERM: app.program_cleanup,
                                                 signal.SIGHUP: app.terminate,
                                                 signal.SIGUSR1: app.reload_program_config}
                                   #                                   ,files_preserve=(sys.stdout)
                                   , stdout=open("/tmp/daemon_stdout.log", 'w')
                                   , stderr=open("/tmp/daemon_stderr.log", 'w')
                                   , gid=app.config["daemon"]["groupid"])
        print("daemon created")
        if app.nodaemon:
            print("no daemon")
            app.daemon.detach_process = False
        else:
            app.daemon.detach_process = True
        try:
            print("before daemon")
            app.daemon.open()
            print("after daemon")
            app.createLogger()
            app.logger.debug('After open')
            app.run()
        except:
            print("Unexpected error:", sys.exc_info()[0])
            raise
