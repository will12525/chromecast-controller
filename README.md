## Setup/Install the necessary system services

Update the config files:
 - config.cfg: Contains a path for the http-server. Assign an absoulte path: /media/raid
 - config.json: Contains information for the server. 

config.json
```json
{
    "media_folders": [
        {
            "media_type": int, from database_handler.common_objects.ContentType, e.g: TV <5>, MOVIE <2>
            "media_directory_path": str, absolute path based on path used in config.cfg with subfolder. e.g. /media/raid/tv_shows
            "media_directory_url": str, server url on the network with subfolder: e.g. http://192.168.1.200:8000/tv_shows/
        }
    ]
}
```

This application uses ffmpeg for image processing, sqlite3 for data, and npm for http-server.

Install packages:
```bash
apt update && apt install sqlite3 ffmpeg npm
```
The setup script will also install the above packages.
```bash
sudo ./setup.sh
```

## To run locally

```bash
./start_server
```

### Use systemctl to control this application

services:

* chromecast_controller.service
* media_drive_as_webpage.service

```bash
sudo systemctl <start|stop|restart> <service>
```

## Sources

Icons: https://fontawesome.com/v4/icons/
Unicode character [chart](https://en.wikipedia.org/wiki/List_of_Unicode_characters).

