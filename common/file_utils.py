import json
import os
from datetime import datetime


def get_file_name(path):
    """"
    获取文件名，不带后缀和目录
    """
    return os.path.splitext(os.path.basename(path))[0]


def get_full_path(dir: str, filename, suffix=None):
    """
    拼接文件全路径
    :param dir: 目录
    :param filename: 文件名
    :param suffix: 后缀
    :return:
    """
    if not dir.endswith('/'):
        dir += '/'
    return os.path.join(dir, filename + "." + suffix if suffix else filename)


def get_file_modify_time(path):
    """
    获取文件修改/创建时间
    :param path: 文件路径
    :return: datetime
    """
    return datetime.fromtimestamp(os.path.getmtime(path))


def check_dir(dir):
    """
    检查并创建目录
    """
    if not os.path.exists(dir):
        os.makedirs(dir)


def json2file(data, path, encoding='utf-8'):
    """
    json数据导出到文件
    """
    parsed = json.loads(data)
    with open(path, 'w', encoding=encoding) as f:
        json.dump(parsed, f, indent=4, sort_keys=True, ensure_ascii=False)


def dict2file(data, path, encoding='utf-8'):
    """
    导出dict到文件
    """
    json2file(json.dumps(data), path, encoding)


def binary2file(data, path):
    """
    保存二进制文件
    """
    with open(path, 'wb') as f:
        f.write(data)


def text2file(text, path, encoding='utf-8'):
    """
    保存文本文件
    """
    with open(path, 'w', encoding=encoding) as f:
        f.write(text)
