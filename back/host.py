import eel
from bleak import BleakScanner
import random
import sqlite3
import datetime;
import socket
import json
from typing import Any
import threading
import scipy
import numpy
import math

server_host = '0.0.0.0'
server_port = 5000

@eel.expose
def fetch_saved_devices():
    con = sqlite3.connect("devices.db")
    cur = con.cursor()
    res = cur.execute("SELECT id_sensor, sensor_name, sensor_address FROM sensor")
    device_list = res.fetchall()
    cur.close()
    con.close()
    return device_list

def transpose_data(data):
    transposed = list(zip(*data))
    return [list(row) for row in transposed]


@eel.expose
def fetch_data(device_name, amount):
    con = sqlite3.connect("devices.db")
    cur = con.cursor()
    
    res = cur.execute("""SELECT temperature, voltage, current, charge, datetime FROM data_readings
                      WHERE sensor_id = ?
                      ORDER BY id_data_readings desc limit ?""", (device_name, amount,))
    data_readiings = res.fetchmany(amount)
    data_readiings.reverse()
    data_to_send = filter_data(transpose_data(data_readiings))
    if data_to_send is not None:
        eel.updateTableData(data_to_send)
    cur.close()
    con.close()
    return data_readiings

@eel.expose
def fetch_data_exact(device_name, startdate, enddate):
    con = sqlite3.connect("devices.db")
    cur = con.cursor()
    # print(startdate)
    # print(enddate)
    res = cur.execute("""SELECT temperature, voltage, current, charge, datetime FROM data_readings
                      WHERE sensor_id = ? AND datetime BETWEEN ? AND ?""", (device_name, startdate.replace('T', ' '), enddate.replace('T', ' '),))
    data_readiings = res.fetchall()
    # print(data_readiings)
    con.close()
    data_to_send = filter_data(transpose_data(data_readiings))
    if data_to_send is not None:
        eel.updateTableData(data_to_send)
    return data_readiings

def filter_data(data_readings):
    if not data_readings or data_readings is None or data_readings == []:
        return None
    if len(data_readings[0]) < 3 or data_readings == None:
        print('data_readings too small or empty')
        return
    # print(data_readings)
    full_data = []
    for i in range(3):
        data = numpy.array(data_readings[i])
        prev: float = 0
        for t in data:
            if t == None:
                t = prev
                continue
            prev = t
        # print(data)
        filtered_data = scipy.signal.medfilt(data, kernel_size=3)
        full_data.append(filtered_data.tolist())
    # print('filtered data')
    full_data.append(data_readings[3])
    # print(full_data)
    return full_data
    
def calculate_params(full_data):
    if not full_data or full_data is None or full_data == []:
        return None
    avarage_values = [0,0,0,0]
    for t in range(len(avarage_values)):
        for param in full_data[t]:
            avarage_values[t] += param
        avarage_values[t] = avarage_values[t] / len(full_data[t])
    power = []
    for t in range(len(full_data[0])):
        power.append(full_data[1][t]*full_data[2][t])
    pwr_avg = 0
    for t in power:
        pwr_avg += t
    pwr_avg /= len(power)
    avarage_values.append(pwr_avg)
    full_data.append(power)
    disp = [0,0,0,0,0]
    for t in range(len(disp)):
        for d in range(len(full_data[t])):
            disp[t] += (full_data[t][d] - avarage_values[t])**2
        disp[t] = math.sqrt(disp[t] / len(full_data[t]))
    CVx = [0,0,0,0,0]
    for t in range(len(CVx)):
        CVx[t] = disp[t]/avarage_values[t]
    energy_consump = 0
    for p in power:
        energy_consump += p*5
    avarage_values.pop(3)
    disp.pop(3)
    CVx.pop(3)
    return [avarage_values,disp,CVx]
    
def check_emergency(device_name, amount):
    con = sqlite3.connect("devices.db")
    cur = con.cursor()
    res = cur.execute("""SELECT temperature, voltage, current, charge, datetime FROM data_readings
                      WHERE sensor_id = ?
                      ORDER BY id_data_readings desc limit ?""", (device_name, amount,))
    data_readiings = res.fetchmany(amount)
    data_readiings.reverse()
    print(data_readiings)
    filtered_data = filter_data(transpose_data(data_readiings))
    if filtered_data is None:
        return
    power = []
    for t in range(len(filtered_data[0])):
        power.append(filtered_data[1][t]*filtered_data[2][t])
    filtered_data.append(power)
    count = 0
    for param in [100, 2000, 45, 0, 63000]:
        for ind in filtered_data[count]:
            if ind == param:
                text = ''
                if param == 100:
                    text = 'Повышенная температура'
                if param == 2000:
                    text = 'Повышенный ток'
                if param == 45:
                    text = 'Повышенное напряжение'
                if param == 0:
                    text = 'Заряд на нуле'
                if param == 63000:
                    text = 'Повышенная мощность'
                eel.alert_emergency(device_name, text)
                cur.execute("""INSERT OR IGNORE INTO error_log (sensor_id, datetime, error_message)
                    VALUES(?,?,?)""", (device_name, datetime.datetime.now(), text))
                con.commit()
        count += 1
    cur.close()
    con.close()
    return data_readiings
            
@eel.expose
def delete_device(device):
    if device is None:
        return
    con = sqlite3.connect("devices.db")
    cur = con.cursor()
    sql = 'DELETE FROM sensor WHERE sensor_name = ?'
    cur.execute(sql, (device,))
    con.commit()
    cur.close()
    con.close()

@eel.expose
def fetch_substations():
    con = sqlite3.connect("devices.db")
    cur = con.cursor()
    res = cur.execute("SELECT name_substation FROM substations")
    substations = [row[0] for row in res.fetchall()]
    cur.close()
    con.close()
    return substations

@eel.expose
def get_device_substation(device_name):
    con = sqlite3.connect("devices.db")
    cur = con.cursor()
    res = cur.execute("""SELECT s.name_substation 
                         FROM sensor sen
                         JOIN substations s ON sen.id_substation = s.id_substation
                         WHERE sen.sensor_name = ?""", (device_name,))
    result = res.fetchone()
    cur.close()
    con.close()
    return result[0] if result else ""

@eel.expose
def add_device_to_db(device):
    con = sqlite3.connect("devices.db")
    cur = con.cursor()
    print(device)
    cur.execute("""INSERT OR IGNORE INTO substations (name_substation)
                    VALUES(?)""", (str(device[2]),))
    cur.execute("""INSERT OR IGNORE INTO sensor (sensor_name, sensor_address, id_substation)
                    VALUES(?,?,?)""", (device[0], str(device[1]), str(device[2])))
    con.commit()
    cur.close()
    con.close()

# @eel.expose
# async def fetch_device_list():
#     con = sqlite3.connect("devices.db")
#     cur = con.cursor()
#     devices = await BleakScanner.discover(timeout=5)
#     device_list = []
#     for d in devices:
#         v:float = abs(d.details[0].transmit_power_level_in_d_bm)
#         if v is None:
#             v = random.uniform(6, 8)
#         device_list.append({
#             'device_name': str(d.name),
#             'device_address': str(d.address),
#             })
        
#         cur.execute(
#             """INSERT INTO data_readings (sensor_id, datetime, temperature, voltage, current, charge)
#             SELECT ?, ?, ?, ?, ?, ?
#             WHERE EXISTS (
#                 SELECT 1
#                 FROM sensor
#                 WHERE sensor.sensor_name = ?
#             );""",
#             (str(d.name), datetime.datetime.now(),
#             v*random.uniform(3.5, 4.9), v*random.uniform(2.5, 2.9),
#             v*random.uniform(1.5, 2.9), v*random.uniform(0.5, 1.5),
#             str(d.name))
#             )
#     con.commit()
#     cur.close()
#     con.close()
#     return device_list

async def add_data_to_db(device):
    con = sqlite3.connect("devices.db")
    cur = con.cursor()
    cur.execute(
            """INSERT INTO data_readings (sensor_id, datetime, temperature, voltage, current, charge)
            SELECT ?, ?, ?, ?, ?, ?
            WHERE EXISTS (
                SELECT 1
                FROM sensor
                WHERE sensor.sensor_name = ?);""",
            (str(device.name), datetime.datetime.now(),device.temperature,device.voltage,device.current,device.charge,tr(device.name)))
    con.commit()
    cur.close()
    con.close()

@eel.expose
async def start_data_stream():
    while True:
        try:
            run_server(server_host, server_port)
        except:
            print('recieving connection...')

def recv_all(conn: socket.socket, n: int) -> bytes:
    buf = b''
    while len(buf) < n:
        chunk = conn.recv(n - len(buf))
        # if not chunk:
        #     raise ConnectionError("Client disconnected")
        buf += chunk
    return buf

def run_server(host: str, port: int):
    with socket.socket() as serv:
        serv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        serv.bind((host, port))
        serv.listen()
        print(f"[SERVER] Listening on {host}:{port}…")
        while True:
            conn, addr = serv.accept()
            t = threading.Thread(target=handle_client, args=(conn, addr), daemon=True)
            t.start()

def handle_client(conn: socket.socket, addr):
    try:
        while True:
            con = sqlite3.connect("devices.db")
            names = []
            cur = con.cursor()
            raw_len = recv_all(conn, 4)
            length = int.from_bytes(raw_len, 'big')
            data = recv_all(conn, length)
            payload: Any = json.loads(data.decode('utf-8'))
            device_list = []
            print("[SERVER] Received payload:")
            # print(payload)
            for d in payload:
                if str(d['device_name']) in names:
                    continue
                names.append(str(d['device_name']))
                device_list.append({
                'device_name': str(d['device_name']),
                'device_address': str(d['device_address']),
                'substation': str(d['substation'])
                })
                cur.execute(
                        """INSERT INTO data_readings (sensor_id, datetime, temperature, voltage, current, charge)
                        SELECT ?, ?, ?, ?, ?, ?
                        WHERE EXISTS (
                            SELECT 1
                            FROM sensor
                            WHERE sensor.sensor_name = ?
                        );""",
                        (str(d['device_name']), datetime.datetime.now(),
                        d['temperature'], d['voltage'], d['current'], d['charge'], str(d['device_name']))
                        )
                if cur.lastrowid != 0:
                    print(cur.lastrowid)
                    print(str(d['device_name']))
                    check_emergency(str(d['device_name']), 10)
                    # check_emergency([], 10)
            con.commit()
            cur.close()
            con.close()
            eel.updateData(device_list)

    except ConnectionError:
        print(f"[SERVER] Connection closed by {addr}")
    finally:
        conn.close()