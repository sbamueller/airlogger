import time
from datetime import datetime
import serial
import struct
import os
import log
import calendar
from threading import *

from gpsclient import *

class sdsclient(Thread):

  def __init__(self):
    Thread.__init__(self)
    self.gps_client = gpsclient()
    self.ser = None
    self.shouldRun = True
    self.header = [0, 0]
    self.file = None
    self.synced_time = False
    self.pm_25 = -1
    self.pm_10 = -1

  def run(self):
    # try to connect to the particle sensor. If the attempt was unsuccesfull
    # retry after 15 seconds
    try:
      while self.ser is None and self.shouldRun:
        try:
          self.ser = serial.Serial("/dev/ttyParticulateMatterSensor", baudrate=9600, stopbits=1, parity="N", timeout=2)
        except Exception as e:
          log.warn('unable to connect to particulate matter sensor, retrying in 15 seconds: %s' % e)
          self.ser = None
          time.sleep(15) 
    except KeyboardInterrupt:
      self.shouldRun = False

    log.info("connected to particulate matter sensor")
    # start the gps client
    self.gps_client.set_port(25544)
    self.gps_client.start()
    try:
      self.init_csv_file()
      # run the main loop until we either receive a keyboard interrupt, or 
      # self.shouldRun is False
      while self.shouldRun:
        # Read the header. blocks until data was received
        # move bytes in the header one slot to the right and read the new byte
        self.header[1] = self.header[0]
        self.header[0] = self.ser.read(size=1) 
        if self.header[1] == b"\xAA" and self.header[0] == b"\xC0":
          sentence = self.ser.read(size=8) # Read 8 more bytes
          # Decode the packet - big endian, 2 shorts for pm2.5 and pm10, 2 reserved bytes, checksum, message tail
          readings = struct.unpack('<hhxxcc',sentence) 
          self.pm_25 = readings[0]/10.0
          self.pm_10 = readings[1]/10.0
          gps_data = self.gps_client.get_data()
          self.write_data_line(self.pm_25, self.pm_10, gps_data)
      time.sleep(1.5)
    except KeyboardInterrupt:
      self.shouldRun = False
    # close the csv file properly
    self.close_csv_file()

  def init_csv_file(self):
    """
     find a suitable place for the file and open it  
    """
    folder = "/home/pi/data/" + datetime.now().strftime("%Y_%m_%d") + "/"
    if not os.path.isdir(folder):
      # append 'a' to the folder name until we find a name that does not exist
      while os.path.exists(folder):
        folder = folder[:-1] + "a" + "/"
      os.mkdir(folder)
    filename = folder + 'particledata_' + datetime.now().strftime ("%H-%M-%S") 
    while os.path.exists(filename):
      filename = filename + '_a'
    filename += '.csv'
    log.info('Writing data to: ' +  filename)
    self.file = open(filename, "w")
    self.file.write('Unix Time;Human Readable Time;pm 2.5;pm 10;Has Fix;Longitude;Latitude;Altitude;GPS Unix Time\n')
    self.file.flush()
    self.synced_time = False

  def close_csv_file(self):
    """
      closes the csv file if it is open
    """
    if self.file is not None:
      self.file.close()

  def write_data_line(self, pm_25, pm_10, gps_data):
    """
      write a line of data into the csv
    """
    self.file.write(str(int(time.time())))  # Unix Time)
    self.file.write(';' + datetime.now().strftime("%d.%m.%y %H:%M:%S"))  # Human Readable Time
    self.file.write(';' + str(pm_25))  # pm 2.5 
    self.file.write(';' + str(pm_10))  # pm 10 
    self.file.write(';' + str(gps_data['fix']))  # has fix 
    self.file.write(';' + str(gps_data['lon']))  # longitude 
    self.file.write(';' + str(gps_data['lat']))  # latitude 
    self.file.write(';' + str(gps_data['alt']))  # altitude 
    self.file.write(';' + str(gps_data['time']))  # gps unix time 
    self.file.write('\n')
    self.file.flush()

  def stop(self):
    self.shouldRun = False


  def csv_to_kml(self, csv):
    kml = """
        <?xml version="1.0" encoding="UTF-8"?>
        <kml xmlns="http://earth.google.com/kml/2.1">
        <Document>
        <Style id="point_green">
            <IconStyle>
                <color>ff00ff00</color>
            </IconStyle>
        </Style>

        <Style id="point_yellow">
            <IconStyle>
                <color>ffffff00</color>
            </IconStyle>
        </Style>
        
        <Style id="point_red">
            <IconStyle>
                <color>ffff0000</color>
            </IconStyle>
        </Style>


        <Style id="point_black">
            <IconStyle>
                <color>ff000000</color>
            </IconStyle>
        </Style>
        """
    print(csv)
    for line in csv.split('\n'):
      print("processing line", line)
      try:
        entries = line.split(';')
        # is the line in the expected format (check only the first column)
        try:
          float(entries[2])
        except Exception as e:
          print(e)
          continue
        if entries[4] == 'True':
          val = float(entries[2])
          color = "point_green"
          if val > 20:
              color = "point_yellow"
          if val > 50:
              color = "point_red"
          if val > 100:
              color = "point_black"
          kml += """
            <Placemark>
                <styleUrl>#""" + color  + """</styleUrl>
                <name>pm 2.5: '""" + entries[2] + """', pm 10: """ + entries[3]  + """</name>
                <description>""" + entries[1] + """</description>
                <Point>
                  <coordinates>""" + entries[5] + ',' + entries[6] + ',0' + """</coordinates>
                </Point>
            </Placemark>
          """
      except Exception as e:
            print(e)
    kml += "</Document>\n</kml>"
    print("reached after loop", kml)
    return kml
