# Vinyl Scrobbler


Tool that allows user to select Album pulled from discogs collection and scrobble to last.fm


Install


Generate Discogs api key

Generate last.fm api key

Copy config.ini.example to config.ini and add api keys

Setup Display on Raspberry Pi

Setup will differ depending on which Raspberry Pi board and display you are using

Using display drivers
https://github.com/juj/fbcp-ili9341

Build Settings for Raspberry Pi Zero 2 with Adafruit 240x320 2.2" TFT w/ILI9340C
cmake -DILI9340=ON -DGPIO_TFT_DATA_CONTROL=25 -DGPIO_TFT_RESET_PIN=24 -DSPI_BUS_CLOCK_DIVISOR=6 -DSTATISTICS=0 -DSINGLE_CORE_BOARD=OFF -DARMV8A=ON ..

Set the display driver to launch on startup
Edit /etc/rtc.local in sudo mode and add
sudo /path/to/fbcp-ili9341/build/fbcp-ili9341 &


Install Dependencies


Due to requirements of keyboard libary requiring root other packages must be installed as root; This is normally (and still kind of is) very bad practice and should never be done. If any of the upstream libraries were to become malicious they would run as root on the raspberry pi. I would recommend not to have anything else running on this pi to lower this risk.

sudo apt install python-pip
sudo pip install python3-discogs-client
sudo pip install keyboard



Run with
sudo python main.py





