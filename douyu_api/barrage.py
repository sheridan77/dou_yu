import datetime
import json
import logging
import random
import time
from queue import Queue
from threading import Thread

import pystt
from websocket import WebSocketApp

from douyu_api.model import Barrage

logger = logging.getLogger(__name__)


class BarrageClient:
    def __init__(
        self,
        room_id: str,
        username: str = None,
        uid: str = None,
        proxy_type: str = None,
        http_proxy_host: str = None,
        http_proxy_port: int = None,
        storage: Queue = None,
    ):
        self.ws = WebSocketApp(
            "wss://danmuproxy.douyu.com:8503/",
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close,
            on_open=self.on_open,
        )
        # 斗鱼房间ID
        self.room_id = str(room_id)

        random_uid = str(random.randint(1000000000, 10000000000))
        # 弹幕登陆名
        if username:
            self.username = username
        else:
            self.username = random_uid
        # 弹幕 user ID
        if uid:
            self.uid = str(uid)
        else:
            self.uid = random_uid
        self.proxy_type = proxy_type
        self.http_proxy_host = http_proxy_host
        if http_proxy_port:
            self.http_proxy_port = str(http_proxy_port)
        else:
            self.http_proxy_port = None
        self.proxies = {
            "proxy_type": self.proxy_type,
            "http_proxy_host": self.http_proxy_host,
            "http_proxy_port": self.http_proxy_port,
        }
        self.running = False
        self.heartbeat_server: Thread = None
        self.barrage_server: Thread = None
        self.storage = storage

    def parse_msg(self, data: dict):
        '''
        解析消息为内部对象
        '''
        data_type = data.get("type")
        if data_type == "chatmsg":
            barrage = Barrage.parse_chatmsg(data)
            logger.debug(
                f"房间 {barrage.room_id} 中的用户 {barrage.nick_name} 说：{barrage.content}"
            )
            return barrage
        elif data_type == "synexp":
            logger.debug(f"房间 {self.room_id} 收到了等级信息")
        elif data_type == "dgb":
            logger.debug(f'房间 {self.room_id} 有用户 {data.get("nn","")} 送了一个礼物')
        elif data_type == "configscreen":
            logger.debug(f'房间 {self.room_id} 有用户 {data.get("userName","")} 送了一个礼物')
        elif data_type == "ro_date_succ":
            logger.debug(f'房间 {self.room_id} 有用户 {data.get("unn","")} 送了一个礼物')
        elif data_type == "noble_num_info":
            logger.debug(f'房间 {self.room_id} 有 {data.get("sum","")} 位贵宾用户正在观看')
        elif data_type == "uenter":
            logger.debug(f'房间 {self.room_id} 有用户 {data.get("nn","")} 加入')
        elif data_type == "mrkl":
            logger.debug(f"房间 {self.room_id} 收到了心跳")
        elif data_type == "pingreq":
            logger.debug(f"房间 {self.room_id} 收到了pingreq信息")
        elif data_type == "spbc":
            logger.debug(
                f'用户 {data.get("sn","")} 在 其他房间 {data.get("drid","")} 送了一个 {data.get("gn","")}'
            )
        elif data_type == "dfrank":
            logger.debug(f"房间 {self.room_id} 收到了钻粉用户信息")
        elif data_type == "ranklist":
            logger.debug(f"房间 {self.room_id} 收到了本周点数信息")
        elif data_type == "frank":
            logger.debug(f"房间 {self.room_id} 收到了今日点数信息")
        elif data_type == "newblackres":
            logger.debug(
                f'房间 {self.room_id} 中的用户 {data.get("dnic","")} 被 {data.get("snic","")} 禁言'
            )
        elif data_type == "blab":
            logger.debug(
                f'房间 {self.room_id} 中的用户 {data.get("nn","")} 粉丝牌升至 {data.get("bl","")} 级 {data.get("bnn","")}'
            )
        elif data_type == "srres":
            logger.debug(f'房间 {self.room_id} 中的用户 {data.get("nickname","")} 分享了直播间')
        elif data_type == "loginres":
            logger.info(f"房间 {self.room_id} 收到了登录回复")
            userid = data.get("userid")
            if str(userid) != str(self.uid):
                self.uid = userid
                logger.info(f"房间 {self.room_id}  的uid已更换 {self.uid}")

            # 执行进入房间操作
            self._join()
            # 调用一个线性发送心跳
            self.heartbeat_server = Thread(target=self.keep_alive)
            self.heartbeat_server.start()
        else:
            logger.warning(
                f"房间 {self.room_id} 中未知的消息类型:{data_type},{json.dumps(data,ensure_ascii=False)}"
            )

    def obj_to_msg(self, dict_info: "dict|list|any") -> bytes:
        '''
        将对象转为ws可发送的字节流
        '''
        # 序列化为STT结构字符串
        content = pystt.dumps(dict_info)
        # 以UTF-8编码格式 编码字符串，字符串转化为字节流
        content_byte = content.encode('utf-8')
        # 头部8字节，尾部1字节，与字符串长度相加即数据长度
        content_length = len(content_byte) + 8 + 1
        # 将数据长度转化为小端整数字节流
        length_byte = int.to_bytes(content_length, length=4, byteorder='little')

        # 前两个字节按照小端顺序拼接为0x02b1，转化为十进制即689（《协议》中规定的客户端发送消息类型）
        # 后两个字节即《协议》中规定的加密字段与保留字段，置0
        send_byte = bytearray([0xB1, 0x02, 0x00, 0x00])
        # 尾部以'\0'结束
        end_byte = bytearray([0x00])
        data = length_byte + length_byte + send_byte + content_byte + end_byte
        return data

    def msg_to_obj(self, msg: bytes) -> "dict|list|any":
        '''
        将从ws接收的字节流转为字典对象
        '''
        pos = 0
        infos = []
        while pos < len(msg):
            # 获取消息长度
            content_length = int.from_bytes(msg[pos : pos + 4], byteorder='little')
            # 获取消息内容
            content_byte = msg[pos + 12 : pos + 4 + content_length - 1]
            # 将消息解码为字符串
            content = content_byte.decode(encoding='utf-8', errors='ignore')
            # logger.debug(content)
            # 将消息反序列化为对象
            data = pystt.loads(content)
            try:
                data = self.parse_msg(data)
            except Exception as e:
                logger.error(f"房间 {self.room_id} 处理数据时失败{str(data)}")
            else:
                if data:
                    infos.append(data)
            pos += 4 + content_length
        return infos

    def _login(self):
        logger.debug(f"房间 {self.room_id} 发送登录请求消息")
        msg = {
            'type': 'loginreq',
            'room_id': self.room_id,
            'dfl': 'sn@A=105@Sss@A=1',
            'username': self.username,
            'uid': self.uid,
            'ver': '20190610',
            'aver': '218101901',
            'ct': '0',
        }
        # 将登陆信息转为二进制数据
        data = self.obj_to_msg(msg)
        self.ws.send(data)

    def _join(self):
        logger.debug(f"房间 {self.room_id} 发送进入房间消息")
        msg = {'type': 'joingroup', 'rid': self.room_id, 'gid': '1'}
        data = self.obj_to_msg(msg)
        self.ws.send(data)

    def _heartbeat(self):
        logger.debug(f"房间 {self.room_id} 发送心跳信息")
        msg = {'type': 'mrkl'}
        data = self.obj_to_msg(msg)
        self.ws.send(data)

    def keep_alive(self):
        '''保持连接，不断发送心跳'''
        logger.debug(f"房间 {self.room_id} 心跳服务启动")
        self.running = True
        while self.running:
            self._heartbeat()
            # 每次心跳间隔90*0.5=45秒
            for _ in range(90):
                # 每隔0.5秒判断服务是否还在运行
                time.sleep(0.5)
                if not self.running:
                    self.ws.close()
                    logger.info(f"房间 {self.room_id} 弹幕服务关闭")
                    break
        logger.debug(f"房间 {self.room_id} 心跳服务关闭")

    def on_message(self, ws, message):
        # print(message)
        infos = self.msg_to_obj(message)
        if self.storage:
            for info in infos:
                self.storage.put(info)
        else:
            # print(infos)
            pass

    def on_error(self, ws, error):
        if str(error) == f"found {self.uid}":
            logger.warning(f"房间 {self.room_id} 中uid {self.uid} 已经存在！")
            random_uid = str(random.randint(1000000000, 10000000000))
            self.uid = random_uid
            self.username = random_uid
            logger.info(f"房间 {self.room_id} 的uid已更换 {self.uid}")
            self._login()
        else:
            logger.error(f"房间 {self.room_id} 的弹幕服务错误：{str(error)}")

    def on_close(self, ws, close_status_code, close_msg):
        self.running = False
        logger.info(
            f"房间 {self.room_id} 弹幕服务器退出:{str(close_status_code)} {str(close_msg)}"
        )

    def on_open(self, ws):
        '''
        初始化弹幕服务器连接
        '''
        logger.info(f"房间 {self.room_id} 初始化弹幕服务器连接")
        # 执行登录操作
        self._login()

    def start(self):
        '''
        生成子进程运行弹幕服务器
        '''
        if self.running == True:
            logger.info(f"房间 {self.room_id} 的弹幕已在采集中")
        else:
            self.barrage_server = Thread(
                target=self.ws.run_forever, kwargs=(self.proxies)
            )
            self.barrage_server.start()
            logger.info(f"房间 {self.room_id} 弹幕服务已启动")

    def stop(self):
        if self.barrage_server:
            if self.running == True:
                logger.info(f"房间 {self.room_id} 的弹幕服务正在关闭")
                self.running = False
            else:
                logger.info(f"房间 {self.room_id} 的弹幕下载已经为关闭状态")
        else:
            logger.debug(f"房间 {self.room_id} 的弹幕服务不存在")


def main():
    pass


if __name__ == "__main__":
    main()
