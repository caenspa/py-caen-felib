from pyfelib import device

dig = device.Device("dig2://10.105.250.7")

val = dig.get_value("/par/recordlengths")
print(val)

dig.set_value("/par/recordlengths", "100")

val = dig.get_value("/par/recordlengths")
print(val)
