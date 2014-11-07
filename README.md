pynsd
=====

pynsd is a library to use new control api of NSD 4 in python.

See: http://www.nlnetlabs.nl/svn/nsd/trunk/doc/NSD-4-features

Additional RPC Daemon: [pynsd-rpcd](https://github.com/greensec/pynsd-rpcd)

Copyright (c) 2007 - 2013 Novutec Inc. (http://www.novutec.com)
Copyright (c) 2014 greenSec Solutions (http://www.greensec.de)

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

Installation
------------

```
1. Download zip file
2. Extract it
3. Execute in the extracted directory: python setup.py install
```

#### Development version

```
pip install -e git+git@github.com:greensec/pynsd.git
```

#### Requirements

* Python 2.7 / 3.2 / 3.3
* SSL support 
