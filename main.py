import os
import sys
import getopt
import eyed3
import random
import string
import asyncio
import requests
from shazamio import Shazam

szm = Shazam()
audio_list = []


def start():
    try:
        requests.get("https://www.google.com", timeout=5)
    except requests.ConnectionError:
        print('No internet connection. Please connect the Internet')

    args = sys.argv[1:]
    opts = 'hf:'
    long_opts = ['Help', 'Folder=']
    music_folder = 'music'
    try:
        arguments, values = getopt.getopt(args, opts, long_opts)
        for c, v in arguments:
            if c in ("-h", "--Help"):
                print(
                    "Hi User, that script needs to set tags for your favorite musics. \n"
                    "\nHow to use script you need to create new folder where script are placed, "
                    "then you need to move all your music to new folder. \n\nNext you need use command '-f' or "
                    "'--Folder'"
                    " with new folder name. \n\nExample 'main.py -f music' "
                    "\n\nBy default we use folder 'music' \n"
                )
            elif c in ('-f', '--Folder'):
                print(f'Your folder: {v}')
                try:
                    music_folder = str(v)
                except FileNotFoundError:
                    print("No such folder with name '%s' ! Try again with correctly folder" % v)

    except getopt.error as err:
        print('Something went wrong', err)

    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(about_track(music_folder))
    except KeyboardInterrupt:
        sys.exit()




def edit_tags(file_path, folder, music_name, title, artist, image_url, genres, album_name, lyrics):
    audio_for_eyed = eyed3.load(file_path)
    audio_for_eyed.initTag(version=(2, 3, 0))

    try:
        audio_for_eyed.rename(music_name)
    except OSError:
        audio_for_eyed.rename(f"{music_name}-copy-{''.join(random.choices(string.ascii_letters, k=1))}")

    audio_for_eyed.tag.title = title
    audio_for_eyed.tag.artist = artist

    if image_url != "-":
        if requests.get(image_url).status_code == 200:
            img_req = requests.get(image_url).content
            with open(f'{folder}/cover_{music_name}.jpeg', 'wb') as img:
                img.write(img_req)
            audio_for_eyed.tag.images.set(3, open(f'{folder}/cover_{music_name}.jpeg', 'rb').read(), 'image/jpeg')
            os.remove(f'{folder}/cover_{music_name}.jpeg')

    audio_for_eyed.tag.genre = genres
    audio_for_eyed.tag.album = album_name
    audio_for_eyed.tag.lyrics.set(lyrics)
    audio_for_eyed.tag.save(encoding='utf-8')

    print(f'Music ---> "{music_name}" <--- has been done')


async def about_track(folder):

    if not os.path.exists(folder):
        print(f'No such directory --> "{folder}" ')
        sys.exit()

    list_dir = os.listdir(folder)
    for m in list_dir:
        if m.endswith('.mp3') and os.path.getsize(f'{folder}/{m}') < 15000000:
            n = ''.join(random.choices(string.ascii_letters, k=6))
            os.rename(f'{folder}/{m}', f'{folder}/{n}.mp3')
            audio_list.append(f'{folder}/{n}.mp3')

    for i in audio_list:
        data_from_szm = await szm.recognize_song(i)

        if len(data_from_szm['matches']) > 0:
            music_name = data_from_szm['track']['share']['subject']
            title = data_from_szm['track']['title']
            artist = data_from_szm['track']['subtitle']

            try:
                image_url = data_from_szm['track']['images']['coverart']
                genres = data_from_szm['track']['genres']['primary']
            except KeyError:
                image_url = '-'
                genres = "-"

            if len(data_from_szm['track']['sections']) > 1 and data_from_szm['track']['sections'][1] is not None:
                try:
                    lyrics = '\n'.join(str(data_from_szm['track']['sections'][1]['text']).split(','))
                except KeyError:
                    lyrics = '-'
            else:
                lyrics = '-'

            if data_from_szm['track']['sections'][0]['metadata'] is not None:
                if len(data_from_szm['track']['sections'][0]['metadata']) > 1:
                    album_name = data_from_szm['track']['sections'][0]['metadata'][0]['text']
                else:
                    album_name = title
            else:
                album_name = title

            edit_tags(i,
                      folder,
                      str(music_name),
                      str(title),
                      str(artist),
                      str(image_url),
                      str(genres),
                      str(album_name),
                      str(lyrics)
                      )


if __name__ == '__main__':
    start()
