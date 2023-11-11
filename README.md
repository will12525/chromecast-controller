## Setup/Install the necessary system services

sudo ./controller.install

## To run locally

./start_server

### Use systemctl to control this application

services:

* chromecast_controller.service
* media_drive_as_webpage.service

```
sudo systemctl stop <service>
sudo systemctl start <service>
sudo systemctl restart <service>
```

## Sources

Icons: https://fontawesome.com/v4/icons/
Unicode character [chart](https://en.wikipedia.org/wiki/List_of_Unicode_characters).
