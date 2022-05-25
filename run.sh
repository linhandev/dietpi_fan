#!/bin/sh
rmmod pwm-fan
echo 0 > /sys/class/pwm/pwmchip1/export
python /root/fan/fan.py
