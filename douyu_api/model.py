import datetime
import json
import logging

logger = logging.getLogger(__name__)


class BaseModel:
    def to_dict(self) -> dict:
        raise NotImplementedError

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False)


class Room(BaseModel):
    def __init__(
        self,
        room_id: "str|int",  # 房间id
        room_name: str = None,  # 房间名称
        owner_uid: "str|int" = None,  # 房间所有者的uid
        nick_name: str = None,  # 房间所有者的昵称
        owner_name: str = None,  # 房间所有者名称
        safe_uid: str = None,  # up主的字母id
        show_id: "str|int" = None,  #
        room_url: str = None,  # 房间的url
        show_status: int = None,  # 开播状态
        video_loop: int = None,  # 是否为录播视频，0 不是，1 是
        game_tag_id: int = None,  # 游戏标签id
        game_short_name: str = None,  # 游戏汉语拼音缩写
        game_tag_name: str = None,  # 游戏标签名称
        game_tag_introduce: str = None,  # 游戏标签简介
    ):
        self.owner_uid = owner_uid
        self.show_id = show_id
        self.room_name = room_name
        self.nick_name = nick_name
        self.room_id = room_id
        self.owner_name = owner_name
        self.room_url = room_url
        self.safe_uid = safe_uid
        self.show_status = show_status
        self.video_loop = video_loop
        self.game_tag_id = game_tag_id
        self.game_short_name = game_short_name
        self.game_tag_name = game_tag_name
        self.game_tag_introduce = game_tag_introduce

    def to_dict(self) -> dict:
        return {
            'owner_uid': self.owner_uid,
            'show_id': self.show_id,
            'room_name': self.room_name,
            'nick_name': self.nick_name,
            'room_id': self.room_id,
            'owner_name': self.owner_name,
            'room_url': self.room_url,
            'safe_uid': self.safe_uid,
            'show_status': self.show_status,
            'video_loop': self.video_loop,
            'game_tag_id': self.game_tag_id,
            'game_tag_short_name': self.game_short_name,
            'game_tag_name': self.game_tag_name,
            'game_tag_introduce': self.game_tag_introduce,
        }


class User(BaseModel):
    def __init__(
        self,
        user_id: int = None,  # 主播个人主页id
        nick_name: str = None,  # 主播个人主页名称
        avatar: str = None,  # 主播头像
        gender: str = None,  # 性别，0是未知，1是男，2是女
        group_id: str = None,
        group_name: str = None,
        level: str = None,  # 等级
        fu_num: int = None,  # 关注了多少人
        fans_num: int = None,  # 有多少粉丝
        safe_uid: str = None,  # 安全ID
        is_anchor: bool = None,  # 是否是主播
    ):
        self.user_id = user_id
        self.nick_name = nick_name
        self.avatar = avatar
        self.gender = gender
        self.group_id = group_id
        self.group_name = group_name
        self.level = level
        self.fu_num = fu_num
        self.fans_num = fans_num
        self.safe_uid = safe_uid
        self.is_anchor = is_anchor

    def to_dict(self) -> dict:
        return {
            'user_id': self.user_id,
            'nick_name': self.nick_name,
            'avatar': self.avatar,
            'gender': self.gender,
            'group_id': self.group_id,
            'group_name': self.group_name,
            'level': self.level,
            'fu_num': self.fu_num,
            'fans_num': self.fans_num,
            'safe_uid': self.safe_uid,
            "is_anchor": self.is_anchor,
        }


class Barrage(BaseModel):
    def __init__(
        self,
        room_id: str = None,
        user_id: str = None,
        nick_name: str = None,
        content: str = None,
        send_time: datetime.datetime = None,
        level: str = None,
    ) -> None:
        super().__init__()
        # 房间ID
        self.room_id = room_id
        # 用户ID
        self.user_id = user_id
        # 用户昵称
        self.nick_name = nick_name
        # 用户等级
        self.level = level
        # 弹幕内容
        self.content = content
        # 发送时间
        self.send_time = send_time

    def to_dict(self) -> dict:
        return {
            "room_id": self.room_id,
            "user_id": self.user_id,
            "nick_name": self.nick_name,
            "level": self.level,
            "content": self.content,
            "send_time": self.send_time,
        }

    def to_json(self) -> str:
        dict_info = self.to_dict()
        # 如果有时间，则转化为北京时间
        if dict_info["send_time"]:
            dict_info["send_time"] = dict_info["send_time"].strftime(
                "%Y-%m-%d %H:%M:%S"
            )

        return json.dumps(dict_info, ensure_ascii=False)

    @staticmethod
    def parse_chatmsg(chatmsg: dict):
        '''解析成对象'''
        barrage = Barrage()
        # 房间ID
        barrage.room_id = chatmsg.get("rid")
        # 用户ID
        barrage.user_id = chatmsg.get("uid")
        # 用户昵称
        barrage.nick_name = chatmsg.get("nn")
        # 用户等级
        barrage.level = chatmsg.get("level")
        # 弹幕内容
        barrage.content = chatmsg.get("txt")
        # 发送时间
        send_timestamp = int(chatmsg.get("cst")) / 1000
        tz_utc_8 = datetime.timezone(datetime.timedelta(hours=8))
        send_time = datetime.datetime.fromtimestamp(send_timestamp, tz=tz_utc_8)
        barrage.send_time = send_time
        return barrage
