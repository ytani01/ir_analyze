# PiIr -- pigpio + python3 による、赤外線リモコン制御

## 1. Comands

### 1.1 IrAnalyze.py -- 赤外線信号受信・解析

赤外線信号を受信して解析結果を表示する。
詳細な情報を /tmp/ir_json.dump に保存する。

### 1.2 IrSend.py -- 赤外線信号送信

デバイス名とボタン名を指定して、赤外線信号を送信する。
デバイス名・ボタンの設定は後述

## 2. *.irconf -- 設定ファイル

検索パスは、以下の順

1. カレントディレクトリ
2. ${HOME}/.irconf.d
3. /etc/irconf.d

## A. References

1. [IR Codes TV LG 55UH8509](https://github.com/arendst/Sonoff-Tasmota/wiki/IR-Codes-for-TV-LG-55UH8509)
2. [irdb](http://irdb.tk/)
