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
VK_APP_ID = '52202339'
DISK_APP_ID = '3810293e5664403584c8d71d9436030c'
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
        return response.json()

    def backup(self, n=5):
        data = {'files': []}
        headers = {
            'Authorization': f'OAuth {self.disk_token}'
        }
        image_json = self.get_photos()['response']
        if image_json['count'] < n:
            n = image_json['count']
            print(f'Only {n} images found')

        requests.put(self.DISK_BASE_URL,
                     params={'path': 'BackupPhotosVK'},
                     headers=headers)

        for i in tqdm(range(n)):
            sizes = {image_json['items'][i]['orig_photo']['height']: (image_json['items'][i]['orig_photo']['url'],
                                                                      'base')}
            filename = [f"{image_json['items'][i]['likes']['count']}",
                        f"{datetime.now().strftime('%d-%m-%y_%H-%M-%S')}"]
                
            for j in image_json['items'][i]['sizes']:
                sizes.update({j['height']: (j['url'],
                                            j['type'])})

            photo = requests.get(sizes[max(sizes)][0]).content
            request_path = f'BackupPhotosVK/{filename[0]}'
            response = requests.get(f"{self.DISK_BASE_URL}/upload",
                                    params={'path': request_path},
                                    headers=headers)
                
            url_for_upload = response.json()
            if 'href' not in url_for_upload:
                request_path = f"BackupPhotosVK/{'@'.join(filename)}"
                response = requests.get(f"{self.DISK_BASE_URL}/upload",
                                        params={'path': request_path},
                                        headers=headers)
                    
            url_for_upload = response.json()['href']
            requests.put(url_for_upload,
                         files={'file': photo})
                
            data['files'].append({
                'filename': f"{request_path.split('/')[1]}.jpg",
                'size': sizes[max(sizes)][1]
                })

        pprint(data)


if __name__ == '__main__':
    vk_client = BackupPhoto(VK_TOKEN, DISK_TOKEN, USER_ID)
    vk_client.backup(count)
