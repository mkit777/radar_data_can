# -*- coding: utf-8 -*-

"""
main.py
~~~~~~~

本脚本用于解析CAN接收的原始雷达数据
"""

import re
from ctypes import c_uint8, c_int8


def uint8(raw):
    return c_uint8(raw).value

def int8(raw):
    return c_int8(raw).value


def parse_60A(body):
    raw = bytes.fromhex(body)

    num = uint8(raw[0])
    count = uint8(raw[1]) << 8 | uint8(raw[2])
    version = uint8(raw[3]) >> 4
    return (num, count ,version)

def parse_60B(body):
    raw = bytes.fromhex(body)

    id = uint8(raw[0])
    dy = uint8(raw[1]) << 5 | uint8(raw[2]) >> 3  
    dx = uint8(uint8(raw[2]) << 5) << 3 | uint8(raw[3])
    vy = uint8(raw[4]) << 2 | uint8(raw[5]) >> 6
    vx = uint8(uint8(raw[5]) << 2) << 1 | uint8(raw[6]) >> 5 
    prop = uint8(raw[6]) & 0b111
    rcs  = uint8(raw[7])
    # print(id, dy, dx, vy, vx, prop, rcs)
    return (id, dy * 0.2 - 500, dx * 0.2 - 204.6, vy * 0.25 - 128, vx * 0.25 - 64, prop, rcs * 0.5 - 64)

def main():
    src_file = open(SRC_FILE)
    out_file = open(OUT_FILE, 'w')

    frame = []
    expect_num = -1
    frame_count = 0
    
    for i, line in enumerate(src_file):
        header, body, ts = tuple(filter(lambda s: len(s.strip()) > 0, re.split(r'\s{2,}', line)))
        if header == '60D':
            continue

        if header == '60A':
            if expect_num != -1:
                if len(frame) < expect_num:
                    print('object miss')
                elif len(frame) > expect_num:
                    print(f'duplicate object1 no={frame_count} expect={expect_num} real={len(frame)}')
                
                if len(set((t[1] for t in frame))) != len(frame):
                    print(f'duplicate object2 no={frame_count}  len1={len(set((t[1] for t in frame)))} len2={len(frame)}')

                for obj in frame:
                    out_file.write(','.join(map(str, obj)) + '\n')

            frame.clear()
            num, count, version = parse_60A(body)
            expect_num = num
            frame_count += 1
            # frame.append((num, count, version))
            
        if header == '60B':
            ret = parse_60B(body)
            frame.append((frame_count, *ret))


SRC_FILE = './data/雷达0804.txt'
OUT_FILE = 'data-0804.csv'

RE_PATTARN = re.compile(r'\s+(\w.+)\s+(\w.+)\s+(\w.+)\s+')

if __name__ == "__main__":
    main()