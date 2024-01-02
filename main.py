import os
import logging
import epd2in7_V2
import time
from PIL import Image,ImageDraw,ImageFont
import RPi.GPIO as GPIO
import time
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import requests
from io import BytesIO
import threading

load_dotenv()
logging.basicConfig(level=logging.ERROR)

KEY_1 = 5
KEY_2 = 6
KEY_3 = 13
KEY_4 = 19
PADDING = 4
TITLE_Y = 100 + PADDING * 5
ARTIST_Y = TITLE_Y + 16 + PADDING
REFRESH_SECS = 3

epd = epd2in7_V2.EPD()
current_dir = os.getcwd()
image_dir = os.path.join(current_dir, 'images')
font_path = os.path.join(image_dir, 'Font.ttc')
font16 = ImageFont.truetype(font_path, 16)
font14 = ImageFont.truetype(font_path, 14)
current_song_name = None
scope = "user-read-playback-state,user-modify-playback-state,user-library-read,user-library-modify"

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope))

def get_current_song():
    current_song = sp.current_user_playing_track()
    if current_song is None:
        return None, None, None
    else:
        return (
            current_song["item"]["name"],
            current_song["item"]["artists"][0]['name'],
            current_song["item"]["album"]["images"][1]["url"],
        )

def is_playing():
    current_song = sp.current_user_playing_track()
    return current_song["is_playing"]

def is_liked():
    current_song = sp.current_user_playing_track()
    uri = current_song["item"]["uri"]
    is_liked = sp.current_user_saved_tracks_contains([uri])

    return is_liked and is_liked[0]

def like_or_unlike():
    current_song = sp.current_user_playing_track()
    uri = current_song["item"]["uri"]
    is_liked = sp.current_user_saved_tracks_contains([uri])
    
    if is_liked and is_liked[0]:
        sp.current_user_saved_tracks_delete([uri])
    else:
        sp.current_user_saved_tracks_add([uri])

def convert_jpeg_url_to_bmp(image_url, output_path):
    try:
        # Fetch the image from the URL
        response = requests.get(image_url)
        response.raise_for_status()

        # Open the image from the response content
        with Image.open(BytesIO(response.content)) as img:
            resized_img = img.resize((100, 100))
            # Save the image in BMP format
            resized_img.save(output_path, "BMP")
        print(f"Conversion successful. BMP file saved at {output_path}")
    except Exception as e:
        print(f"Error during conversion: {e}")

def display_no_song():
    epd.init_Fast()

    image = Image.new('1', (epd.height, epd.width), 255)
    draw = ImageDraw.Draw(image)
    draw.text((PADDING, PADDING), 'No Current Song', font = font16)

    epd.display_Fast(epd.getbuffer(image))

def display_song():
    try:
        song, artist, image_url = get_current_song()
        if song is None:
            display_no_song()
            return
        
        image_output_path = os.path.join(image_dir, 'album_image.bmp')
        
        convert_jpeg_url_to_bmp(image_url, image_output_path)

        epd.init_Fast()

        image = Image.new('1', (epd.height, epd.width), 255)
        draw = ImageDraw.Draw(image)
        album_art = Image.open(image_output_path)
        image.paste(album_art, (PADDING,PADDING))

        if is_playing():
            playing_icon_path = os.path.join(image_dir, "play.bmp")
            playing_icon = Image.open(playing_icon_path).convert("RGBA")
            _, _, _, a = playing_icon.split()
            image.paste(playing_icon, (226, PADDING), mask=a)
        else:
            pause_icon_path = os.path.join(image_dir, "pause.bmp")
            pause_icon = Image.open(pause_icon_path).convert("RGBA")
            _, _, _, a = pause_icon.split()
            image.paste(pause_icon, (226, PADDING), mask=a)

        if is_liked():
            like_icon_path = os.path.join(image_dir, "heart-liked.bmp")
            like_icon = Image.open(like_icon_path).convert("RGBA")
            _, _, _, a = like_icon.split()
            image.paste(like_icon, (228, PADDING + 32 + PADDING), mask=a)
        
        draw.text((PADDING, TITLE_Y), song, font = font16)
        draw.text((PADDING, ARTIST_Y), artist, font = font14)

        epd.display_Fast(epd.getbuffer(image))

    except IOError as e:
        logging.info(e)
        
    except KeyboardInterrupt:    
        logging.info("ctrl + c:")
        epd2in7_V2.epdconfig.module_exit(cleanup=True)
        exit()

def clear_screen():
    epd.init()
    epd.Clear()

def check_song():
    global current_song_name
    while True:
        new_song_name = get_current_song()[0]
        if current_song_name != new_song_name:
            # Song has been updated, perform necessary actions
            current_song_name = new_song_name
            display_song()
        time.sleep(REFRESH_SECS)

def previous_song():
    sp.previous_track()

def next_song():
    sp.next_track()

def button_check():
    # pin numbers are interpreted as BCM pin numbers.
    GPIO.setmode(GPIO.BCM)
    # Sets the pin as input and sets Pull-up mode for the pin.
    GPIO.setup(KEY_1,GPIO.IN,GPIO.PUD_UP)
    GPIO.setup(KEY_2,GPIO.IN,GPIO.PUD_UP)
    GPIO.setup(KEY_3,GPIO.IN,GPIO.PUD_UP)
    GPIO.setup(KEY_4,GPIO.IN,GPIO.PUD_UP)

    while True:
        time.sleep(0.05)
        # Returns the value read at the given pin. It will be HIGH or LOW (0 or 1).

        if GPIO.input(KEY_1) == 0:
            if is_playing():
                sp.pause_playback()
            else:
                sp.start_playback()
            display_song()
            while GPIO.input(KEY_2) == 0:
                time.sleep(0.01)

        elif GPIO.input(KEY_2) == 0:
            like_or_unlike()
            display_song()
            while GPIO.input(KEY_1) == 0:
                time.sleep(0.01)

        elif GPIO.input(KEY_3) == 0:
            previous_song()
            while GPIO.input(KEY_3) == 0:
                time.sleep(0.01)

        elif GPIO.input(KEY_4) == 0:
            next_song()
            while GPIO.input(KEY_4) == 0:
                time.sleep(0.01)

def main():
    clear_screen()

    update_thread = threading.Thread(target=check_song)
    update_thread.start()

    try:
        button_check()
    except KeyboardInterrupt:
        print("Program terminated. Cleaning up...")
        GPIO.cleanup()
        update_thread.join()

if __name__ == "__main__":
    main()