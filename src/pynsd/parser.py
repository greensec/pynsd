# coding: utf-8
"""
Copyright (c) 2007 - 2013 Novutec Inc. (http://www.novutec.com)
Copyright (c) 2014 greenSec Solutions (http://www.greensec.de)

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

@category Novutec
@package pynsd
@copyright Copyright (c) 2007 - 2013 Novutec Inc. (http://www.novutec.com)
@copyright Copyright (c) 2014 greenSec Solutions (http://www.greensec.de)
@license http://www.apache.org/licenses/LICENSE-2.0
"""

import re

""" generic result class with all default values set
"""
class ControlResult(object):
    """ constructor which gets static values
    """
    def __init__(self, data):
        self.msg = None
        self.data = None
        self.success = None
        if 'success' in data:
            self.success = data['success']

        if 'msg' in data:
            self.msg = data['msg']

        if 'result' in data:
            self.data = data['result']

    """ return if call was successful
    """
    def isSuccess(self):
        return self.success

    """ get call message
    """
    def getMessage(self):
        return self.msg

    """ get call result
    """
    def getData(self):
        return self.data

    def __dict__(self):
        return { 'msg' : self.msg, 'success': self.success, 'data': self.data }

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return repr(self.__dict__())

""" nsd control protocol parser
"""
class ControlResultParser(object):
    __KVRE = re.compile("""^([^:]+):\s*(.+)$""", re.M)
    __KVRE2 = re.compile("""^([^=]+)=\s*(.+)$""", re.M)

    """ all static commands that normaly only return "ok"
    """
    __ok_commands = [ 'addzone', 'delzone', 'reconfig', 'log_reopen', 'notify' ]

    """ main method to start parsing and return result object
    """
    @staticmethod
    def parse(cmd, data):
        return ControlResult(ControlResultParser.__parse(cmd, data))

    """ start parsing process by switch to different methods for each command
    """
    @staticmethod
    def __parse(cmd, data):
        if not data or not cmd:
            return data

        if cmd == 'status':
            return ControlResultParser.status(data)
        elif cmd == 'stats' or cmd == 'stats_noreset':
            return ControlResultParser.stats(data)
        elif cmd == 'transfer' or cmd == 'force_transfer':
            return ControlResultParser.transfer(data)
        elif cmd in ControlResultParser.__ok_commands:
            return ControlResultParser.ok_check(data)
        return {
            'msg': data.strip().split('\n'),
            'success': None
        }

    """ parse "status" command call
    """
    @staticmethod
    def status(data):
        result = {
            'success': False,
            'result': {}
        }

        for (ky, vl) in ControlResultParser.__KVRE.findall(data):
            result['result'][ky] = vl

        if 'version' in result['result']:
            result['success'] = True

        return result

    """ parse "stats" command call
    """
    @staticmethod
    def stats(data):
        result = {
            'success': False,
            'result': {}
        }
        for (ky, vl) in ControlResultParser.__KVRE2.findall(data):
            result['result'][ky] = vl

        if 'time.elapsed' in result['result']:
            result['success'] = True

        return result

    """ parse static OK command calls
    """
    @staticmethod
    def ok_check(data):
        result = {
            'msg': data.strip().split('\n'),
            'success': False
        }

        if 'ok' in result['msg'] or re.search('^ok,', data):
            result['success'] = True
        return result

    """ parse zone transfer command calls
    """
    @staticmethod
    def transfer(data):
        result = ControlResultParser.ok_check(data)
        result['zones'] = None
        if result['success'] :
            f = re.search('(\d+) zones', data, re.I)
            if f:
                result['zones'] = int(f.group(1))

        return result
