from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
)
from get_data import get_data as gd
import os
import json

line_bot_api = LineBotApi(os.environ['Channel_access_token'])
handler = WebhookHandler(os.environ['Channel_secret'])
url = "https://houchihlung.com/hzlnum.php"
url2= "https://houchihlung.com/shift/today.php"
no_raw=gd.get_current_data(url)
doc_list=gd.get_current_data(url2)

def lambda_handler(event, context):
    @handler.add(MessageEvent, message=TextMessage)
    def handle_message(event):
        if event.message.text == "看診進度":
            message_list = ""
            for i in no_raw.split(';'):
                for j in [i.split('-')]:
                    room_no=j[1]
                    curr_no=j[2]
                    update_time=j[5]
                    message_list += "目前"+room_no+"診看的號碼是:"+ curr_no +" 更新時間:" +update_time+"\n"
                    #print("目前"+room_no+"診看的號碼是:"+ curr_no +" 更新時間:" +update_time)
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=message_list))
        elif event.message.text == "醫生":
            message_list=""
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
                    message_list+="日期:"+curr_date+"\n早珍\n一診是:" +room1+"\n二診是:" +room2+"\n"
                elif job_time == "afternoon":
                   message_list+="午珍\n一診是:" +room1+"\n二診是:" +room2+"\n"
                elif job_time == "night":
                    message_list+="晚珍\n一診是:" +room1+"\n二診是:" +room2+"\n"
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=message_list))
        else:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=event.message.text))

    # get X-Line-Signature header value
    signature = event['headers']['x-line-signature']

    # get request body as text
    body = event['body']

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        return {
            'statusCode': 502,
            'body': json.dumps("Invalid signature. Please check your channel access token/channel secret.")
            }
    return {
        'statusCode': 200,
        'body': json.dumps("Hello from Lambda!")
        }