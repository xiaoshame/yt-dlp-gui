# -*- coding:utf-8 -*-
import copy
import http.client
import json
import time
import urllib
import urllib.request
from urllib import parse
from urllib.parse import urlencode, urlparse, parse_qs
from video_fields_std import Std_fields_video
import requests
import gzip

class haokan(object):
    def __init__(self, url):
        self.bv = url
        self.video_data_template = Std_fields_video().video_data
        self.video_data_template['platform'] = 'haokan'
        pop_lst = ['channel', 'describe', 'isOriginal', 'repost_count']
        for key in pop_lst:
            self.video_data_template.pop(key)
    def get_video(self):
        base_url = self.bv
        
        headers = {
            "user-agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.3 Mobile/15E148 Safari/604.1"
        }
        try:
            response = urllib.request.urlopen(base_url)
            if response.code == 200:    
                data = response.read()
                html = data.decode('utf-8')
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

    def video_page(self, url,vid=None):
        """
        For Haokan App, video_page method ONLY accept pass in vid, rather than
        video url.
        """
        url = self.bv
        if vid is None:
            return None

        # post_url = ('https://sv.baidu.com/haokan/api?'
        #             'cmd=comment/getreply&log=vhk&tn=1001128v&ctn=1001128v'
        #             '&imei=279014587228348'
        #             '&cuid=C577C0F8F6AA9FFE3E41CB0B3E507A14|843822785410972'
        #             '&os=android&osbranch=a0&ua=810_1440_270&ut=ALP-AL00_6.0.1_23_HUAWEI'
        #             '&apiv=4.6.0.0&appv=409011&version=4.9.1.10'
        #             '&life=1546591253&clife=1546591253&hid=B3697DD2F02F9A031714A93CCDF0A4C7'
        #             '&imsi=0&network=1'
        #             '&sids=1373_1-1436_4-1629_2-1647_1-1646_2-1708_1-1715_2'
        #             '-1736_1-1738_3-1739_1-1748_3-1754_2-1757_1-1767_1'
        #             '-1772_2-1776_1-1778_1-1780_3-1782_1-1786_2-1803_1'
        #             '-1805_2-1806_3-1814_2 HTTP/1.1')
        post_url = 'https://sv.baidu.com/haokan/api?tn=1008350o&ctn=1008350o&os=ios&cuid=E8019FD33EC4EBA7B853AF10A50A02D705F02DECEFMBGNNIETE&osbranch=i0&ua=640_1136_326&ut=iPhone5%2C4_10.3.3&net_type=-1&apiv=5.1.0.10&appv=1&version=5.1.0.10&life=1563337077&clife=1563337077&sids=&idfa=E3FC9054-384B-485F-9B4C-936F33D7D099&hid=9F5E84EAEEE51F4C190ACE7AABEB915F&young_mode=0&log=vhk&location=&cmd=video/detail'
        # raw header str:
        # header_str = ('Charset: UTF-8'
        #             'User-Agent: Mozilla/5.0 (Linux; Android 6.0.1; ALP-AL00 Build/V417IR; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/52.0.2743.100 Mobile Safari/537.36 haokan/4.9.1.10 (Baidu; P1 6.0.1)/IEWAUH_32_1.0.6_00LA-PLA/1001128v/C577C0F8F6AA9FFE3E41CB0B3E507A14%7C843822785410972/1/4.9.1.10/409011/1'
        #             'XRAY-TRACEID: 9624a81f-15e0-486e-b79f-d97b30c5b7d0'
        #             'XRAY-REQ-FUNC-ST-DNS: okHttp;1546598993248;0'
        #             'Content-Type: application/x-www-form-urlencoded'
        #             'Content-Length: 267'
        #             'Host: sv.baidu.com'
        #             'Connection: Keep-Alive'
        #             'Accept-Encoding: gzip'
        #             'Cookie: BAIDUID=1EA157CF3563181B98E5ABC1DED982D6:FG=1; BAIDUZID=805xaZQOUQRP3LqnkFs1bl2Bv-TD-CMHnotPgI4vkWabaQgbAx_tx4yMxTHzMBqpC0hwc6ZRa4xUFEkFwB3jxCO_Lg8d5s9gk9OSOeIowQ2k; BAIDUCUID=luvyi0aLHf0RuSajY8S2ug8fvi0u82uugi2IigiS2i80Pv8hYavG8jafv8gqO28EA'
        #             )
        headers = {
                "Accept": "*/*",
                "Accept-Encoding": "gzip, deflate",
                'Charset': 'UTF-8',
                "Accept-Language": "zh-Hans-CN;q=1",
                "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 10_3_3 like Mac OS X) AppleWebKit/603.3.8 (KHTML, like Gecko) Mobile/14G60 haokan/5.1.0.10 (Baidu; P2 10.3.3)/3.3.01_4,5enohP/381d/E7919FD33EC4EBA7B853AF10A50A02D705F02DECEFMBGNNIETE/1 HTTP/1.1",
                # "XRAY-REQ-FUNC-ST-DNS": "okHttp;1562813246444;0",
                # "XRAY-TRACEID": "5bd68916-4696-4bb3-b3a3-57a0c6a15949",
                'Content-Type': 'application/x-www-form-urlencoded',
                # 'Content-Length': '267',
                'Host': 'sv.baidu.com',
                'Connection': 'Keep-Alive',
                "X-Bfe-Quic": "enable=1",
                "Cookie": "BAIDUCUID=luBHiY8JSig3iHiZ0iSLi0O_v80Gi2iqlav6u_aCS8g1aH8H_iS9a0ivWu0dtQODzbXmA; BAIDUID=F2385E8E821854CA8BE4E30920EED52F:FG=1"
        }

        # raw post data is like:
        # 'comment%2Fgetreply=method%3Dget%26url_key%3D13089959609189000356%26pn%3D1%26rn%3D10%26child_rn%3D2%26need_ainfo%3D0%26type%3D0%26vid%3D13089959609189000356&video%2Fdetail=method%3Dget%26url_key%3D13089959609189000356%26log_param_source%3D%26vid%3D13089959609189000356'
        # which can be decoded as urlencode rule as
        # post_str_decoded = ('comment/getreply=method=get'
        #                     '&url_key=13089959609189000356&pn=1'
        #                     '&rn=10'
        #                     '&child_rn=2'
        #                     '&need_ainfo=0'
        #                     '&type=0'
        #                     '&vid=13089959609189000356'
        #                     '&video/detail=method=get'
        #                     '&url_key=13089959609189000356'
        #                     '&log_param_source='
        #                     '&vid=13089959609189000356')
        # We cannot directly nest dict within dict for post data, or
        # the '{' and '}' will be treated as straight character rather than
        # dictionary boundary, which will lead to un-expected results.
        # The correct way to do this is two-set urlencode.
        comment_getreplyDict = {'method': 'get',
                                # 'url_key': '13089959609189000356&pn=1',
                                'url_key': '%s&pn=1' % vid,
                                'rn': '10',
                                'child_rn': '2',
                                'need_ainfo': '0',
                                'type': '0',
                                # 'vid': '13089959609189000356',
                                'vid': vid,
                                }
        comment_getreplyEncodedStr = urlencode(comment_getreplyDict)
        video_detailDict = {'method': 'get',
                            # 'url_key': '13089959609189000356',
                            'url_key': vid,
                            'log_param_source': 'author',
                            # 'vid': '13089959609189000356'
                            'vid': vid,
                            # "adparam": r"""{"screen_type":0,"pid":"","ac":"1","install_timestamp":"","ext":"[{\"k\":\"video_vid\",\"v\":\"%s\"},{\"k\":\"iad\",\"v\":\"327681\"}]","ver":"5.1.0.10","mod":"VIVO X20","ov":"6.0.1","baiduId":"A6DC59055E4FC518778A19436C23B49A:FG=1","fmt":"json","apna":"com.baidu.haokan","eid":"1957_2,2193_3,2230_4,2320_1,2326_2,2353_1,2359_3,2376_1,2391_1,2433_4,2436_5,2438_1,2442_1,2443_2,2452_1,2457_2,2470_1,2480_2,2511_1,2525_4,2529_1,2537_1,2538_1,2540_1,2555_2,2563_1,2565_2,2568_1,2574_1,2575_1,2577_1,2582_1","ot":"2","ct":"2","nt":"1","android_id":"7313ae71df9e5367","iad":327681,"ua":"810_1399_android_5.1.0.10_270","apinfo":"na_z_vOm8vLw8fDy8v-sqvLys_by8fX_9__18ff28fbhpKiq6aWmrqOy6a-mqKymqeH1__H18_P1__X-8P728v_HA_..%7Cqloc2","latitude":"39.911017","longitude":"116.413562","source":"videolanding"}"""
                            }
        video_detailEncodedStr = urlencode(video_detailDict)
        post_data = {'comment/getreply': comment_getreplyEncodedStr,
                     'video/detail': video_detailEncodedStr}

        get_page = requests.post(post_url, data=post_data, headers=headers)
        # print(get_page.text)
        try:
            page_dict = get_page.json()
            print(page_dict)
        except:
            self.count_false += 1
            if self.count_false <= 5:
                self.video_page(url, vid=vid)
            else:
                return None
        self.count_false = 0
        video_dict = copy.deepcopy(self.video_data_template)
        try:
            videoD = page_dict['video/detail']['data']
            commntD = page_dict['comment/getreply']['data']
        except:
            return None
        try:
            video_dict['comment_count'] = int(commntD['comment_count'])
            video_dict['favorite_count'] = videoD['like_num']
        except Exception:
            return None
        else:
            try:
                video_dict['duration'] = videoD['duration']
                fetch_time = int(time.time() * 1e3)
                video_dict['fetch_time'] = fetch_time
                video_dict['play_count'] = videoD['playcnt']
                video_dict['release_time'] = int(videoD['publishTime'] * 1e3)
                video_dict['releaser'] = videoD['author']
                video_dict['title'] = videoD['title']
                video_dict['video_id'] = vid
                partial_url = '{"nid":"sv_%s"}' % vid
                partial_url_encode = urllib.parse.quote_plus(partial_url)
                video_dict['url'] = ('https://sv.baidu.com/videoui/page/videoland?context=%s'
                                     % partial_url_encode)
                releaser_id = videoD['appid']
                video_dict['releaserUrl'] = 'https://haokan.baidu.com/haokan/wiseauthor?app_id=' + releaser_id
                video_dict['releaser_id_str'] = 'haokan_' + releaser_id
                video_dict['video_img'] = videoD['cover_src']
            except:
                return None
        print(video_dict)
        return video_dict
    
    def video_page1(self):
        """
        For Haokan App, video_page method ONLY accept pass in vid, rather than
        video url.
        """
        parsed_url = urlparse(self.bv)
        query_params = parse_qs(parsed_url.query)
        vid = query_params.get('vid', [''])[0]

        if vid is None:
            return None

        post_url = 'https://sv.baidu.com/haokan/api?tn=1008350o&ctn=1008350o&os=ios&cuid=E8019FD33EC4EBA7B853AF10A50A02D705F02DECEFMBGNNIETE&osbranch=i0&ua=640_1136_326&ut=iPhone5%2C4_10.3.3&net_type=-1&apiv=5.1.0.10&appv=1&version=5.1.0.10&life=1563337077&clife=1563337077&sids=&idfa=E3FC9054-384B-485F-9B4C-936F33D7D099&hid=9F5E84EAEEE51F4C190ACE7AABEB915F&young_mode=0&log=vhk&location=&cmd=video/detail'
        # raw header str:
        # header_str = ('Charset: UTF-8'
        #             'User-Agent: Mozilla/5.0 (Linux; Android 6.0.1; ALP-AL00 Build/V417IR; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/52.0.2743.100 Mobile Safari/537.36 haokan/4.9.1.10 (Baidu; P1 6.0.1)/IEWAUH_32_1.0.6_00LA-PLA/1001128v/C577C0F8F6AA9FFE3E41CB0B3E507A14%7C843822785410972/1/4.9.1.10/409011/1'
        #             'XRAY-TRACEID: 9624a81f-15e0-486e-b79f-d97b30c5b7d0'
        #             'XRAY-REQ-FUNC-ST-DNS: okHttp;1546598993248;0'
        #             'Content-Type: application/x-www-form-urlencoded'
        #             'Content-Length: 267'
        #             'Host: sv.baidu.com'
        #             'Connection: Keep-Alive'
        #             'Accept-Encoding: gzip'
        #             'Cookie: BAIDUID=1EA157CF3563181B98E5ABC1DED982D6:FG=1; BAIDUZID=805xaZQOUQRP3LqnkFs1bl2Bv-TD-CMHnotPgI4vkWabaQgbAx_tx4yMxTHzMBqpC0hwc6ZRa4xUFEkFwB3jxCO_Lg8d5s9gk9OSOeIowQ2k; BAIDUCUID=luvyi0aLHf0RuSajY8S2ug8fvi0u82uugi2IigiS2i80Pv8hYavG8jafv8gqO28EA'
        #             )
        headers = {
                "Accept": "*/*",
                "Accept-Encoding": "gzip, deflate",
                'Charset': 'UTF-8',
                "Accept-Language": "zh-Hans-CN;q=1",
                "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 10_3_3 like Mac OS X) AppleWebKit/603.3.8 (KHTML, like Gecko) Mobile/14G60 haokan/5.1.0.10 (Baidu; P2 10.3.3)/3.3.01_4,5enohP/381d/E7919FD33EC4EBA7B853AF10A50A02D705F02DECEFMBGNNIETE/1 HTTP/1.1",
                # "XRAY-REQ-FUNC-ST-DNS": "okHttp;1562813246444;0",
                # "XRAY-TRACEID": "5bd68916-4696-4bb3-b3a3-57a0c6a15949",
                'Content-Type': 'application/x-www-form-urlencoded',
                # 'Content-Length': '267',
                'Host': 'sv.baidu.com',
                'Connection': 'Keep-Alive',
                "X-Bfe-Quic": "enable=1",
                "Cookie": "BAIDUCUID=luBHiY8JSig3iHiZ0iSLi0O_v80Gi2iqlav6u_aCS8g1aH8H_iS9a0ivWu0dtQODzbXmA; BAIDUID=F2385E8E821854CA8BE4E30920EED52F:FG=1"
        }

        # raw post data is like:
        # 'comment%2Fgetreply=method%3Dget%26url_key%3D13089959609189000356%26pn%3D1%26rn%3D10%26child_rn%3D2%26need_ainfo%3D0%26type%3D0%26vid%3D13089959609189000356&video%2Fdetail=method%3Dget%26url_key%3D13089959609189000356%26log_param_source%3D%26vid%3D13089959609189000356'
        # which can be decoded as urlencode rule as
        # post_str_decoded = ('comment/getreply=method=get'
        #                     '&url_key=13089959609189000356&pn=1'
        #                     '&rn=10'
        #                     '&child_rn=2'
        #                     '&need_ainfo=0'
        #                     '&type=0'
        #                     '&vid=13089959609189000356'
        #                     '&video/detail=method=get'
        #                     '&url_key=13089959609189000356'
        #                     '&log_param_source='
        #                     '&vid=13089959609189000356')
        # We cannot directly nest dict within dict for post data, or
        # the '{' and '}' will be treated as straight character rather than
        # dictionary boundary, which will lead to un-expected results.
        # The correct way to do this is two-set urlencode.
        comment_getreplyDict = {'method': 'get',
                                # 'url_key': '13089959609189000356&pn=1',
                                'url_key': '%s&pn=1' % vid,
                                'rn': '10',
                                'child_rn': '2',
                                'need_ainfo': '0',
                                'type': '0',
                                # 'vid': '13089959609189000356',
                                'vid': vid,
                                }
        comment_getreplyEncodedStr = urlencode(comment_getreplyDict)
        video_detailDict = {'method': 'get',
                            # 'url_key': '13089959609189000356',
                            'url_key': vid,
                            'log_param_source': 'author',
                            # 'vid': '13089959609189000356'
                            'vid': vid,
                            # "adparam": r"""{"screen_type":0,"pid":"","ac":"1","install_timestamp":"","ext":"[{\"k\":\"video_vid\",\"v\":\"%s\"},{\"k\":\"iad\",\"v\":\"327681\"}]","ver":"5.1.0.10","mod":"VIVO X20","ov":"6.0.1","baiduId":"A6DC59055E4FC518778A19436C23B49A:FG=1","fmt":"json","apna":"com.baidu.haokan","eid":"1957_2,2193_3,2230_4,2320_1,2326_2,2353_1,2359_3,2376_1,2391_1,2433_4,2436_5,2438_1,2442_1,2443_2,2452_1,2457_2,2470_1,2480_2,2511_1,2525_4,2529_1,2537_1,2538_1,2540_1,2555_2,2563_1,2565_2,2568_1,2574_1,2575_1,2577_1,2582_1","ot":"2","ct":"2","nt":"1","android_id":"7313ae71df9e5367","iad":327681,"ua":"810_1399_android_5.1.0.10_270","apinfo":"na_z_vOm8vLw8fDy8v-sqvLys_by8fX_9__18ff28fbhpKiq6aWmrqOy6a-mqKymqeH1__H18_P1__X-8P728v_HA_..%7Cqloc2","latitude":"39.911017","longitude":"116.413562","source":"videolanding"}"""
                            }
        video_detailEncodedStr = urlencode(video_detailDict)
        post_data = {'comment/getreply': comment_getreplyEncodedStr,
                     'video/detail': video_detailEncodedStr}
        data = urlencode(post_data).encode('utf-8')
        req = urllib.request.Request(post_url, data=data, method='POST',headers=headers)
        response = urllib.request.urlopen(req)
        get_page = response.read()
        uncompressed_data = gzip.decompress(get_page).decode('utf-8')
        # get_page = requests.post(post_url, data=post_data, headers=headers)
        # print(get_page.text)
        try:
            page_dict = json.loads(uncompressed_data)
            videoD = page_dict['video/detail']['data']
            download_url = videoD['video_list']['sc']
            title = videoD['title']
            print(download_url + title)
        except Exception as e:
            print(e)

if __name__ == '__main__':
    # test = haokan("https://haokan.baidu.com/v?vid=11231414361411904045")
    test = haokan("https://haokan.baidu.com/v?pd=wisenatural&vid=4080265651564946911")
    
    # title,url = test.get_video()
    # title1,url1 = test.get_video1()
    video_dict = test.video_page1()
    input("press any key to exit!")