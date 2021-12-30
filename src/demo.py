#!/usr/bin/env python3
import pynsd

clt = pynsd.ControlClient(clientCert='/home/ubuntu/nsd_control.pem', 
                          clientKey='/home/ubuntu/nsd_control.key',
                          host='127.0.0.1',
                          port=8952)
print(clt.status())
