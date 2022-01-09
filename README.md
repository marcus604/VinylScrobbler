# Vinyl Scrobbler


Tool that allows user to select Album pulled from discogs collection and scrobble to last.fm

## Setup

### Setup Display on Raspberry Pi
Display build options will differ depending on which Raspberry Pi board and display you are using

Using display drivers [fbcp-ili9341](https://github.com/juj/fbcp-ili9341) - follow instructions on page for specific steps

Build Options for Raspberry Pi Zero 2 with Adafruit 240x320 2.2" TFT w/ILI9340C
```-DILI9340=ON -DGPIO_TFT_DATA_CONTROL=25 -DGPIO_TFT_RESET_PIN=24 -DSPI_BUS_CLOCK_DIVISOR=6 -DSTATISTICS=0 -DSINGLE_CORE_BOARD=OFF -DARMV8A=ON ..```

Add the lines to /boot/config.txt
```
hdmi_group=2
hdmi_mode=87
hdmi_cvt=320 240 60 1 0 0 0
hdmi_force_hotplug=1
```

Set the display driver to launch on startup
Edit /etc/rtc.local in sudo mode and add

```sudo /path/to/fbcp-ili9341/build/fbcp-ili9341 &```

## Install Dependencies

### [System]
```
sudo apt install python3-pip
sudo apt install python3-pigpio
sudo systemctl enable pigpiod
sudo apt install fim
sudo apt install libopenjp2-7
```
### [Python]

Due to requirements of keyboard libary requiring root, other packages must be installed as root; This is normally (and still kind of is) very bad practice and should be avoided. **I would recommend not to have anything else running on this pi to lower this risk.**
```
sudo pip install keyboard
sudo pip install python3-discogs-client
sudo pip install Pillow
```

Install

Generate Discogs api key

Generate last.fm api key

```git clone https://github.com/marcus604/VinylScrobbler.git```

Copy config.ini.example to config.ini and add api keys


Run 

```sudo python main.py```





