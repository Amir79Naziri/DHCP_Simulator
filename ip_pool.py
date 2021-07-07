import json
from threading import Semaphore, Thread
import time
from datetime import timedelta
from tabulate import tabulate


class Pool:
    def __init__(self):
        configuration = Pool.__read_from_json()
        self.__allocation_lock = Semaphore()
        self.__release_lock = Semaphore()
        self.__pool_mode = configuration['pool_mode']
        self.__ip_pool = dict()
        self.__reservation_list = dict()
        self.__black_list = configuration['black_list']
        self.__lease_time = configuration['lease_time']

        for key in configuration['reservation_list']:
            ip = configuration['reservation_list'][key]
            self.__reservation_list[key] = IPConfig(ip, mac_addr=key)

        if self.__pool_mode == 'range':
            start = configuration['range']['from']
            end = configuration['range']['to']

            index = start

            while True:
                if index not in self.__reservation_list.keys():
                    self.__ip_pool[index] = IPConfig(index)

                if index == end:
                    break
                data = list(map(lambda x: int(x), index.split('.')))
                if data[3] < 255:
                    data[3] += 1
                elif data[3] == 255:
                    data[3] = 0
                    if data[2] < 255:
                        data[2] += 1
                    elif data[2] == 255:
                        data[2] = 0
                        if data[1] < 255:
                            data[1] += 1
                        elif data[1] == 255:
                            data[1] = 0
                            if data[0] < 255:
                                data[0] += 1
                            else:
                                break
                index = '.'.join(map(lambda x: str(x), data))
        else:
            pass  # todo


    @staticmethod
    def __read_from_json():
        try:
            with open('./config.json', ) as file:

                return json.load(file)

        except FileNotFoundError:
            print('could not found config.json')
        except IOError as msg:
            print(msg)

    def offer_allocation_ip(self, mac_addr, device_name):
        self.__allocation_lock.acquire()

        if mac_addr in self.__black_list:
            self.__allocation_lock.release()
            return None

        if mac_addr in self.__reservation_list:
            self.__reservation_list[mac_addr].offer(mac_addr, device_name)
            self.__allocation_lock.release()
            return self.__reservation_list[mac_addr].get_ip()

        for ip in self.__ip_pool:
            if not (self.__ip_pool[ip].is_offered() or self.__ip_pool[ip].is_reserved()):
                self.__ip_pool[ip].offer(mac_addr, device_name)
                self.__allocation_lock.release()
                return self.__ip_pool[ip].get_ip()

        self.__allocation_lock.release()
        return None

    def allocate_ip(self, device_name, mac_addr):
        self.__allocation_lock.acquire()

        if mac_addr in self.__black_list:
            self.__allocation_lock.release()
            return None

        if mac_addr in self.__reservation_list:
            self.__reservation_list[mac_addr].allocate(mac_addr, device_name, self.__lease_time)
            self.__allocation_lock.release()
            return self.__reservation_list[mac_addr].get_ip()

        for ip in self.__ip_pool:
            if self.__ip_pool[ip].is_offered() and not self.__ip_pool[ip].is_reserved() and \
                    self.__ip_pool[ip].get_mac_addr() == mac_addr:
                self.__ip_pool[ip].allocate(mac_addr, device_name, self.__lease_time)
                self.__allocation_lock.release()
                return self.__ip_pool[ip].get_ip()

        self.__allocation_lock.release()
        return None

    def print_status(self):
        print(self.__ip_pool)
        print('****************')
        print(self.__reservation_list)
        print('****************')
        print(self.__black_list)
        print('****************')
        print(self.__lease_time)
        print('****************')

        data = []
        for ip in self.__ip_pool:
            if self.__ip_pool[ip].is_reserved():
                data.append(self.__ip_pool[ip].status())
        for mac in self.__reservation_list:
            if self.__reservation_list[mac].is_reserved():
                data.append(self.__reservation_list[mac].status())

        print(tabulate(data, headers=['Device Name', 'MAC Address', 'IP Address', 'Expire Time'],
                       tablefmt="pretty"), )



class IPConfig:
    def __init__(self, ip, mac_addr=None):
        self.__ip = ip
        self.__mac_addr = mac_addr
        if mac_addr is not None:
            self.__static = True
        else:
            self.__static = False
        self.__device_name = None
        self.__lease_time = -1
        self.__offer_time = -1
        self.__offered = False
        self.__reserved = False

        Thread(target=self.__lease_time_timer).start()
        Thread(target=self.__offer_time_timer).start()


    def __lease_time_timer(self):
        while True:
            if self.__reserved:
                time.sleep(1)
                self.__lease_time -= 1
                if self.__lease_time == 0:
                    if not self.__static:
                        self.__mac_addr = None
                    self.__device_name = None
                    self.__lease_time = -1
                    self.__reserved = False

    def __offer_time_timer(self):
        while True:
            if self.__offer_time:
                time.sleep(1)
                self.__offer_time -= 1
                if self.__offer_time == 0:
                    if not self.__static:
                        self.__mac_addr = None
                    self.__device_name = None
                    self.__offered = False
                    self.__offer_time = -1

    def allocate(self, mac_addr, device_name, lease_time):
        if not self.__reserved and self.__offered and self.__mac_addr == mac_addr:
            self.__lease_time = lease_time
            self.__offer_time = -1
            self.__mac_addr = mac_addr
            self.__reserved = True
            self.__offered = False
            self.__device_name = device_name

    def offer(self, mac_addr, device_name):
        if not self.__reserved and not self.__offered:
            if not self.__static or (self.__static and self.__mac_addr == mac_addr):
                self.__offer_time = 10
                self.__lease_time = -1
                self.__mac_addr = mac_addr
                self.__device_name = device_name
                self.__offered = True
                self.__reserved = False

    def is_reserved(self):
        return self.__reserved

    def is_offered(self):
        return self.__offered

    def get_mac_addr(self):
        return self.__mac_addr

    def get_ip(self):
        return self.__ip

    def status(self):
        time_ = str(timedelta(seconds=self.__lease_time)).split(':')
        expired_time = time_[0] + ' hours, ' + time_[1] + ' minutes, ' + time_[2] + ' seconds'
        return [self.__device_name, self.__mac_addr, self.__ip, expired_time]


if __name__ == '__main__':
    print(int('255', 10))
    int('255', 2)