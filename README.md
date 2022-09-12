# SBFspot_to_fissio
Script to convert SBFspot CSV log files to Fissio.fi mittaustiedot.txt

# Install instructions:
1. Install SBFspot to Raspberry Pi

> https://github.com/SBFspot/SBFspot/wiki/Installation-Linux-SQLite#%EF%B8%8F-sbfspot-config

2. Copy SBFSpot_to_fissio.py to /home/pi/.fissio/

3. Make sure the configs in the beginning of SBFSpot_to_fissio.py are correct

4. SBFspot installs its crontab to the user pi, move the crontabs from pi to root:

```
pi@raspberrypi:~ $ crontab -e    # and remove SBFSpot's rows
```

and add them to user root:

```
pi@raspberrypi:~ $ sudo crontab -e    # and add them back to root's crontab with adding
                                      # SBFspot_to_fissio's command after daydata
```

```
&& python3 /home/pi/.fissio/SBFspot_to_fissio.py 2>&1 >> /home/pi/.fissio/SBFspot_to_fissio.log.txt
```

Like this:

```
## SBFspot
*/5 6-22 * * * /usr/local/bin/sbfspot.3/daydata && python3 /home/pi/.fissio/SBFspot_to_fissio.py 2>&1 >> /home/pi/.fissio/SBFspot_to_fissio.log.txt
55 05 * * * /usr/local/bin/sbfspot.3/monthdata
```




