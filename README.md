# KNXPClient
EIB/KNX client implementation for Python

## Getting started
```
    cf = EIBClientFactory()
    c = cf.getClient()

    # read sample value
    val = c.GroupCache_Read("1/0/3")
    print("Read group cache value: \t" + str(val))
    
    # monitor sample value
    class MyEIBClientListener(EIBClientListener):
        def updateOccurred(self, srcAddr, val):
            print("### This is the value you were waiting for - FROM: {0} VALUE: {1}".format(printGroup(srcAddr), val))

    cf.registerListener(MyEIBClientListener('1/0/3'))

    # monitor another sample value
    class MyEIBClientListener2(EIBClientListener):
        def updateOccurred(self, srcAddr, val):
            print("### This is another value you were waiting for - FROM: {0} VALUE: {1}".format(printGroup(srcAddr), val))

    cf.registerListener(MyEIBClientListener2('1/0/4'))
```
