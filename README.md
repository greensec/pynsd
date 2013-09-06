pynsd
=====

pynsd is a library to use new control api of NSD 4 in python.

See: http://www.nlnetlabs.nl/svn/nsd/trunk/doc/NSD-4-features

Additional a [zerorpc](https://github.com/dotcloud/zerorpc-python) based RPC Daemon to create, update and delete zones on NSD master.

Copyright (c) 2007 - 2013 Novutec Inc. (http://www.novutec.com)
Licensed under the Apache License, Version 2.0 (the "License").

Basic Example of Usage
------------------------

To create connect to nsd host, get status, add sample zone and delete sample zone

```python
import pynsd

clt = pynsd.ControlClient(clientCert='/etc/nsd/nsd_control.pem', 
                          clientKey='/etc/nsd/nsd_control.key',
                          host='127.0.0.1',
                          port=8952)
print clt.call('status')
print clt.call('addzone', ['testzone.example.', 'cust'])
print clt.call('delzone', ['testzone.example.', 'cust'])
```

It is also possible to use the magic method __getattr__ to call a method directly:
```python
print clt.zonestatus('testzone.example.')
```

Usage of RPC Daemon
-------------------
To use the rpc daemon you have to change the sample config /etc/[pynsd-rpcd.cfg](https://raw.github.com/novutec/pynsd/master/src/etc/pynsd-rpcd.cfg) to your settings
and start daemon.
 
```bash
pynsd-rpcd -c /etc/pynsd-rpcd.cfg
```

Send requests to rpc daemon:

```bash
zerorpc tcp://127.0.0.1:5912 zoneStatus testzone.example.
```

#### Available Commands
* addZone(name, zonedata, pattern = None)
* updateZone(name, zonedata)
* delZone(name)
* zoneStatus(name)
* reloadZone(name)
* notifyZone(name)
* transferZone(name)
* reconfig
* stats(noreset = True)

Installation
------------

```
1. Download zip file
2. Extract it
3. Execute in the extracted directory: python setup.py install
```

#### Development version

```
pip install -e git+git@github.com:novutec/pynsd.git
```

#### Requirements

* Python 2.7 / 3.2 / 3.3
* [zerorpc](https://github.com/dotcloud/zerorpc-python) (for rpc daemon)
* argparse (to set config file in rpc daemon)