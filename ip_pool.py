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
        self.ip_allocation_table = IpAllocationTable()
        for key in configuration['reservation_list']:
            ip = configuration['reservation_list'][key]
            self.__reservation_list[key] = [ip, True]

        self.__black_list = configuration['black_list']
        self.__lease_time = configuration['lease_time']
        if self.__pool_mode == 'range':
            start = configuration['range']['from']
            end = configuration['range']['to']

            index = start

            while True:
                if index not in self.__reservation_list.keys():
                    self.__ip_pool[index] = None
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

    def allocate_ip(self, device_name, mac_addr):
        self.__allocation_lock.acquire()

        if mac_addr in self.__black_list:
            self.__allocation_lock.release()
            return None

        if mac_addr in self.__reservation_list.keys():
            if self.__reservation_list[mac_addr][1]:
                self.__reservation_list[mac_addr][1] = False
                self.__allocation_lock.release()
                self.ip_allocation_table.add_allocation(device_name, mac_addr,
                                                        self.__reservation_list[mac_addr][0], self.__lease_time)
                return self.__reservation_list[mac_addr][0]
            else:
                self.__allocation_lock.release()
                return None

        for ip in self.__ip_pool.keys():
            if self.__ip_pool[ip] is None:
                self.__ip_pool[ip] = mac_addr
                self.__allocation_lock.release()
                self.ip_allocation_table.add_allocation(device_name, mac_addr,
                                                        ip, self.__lease_time)
                return ip

        self.__allocation_lock.release()
        return None

    def release_ip(self, ip, mac_addr):
        self.__release_lock.acquire()

        if mac_addr in self.__black_list:
            self.__release_lock.release()
            return False

        if mac_addr in self.__reservation_list.keys():
            if ip == self.__reservation_list[mac_addr][0] and not self.__reservation_list[mac_addr][1]:
                self.__reservation_list[mac_addr][1] = True
                self.ip_allocation_table.remove_allocation(mac_addr, ip)
                self.__release_lock.release()
                return True
            else:
                self.__release_lock.release()
                return False

        if ip in self.__ip_pool.keys():
            if self.__ip_pool[ip] == mac_addr:
                self.__ip_pool[ip] = None
                self.ip_allocation_table.remove_allocation(mac_addr, ip)
                self.__release_lock.release()
                return True
            else:
                self.__release_lock.release()
                return False

    def print_status(self):
        # print(self.__ip_pool)
        # print('****************')
        # print(self.__reservation_list)
        # print('****************')
        # print(self.__black_list)
        # print('****************')
        # print(self.__lease_time)
        # print('****************')
        self.ip_allocation_table.print_table()

    def lease_time(self):
        return self.__lease_time


class IpAllocationLog:
    def __init__(self, device_name, mac_addr, allocated_ip, lease_time):
        self.__device_name = device_name
        self.__mac_addr = mac_addr
        self.__allocated_ip = allocated_ip
        self.__lease_time = lease_time
        Thread(target=self.__timer).start()

    def __timer(self):
        while self.__lease_time > 0:
            time.sleep(1)
            self.__lease_time -= 1

    def expired_time(self):
        return self.__lease_time

    def __eq__(self, other):
        if type(other) != type(self):
            return False

        return self.__mac_addr == other.__mac_addr and self.__allocated_ip == other.__allocated_ip

    def information(self):
        _ = str(timedelta(seconds=self.__lease_time)).split(':')
        expired_time = _[0] + ' hours, ' + _[1] + ' minutes, ' + _[2] + ' seconds'
        return [self.__device_name, self.__mac_addr, self.__allocated_ip, expired_time]

    def mac_addr(self):
        return self.__mac_addr

    def allocated_ip(self):
        return self.__allocated_ip


class IpAllocationTable:
    def __init__(self):
        self.table = []
        self.lock = Semaphore()

    def add_allocation(self, device_name, mac_addr, allocated_ip, lease_time):
        self.lock.acquire()
        new_log = IpAllocationLog(device_name, mac_addr, allocated_ip, lease_time)
        if new_log not in self.table:
            self.table.append(new_log)
        self.lock.release()

    def remove_allocation(self, mac_addr, allocated_ip):
        self.lock.acquire()
        for l_ in self.table:
            if l_.allocated_ip() == allocated_ip and l_.mac_addr() == mac_addr:
                self.table.remove(l_)
                self.lock.release()
                return
        self.lock.release()

    def get_allocation(self, mac_addr, allocated_ip):
        self.lock.acquire()
        for l_ in self.table:
            if l_.allocated_ip() == allocated_ip and l_.mac_addr() == mac_addr:
                self.lock.release()
                return l_
        self.lock.release()
        return None

    def print_table(self):
        self.lock.acquire()

        data = []
        for l_ in self.table:
            if l_.expired_time() > 0:
                data.append(l_.information())

        print(tabulate(data, headers=['Device Name', 'MAC Address', 'IP Address', 'Expire Time'],
                       tablefmt="pretty"), )
        self.lock.release()
