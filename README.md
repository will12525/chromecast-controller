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
  "mode": "CLIENT",
  "media_folders": [
    {
      "content_src": "/media/raid/",
      "content_url": "http://192.168.x.xxx:8000/"
    }
  ]
}
```

- "mode": CLIENT, SERVER
- "media_folders": list, Contains a list of paths to the media
- "content_src": str, absolute path based on path used in config.cfg with sub-folder. e.g. /media/raid/
- "content_url": str, server url on the network with sub-folder: e.g. http://192.168.x.xxx:8000/tv_shows/

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