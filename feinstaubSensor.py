#!/usr/bin/env python3
import sds011client
import webserver

import time

if __name__ == "__main__":
  # start the sensor client
  sensor_client = sds011client.sdsclient()
  sensor_client.start()
  server = webserver.webserver(sensor_client)
  server.start()
  sensor_client.join()
  server.join()

