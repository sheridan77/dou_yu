import pymysql
from douyu_api.room import RoomClient


def abc():
    password = "2q5p77c9"
    username = "t17597198489745"
    proxy_ip = "tps189.kdlapi.com:15818"
    proxy = {
        "http": "http://%(user)s:%(pwd)s@%(proxy)s/" % {"user": username, "pwd": password, "proxy": proxy_ip},
        "https": "http://%(user)s:%(pwd)s@%(proxy)s/" % {"user": username, "pwd": password, "proxy": proxy_ip}
    }
    return proxy


def parse_data(room_id):
    proxies = abc()
    room = RoomClient(proxies=proxies)
    room_info = room.get_room_info(room_id=room_id)
    safe_id = room_info.safe_uid
    user_info = room.get_user_info(safe_uid=safe_id)
    sql = "insert into douyu_room(room_id, room_name, owner_uid, nick_name, owner_name, safe_uid, show_id, room_url, " \
          "show_status, video_loop, game_tag_id, game_short_name, game_tag_name, game_tag_introduce) " \
          "values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
    cursor.execute(sql, (
        room_info.room_id, room_info.room_name, room_info.owner_uid, room_info.nick_name, room_info.nick_name,
        room_info.safe_uid, room_info.show_id, room_info.room_url, room_info.show_status, room_info.video_loop,
        room_info.game_tag_id, room_info.game_short_name, room_info.game_tag_name, room_info.game_tag_introduce
    ))
    db.commit()
    sql = "insert into douyu_user(user_id, nick_name, avatar, gender, group_id, group_name, " \
          "level, fu_num, fans_num, safe_uid, is_anchor) " \
          "values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
    cursor.execute(sql, (
        user_info.user_id, user_info.nick_name, user_info.avatar, user_info.gender, user_info.group_id,
        user_info.group_name, user_info.level, user_info.fu_num, user_info.fans_num, user_info.safe_uid,
        user_info.is_anchor
    ))
    db.commit()
    print(room_info.to_dict())
    print(user_info.to_dict())


if __name__ == '__main__':

    db = pymysql.connect(
        host="test1231111.f3322.net",
        user="zrq",
        port=53306,
        password="ZMoU#XOuQ5nU",
        database="we_media"
    )
    cursor = db.cursor()
    with open('finish', 'r', encoding='utf-8') as f:
        start = int(f.read().strip())
    for i in range(start, 100000000):
        with open('finish', 'w', encoding='utf-8') as f:
            f.write(str(i + 1))
        print(i)
        try:
            parse_data(i)
        except Exception as e:
            print(e)
            pass
