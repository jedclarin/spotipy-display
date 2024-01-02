# Spotipy Display
Raspberry Pi-powered display to view and control Spotify playback.

**Features:**
- View current playing song title and artist, liked status 
- Play / Pause
- Like / Unlike
- Previous / Next song

![spotipy-display](https://github.com/jedclarin/spotipy-display/assets/34991412/29261ffa-ba3b-4048-be6f-672b643eee58)


## Hardware
- [Raspberry Pi 4](https://www.amazon.ca/Raspberry-Model-2019-Quad-Bluetooth/dp/B07TC2BK1X/ref=sr_1_5)
- [Raspberry Pi OS Lite 64 bit (bookworm)](https://downloads.raspberrypi.com/raspios_lite_arm64/images/raspios_lite_arm64-2023-12-11/2023-12-11-raspios-bookworm-arm64-lite.img.xz)
- [Waveshare 2.7" ePaper GPIO HAT](https://www.amazon.ca/2-7inch-HAT-Resolution-Electronic-Communicating/dp/B075FQKSZ9/ref=sr_1_1)

## Setup
Clone the repository: `git clone https://github.com/jedclarin/spotipy-display`

### Configure Raspberry Pi
Turn on SPI after attaching e-paper display to Pi via GPIO.
1. Open Raspberry Pi config: `sudo raspi-config`
2. Choose Interfacing Options -> SPI -> Yes Enable SPI interface
3. Save config changes
4. Reboot Pi: `sudo reboot`

### Set up Spotify Developer Application
1. Go to [Spotify for Developers](https://developer.spotify.com/)
2. Log in / Make a spotify developer account
3. Navigate to dashboard and create a new application
4. Complete form, set Redirect URI to: `http://localhost`
5. Select Web API
6. Save app
7. Go to app settings
8. Copy Client ID and Client Secret
    
### Install dependencies
1. Open terminal in folder: `cd spotipy-display`
2. Create a `.env` file based on `.env.example` with your Spotify Developer Application client ID and secret
3. Set up virtualenv: `python3 -m venv --system-site-packages venv`
4. Activate virtualenv: `source venv/bin/activate`
5. Install dependencies: `pip3 install python-dotenv RPi.GPIO Pillow spotipy numpy`

### Test spotipy-display
Before configuring `spotipy-display` to run automatically, test it first.
1. Activate virtualenv: `source venv/bin/activate`
2. Run: `python3 main.py`
3. After confirming that it works quit with <kbd>CTRL+C</kbd>

### Run on reboot
1. Add systemctl service: `sudo nano /etc/systemd/system/spotipy.service`
    ```
    # This assumes your username is also `pi`. Update accordingly.
    # /etc/systemd/system/spotipy.service
    [Unit]
    Description=Spotipy Service
    After=network.target

    [Service]
    ExecStart=/home/pi/spotipy-display/venv/bin/python3 /home/pi/spotipy-display/main.py
    WorkingDirectory=/home/pi/spotipy-display
    Restart=always
    User=pi
    Group=pi
    Environment=PATH=/home/pi/spotipy-display/venv/bin:/usr/bin:$PATH

    [Install]
    WantedBy=multi-user.target
    ```
2. Reload systemctl: `sudo systemctl daemon-reload`
3. Enable `spotipy-display`: `sudo systemctl enable spotipy.service`
4. Start `spotipy-display`: `sudo systemctl start spotipy.service`
5. Monitor logs: `sudo journalctl -fu spotipy.service`
6. Reboot Pi to ensure everything works :)