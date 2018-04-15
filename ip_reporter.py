import inspect
import logging
import os
import socket
import sys
import time

from email_util import EmailSender


class IpReporter(object):
    def __init__(self):
        self.logger = self._get_logger()
        self.sender = EmailSender()
        # check ip address every 10 minutes
        self.cycle_time = 60 * 10
        # the minimum timing scale is 5 seconds
        self.time_slice = 5

    def _get_logger(self):
        logger = logging.getLogger('IpReporter')
        logger.setLevel(logging.DEBUG)
        LOG_FILENAME = './log/reporter.log'
        handler_file = logging.FileHandler(LOG_FILENAME, encoding='utf8')
        handler_console = logging.StreamHandler(stream=sys.stdout)
        handler_file.setLevel(logging.DEBUG)
        handler_console.setLevel(logging.INFO)
        formatter = logging.Formatter('[%(asctime)s] %(name)s %(levelname)s: %(message)s')
        handler_file.setFormatter(formatter)
        handler_console.setFormatter(formatter)
        logger.addHandler(handler_file)
        logger.addHandler(handler_console)
        return logger

    def _get_current_ip(self):
        """get cached current ip address from file"""
        current_ip = None
        FILE_CURRENT_IP = './current_ip.txt'
        if os.path.isfile(FILE_CURRENT_IP):
            with open(FILE_CURRENT_IP, 'r') as f:
                current_ip = f.read().strip()
                current_ip = current_ip or None
        return current_ip

    def _save_current_ip(self, current_ip):
        """save current ip to file"""
        current_ip = current_ip or ''
        FILE_CURRENT_IP = './current_ip.txt'
        with open(FILE_CURRENT_IP, 'w') as f:
            f.write(current_ip)

    @staticmethod
    def _get_all_ips():
        """get all ip address in local host, including ipv4 and ipv6"""
        addrs = socket.getaddrinfo(socket.gethostname(), None)
        return [a[4][0] for a in addrs]

    def _get_outer_ip(self):
        """get the external network IP address, by which we can access this computer from remote"""
        all_ips = self._get_all_ips()
        # filter off ipv6, intranet IP address and reserved IP address
        filt = lambda s: (':' not in s) \
            and (not s.startswith('192.168.')) \
            and (not s.startswith('169.254.'))
        outer_ips = [ip for ip in all_ips if filt(ip)]
        if not outer_ips:
            self.logger.error('*** Error: Failed to get outer IP address ***')
            return
        elif len(outer_ips) > 1:
            self.logger.warning('*** Error: Too many outer IP addresses: %s ***' %outer_ips)
            return outer_ips[0]
        return outer_ips[0]

    def _handle_ip_change(self):
        """send email and save the newer IP address when IP changed"""
        hostname = socket.gethostname()
        current_ip = self._get_current_ip()
        detected_ip = self._get_outer_ip()
        if detected_ip != current_ip:
            self.logger.info('IP address changed from %s to %s.' %(current_ip, detected_ip))
            _time = time.strftime('%Y-%m-%d %H:%M:%S', tuple(time.localtime()))
            MSG_TEMPLATE = '\n'.join(['Hostname：%s', 'Old IP：%s', 'New IP：%s', 'Occur at：%s'])
            msg = MSG_TEMPLATE %(hostname, current_ip, detected_ip, _time)
            self.sender.send_email(msg)
            self._save_current_ip(detected_ip)
        else:
            self.logger.info('IP address (%s) remains unchanged.' %(current_ip,))

    def loop(self):
        """main loop"""
        slice_count = int(self.cycle_time / self.time_slice)
        n = 1
        while True:
            n = n - 1
            if n == 0:
                self._handle_ip_change()
                n = slice_count
            time.sleep(self.time_slice)


if __name__ == '__main__':
    reporter = IpReporter()
    print('IP Reporter is running, please don\'t close this window!')
    reporter.logger.info('*** ip_reporter started ***')
    try:
        reporter.loop()
    except Exception as e:
        reporter.logger.exception(e)
    finally:
        reporter.logger.info('*** ip_reporter closed ***\n')

