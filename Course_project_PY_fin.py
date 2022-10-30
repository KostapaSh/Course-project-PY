import time
from time import sleep
import requests
from pprint import pprint
from tqdm import tqdm
from datetime import datetime
import json


class GetFirstData:
    def _get_token(self):
        tokens = {}
        with open('token.txt', 'r', encoding='utf8') as file_object:
            for vkya in file_object:
                token_vkya = vkya.split(":")
                tokens[token_vkya[0]] = token_vkya[1]
        return tokens
        # _yatoken = tokens['yatoken'].rstrip('\n')
        # _vktoken = tokens['vktoken'].rstrip('\n')

    def get_yatoken(self):
        yatoken = self._get_token()
        return yatoken['yatoken'].rstrip('\n')

    def get_vktoken(self):
        vktoken = self._get_token()
        return vktoken['vktoken'].rstrip('\n')

    def get_user_id(self):
        user_id = input("Укажите User id VK: ")
        return str(user_id)

    def get_name_folder(self):
        name_folder = input("Укажите имя папки куда будут сохранены фотографии : ")
        if name_folder == '':
            name_folder = "MK_Foto"
        return str(name_folder)

    def get_number_photos(self):
        number_photos = input("Укажите количество фотографий для сохранения (по умолчанию 5): ")
        if number_photos == '':
            number_photos = 5
        elif number_photos.isdigit() == False:
            number_photos = 5
            print('Вы указали не цифру добавлено значение по умолчанию')
        return int(number_photos)

class ProgressBar():
    def __init__(self,for_cycle):
        self.for_cycle = for_cycle


class VkFoto:

    _file_name = ''
    _for_yadisk = []

    def __init__(self, user_id, vktoken, number_photos):
        self.user_id = user_id
        self.vktoken = vktoken
        self.number_photos = int(number_photos)

    def get_params(self):
       return {'user_ids': self.user_id,
               'album_id': 'profile',
               'extended': '1',
               'photo_sizes': '1',
               'access_token': self.vktoken,
               'v':'5.131'}

    def foto_vk(self):
        global _for_yadisk

        url = 'https://api.vk.com/method/photos.get'

        to_yadisk = []
        json_to_file = []
        get_likes = []

        get_all_res = requests.get(url, params=self.get_params()).json()
        get_res_dict = get_all_res['response']['items']

        if self.number_photos <= len(get_res_dict):
            for_cycle = self.number_photos
        else:
            for_cycle = len(get_res_dict)

        for cycle_number in tqdm(range(for_cycle)):
            options = get_res_dict[cycle_number]
            date = datetime.utcfromtimestamp(int(options['date'])).strftime('%d-%m-%Y')
            likes = options['likes']['count']
            sizes = options['sizes']
            for sizes_z in sizes:
                if sizes_z['type'] == 'z':
                    url_jpg = sizes_z['url']
            if likes not in get_likes:
                to_yadisk.append({'path': f"{likes}.jpg", 'url': url_jpg})
                json_to_file.append({'file_name':f"{likes}.jpg", 'size': sizes_z['type']})

            else:
                to_yadisk.append({'path':f"{likes}_{date}.jpg", 'url': url_jpg})
                json_to_file.append({'file_name':f"{likes}_{date}.jpg", 'size': sizes_z['type']})
            sleep(0.2)

        pprint(f"Найдено {for_cycle} фотографии")
        self._for_yadisk = to_yadisk
        self.creat_file(json_to_file)


    def creat_file(self, file):
        global _file_name
        to_file = file
        with open('list_foto.json', 'w', encoding='utf8') as w_json_file:
            json.dump(to_file, w_json_file)
            self._file_name = w_json_file.name

    def get_file_name(self):
        return self._file_name

    def get_param_for_yadisk(self):
        return self._for_yadisk


class YaDisk():

    url_upload = "https://cloud-api.yandex.net/v1/disk/resources/upload"

    def __init__(self, yatoken, name_folder):
        self.name_folder = name_folder
        self.yatoken = yatoken
        # if name_folder == '':
        #     self.name_folder = "MK_Foto"


    def get_headers(self):
        return {
            'Content-Type': 'application/json',
            'Authorization': 'OAuth {}'.format(self.yatoken)
        }

    def folder_yadisk(self):
        url_resources = "https://cloud-api.yandex.net/v1/disk/resources"
        print()
        params = {"path": self.name_folder, "fields": "true", "overwrite": "false"}

        put_response = requests.put(url_resources, params = params,  headers = self.get_headers())
        #print(put_response.status_code)
        if put_response.status_code == 201:
            #print("Success")
            return params['path']
        elif put_response.status_code == 409:
            return params['path']

    def load_foto_yadisk(self, data_from_vk):
        save_yadisk = data_from_vk
        folder = self.folder_yadisk()
        number_of_photos = 0

        for int_foto_save in tqdm(range(len(save_yadisk))):
            foto_save = save_yadisk[int_foto_save]
            foto_params = {'path': f"{folder}/{foto_save['path']}", 'url': foto_save['url'], 'overwrite': 'true'}
            put_response = requests.post(self.url_upload, headers=self.get_headers(), params=foto_params)
            if put_response.status_code == 202:
                number_of_photos += int_foto_save

        print(f"Ня яндекс диск в папку {folder} загружены фотографии")

    def load_file_yadisk(self, file_name):
        foto_file = file_name
        params_foto_file = {"path": f"{self.folder_yadisk()}/{foto_file}", "overwrite": "true"}
        get_response = requests.get(self.url_upload, headers=self.get_headers(), params=params_foto_file)
        href = get_response.json().get("href", "")
        #pprint(get_response.json())

        put_response = requests.put(href, data=open(foto_file, 'rb'))
        put_response.raise_for_status()
        if put_response.status_code == 201:
            print("Файл с названием фотографий сформирован")


if __name__ == '__main__':

    first_data = GetFirstData()
    vk_foto = VkFoto(first_data.get_user_id(), first_data.get_vktoken(), first_data.get_number_photos())
    yadisk = YaDisk(first_data.get_yatoken(), first_data.get_name_folder())
    vk_foto.foto_vk()
    yadisk.load_foto_yadisk(vk_foto.get_param_for_yadisk())
    yadisk.load_file_yadisk(vk_foto.get_file_name())
