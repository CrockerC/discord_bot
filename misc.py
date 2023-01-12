import datetime
import re


def dlog(*args, **kwargs):
    print("["+str(datetime.datetime.now())+"]", *args, **kwargs)


def str_to_nums(query) -> object:
    if not re.search("^([0-9]+(-[0-9]+)?)(,([0-9]+(-[0-9]+)?))*$", query):
        return False

    comma_split = query.split(",")

    values = []
    for n_range in comma_split:
        r_vals = n_range.split("-")
        for i, r in enumerate(r_vals):
            r_vals[i] = int(r)
        if len(r_vals) == 2:
            r_vals.sort()
            tmp = list(range(r_vals[0], r_vals[1]+1))
            values.extend(tmp)
        elif len(r_vals) == 1:
            values.extend(r_vals)

    values.sort(reverse=True)
    return values


if __name__ == "__main__":
    print(str_to_nums("1,2-4,5,6-8,12-10"))
