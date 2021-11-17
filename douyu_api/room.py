import json
import re

from requests.models import Response

from .core import BaseClient
from .model import Room, User
from .exceptions import NotOpenError, RoomCloseError, UnknownError, RoomNotFindError


class RoomClient(BaseClient):
    def __init__(self, proxies: dict = None, timeout: int = 15) -> None:
        super().__init__(proxies=proxies, timeout=timeout)

    def get_room_id_by_room_url(self, room_url: str, **kwargs) -> "int|str":
        '''
        room_url L "https://www.douyu.com/22222"
        '''
        room_url_id = re.search(r"https://(www|m).douyu.com/(\d{1,8})", room_url)

        if room_url_id:
            room_url = "https://m.douyu.com/" + room_url_id.group(2)
        else:
            raise ValueError("不是标准的房间链接")

        response = self.get(room_url, **kwargs)

        result = re.search(r'rid":(\d{1,8}),"vipId', response.text)

        if result:
            room_id = result.group(1)
            return room_id
        else:
            raise ValueError('获取房间号错误')

    def get_room_info(
        self, room_id: "str|int" = None, room_url: str = None, **kwargs
    ) -> Room:
        if not room_id:
            if room_url:
                room_id = self.get_room_id_by_room_url(room_url=room_url, **kwargs)
            else:
                raise ValueError("room_id 和 room_url 必须提供其中之一")
        url = f'https://www.douyu.com/betard/{room_id}'
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36"
        }
        response = self.get(url, headers=headers, **kwargs)
        text_response = response.text
        if "您观看的房间已被关闭" in text_response:
            raise RoomCloseError("房间被关闭")
        elif "该房间目前没有开放" in text_response:
            raise NotOpenError("房间未开放")
        elif "没有找到该房间" in text_response:
            raise RoomNotFindError("没有找到这个房间")
        else:
            try:
                response = response.json()
            except Exception as e:
                raise UnknownError("未知的错误")

        data = response.get("room")
        game = response.get('game')

        return Room(
            owner_uid=data.get('owner_uid'),
            show_id=data.get('show_id'),
            room_name=data.get('room_name'),
            nick_name=data.get('nickname'),
            room_id=data.get('room_id'),
            owner_name=data.get('owner_name'),
            room_url=data.get('room_url'),
            safe_uid=data.get('up_id'),
            show_status=data.get('show_status'),
            video_loop=data.get('videoLoop'),
            game_tag_id=game.get('tag_id'),
            game_short_name=game.get('short_name'),
            game_tag_name=game.get('tag_name'),
            game_tag_introduce=game.get('tag_introduce'),
        )

    def get_user_info(
        self, safe_uid: str = None, room_id: "str|int" = None, **kwargs
    ) -> User:
        if safe_uid:
            pass
        elif room_id:
            room = self.get_room_info(room_id)
            safe_uid = room.safe_uid
        else:
            raise ValueError("up_id和room_id必须指定一个")

        response = self.get(f"https://yuba.douyu.com/wbapi/web/user/detail/{safe_uid}")
        json_info = response.json().get("data")

        return User(
            user_id=json_info.get("uid"),
            nick_name=json_info.get("nickname"),
            avatar=json_info.get("avatar"),
            gender=json_info.get("gender"),
            group_id=json_info.get("group_id"),
            group_name=json_info.get("group_name"),
            level=json_info.get("level"),
            fu_num=json_info.get("fu_num"),
            fans_num=json_info.get("fans_num"),
            safe_uid=json_info.get("safe_uid"),
            is_anchor=json_info.get("is_anchor"),
        )
