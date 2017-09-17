# -*- coding: utf-8 -*-

import win32serviceutil
import win32service
import win32event
import servicemanager
import os, sys
import logging
import inspect
import time
import socket

from email_util import EmailSender


class IPReporterService(win32serviceutil.ServiceFramework):

    _svc_name_ = 'IPReporterService'
    _svc_display_name_ = 'IP Reporter Service'
    _svc_description_ = 'Send report to specified emails when IP address changed.\n当本机 IP 地址发生变化时，向指定的邮箱发送通知邮件。'

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        socket.setdefaulttimeout(60)
        self.appRoot = self._getAppRoot()
        self.logger = self._getLogger()
        self.currentIp = self._getCurrentIp()
        self.msgTemplate = '\n'.join(['主机名：%s', '原 IP 地址：%s', '新 IP 地址：%s', '发生时间：%s'])
        self.sender = EmailSender(self.appRoot)
        self.isAlive = True
        self.timeSlice = 5
        self.cycleTime = 60 * 20

    def _getAppRoot(self):
        this_file = inspect.getfile(inspect.currentframe())
        return os.path.dirname(os.path.abspath(this_file))

    def _getLogger(self):
        appRoot = self._getAppRoot()
        logger = logging.getLogger('IPReporterService')
        handler = logging.FileHandler(os.path.join(appRoot, 'log', 'service.log'))
        formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)
        return logger

    def _getCurrentIp(self):
        currentIp = None
        fileCurrentIp = os.path.join(self.appRoot, 'current_ip.txt')
        if os.path.isfile(fileCurrentIp):
            with open(fileCurrentIp, 'r') as f:
                currentIp = f.read().strip()
                if not currentIp: currentIp = None
        return currentIp

    def _saveCurrentIp(self):
        fileCurrentIp = os.path.join(self.appRoot, 'current_ip.txt')
        with open(fileCurrentIp, 'w') as f:
            f.write(self.currentIp)

    @staticmethod
    def _getAllIps():
        addrs = socket.getaddrinfo(socket.gethostname(), None)
        return [a[4][0] for a in addrs]

    def _getOuterIp(self):
        all_ips = self._getAllIps()
        # 筛去 ipv6 、内网地址和保留地址
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

    def _handleIpChange(self):
        hostname = socket.gethostname()
        detectedIp = self._getOuterIp()
        if detectedIp != self.currentIp:
            self.logger.info('IP address changed from %s to %s.' %(self.currentIp, detectedIp))
            _time = time.strftime('%Y-%m-%d %H:%M:%S', tuple(time.localtime()))
            msg = self.msgTemplate %(hostname, self.currentIp, detectedIp, _time)
            mail = self.sender.make_email(msg)
            self.sender.send_email(mail)
            self.currentIp = detectedIp
            self._saveCurrentIp()
        else:
            self.logger.info('IP address (%s) remains unchanged.' %(self.currentIp,))

    def loop(self):
        sliceCount = int(self.cycleTime / self.timeSlice)
        n = 1
        while n:
            n = n - 1
            if not self.isAlive:
                break
            if n == 0:
                self._handleIpChange()
                n = sliceCount
            time.sleep(self.timeSlice)

    def SvcDoRun(self):
        self.logger.info('====================== IP Reporter Service Started ======================')
        try:
            self.loop()
        except Exception as e:
            self.logger.exception(e)

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)
        self.isAlive = False
        self.logger.info('====================== IP Reporter Service Stoped ======================')

if __name__=='__main__':
    if len(sys.argv) == 1:
        # 用户未输入参数则打印帮助信息
        try:
            evtsrc_dll = os.path.abspath(servicemanager.__file__)
            servicemanager.PrepareToHostSingle(IPReporterService)
            servicemanager.Initialize('IPReporterService', evtsrc_dll)
            servicemanager.StartServiceCtrlDispatcher()
        except win32service.error as e:
            import winerror
            if e.args[0] == winerror.ERROR_FAILED_SERVICE_CONTROLLER_CONNECT:
                win32serviceutil.usage()
    else:
        win32serviceutil.HandleCommandLine(IPReporterService)

