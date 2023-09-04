import os
import sys
import getopt
import eyed3
import random
import string
import asyncio
import requests
from shazamio import Shazam


class MusicTagEditor:
    def __init__(self):
        self.szm = Shazam()
        self.music_list = []
        self.directory = ''
        self.audio_for_eyed = ''
        self.music_folder = 'music'
        self.opts = 'hf:'
        self.args = sys.argv[1:]
        self.long_opts = ['Help', 'Folder=']

    def help(self):
        try:
            requests.get("https://www.google.com", timeout=5)
        except requests.ConnectionError:
            print('No internet connection. Please connect the Internet')


        try:
            arguments, values = getopt.getopt(self.args, self.opts, self.long_opts)
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
                        self.music_folder = str(v)
                    except FileNotFoundError:
                        print("No such folder with name '%s' ! Try again with correctly folder" % v)

        except getopt.error as err:
            print('Something went wrong', err)

        try:
            loop = asyncio.get_event_loop()
            loop.run_until_complete(self.sazam())
        except KeyboardInterrupt:
            sys.exit()

    async def sazam(self):
        if not os.path.exists(self.music_folder):
            print(f'No such directory --> "{self.music_folder}" ')
            sys.exit()

        self.directory = os.listdir(self.music_folder)

        for m in self.directory:
            if m.endswith('.mp3') and os.path.getsize(f'{self.music_folder}/{m}') < 15000000:
                n = ''.join(random.choices(string.ascii_letters, k=6))
                os.rename(f'{self.music_folder}/{m}', f'{self.music_folder}/{n}.mp3')
                self.music_list.append(f'{self.music_folder}/{n}.mp3')

        for i in self.music_list:
            data_from_szm = await self.szm.recognize_song(i)

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

                self.tag_editor(i,
                                self.music_folder,
                                str(music_name),
                                str(title),
                                str(artist),
                                str(image_url),
                                str(genres),
                                str(album_name),
                                str(lyrics)
                                )

    def tag_editor(self, file_path, folder, music_name, title, artist, image_url, genres, album_name, lyrics):
        self.audio_for_eyed = eyed3.load(file_path)
        self.audio_for_eyed.initTag(version=(2, 3, 0))

        try:
            self.audio_for_eyed.rename(music_name)
        except OSError:
            self.audio_for_eyed.rename(f"{music_name}-copy-{''.join(random.choices(string.ascii_letters, k=1))}")

        self.audio_for_eyed.tag.title = title
        self.audio_for_eyed.tag.artist = artist

        if image_url != "-":
            if requests.get(image_url).status_code == 200:
                img_req = requests.get(image_url).content
                with open(f'{folder}/cover_{music_name}.jpeg', 'wb') as img:
                    img.write(img_req)
                self.audio_for_eyed.tag.images.set(3, open(f'{folder}/cover_{music_name}.jpeg', 'rb').read(), 'image/jpeg')
                os.remove(f'{folder}/cover_{music_name}.jpeg')

        self.audio_for_eyed.tag.genre = genres
        self.audio_for_eyed.tag.album = album_name
        self.audio_for_eyed.tag.lyrics.set(lyrics)
        self.audio_for_eyed.tag.save(encoding='utf-8')

        print(f'Music ---> "{music_name}" <--- has been done')


if __name__ == '__main__':
    music = MusicTagEditor()
    music.help()
