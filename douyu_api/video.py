import hashlib
import re
import time
import datetime
import execjs
import logging
import requests
from douyu_api.exceptions import RoomNotExistError
from douyu_api.core import BaseClient
import os
import threading
from urllib.parse import parse_qs
from requests import Session

logger = logging.getLogger(__name__)


class VideoClient(BaseClient):
    def __init__(
            self,
            video_id: str,
            storage: str = './video',
            session: Session = None,
            proxies: dict = None,
            timeout: int = 15
    ):
        super().__init__(proxies=proxies, timeout=timeout, session=session)
        self.storage = storage
        self.video_id = video_id
        self.d_id = '10000000000000000000000000001501'
        self.t_10 = str(int(time.time()))
        self.url = 'https://v.douyu.com/api/stream/getStreamUrl'
        self.headers = {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36'
        }
        self.running = False

    @staticmethod
    def md5(data):
        return hashlib.md5(data.encode('utf-8')).hexdigest()

    def get_param(self):
        """
        获取斗鱼getStreamUrl的参数
        :return: 参数
        """
        res = requests.get(
            'https://v.douyu.com/show/' + str(self.video_id), proxies=self.proxies
        ).text
        try:
            result = re.search(
                r'(vdwdae325w_64we[\s\S]*function ub98484234[\s\S]*?)function', res
            ).group(1)
        except AttributeError:
            logger.error(f'视频{self.video_id}不存在')
            raise RoomNotExistError(f"视频{self.video_id}不存在")
        point_id = re.findall(r'point_id":(\d+),', res)[0]

        func_ub9 = re.sub(r'eval.*?;}', 'strc;}', result)
        func_ub9 = re.sub(r'</script><script>!', '', func_ub9)
        # print(func_ub9)
        js = execjs.compile(func_ub9)
        res = js.call('ub98484234', point_id, self.d_id, self.t_10)
        v = re.search(r'v=(\d+)', res).group(1)
        rb = self.md5(point_id + self.d_id + self.t_10 + v)
        func_sign = re.sub(r'return rt;}\);?', 'return rt;}', res)

        func_sign = re.sub(r'\(function \(', 'function sign(', func_sign)
        func_sign = re.sub('CryptoJS\.MD5\(cb\)\.toString\(\)', '"' + rb + '"', func_sign)

        js = execjs.compile(func_sign)
        res = js.call('sign', point_id, self.d_id, self.t_10)
        params = res + f'&vid={self.video_id}'
        return params

    @staticmethod
    def get_save_file_path(save_path, room_id) -> str:
        format_string = "%Y-%m-%d %H-%M-%S"
        date_string = "%Y-%m-%d"
        now_time = datetime.datetime.now()
        time_string = now_time.strftime(format_string)
        date_string = now_time.strftime(date_string)
        file_name = f"{time_string}[{room_id}].flv"
        file_path = os.path.join(save_path, date_string, str(room_id))
        if not os.path.exists(file_path):
            os.makedirs(file_path)
        file_path = os.path.join(file_path, file_name)

        return file_path

    def download(self):
        params = self.get_param()
        params = parse_qs(params)
        result = {key: params[key][0] for key in params}
        try:
            response = requests.post(self.url, data=result, headers=self.headers).json()
        except Exception as e:
            self.running = False
            logger.error(f'视频{self.video_id}获取下载m3u8文件链接报错：{str(e)}')
            raise
        video_m3u8 = response.get('data').get('thumb_video').get('high').get('url')
        try:
            response = requests.get(video_m3u8, headers=self.headers).text
        except Exception as e:
            self.running = False
            logger.error(f'视频{self.video_id}获取m3u8文件报错: {str(e)}')
            raise
        video_list = re.findall(r'(transcode.*?)\n', response)
        file_path = self.get_save_file_path(self.storage, self.video_id)
        a = 0
        with open(f'{file_path}.ts', 'ab') as f:
            for video in video_list:
                res = re.findall(r'(_\d+-upload-.*?)_', video)[0]
                full_url = f'https://play-tx-ugcpub.douyucdn2.cn/live/high{res}/{video}'
                response = requests.get(full_url, headers=self.headers).content
                f.write(response)
                a += 1
                print(f'{a} / {len(video_list)}')

    def start(self):
        if self.running:
            logger.info(f"视频{self.video_id}正在下载")

        else:
            self.running = True
            self.video_server = threading.Thread(target=self.download)
            self.video_server.start()
            logger.info(f"视频{self.video_id}下载已启动")

    def stop(self):
        if self.video_server:
            if self.running:
                logger.info(f'视频{self.video_id}正在关闭下载')
                self.running = False
            else:
                logger.info(f'视频{self.video_id}下载服务已经关闭')

        else:
            logger.info(f'视频{self.video_id}下载服务不存在')








