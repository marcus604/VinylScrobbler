# Vinyl Scrobbler


Tool that allows user to select Album pulled from discogs collection and scrobble to last.fm


Install


Generate Discogs api key

Generate last.fm api key

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
sudo apt install pipenv
pipenv install


Run with
sudo python main.py





