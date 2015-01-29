from flask import Flask
from flask import jsonify
from flask import render_template
import mysql.connector
import logging
import time
from datetime import datetime
from mysql.connector import errorcode
import os
from datetime import tzinfo, timedelta, datetime

global FILEPATH
global SERVICE

FILEPATH = os.path.dirname(os.path.realpath(__file__))
SERVICE = 'service.log'

logging.basicConfig(
    filename = '%s\\%s' % (FILEPATH, SERVICE),
    level = logging.DEBUG, 
    format = '%(asctime)s [CBW Logger] %(levelname)-7.7s %(message)s',
    datefmt='%m/%d/%Y %I:%M:%S %p'
)

#Key words for database access
kwargs = {
    'user': 'root',
    'password': 'password',
    'host': '192.168.1.4',
    'port' : 3306,
    'database' : 'cbw',
    'raise_on_warnings': True,
}

app = Flask(__name__)

def testDBConnection(kwargs):
     try:
          cnx = mysql.connector.connect(**kwargs)
     except mysql.connector.Error as err:
          if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
               logging.error("DB: Something is wrong with your user name or password")
               return False
          elif err.errno == errorcode.ER_BAD_DB_ERROR:
               logging.error("DB: Database does not exists")
               return False
          else:
               logging.error(err)
               return False
     else:
          cnx.close()
          return True

def getDeviceDescription(id_sensor):
  cnx = mysql.connector.connect(**kwargs)
  cursor = cnx.cursor()
  query = ("SELECT s.description FROM history h JOIN sensor s on s.id = h.id_sensor WHERE h.id_sensor = %s limit 1" % id_sensor)
  cursor.execute(query)
  for value in cursor:
    description = value[0]
  cnx.close()
  return description

def getGraphResult(id_sensor):
  startTime = datetime.now() - timedelta(1)
  cnx = mysql.connector.connect(**kwargs)
  cursor = cnx.cursor()
  query = ("SELECT h.timestamp as 'time', h.value FROM history h WHERE h.id_sensor = %s AND h.timestamp > '%s' ORDER BY timestamp limit 100" % (id_sensor,startTime))
  cursor.execute(query)
  axisDescriptions = "[['hour', 'temperature'],"
  result = axisDescriptions
  for row in cursor:
    data = "['%s',%s]," % (row[0], row[1])
    result = result + data
  result = result.rstrip(",")
  result = result + "]"
  cnx.close()
  return result

def getTempAndDescription(id_sensor):
  cnx = mysql.connector.connect(**kwargs)
  cursor = cnx.cursor()
  query = ("SELECT value, description FROM history h JOIN sensor s on s.id = h.id_sensor WHERE h.id_sensor = %s ORDER BY timestamp DESC limit 1" % id_sensor)
  cursor.execute(query)
  for value in cursor:
    temp = value[0]
    description = value[1]
  cnx.close()
  return temp, description

@app.route('/', methods=['GET'])
def get_home():
  return render_template('static.htm')

@app.route('/temp/<id_sensor>', methods=['GET'])
def get_temp(id_sensor=None):
  temp, description = getTempAndDescription(id_sensor)
  return render_template('temp.htm', temp=temp, description=description)

@app.route('/history/<id_sensor>')
def get_history(id_sensor=None):
  deviceName = getDeviceDescription(id_sensor)
  result = getGraphResult(id_sensor)
  return render_template('history.htm', data=result, deviceName=deviceName)

if __name__ == '__main__':
  if testDBConnection(kwargs):
    app.run(debug=True)
  else:
    logging.error("Server could not connect to the database")