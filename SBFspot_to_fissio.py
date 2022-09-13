import csv
import re
from itertools import islice
import datetime
import glob
import json
import os



#### sudo crontab -l

'''
## SBFspot
*/5 6-22 * * * /usr/local/bin/sbfspot.3/daydata && python3 /home/pi/.fissio/SBFspot_to_fissio.py 2>&1 >> /home/pi/.fissio/SBFspot_to_fissio.log.txt
55 05 * * * /usr/local/bin/sbfspot.3/monthdata
'''


### Set here locations of the SBFspot output and Fissio install location.

sma_log_dir = '/home/pi/smadata/%Y'
fissio_dir = '/home/pi/.fissio'
sma_spot_log_wildcard = "*-Spot-*.csv"


sbfbot_csv_to_fissio_status_filename = fissio_dir+'/SBFspot_to_fissio.json'
fissio_mittaustiedot_filename = fissio_dir+'/mittaustiedot.txt'


def get_last_csv_file_from_dir(dir_name):
    if '%' in dir_name:
        dir_name = datetime.datetime.now().strftime(dir_name)
    return sorted(glob.glob(os.path.join(dir_name.rstrip('/'), sma_spot_log_wildcard)))[-1]

def load_conversion_status():
    try:
        with open(sbfbot_csv_to_fissio_status_filename, 'r') as f:
            conversion_status = json.load(f)
            print("Loaded status: ", conversion_status)
    except Exception as e:
        print("Previous save file not found or loading failed", e)
        return None
    return conversion_status

def save_conversion_status(conversion_status):
    with open(sbfbot_csv_to_fissio_status_filename, 'w') as savefile:
        savefile.write(json.dumps(conversion_status))
        print("Saved status file: ", conversion_status)


# Open SBFbot logfile first as normal text file to find out the CSV parameters

def find_csv_file_format(filename):
    sep = None
    decimal_separator = None
    unit_line_idx = 0
    units = None
    with open(filename, newline='') as f:
        for i, line in enumerate(f):
            if 'sep=' in line:
                sep = line.rstrip().split('=')[1]
            if 'Decimalpoint' in line:
                for kp in line.split('|'):
                    kp = kp.split(' ')
                    if kp[0] == 'Decimalpoint':
                        decimal_separator = kp[1]
            if sep+'Watt'+sep in line:
                units = line.split(sep)
                unit_line_idx = i
            if sep is not None and decimal_separator is not None and unit_line_idx > 0:
                break

    return sep, decimal_separator, unit_line_idx, units

def convert_timestamp_field_to_format(field_name):
    time_format = field_name
    time_format = re.sub(r'dd', '%d', time_format)
    time_format = re.sub(r'MM', '%m', time_format)
    time_format = re.sub(r'yyyy', '%Y', time_format)
    time_format = re.sub(r'HH', '%H', time_format)
    time_format = re.sub(r'mm', '%M', time_format)
    time_format = re.sub(r'ss', '%S', time_format)
    return time_format

def field_to_float(value, decimal_separator):
    if decimal_separator == 'comma':
        value = re.sub(r",",'.',value)
    return float(value)

def main():
    filename = get_last_csv_file_from_dir(sma_log_dir)
    conversion_status = load_conversion_status()
    print("Reading", filename)
    sep, decimal_separator, unit_line_idx, units = find_csv_file_format(filename)

    with open(filename, newline='') as csvfile:
        reader = csv.DictReader(islice(csvfile, unit_line_idx+1, None), delimiter=sep)
        etotal_data = []

        for i, row in enumerate(reader):
            timestamp_field_name = list(row)[0]
            time_format = convert_timestamp_field_to_format(timestamp_field_name)
            epoch_timestamp = int(datetime.datetime.strptime(row[timestamp_field_name], time_format).strftime('%s'))
            etotal_data.append([epoch_timestamp,field_to_float(row['ETotal'], decimal_separator)])

        previous_ts = None
        previous_etotal = None
        last_printed_ts = None
        last_printed_etotal = None
        data_str = ""

        for etotal_row in etotal_data:
            if previous_ts is None and conversion_status is not None:
                previous_ts = conversion_status['previous_ts']
                previous_etotal = conversion_status['previous_etotal']
                continue
            if previous_ts is None and conversion_status is None:
                previous_ts = etotal_row[0]
                previous_etotal = etotal_row[1]
                continue
            if previous_ts is not None and etotal_row[0] <= previous_ts:
                #print("Skipping timestamp until reaching latest written conversion status", previous_ts)
                continue
            if previous_ts is not None and etotal_row[0] > previous_ts:
                yield_diff = int((etotal_row[1] - previous_etotal)*1000)
                timestamp_diff = int(etotal_row[0] - previous_ts)
                data_str += "{};imp;Solar_PV_Wh;{};{}\n".format(previous_ts, yield_diff, timestamp_diff)
                last_printed_ts = previous_ts
                last_printed_etotal = previous_etotal
                previous_ts = etotal_row[0]
                previous_etotal = etotal_row[1]

        if len(data_str) > 0:
            print("Collected {} rows of new data for Fissio.".format(len(data_str.split('\n'))-1))
            with open(fissio_mittaustiedot_filename, "a") as f:
                f.write(data_str)
                print("Wrote: ", data_str)

            conversion_status = {"last_printed_ts": last_printed_ts,
                              "last_printed_etotal": last_printed_etotal,
                              "previous_ts": previous_ts,
                              "previous_etotal": previous_etotal,
                              "yield_diff": yield_diff,
                              "timestamp_diff": timestamp_diff}

            save_conversion_status(conversion_status)
        else:
            print("No new data collected for Fissio.")



if __name__ == '__main__':
    main()
