# -*- coding:utf-8 -*-
import http.client
import json
from urllib.parse import urlparse

import requests
from downloaders import HaoKanDownloader


class haokan(object):
    def __init__(self, bv):
        self.bv = bv

    def get_video(self):
        base_url = self.bv
        
        headers = {
            "user-agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.3 Mobile/15E148 Safari/604.1"
        }
        try:
            response = requests.get(url=base_url, headers=headers, timeout=5)
            if response.status_code == 200:    
                # soup = BeautifulSoup(response.text, 'html.parser')
                html = response.text
                start = html.find("window.__PRELOADED_STATE__ = ")
                end = html.find("}};", start)
                json_str = html[start+len("window.__PRELOADED_STATE__ = "):end+2]
                json_data = json.loads(json_str)
                title= json_data['curVideoMeta']['title']
                videoInfo = json_data['curVideoMeta']['clarityUrl']
                url = ''
                for item in videoInfo:
                    if item['key'] == 'sc':
                        url = item['url']
                return title,url
        except Exception as e:
            return '',''
    def get_video1(self):
        base_url = urlparse(self.bv)      
        try:
            headers = {
                "user-agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.3 Mobile/15E148 Safari/604.1"
            }
            if base_url.scheme == 'https':
                conn = http.client.HTTPSConnection(base_url.netloc)
            else:
                conn = http.client.HTTPConnection(base_url.netloc)
            conn.request('GET', base_url.path,headers=headers)
            response = conn.getresponse()
            if response.status == 200:
                data = response.read()
                html = data.decode('utf-8')
                start = html.find("window.__PRELOADED_STATE__ = ")
                end = html.find("}};", start)
                if end > 0:
                    json_str = html[start+len("window.__PRELOADED_STATE__ = "):end+2]
                    json_data = json.loads(json_str)
                    title= json_data['curVideoMeta']['title']
                    videoInfo = json_data['curVideoMeta']['clarityUrl']

                    for item in videoInfo:
                        if item['key'] == 'sc':
                            url = item['url']
                elif html.find("};",start) > 0:
                    end = html.find("};",start)
                    json_str = html[start+len("window.__PRELOADED_STATE__ = "):end+1]
                    json_data = json.loads(json_str)
                    title= json_data['curVideoRelate'][0]['title']
                    url = json_data['curVideoRelate'][0]['playurl']
                else:
                    self._return_code = 0
                conn.close()
                return title,url
        except Exception as e:
            print(e)
            conn.close()
            return '',''

if __name__ == '__main__':
    test = haokan("https://haokan.baidu.com/v?vid=11231414361411904045")
    title,url = test.get_video()
    title1,url1 = test.get_video1()
    dl = HaoKanDownloader(url, title)
    dl.download()
    input("press any key to exit!")