import sys
import os
import logging
import datetime
import smtplib
from copy import deepcopy
from base64 import b64decode
from base64 import b64encode
from logging.handlers import TimedRotatingFileHandler
from pprint import pprint


class SMTP:
    _url = ""
    _conn = None

    def __init__(self):
        self._url = "mailhost.outlook.com"

    def _start(self):
        self._conn = smtplib.SMTP(self._url)

    def _quit(self):
        self._conn.quit()

    def send_mail(self, subject, body, sender='pratyushpratapsingh11@gmail.com.com', sender_header="User Account Management <pratyushpratapsingh11@gmail.com.com>", recipients=['pratyushpratapsingh11@outlook.com'], recipients_header='pratyushpratapsingh11@outlook.com', reply_to='Dev Team <pratyushpratapsingh11@outlook.com>'):
        self._start()
        # Remove possible duplicate email recipients 
        recipients = list(set(recipients))
        message = "From: %s\n" \
                  "Reply-To: %s\n" \
                  "To: %s\n" \
                  "Importance: high\n" \
                  "Subject: %s\n\n" \
                  "%s" % (sender_header, reply_to, recipients_header, subject, body)
        self._conn.sendmail(sender, recipients, message)
        self._quit()
        return True 


# GENERAL UTILITIES #
# Okta App Inventory configuration parameters in global dictionary #
conf_params = {}


def load_conf(filename, conf_type):
    if conf_type == 'SP':
        required_params = [
            'sp_site',
            'sp_client_id',
            'sp_client_secret',
            'tenant_id'
        ]

    elif conf_type == 'APP1':
        required_params = [
            'app1_api_token'
       ]
    
    elif conf_type == 'APP2':
        required_params = [
            'app2_api_token'
       ]

    else:
        write_log("Invalid configuration type given: '%s'." % conf_type, 3)
        sys.exit(1)

    try:
        with open(filename, 'r') as stream:
            file_contents = stream.read()

    except IOError:
        write_log("Cannot load configuration file '%s'." % filename, 4)
        sys.exit(1)
		
    file_contents = file_contents.encode('utf-8')
    counter = 0
    try:
        while (counter < 20):
            file_contents = b64decode(file_contents)
            counter += 1
    except TypeError:
        write_log("Invalid format for configuration file '%s'." % filename, 3)
        sys.exit(1)

    file_contents = file_contents.decode('utf-8')
    file_contents = file_contents.split('\n')
    for line in file_contents:
        line = line.strip()

        if line.startswith('#'):
            continue

        elif line.find('::') == -1:
            continue

        else:
            key_value = line.split('::')
            key = key_value[0].strip()
            value = key_value[1].strip()
            conf_params[key] = value

    if not conf_params:
        write_log("Empty configuration file given: '%s'." % filename, 4)
        sys.exit(1)

    for param in required_params:
        if not param in conf_params:
            write_log("'%s' value missing from configuration file '%s'." % (param, filename), 4)
            sys.exit(1)


def write_log(message, criticality):
    '''Prints a message to console as well as logging that message to a log file

    :param message: string
    :param criticality: int
    :return: None
    '''

    # Debug #
    if criticality == 0:
        logging.debug(message)
        print('[DEBUG] %s' % message)

    # Info #
    elif criticality == 1:
        logging.info(message)
        print('[INFO] %s' % message)

    # Warning #
    elif criticality == 2:
        logging.warning(message)
        print('[WARNING] %s' % message)

    # Error #
    elif criticality == 3:
        logging.error(message)
        print('[ERROR] %s' % message)

    # Critical #
    elif criticality == 4:
        logging.critical(message)
        print('[CRITICAL] %s' % message)

    else:
        error_message = '[ERROR] Invalid criticality setting: %s\n Log message ignored.' % criticality
        print(error_message)
        logging.error(error_message)


def encrypt_config(filename):
    new_config_file = '%s.encrypted' % filename

    try:
        with open(filename, 'r') as stream:
            config_file_contents = stream.read()
    except IOError:
        write_log("Cannot open file '%s' for reading." % filename, 3)
        return False

    config_file_contents = config_file_contents.encode('utf-8')

    counter = 0
    while counter < 20:
        config_file_contents = b64encode(config_file_contents)
        counter += 1

    config_file_contents = config_file_contents.decode('utf-8')

    try:
        with open(new_config_file, 'w') as stream:
            stream.write('%s' % config_file_contents)
    except IOError:
        write_log("Location '%s' could not be written to." % new_config_file, 3)
        return False

    write_log("Config file successfully encrypted.", 1)
    return True


def decrypt_config(filename):
    try:
        with open(filename, 'r') as stream:
            config_file_contents = stream.read()
    except IOError:
        write_log("Cannot open file '%s' for reading." % filename, 3)
        return False

    counter = 0
    new_config_file = '%s.decrypted' % filename

    try:
        while counter < 20:
            config_file_contents = b64decode(config_file_contents)
            counter += 1
    except TypeError:
        write_log("Invalid encryption format for file '%s'." % filename, 3)
        return False

    config_file_contents = config_file_contents.decode('utf-8')

    try:
        with open(new_config_file, 'w') as stream:
            stream.write(config_file_contents)
    except IOError:
        write_log("Location '%s' could not be written to." % new_config_file, 3)
        return False

    write_log("Config file successfully decrypted.", 1)
    return True


def pause():
    input("Continue?: ")


def decode_dictionary(data):
    """Removes any byte-string and replaces it with a Python string."""
    for key in data:
        value = data[key]
        if isinstance(value, bytes):
            string_value = value.decode('utf-8')
            data[key] = string_value
        elif isinstance(value, list):
            for counter, sub_value in enumerate(value):
                if isinstance(sub_value, bytes):
                    string_value = sub_value.decode('utf-8')
                    data[key][counter] = string_value

                    
def get_date_from_timestamp(utc_timestamp):
    date_time = utc_timestamp[:utc_timestamp.find('T')]
    return datetime.datetime.strptime(date_time, '%Y-%m-%d')


def sigint_signal_handler(signal, frame):
    print('')
    sys.exit(0)


def configure_log(log_type=''):

    # Set log type
    if log_type:
        log_path = '%s/logs/program_run.log' % log_type
    else:
        log_path = 'logs/program_run.log'

    # Set initial log format
    formatter = logging.Formatter('%(message)s')
    handler = TimedRotatingFileHandler(log_path, when='D', interval=1, backupCount=31)

    # By default, log will only rotate if a program run is separated by at least a day.
    # Adding logic to manually check if the file timestamp's date differs by the current date by more than a day
    # If it does, manually roll over

    current_time = datetime.datetime.now()
    file_time = datetime.datetime.fromtimestamp(os.path.getmtime(log_path))

    if current_time.day != file_time.day:
        handler.doRollover()

    handler.setFormatter(formatter)

    # Get root logger
    logger = logging.getLogger('')
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)
    logging.info('\n\nPROGRAM START\n-------------')

    # Set format for rest of log
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
