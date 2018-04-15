import os
import sys
import logging
from email.header import Header
from email.mime.text import MIMEText
from email.utils import parseaddr, formataddr
import smtplib


class SmtpLogger(object):
    def __init__(self, logger):
        self.logger = logger

    def write(self, message):
        if not message.strip():
            return
        self.logger.debug(message)

class EmailSender(object):
    """generate and send emails"""
    def __init__(self):
        email_params = os.environ['ipreporter'].split(',')
        self.from_email, \
        self.from_smtp, \
        self.password = email_params[:3]
        self.to_emails = email_params[3:]
        self.logger = self._get_logger()

    def _get_logger(self):
        logger = logging.getLogger('EmailSender')
        logger.setLevel(logging.DEBUG)
        log_file = './log/email.log'
        handler = logging.FileHandler(log_file, encoding='utf8')
        formatter = logging.Formatter('[%(asctime)s] %(levelname)s: %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        return logger

    def _format_addr(self, s):
        name, addr = parseaddr(s)
        return formataddr((Header(name, 'utf-8').encode(), addr))

    def make_email(self, msg_str):
        mail = MIMEText(msg_str, 'plain', 'utf-8')
        mail['From'] = self._format_addr('IP Reporter <%s>' %self.from_email)
        mail['To'] = self._format_addr(', '.join(['<%s>' %te for te in self.to_emails]))
        mail['Subject'] = Header('Remote IP Address has Changed', 'utf-8').encode()
        return mail

    def _send_email(self, mail):
        orig_std = (sys.stdout, sys.stderr)
        sys.stdout = sys.stderr = SmtpLogger(self.logger)
        try:
            self.logger.info('========================= email begin =========================')
            server = smtplib.SMTP(self.from_smtp, 25)
            server.set_debuglevel(1)
            server.login(self.from_email, self.password)
            server.sendmail(self.from_email, self.to_emails, mail.as_string())
            server.quit()
            self.logger.info('========================= email over =========================\n\n')
        finally:
            sys.stdout, sys.stderr = orig_std

    def send_email(self, msg_str):
        self._send_email(self.make_email(msg_str))
