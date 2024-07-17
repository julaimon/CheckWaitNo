#! /usr/bin/python

from lib.get_data import get_data as gd

url = "https://houchihlung.com/hzlnum.php"
url2= "https://houchihlung.com/shift/today.php"

no_raw=gd.get_current_data(url)
doc_list=gd.get_current_data(url2)
#print(r1.text.split(",,"))

#print(no_raw)
for i in no_raw.split(';'):
    for j in [i.split('-')]:
        room_no=j[1]
        curr_no=j[2]
        update_time=j[5]
        print("目前"+room_no+"診看的號碼是:"+ curr_no +" 更新時間:" +update_time)

for i in doc_list.split(',,'):
    if len (i.split(',')) == 3:
       if '-' in i.split(',')[0]:
          curr_date=i.split(',')[0]
          room1 =i.split(',')[1]
          room2 =i.split(',')[2]
          job_time="morning"
       else:
           room1 =i.split(',')[0]
           room2 =i.split(',')[1]
           job_time="night"
    else:
        room1 =i.split(',')[0]
        room2 =i.split(',')[1]
        job_time="afternoon"
    if job_time == "morning":
        print("日期:"+curr_date)
        print("早珍")
        print("一診是:" +room1)
        print("二診是:" +room2)
    elif job_time == "afternoon":
        print("午珍")
        print("一診是:" +room1)
        print("二診是:" +room2)
    elif job_time == "night":
        print("晚珍")
        print("一診是:" +room1)
        print("二診是:" +room2)