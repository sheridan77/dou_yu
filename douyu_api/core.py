import requests
import logging
from requests.models import Response

logger = logging.getLogger(__name__)


class BaseClient:
    def __init__(self, proxies: dict = None, timeout: int = 15, session: requests.Session=None) -> None:
        self.proxies = proxies
        self.timeout = timeout
        self.requests_args = {"timeout": timeout, "proxies": proxies}
        if session:
            self.session: requests.Session = session
        else:
            self.session = self.init_session()

    def post(self, url, **args) -> Response:
        requests_args = dict(**self.requests_args)
        requests_args.update(args)
        return requests.post(url, **requests_args)

    def get(self, url, **args) -> Response:
        requests_args = dict(**self.requests_args)
        requests_args.update(args)
        return requests.get(url, **requests_args)

    def put(self, url, **args) -> Response:
        requests_args = dict(**self.requests_args)
        requests_args.update(args)
        return requests.put(url, **requests_args)

    def delete(self, url, **args) -> Response:
        requests_args = dict(**self.requests_args)
        requests_args.update(args)
        return requests.delete(url, **requests_args)

    def init_session(self, **args) -> requests.Session:
        requests_args = dict(**self.requests_args)
        requests_args.update(args)
        session = requests.session()
        for key, value in requests_args.items():  # 遍历数据字典
            if hasattr(session, key):  # 如果存在同名属性
                setattr(session, key, value)  # 则添加属性到对象中
        return session
