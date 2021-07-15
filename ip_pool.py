import json
from threading import Semaphore
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
                valid = True
                for val in self.__reservation_list.values():
                    if val.get_ip() == index:
                        valid = False
                        break
                if valid:
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
            mask = Pool.change_10ip_2ip(configuration["subnet"]["subnet_mask"])
            init_ip_2 = Pool.change_10ip_2ip(configuration["subnet"]["ip_block"])

            number_of_mask = mask.count('1')
            offset = 0
            while offset < number_of_mask:
                if init_ip_2[offset] == '.':
                    number_of_mask += 1
                offset += 1

            index = configuration["subnet"]["ip_block"]
            while True:

                if Pool.change_10ip_2ip(index)[0:offset] != init_ip_2[0:offset]:
                    break

                valid = True
                for val in self.__reservation_list.values():
                    if val.get_ip() == index:
                        valid = False
                        break

                if valid and index != '192.168.1.0':
                    self.__ip_pool[index] = IPConfig(index)


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

                if Pool.change_10ip_2ip(index)[0:offset] != init_ip_2[0:offset]:
                    break
                if index not in self.__reservation_list.keys():
                    self.__ip_pool[index] = IPConfig(index)

    @staticmethod
    def __read_from_json():
        try:
            with open('./config.json', ) as file:

                return json.load(file)

        except FileNotFoundError:
            print('could not found config.json')
        except IOError as msg:
            print(msg)

    @staticmethod
    def change_10ip_2ip(ip_addr):
        new_ip = ''
        ip_addr = ip_addr.split('.')
        for part in ip_addr:
            part = int(part)
            part = str(bin(part)[2:])
            part = (8 - len(part)) * '0' + part
            if new_ip != '':
                new_ip += '.'
            new_ip += part

        return new_ip

    @staticmethod
    def change_2ip_10ip(ip_addr):
        parts = ip_addr.split('.')
        new_ip = ''
        for part in parts:
            if new_ip != '':
                new_ip += '.'
            new_ip += str(int(part, 2))
        return new_ip

    def offer_ip(self, mac_addr, device_name):
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

    def allocate_ip(self, mac_addr, device_name):
        self.__allocation_lock.acquire()

        if mac_addr in self.__black_list:
            self.__allocation_lock.release()
            return None

        if mac_addr in self.__reservation_list:
            self.__reservation_list[mac_addr].allocate(mac_addr, device_name)
            self.__allocation_lock.release()
            return self.__reservation_list[mac_addr].get_ip()

        for ip in self.__ip_pool:
            if ((self.__ip_pool[ip].is_offered() and not self.__ip_pool[ip].is_reserved()) or
                (self.__ip_pool[ip].is_reserved() and not self.__ip_pool[ip].is_offered())) and \
                    self.__ip_pool[ip].get_mac_addr() == mac_addr:
                self.__ip_pool[ip].allocate(mac_addr, device_name)
                self.__allocation_lock.release()
                return self.__ip_pool[ip].get_ip()

        self.__allocation_lock.release()
        return None

    def deallocate_ip(self, mac_addr):
        self.__allocation_lock.acquire()

        if mac_addr in self.__black_list:
            self.__allocation_lock.release()
            return

        if mac_addr in self.__reservation_list:
            if self.__reservation_list[mac_addr].is_reserved():
                self.__reservation_list[mac_addr].deallocate()
                self.__allocation_lock.release()
                return

        for ip in self.__ip_pool:
            if self.__ip_pool[ip].is_reserved() and self.__ip_pool[ip].get_mac_addr() == mac_addr:
                self.__ip_pool[ip].deallocate()
                self.__allocation_lock.release()
                return

        self.__allocation_lock.release()

    def reject_ip(self, mac_addr):
        self.__allocation_lock.acquire()

        if mac_addr in self.__black_list:
            self.__allocation_lock.release()
            return

        if mac_addr in self.__reservation_list:
            if self.__reservation_list[mac_addr].is_offered():
                self.__reservation_list[mac_addr].reject()
                self.__allocation_lock.release()
                return

        for ip in self.__ip_pool:
            if self.__ip_pool[ip].is_offered() and self.__ip_pool[ip].get_mac_addr() == mac_addr:
                self.__ip_pool[ip].reject()
                self.__allocation_lock.release()
                return

        self.__allocation_lock.release()

    def print_status(self, status_list):
        # print(self.__ip_pool)
        # print('****************')
        # print(self.__reservation_list)
        # print('****************')
        # print(self.__black_list)
        # print('****************')
        # print(self.__lease_time)
        # print('****************')

        data = []
        for ip in self.__ip_pool:
            if self.__ip_pool[ip].is_reserved():
                try:
                    data.append(self.__ip_pool[ip].
                                status(status_list[self.__ip_pool[ip].get_mac_addr()][0]))
                except KeyError:
                    pass
        for mac in self.__reservation_list:
            if self.__reservation_list[mac].is_reserved():
                try:
                    data.append(self.__reservation_list[mac].status(status_list[mac][0]))
                except KeyError:
                    pass

        print(tabulate(data, headers=['Device Name', 'MAC Address', 'IP Address', 'Expire Time'],
                       tablefmt="pretty"), )

    def lease_time(self):
        return self.__lease_time


class IPConfig:
    def __init__(self, ip, mac_addr=None):
        self.__ip = ip
        self.__mac_addr = mac_addr
        if mac_addr is not None:
            self.__static = True
        else:
            self.__static = False
        self.__device_name = None
        self.__offered = False
        self.__reserved = False

    def deallocate(self):
        if not self.__static:
            self.__mac_addr = None
        self.__device_name = None
        self.__reserved = False

    def reject(self):
        if not self.__static:
            self.__mac_addr = None
        self.__device_name = None
        self.__offered = False

    def allocate(self, mac_addr, device_name):
        self.__mac_addr = mac_addr
        self.__reserved = True
        self.__offered = False
        self.__device_name = device_name

    def offer(self, mac_addr, device_name):
        if not self.__static or (self.__static and self.__mac_addr == mac_addr):
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

    def status(self, remained_time):
        time_ = str(timedelta(seconds=remained_time)).split(':')
        expired_time = time_[0] + ' hours, ' + time_[1] + ' minutes, ' + time_[2] + ' seconds'
        return [self.__device_name, self.__mac_addr, self.__ip, expired_time]
