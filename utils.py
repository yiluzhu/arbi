import os
import zlib
import gzip
import StringIO
import datetime
import psutil
# from dateutil import tz


def merge_dict(d1, d2):
    """
    Modifies d1 in-place to contain values from d2.  If any value
    in d1 is a dictionary (or dict-like), *and* the corresponding
    value in d2 is also a dictionary, then merge them in-place.
    """
    for k, v2 in d2.items():
        v1 = d1.get(k)
        if isinstance(v1, dict) and isinstance(v2, dict):
            merge_dict(v1, v2)
        else:
            d1[k] = v2


# def utc_time_to_local_time(utc_time):
#     from_zone = tz.tzutc()
#     to_zone = tz.tzlocal()
#     utc_time = utc_time.replace(tzinfo=from_zone)
#     return utc_time.astimezone(to_zone)


def unzip_string(zipped_string):
    try:
        data = zlib.decompress(zipped_string, 16 + zlib.MAX_WBITS)
    except Exception:
        data = None

    return data


def gzip_string(arbi_opps_orders_str):
    """Given a string, return a string compressed by gnu gzip"""
    buf = StringIO.StringIO()
    gz = gzip.GzipFile(fileobj=buf, mode='w')
    try:
        gz.write(arbi_opps_orders_str)
    finally:
        gz.close()

    return buf.getvalue()


def get_body_size(s):
    i1 = ord(s[0])
    i2 = ord(s[1])
    i3 = ord(s[2])
    i4 = ord(s[3])
    return i1 + (i2 << 8) + (i3 << 16) + (i4 << 24)


def create_packet_header(size):
    """A packet head is constituted by 4 ascii characters, while the first character represents lowest number.
    """
    head = [None] * 4
    head[3], remainder = divmod(size, 256 ** 3)
    assert head[3] < 256, 'Packet size too big!'
    head[2], remainder = divmod(remainder, 256 ** 2)
    head[1], head[0] = divmod(remainder, 256)

    return ''.join([chr(i) for i in head])


def get_hk_time_now():
    return datetime.datetime.utcnow() + datetime.timedelta(hours=8)


def get_memory_usage(pid=None):
    # return the memory usage in MB
    process = psutil.Process(pid or os.getpid())
    mem = process.memory_info()[0] / 2 ** 20
    return mem