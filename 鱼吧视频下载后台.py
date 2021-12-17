import logging
from logging import handlers
from douyu_api.video import VideoClient
from concurrent_log_handler import ConcurrentRotatingFileHandler
import time
TASKS = {
    "85": None,
    # "7672892": None,
    # "9597209": None,
    # "4521568": None
}


def init_logger(
        logger_name,
        logger_level=logging.DEBUG,
        log_file: bool = False,
        multiprocess=False,
        console: bool = True,
        loggers: list = [],
):
    '''
    logger_name : logger名
    logger_level ： logger等级
    log_file: 日志是否输出至文件，默认为False
    multiprocess: 是否开启多进程模式,默认为False
    console : 日志是否输出至终端，默认为True
    loggers : 其他包名的句柄
    '''
    # 生成logger
    logger = logging.getLogger(logger_name)
    formatter = logging.Formatter(
        '%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s'
    )
    if log_file:
        if multiprocess:
            hf = ConcurrentRotatingFileHandler(
                filename="log/" + logger_name + '.log',
                mode='a',
                maxBytes=1024 * 1024 * 50,
                backupCount=5,
                encoding='utf-8',
            )
            hf.setFormatter(formatter)
        else:
            # 文件流
            hf = handlers.TimedRotatingFileHandler(
                "log/" + logger_name + '.log',
                when='midnight',
                backupCount=10,
                encoding='utf-8',
            )
            hf.suffix = '_%Y-%m-%d.log'
            hf.setFormatter(formatter)
    if console:
        # 终端流
        consoleHandler = logging.StreamHandler()
        consoleHandler.setFormatter(formatter)
    # 配置logger
    logger.setLevel(logger_level)
    if log_file:
        logger.addHandler(hf)
    if console:
        logger.addHandler(consoleHandler)
    for _logger_name in loggers:
        _logger = logging.getLogger(_logger_name)
        _logger.setLevel(logger_level)
        if log_file:
            _logger.addHandler(hf)
        if console:
            _logger.addHandler(consoleHandler)
    return logger


def main():
    while True:
        for video_id in TASKS:
            if not TASKS.get(video_id):
                video_client = VideoClient(video_id=video_id)
                TASKS[video_id] = video_client
                video_client.start()
            else:
                video_client = TASKS[video_id]

            if video_client.running:
                logger.info("视频正在下载")
            else:
                video_client.start()
        time.sleep(60)


if __name__ == '__main__':
    logger = init_logger(
        "视频下载",
        logger_level=logging.DEBUG,
        log_file=True,
        multiprocess=True,
        loggers=["douyu_api"]
    )
    try:
        main()
    except Exception as e:
        print(e)


