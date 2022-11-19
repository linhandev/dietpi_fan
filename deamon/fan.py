import time
import os
from datetime import datetime
import subprocess

class FanManager:
    def __init__(self):
        self.spinning = True # start spinning with min speed when run
        self.start_temp = 36 # start spinning when temp > start_temp
        self.stop_temp = 32 # stop spinning when temp < stop_temp
        self.target_temp = 34 # try to get temp to this value

        self.period = 100
        self.min_speed = 0.4
        self.max_speed = 1
        self.prev_duty_cycle = -1
        self.intv = 10 # update every intv seconds
        self.step = 0.1 # change step each update

        # start spin when run
        self.set_spin(True)
        self.set_speed(1)
        
        # set peroid
        with open("/sys/class/pwm/pwmchip1/pwm0/period", "w") as f:
            print(int(self.period), file=f)
        
        time.sleep(3)


    def set_spin(self, spin:bool):
        self.spinning = spin
        with open("/sys/class/pwm/pwmchip1/pwm0/enable", "w") as f:
            print(int(spin), file=f) 

    def set_speed(self, speed, bin_size=5):
        percent = speed * (self.max_speed - self.min_speed) + self.min_speed
        duty_cycle = int(percent * self.period)
        duty_cycle = int(duty_cycle // bin_size * bin_size)
        # only set when change
        if duty_cycle != self.prev_duty_cycle:
            print("setting new duty_cycle", duty_cycle)
            with open("/sys/class/pwm/pwmchip1/pwm0/duty_cycle", "w") as f:
                print(duty_cycle, file=f)
            self.set_spin(True)
            self.prev_duty_cycle = duty_cycle
        return duty_cycle

    def get_temp(self):
        thermal_files = ['/sys/devices/virtual/thermal/thermal_zone0/temp']
        # '/sys/devices/virtual/thermal/thermal_zone1/temp'
        temps = [open(f, "r").read().strip() for f in thermal_files]
        temps = [int(t)//1000 for t in temps]
        return sum(temps) / len(temps)

    def start(self):
        log_file = open("/var/log/fan.log", "w+")

        curr_speed = 1

        flush_itv = 100
        cache_count = flush_itv

        while True:
            temp = self.get_temp()

            if not self.spinning and temp >= self.start_temp:
                self.set_speed(1)
                self.set_spin(True)
                continue
            
            if self.spinning and temp <= self.stop_temp:
                self.set_spin(False)
                continue
            
            if self.spinning:
                if abs(temp - self.target_temp) <= 1:
                    continue
                
                if temp < self.target_temp:
                    curr_speed = max(curr_speed - self.step, 0)
                else:
                    curr_speed = min(curr_speed + self.step, 1)
                
                duty_cycle = self.set_speed(curr_speed)
            
            now = datetime.now()
            print(now.strftime("%m/%d/%Y %H:%M:%S"), temp, self.spinning, "{:.2f}".format(curr_speed), duty_cycle if self.spinning else "Na", file=log_file)
            cache_count -= 1
            if cache_count == 0:
                log_file.flush()
                cache_count = flush_itv
            # print(now.strftime("%m/%d/%Y %H:%M:%S"), temp, self.spinning, "{:.2f}".format(curr_speed), duty_cycle if self.spinning else "Na")
            time.sleep(self.intv)


fan_manager = FanManager()
fan_manager.start()


'''
rmmod pwm-fan
echo 0 > /sys/class/pwm/pwmchip1/export
echo 40 > /sys/class/pwm/pwmchip1/pwm0/duty_cycle
echo 100 > /sys/class/pwm/pwmchip1/pwm0/period
echo 1 > /sys/class/pwm/pwmchip1/pwm0/enable
'''
