import json


class Pool:
    def __init__(self):
        configuration = Pool.__read_from_json()
        self.pool_mode = configuration['pool_mode']
        self.ip_pool = []
        self.reservation_list = list(configuration['reservation_list'])
        self.black_list = list(configuration['black_list'])
        self.lease_time = configuration['lease_time']
        if self.pool_mode == 'range':
            start = configuration['range']['from']
            end = configuration['range']['to']
            print(end)

            index = start

            while True:
                self.ip_pool.append(index)
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
            pass

    @staticmethod
    def __read_from_json():
        try:
            with open('./config.json', ) as file:

                return json.load(file)

        except FileNotFoundError:
            print('could not found config.json')
        except IOError as msg:
            print(msg)

    def suggest_ip(self):
        pass

    def allocate_ip(self):
        pass



if __name__ == '__main__':
    p = Pool()
