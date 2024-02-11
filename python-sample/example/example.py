#! /usr/bin/env python3

import logging
import sys
sys.path.append('./../mnbcard')

from reader import get_reader, connect_card
from api import *

# ログレベルを設定する
root = logging.getLogger()
root.setLevel(logging.DEBUG)

# ログをコンソールに出力
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
root.addHandler(handler)

# カードリーダー取得
reader = get_reader()
# カードに接続する
connection = connect_card(reader)

profile_pin = input("Please input the profile PIN: ")

# カードインスタンス作成
card = Card(connection)

# 基本４情報取得(券面補助PIN必要)
for iter in card.get_basic_info( profile_pin):
    print(iter)
