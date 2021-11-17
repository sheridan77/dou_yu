class DouYuApiException(Exception):
    """基础异常"""


class NotOpenError(DouYuApiException):
    """房间没有开放异常"""


class RoomCloseError(DouYuApiException):
    """房间被关闭异常"""


class UnknownError(DouYuApiException):
    """未知的错误"""


class RoomNotFindError(DouYuApiException):
    """未找到直播房间的错误"""


class NotOnlineError(DouYuApiException):
    """直播未开始异常"""


class RoomNotExistError(DouYuApiException):
    """房间不存在的错误"""


class ObsoleteError(DouYuApiException):
    """session过期错误"""
