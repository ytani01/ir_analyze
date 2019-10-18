# lirc-analyze.py

## 0. pigpio



## 1. lirc-analyze.py

### 1.1 インストール

```bash
$ cd
$ git clone https://github.com/ytani01/ir_analyze
$ cd ir_analyze
$ setup.sh
```

### 1.2 使い方

```bash
$ lirc-analyze --help
Usage: lirc-analyze.py [OPTIONS] [INFILE] [BUTTON_NAME]

  LIRC analyzer

```

## (Deprecated?)1. LIRCのインスト－ル

### 1.1 パッケージインストール

```bash
$ sudo apt -y install lirc
```

※(buster) 下記設定ファイルを作成した後にインストール(？)

### 1.2 設定ファイル

#### 1.2.1 /etc/lirc/lirc_options.confの編集

```
[lircd]
 nodaemon        = False
-driver          = devinput
-device          = auto
+driver          = default
+device          = "/dev/lirc0"
 output          = /var/run/lirc/lircd
 pidfile         = /var/run/lirc/lircd.pid
```

#### 1.2.2 /etc/lirc/hardware.confの作成

```
LIRCD_ARGS="--uinput"
LOAD_MODULES=true
DRIVER="default"
DEVICE="/dev/lirc0"
MODULES="lirc_rpi"
LIRCD_CONF=""
LIRCMD_CONF=""
```

#### 1.2.3 /boot/config.txt の編集

```
dtoverlay=gpio-ir-tx,gpio_pin=22
dtoverlay=gpio-ir,gpio_pin=27
```

deprecated ..
```
dtoverlay=lirc-rpi
dtparam=gpio_out_pin=13
dtparam=gpio_in_pin=4
dtparam=gpio_in_pull=up
```

### 1.3 reboot

```bash
$ sudo reboot
```

## 2. LIRC 学習・設定

```bash
$ sudo service lircd stop
$ lirc-analyze.py -n | tee /tmp/a
$ sudo cp lircd.conf.template /etc/lirc/lircd.conf.d/device.conf
$ sudo vi /etc/lirc/lircd.conf.d/device.conf
(適切な場所で)
:r /tmp/a
(名前等の編集)
:wq
$ sudo service lircd start
```

## 3. LIRC リモコン操作

```bash
$ irsend SEND_ONCE device button
```


## A. Reference

1. [IR Codes TV LG 55UH8509](https://github.com/arendst/Sonoff-Tasmota/wiki/IR-Codes-for-TV-LG-55UH8509)


## A1 pigpioによる受信波形の分析

### A1.1 [Win10]に「GTKWave」をインストール

### A1.2 Raspberry Piで以下を実行

```bash
$ sudo pigpiod

# get notification handle
$ pigs no
0

# output vcd file
$ pig2vcd < /dev/pigpio0 > ir.vcd &

# start notification
## for pin 27, "bits" will be ...
##
## 0000 1000 0000 0000 0000 0000 0000 0000
## 0x8000000
$ pigs nb 0 0x8000000

# close notification
$ pigs nc 0
```

### A1.3 ir.vcdをGTKWaveで読み込む
