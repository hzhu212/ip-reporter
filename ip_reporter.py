# -*- coding: utf-8 -*-

import os
import time
import inspect
import socket
import logging

from email_util import EmailSender


class IpReporter(object):
    def __init__(self):
        self.app_root = self._get_app_root()
        self.logger = self._get_logger()
        self.current_ip = self._get_current_ip()
        self.msg_template = '\n'.join(['主机名：%s', '原 IP 地址：%s', '新 IP 地址：%s', '发生时间：%s'])
        self.sender = EmailSender(self.app_root)
        self.time_slice = 5
        self.cycle_time = 60 * 20

    def _get_app_root(self):
        this_file = inspect.getfile(inspect.currentframe())
        return os.path.dirname(os.path.abspath(this_file))

    def _get_logger(self):
        logger = logging.getLogger('IpReporter')
        logger.setLevel(logging.DEBUG)
        log_file = os.path.join(self.app_root, 'log', 'reporter.log')
        handler = logging.FileHandler(log_file, encoding='utf8')
        formatter = logging.Formatter('[%(asctime)s] %(levelname)s: %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        return logger

    def _get_current_ip(self):
        current_ip = None
        file_current_ip = os.path.join(self.app_root, 'current_ip.txt')
        if os.path.isfile(file_current_ip):
            with open(file_current_ip, 'r') as f:
                current_ip = f.read().strip()
                if not current_ip: current_ip = None
        return current_ip

    def _save_current_ip(self):
        file_current_ip = os.path.join(self.app_root, 'current_ip.txt')
        with open(file_current_ip, 'w') as f:
            f.write(self.current_ip)

    def _handle_ip_change(self):
        hostname = socket.gethostname()
        detected_ip = socket.gethostbyname(hostname)
        if detected_ip != self.current_ip:
            self.logger.info('IP address changed from %s to %s.' %(self.current_ip, detected_ip))
            _time = time.strftime('%Y-%m-%d %H:%M:%S', tuple(time.localtime()))
            msg = self.msg_template %(hostname, self.current_ip, detected_ip, _time)
            mail = self.sender.make_email(msg)
            self.sender.send_email(mail)
            self.current_ip = detected_ip
            self._save_current_ip()
        else:
            self.logger.info('IP address (%s) remains unchanged.' %(self.current_ip,))

    def loop(self):
        slice_count = int(self.cycle_time / self.time_slice)
        n = 1
        while n:
            n = n - 1
            if n == 0:
                self._handle_ip_change()
                n = slice_count
            time.sleep(self.time_slice)


if __name__ == '__main__':
    reporter = IpReporter()
    reporter.logger.info('========================= ip_reporter started =========================')
    print('\n*** IP Reporter is running, please don\'t close the window! ***')
    try:
        reporter.loop()
    except Exception as e:
        reporter.logger.exception(e)
    finally:
        reporter.logger.info('========================= ip_reporter closed =========================\n')

