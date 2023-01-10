import datetime


def dlog(*args, **kwargs):
    print("["+str(datetime.datetime.now())+"]", *args, **kwargs)


def str_to_nums(query):
    if ',' in query:
        split = query.split(',')
        for i,num in enumerate(split):
            if not num.isnumeric():
                return None
            split[i] = int(num)
        return ',', split

    if '-' in query:
        split = query.split('-')
        for i,num in enumerate(split):
            if not num.isnumeric():
                return None
            split[i] = int(num)
        return '-', split

    if query.isnumeric():
        return '#', int(query)
