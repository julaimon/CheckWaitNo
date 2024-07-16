#! /usr/bin/python

from lib.get_data import get_data as gd

url = "https://houchihlung.com/hzlnum.php"
url2= "https://houchihlung.com/shift/today.php"

no_raw=gd.get_current_data(url)
doc_list=gd.get_current_data(url)
#print(r1.text.split(",,"))


for i in no_raw.split(';'):
    for j in [i.split('-')]:
        room_no=j[1]
        curr_no=j[2]
        update_time=j[5]
        print(update_time)