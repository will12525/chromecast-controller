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
