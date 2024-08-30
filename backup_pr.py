# For the code to work, create a settings.ini file in the root of the repository using the template:
# [VK]
# VK_TOKEN=<your vk token without quotes>


import requests
import configparser
from pprint import pprint
from datetime import datetime
from tqdm import tqdm


print('\n'.join([
    '1. Input USER ID VK',
    '2. Input Ya.disk token',
    '3. How many images to backup? (default - 5)',
    '==========================================='
    ]))

config = configparser.ConfigParser()
config.read("settings.ini")

VK_TOKEN = config["VK"]["VK_TOKEN"]
USER_ID = int(input())
DISK_TOKEN = input()
count = int(input())


class BackupPhoto:
    VK_BASE_URL = 'https://api.vk.com/method'
    DISK_BASE_URL = 'https://cloud-api.yandex.net/v1/disk/resources'

    def __init__(self, vk_token, disk_token, user_id):
        self.vk_token = vk_token
        self.disk_token = disk_token
        self.user_id = user_id
        self.headers = {'Authorization': f'OAuth {disk_token}'}

    def get_photos(self):
        params = {
            'owner_id': self.user_id,
            'album_id': 'profile',
            'rev': '0',
            'extended': '1',
            'access_token': self.vk_token,
            'v': '5.199',
        }
        response = requests.get(f"{self.VK_BASE_URL}/photos.get", params=params)
        return response.json()['response']

    def mkdir_on_disk(self):
        requests.put(self.DISK_BASE_URL,
                     params={'path': 'BackupPhotosVK'},
                     headers=self.headers)
    
    def make_url_for_backup(self, images_json, item):
        filename = [f"{images_json['items'][item]['likes']['count']}",
                    f"{datetime.now().strftime('%d-%m-%y_%H-%M-%S')}"]
        request_path = f'BackupPhotosVK/{filename[0]}'
        response = requests.get(f"{self.DISK_BASE_URL}/upload",
                                params={'path': request_path},
                                headers=self.headers)
        if 'href' not in response.json():
            request_path = f"BackupPhotosVK/{'@'.join(filename)}"
            response = requests.get(f"{self.DISK_BASE_URL}/upload",
                                    params={'path': request_path},
                                    headers=self.headers)
        return response.json()['href'], request_path

    @staticmethod
    def to_disk(url, file):
        requests.put(url[0],
                     files={'file': file})


if __name__ == '__main__':
    vk_client = BackupPhoto(VK_TOKEN, DISK_TOKEN, USER_ID)
    image_json = vk_client.get_photos()['response']
    vk_client.mkdir_on_disk()
    if image_json['count'] < count:
        count = image_json['count']
        print(f'Only {count} images found')
    for i in tqdm(range(count)):
        data = {'files': []}
        sizes = dict()
        for j in image_json['items'][i]['sizes']:
            sizes.update({j['height']: (j['url'],
                                        j['type'])})
        photo = requests.get(sizes[max(sizes)][0]).content
        url_and_name = vk_client.make_url_for_backup(image_json, i)
        vk_client.to_disk(url_and_name, photo)
        data['files'].append({
            'filename': f"{url_and_name[1].split('/')[1]}.jpg",
            'size': sizes[max(sizes)][1]
        })
        pprint(data)
