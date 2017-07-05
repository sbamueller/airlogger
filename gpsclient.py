import sys
sys.path.append('/home/pi/lib')

from threading import *
import calendar
from datetime import datetime
from gpspython3.gps import *
import log
import arrow


class gpsclient(Thread):

  def __init__(self):
    super(gpsclient, self).__init__() 
    self.session = None
    self.fix = False
    self.lat = 0
    self.lon = 0
    self.alt = 0
    self.time = 0
    self.lock = Lock()
    self.shouldRun = Lock()
    self.shouldRun.acquire()
    self.port=25544
    self.parser = arrow.parser.DateTimeParser()


  def run(self):
    while self.session is None and self.shouldRun.locked():
      try:
        self.session = GPS(port=self.port,mode=WATCH_ENABLE)
      except OSError as e:
        log.info("unable to connect to gps, retrying in 15 sec: " +  str(e))
        time.sleep(15)

    while self.shouldRun.locked():
      try:
        self.session.next()
      except:
          log.error("unable to read from gps")
      
      if self.lock.acquire(False):
        self.fix = self.session.satellites_used >= 3
        self.lat = self.session.fix.latitude
        self.lon = self.session.fix.longitude
        self.alt = self.session.fix.altitude
        # the timestamp could be a unix timestamp (according to the gps library)
        try:
          self.time = int(self.session.utc)
        except:
          # time appears to be an ISO time string
          try:
            self.time = calendar.timegm(self.parser.parse_iso(self.session.utc).utctimetuple())
          except:
            print("got unexpected time format: " + str(self.session.utc))
            self.time = 0 
        self.lock.release()

  def get_data(self):
    d = {}
    self.lock.acquire() 
    d['fix'] = self.fix
    d['lat'] = self.lat
    d['lon'] = self.lon
    d['alt'] = self.alt
    d['time'] = self.time
    self.lock.release()
    return d

  def stop(self):
    self.shouldRun.release()

  def set_port(self, port):
    self.port = port
