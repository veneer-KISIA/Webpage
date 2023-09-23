import logging, logging.config

def get(name: str, file=None):
    """
    이름이 name인 로거를 가져온다.
    
    :param name: 로거 이름
    :param file: 로그 파일 경로 (기본값: ./log.log)
    """
    if not file:
        if name.startswith('modules.'):  # modules.stt
            name = name.split('.')[-1]  # stt
        file = f'./logs/{name}.log'

    logger = logging.getLogger(name)

    if not logger.hasHandlers():
        logger.setLevel(logging.DEBUG)

        stream_formatter = logging.Formatter(
            "[%(asctime)s] [%(levelname)s] %(message)s"
        )
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(stream_formatter)
        stream_handler.setLevel(logging.DEBUG)
        logger.addHandler(stream_handler)

        file_handler = logging.FileHandler(file, mode="a", encoding="utf-8")
        file_formatter = logging.Formatter(
            "[%(asctime)s] %(levelname)s(%(name)s) %(message)s"
        )
        file_handler.setFormatter(file_formatter)
        file_handler.setLevel(logging.INFO)
        logger.addHandler(file_handler)

    return logger


levels = {
    "d": logging.DEBUG,
    "i": logging.INFO,
    "w": logging.WARNING,
    "e": logging.ERROR,
    "c": logging.CRITICAL,
}

def set_level(name, level):
    """
    로그 레벨을 설정

    :param name: 로거 이름
    :param level: 로그 레벨 (d: debug, i: info, w: warning, e: error, c: critical)
    """

    level = levels[level]
    logger = logging.getLogger(name)
    logger.setLevel(level)
    for hander in logger.handlers:
        hander.setLevel(level)


# main일 때
if __name__ == "__main__":
    logger = get(__name__)
    set_level(__name__, "c")
    logger.info("안녕")