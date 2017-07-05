from threading import *
from flask import * 
from urllib.parse import quote
import os
import log
from subprocess import call

app = Flask("Particulate Matter Sensor")
sds_client = None


class webserver(Thread):
  def __init__(self, sensor_client):
      super().__init__()
      global sds_client
      sds_client = sensor_client

  def run(self):
    try:
      app.run(host="0.0.0.0")
    except KeyboardInterrupt:
      pass


def get_file_list():
    l = []
    for d in os.listdir('data'):
        for f in os.listdir('data/' + d):
            fname = 'data/' + d + '/' + f
            l.append((fname, quote(fname, safe='')))
    return l


@app.route('/')
def start_page():
  gps_data = sds_client.gps_client.get_data() 
  return render_template('index.html', pm25 = sds_client.pm_25, pm10 = sds_client.pm_10, gpsfix = "yes" if gps_data['fix'] else "no", lon = gps_data['lon'], lat = gps_data['lat'], alt = gps_data['alt'], files=get_file_list()) 


@app.route('/hello')
def test():
    return 'Hello World'

@app.route('/csv')
def get_csv_file():
    f = request.args.get('filename')
    if not f.startswith('data'):
        return 'invalid path';
    try:
        text = ''
        with open(f, 'r') as fi:
            text = fi.read() 
        generator = (c for c in text)
        return Response(generator, mimetype="text/plain", headers={"Content-Disposition:": "attachement;filename=\"airlogger.csv\""}) 
    except Exception as e:
        print(e)
    return 'unable to open file'

@app.route('/kml')
def get_kml_file():
    f = request.args.get('filename')
    if not f.startswith('data'):
        return 'invalid path';
    try:
        with open(f, 'r') as fi:
            text = sds_client.csv_to_kml(fi.read())
            generator = (c for c in text)
            return Response(generator, mimetype="text/plain", headers={"Content-Disposition:": "attachement;filename=\"airlogger.kml\""}) 
    except Exception as e:
        print(e)
    return 'unable to open file'

@app.route('/delete')
def delete_csv():
    f = request.args.get('filename')
    if f == 'all':
       call(['rm', '-r', 'data']) 
       os.mkdir('data')
    else:
        if not f.startswith('data'):
            return 'invalid path';
        try:
            os.remove(f)
        except:
            return 'unable to remove'
    return 'success'
