# ir_analize.py

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

## [Deprecated] 2. LIRC 学習・設定

```bash
$ sudo service lircd stop
$ mode2 | tee /tmp/a
$ ir_analyze.py /tmp/a
$ vi /etc/lirc/lircd.conf.d/device.conf
```

## 3. LIRC リモコン操作

```bash
$ sudo service lircd start
$ irsend SEND_ONCE device command
```
