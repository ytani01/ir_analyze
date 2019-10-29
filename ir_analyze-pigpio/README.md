# PiIr -- pigpio + python3 による、赤外線リモコン制御

## 1. Comands

### 1.1 IrAnalyze.py -- 赤外線信号受信・解析

赤外線信号を受信して解析結果を表示する。
詳細な情報を /tmp/ir_json.dump に保存する。

### 1.2 IrSend.py -- 赤外線信号送信

デバイス名とボタン名を指定して、赤外線信号を送信する。
デバイス名・ボタンの設定は後述

## 2. *.irconf -- 設定ファイル

### 2.1 書式 -- JSON

{
  "comment": "comment text",
  "header": {
  },
  "buttons: {
  }
}

### 2.2 拡張子

「.irconf」。

### 2.3 検索パス

1. カレントディレクトリ
2. ${HOME}/.irconf.d
3. /etc/irconf.d

## A. References

* [ESP-WROOM-02で赤外線学習リモコン](https://github.com/Goji2100/IRServer)
* [irdb](http://irdb.tk/)
* [Codes for IR Remotes (for YTF IR Bridge)](https://github.com/arendst/Tasmota/wiki/Codes-for-IR-Remotes-(for-YTF-IR-Bridge))
