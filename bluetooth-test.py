from serial import Serial

ser = Serial('/dev/rfcomm0')
ser.write(b'Hi!')

ser.close()
