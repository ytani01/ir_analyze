# PiIr -- pigpio + python3 による、赤外線リモコン制御

## 1. Comands

### 1.1 IrAnalyze.py -- 赤外線信号受信・解析

赤外線信号を受信して解析結果を表示する。
詳細な情報を /tmp/ir_json.dump に保存(追記)する。

### 1.2 IrSend.py -- 赤外線信号送信

デバイス名とボタン名を指定して、赤外線信号を送信する。
デバイス名・ボタンの設定は後述

## 2. *.irconf -- 設定ファイル

### 2.1 書式 -- JSON

```
{
  "comment": "example 2.",
  "header": {
    "dev_name": ["lamp", "ball_lamp"],
    "format":   "NEC",
    "T":        557.735294,
    "sym_tbl": {
      "-":      [[16, 8]],
      "=":      [],
      "0":      [[1, 1]],
      "1":      [[1, 3]],
      "/":      [[1, 71], [1, 73], [1, 108], [1, 1875]],
      "*":      [[16, 4]],
      "?":      []
    },
    "macro": {
      "[prefix]": "00F7",
      "[suffix]": "F /*/"
    }
  },
  "buttons": {
    "on":  ["- [prefix] C03 [suffix]", 2],
    "off": ["- [prefix] 40B [suffix]", 2]
  }
}

{
  "comment": "example 1",
  "header": {
    "dev_name": ["sony_bl", "bl"],
    "format":   "SONY",
    "T":        598.750000,
    "sym_tbl": {
      "-":      [[4, 1]],
      "=":      [],
      "0":      [[1, 1]],
      "1":      [[2, 1]],
      "/":      [[2, 20], [2, 1966]],
      "*":      [],
      "?":      []
    },
    "macro": {
      "[prefix]": "-(0b)",
      "[suffix]": "0101 1010 0111/"
    }
  },
  "buttons": {
    "null":    ["[prefix]  [suffix]",
                "[prefix]  [suffix]",
                "[prefix]  [suffix]"],

    "ch_01":   ["[prefix] 000 0000 [suffix]", 3],
    "ch_02":   ["[prefix] 100 0000 [suffix]", 3],
    "ch_03":   ["[prefix] 010 0000 [suffix]", 3],
    "ch_04":   ["[prefix] 110 0000 [suffix]", 3],
  }
}
```


### 2.2 拡張子

「.irconf」。

### 2.3 検索パス

1. カレントディレクトリ
2. ${HOME}/.irconf.d
3. /etc/irconf.d

## A.1 References

* [pigpio](http://abyz.me.uk/rpi/pigpio/)
* [ESP-WROOM-02で赤外線学習リモコン](https://github.com/Goji2100/IRServer)
* [irdb](http://irdb.tk/)
* [Codes for IR Remotes (for YTF IR Bridge)](https://github.com/arendst/Tasmota/wiki/Codes-for-IR-Remotes-(for-YTF-IR-Bridge))
