## Set up the config files

Update the config files:

- [config.cfg](config.cfg): Contains a path for the http-server.
- [config.json](config.json): Contains information for the server.

[config.cfg](config.cfg)

```bash
MEDIA_DIR=/media/raid/
```

[config.json](config.json)

```json
{
  "media_folders": [
    {
      "media_type": 5,
      "media_directory_path": "/media/raid/tv_shows",
      "media_directory_url": "http://192.168.x.xxx:8000/tv_shows/"
    }
  ]
}
```

- "media_type": int, from [database_handler.common_objects.ContentType](database_handler/common_objects.py), e.g: TV <
  5>,
  MOVIE <2>
- "media_directory_path": str, absolute path based on path used in config.cfg with sub-folder. e.g. /media/raid/tv_shows
- "media_directory_url": str, server url on the network with sub-folder: e.g. http://192.168.x.xxx:8000/tv_shows/
    - Do not use localhost, this address needs to be visible for the chromecast

## Setup and Install the necessary system services

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

