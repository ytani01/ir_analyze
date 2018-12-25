# lirc-analyze.py

## 0. lirc-analyze.py

### 0.1 インストール

```bash
$ cd
$ git clone https://github.com/ytani01/ir_analyze
$ cd ir_analyze
$ setup.sh
```

### 0.2 使い方

```bash
$ lirc-analyze --help
Usage: lirc-analyze.py [OPTIONS] [INFILE] [BUTTON_NAME]

  LIRC analyzer

Options:
  -f, --forever         loop forever
  -i, -l, --disp_info   output information
  -h, --disp_hex        output hex data
  -b, --disp_bit        output bit pattern
  -r, --disp_raw        output raw data
  -n, --disp_normalize  output normalized data
  --help                Show this message and exit.
```

## 1. LIRCのインスト－ル

### 1.1 パッケージインストール

```bash
$ sudo apt -y install lirc
```

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
