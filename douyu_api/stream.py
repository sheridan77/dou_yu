import hashlib
import re
import time
import sys
import logging
import execjs
import threading
from douyu_api.exceptions import RoomNotExistError
from douyu_api.core import BaseClient
from requests import Session
import datetime
from io import BufferedWriter
from queue import Queue
import os


logger = logging.getLogger(__name__)


class StreamClient(BaseClient):
    def __init__(
        self,
        room_id: str,
        rate: int = 0,
        proxies: dict = None,
        timeout: int = 15,
        session: Session = None,
        storage: "BufferedWriter|Queue|str" = "./stream",
        interval_queue: Queue = None,
        file_interval: int = 10 * 60,
        chunk_size: int = 102400,
    ) -> None:
        '''
        rate: 1流畅；2高清；3超清；4蓝光4M；0蓝光8M或10M
        '''
        super().__init__(proxies=proxies, timeout=timeout, session=session)

        self.room_id = room_id
        self.rate = rate
        self.storage = storage
        self.chunk_size = chunk_size
        self.download_size = 0
        self.running = False
        self.stream_server: threading.Thread = None
        self.interval_queue = interval_queue

        if file_interval:
            self.file_interval = file_interval
        else:
            self.file_interval = None

        self.d_id = '10000000000000000000000000001501'
        self.t_10 = str(int(time.time()))
        self.t_13 = str(int((time.time()) * 1000))

    @staticmethod
    def md5(data):
        return hashlib.md5(data.encode('utf-8')).hexdigest()

    def get_pre(self):
        self.t_10 = str(int(time.time()))
        self.t_13 = str(int((time.time()) * 1000))
        url = 'https://playweb.douyucdn.cn/lapi/live/hlsH5Preview/' + self.room_id
        data = {'rid': self.room_id, 'did': self.d_id}
        auth = self.md5(self.room_id + self.t_13)
        headers = {'rid': self.room_id, 'time': self.t_13, 'auth': auth}
        res = self.session.post(
            url, headers=headers, data=data, proxies=self.proxies
        ).json()
        error = res['error']
        data = res['data']
        key = ''
        if data:
            rtmp_live = data['rtmp_live']
            key = re.search(
                r'(\d{1,8}[0-9a-zA-Z]+)_?\d{0,4}(/playlist|.m3u8)', rtmp_live
            ).group(1)
        return error, key

    def get_js(self):
        res = self.session.get(
            'https://m.douyu.com/' + str(self.room_id), proxies=self.proxies
        ).text
        result = re.search(r'(function ub98484234.*)\s(var.*)', res).group()
        func_ub9 = re.sub(r'eval.*;}', 'strc;}', result)
        js = execjs.compile(func_ub9)
        res = js.call('ub98484234')

        v = re.search(r'v=(\d+)', res).group(1)
        rb = self.md5(self.room_id + self.d_id + self.t_10 + v)

        func_sign = re.sub(r'return rt;}\);?', 'return rt;}', res)
        func_sign = func_sign.replace('(function (', 'function sign(')
        func_sign = func_sign.replace('CryptoJS.MD5(cb).toString()', '"' + rb + '"')

        js = execjs.compile(func_sign)
        params = js.call('sign', self.room_id, self.d_id, self.t_10)
        params += '&ver=219032101&rid={}&rate=-1'.format(self.room_id)

        url = 'https://m.douyu.com/api/room/ratestream'
        res = self.session.post(url, params=params, proxies=self.proxies).text
        key = re.search(r'(\d{1,8}[0-9a-zA-Z]+)_?\d{0,4}(.m3u8|/playlist)', res).group(
            1
        )

        return key

    def get_pc_js(self, cdn='ws-h5'):
        res = self.session.get(
            'https://m.douyu.com/' + str(self.room_id), proxies=self.proxies
        ).text
        result = re.search(
            r'(vdwdae325w_64we[\s\S]*function ub98484234[\s\S]*?)function', res
        ).group(1)
        func_ub9 = re.sub(r'eval.*?;}', 'strc;}', result)
        js = execjs.compile(func_ub9)
        res = js.call('ub98484234')

        v = re.search(r'v=(\d+)', res).group(1)
        rb = self.md5(self.room_id + self.d_id + self.t_10 + v)

        func_sign = re.sub(r'return rt;}\);?', 'return rt;}', res)
        func_sign = func_sign.replace('(function (', 'function sign(')
        func_sign = func_sign.replace('CryptoJS.MD5(cb).toString()', '"' + rb + '"')

        js = execjs.compile(func_sign)
        params = js.call('sign', self.room_id, self.d_id, self.t_10)

        params += '&cdn={}&rate={}'.format(cdn, self.rate)
        url = 'https://www.douyu.com/lapi/live/getH5Play/{}'.format(self.room_id)
        res = self.session.post(url, params=params, proxies=self.proxies).json()

        return res

    def get_save_file_path(self, save_path, room_id) -> str:
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

    def download_video(self):
        while self.running:
            try:
                error, key = self.get_pre()
                if error == 0:
                    pass
                elif error == 102:
                    self.running = False
                    logger.error(f"房间 {self.room_id} 不存在")
                    raise RoomNotExistError(f"房间 {self.room_id} 不存在")
                elif error == 104:
                    self.running = False
                    logger.info(f"房间 {self.room_id} 未开播")
                    break
                    # raise NotOnlineError('房间未开播')
                else:
                    key = self.get_js()
            except Exception as e:
                self.running = False
                logger.error(f"房间 {self.room_id} 获取真实视频地址报错:{str(type(e))} {str(e)}")
                raise
            # real_url = {}
            # real_url = "http://dyscdnali1.douyucdn.cn/live/{}.flv?uuid=".format(key)
            real_url = "http://tx2play1.douyucdn.cn/live/{}.xs?uuid=".format(key)
            # real_url["flv"] = "http://dyscdnali1.douyucdn.cn/live/{}.flv?uuid=".format(key)
            # real_url["x-p2p"] = "http://tx2play1.douyucdn.cn/live/{}.xs?uuid=".format(key)
            headers = {
                'Connection': 'keep-alive',
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36',
            }

            last_time = time.time()
            start_time = datetime.datetime.now()
            try:
                with self.session.get(
                    real_url, headers=headers, stream=True, proxies=self.proxies
                ) as response:

                    # 目前主要使用该模式
                    if isinstance(self.storage, str):
                        file_path = self.get_save_file_path(self.storage, self.room_id)
                        fp = open(file_path, "ab")

                        for data in response.iter_content(chunk_size=self.chunk_size):
                            self.download_size += self.chunk_size
                            logger.debug(f"房间 {self.room_id} 视频下载中")
                            fp.write(data)
                            # 判断是否需要停止
                            if not self.running:
                                logger.debug(f"房间 {self.room_id} 视频下载停止")
                                fp.close()
                                break
                            now_time = time.time()
                            # 判断是否需要分割
                            if (
                                self.file_interval
                                and now_time - last_time > self.file_interval
                            ):
                                fp.close()
                                logger.info(f"房间 {self.room_id} 视频分段")
                                break
                        else:
                            self.running = False
                            logger.warning(f"房间 {self.room_id} 直播视频流中断")
                        fp.close()
                    elif isinstance(self.storage, BufferedWriter):
                        for data in response.iter_content(chunk_size=self.chunk_size):
                            self.download_size += self.chunk_size
                            self.storage.write(data)
                            if not self.running:
                                logger.debug(f"房间 {self.room_id} 视频下载停止")
                                break
                    elif isinstance(self.storage, Queue):
                        for data in response.iter_content(chunk_size=self.chunk_size):
                            self.download_size += self.chunk_size
                            self.storage.put(
                                {
                                    "room_id": self.room_id,
                                    "start_time": start_time,
                                    "end_time": datetime.datetime.now(),
                                    "data": data,
                                }
                            )
                            if not self.running:
                                logger.debug(f"房间 {self.room_id} 视频下载停止")
                                break
                    else:
                        raise ValueError("不支持的storage类型")
            except Exception as e:
                self.running = False
                logger.error(f"房间 {self.room_id} 下载视频报错:{str(type(e))} {str(e)}")
                raise
            finally:
                # 最后将此次保存的视频信息存入interval_queue
                logger.debug(f"房间 {self.room_id} 存入视频数据")
                if isinstance(self.storage, str) and self.interval_queue:
                    self.interval_queue.put(
                        {
                            "room_id": self.room_id,
                            "start_time": start_time,
                            "end_time": datetime.datetime.now(),
                            "file_path": file_path,
                        }
                    )

    def start(self):
        if self.running == True:
            logger.info(f"房间 {self.room_id} 的视频已在采集中")
        else:
            self.running = True
            self.stream_server = threading.Thread(target=self.download_video)
            self.stream_server.start()
            logger.info(f"房间 {self.room_id} 的视频下载服务已启动")

    def stop(self):
        if self.stream_server:
            if self.running == True:
                logger.info(f"房间 {self.room_id} 的视频下载服务正在关闭")
                self.running = False
            else:
                logger.info(f"房间 {self.room_id} 的视频下载已经为关闭状态")
        else:
            logger.debug(f"房间 {self.room_id} 的视频下载服务不存在")
