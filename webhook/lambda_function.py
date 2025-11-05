from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from get_data import get_current_data as gd
import os
import json
import boto3

line_bot_api = LineBotApi(os.environ['Channel_access_token'])
handler = WebhookHandler(os.environ['Channel_secret'])
bot_id = os.environ['bot_id']
table_name = os.environ.get('DYNAMO_TABLE', 'line_queue_watch')

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(table_name)

# URLs for queue and doctor data
url_progress = "https://houchihlung.com/hzlnum.php"
url_doctor = "https://houchihlung.com/shift/today.php"

def lambda_handler(event, context):
    # Verify LINE signature
    signature = event['headers'].get('x-line-signature')
    body = event['body']

    @handler.add(MessageEvent, message=TextMessage)
    def handle_message(event):
        user_msg = event.message.text.strip()
        user_id = event.source.user_id

        if user_msg == "看診進度":
            message_list = ""
            no_raw = gd(url_progress)
            for i in no_raw.split(';'):
                parts = i.split('-')
                if len(parts) > 5:
                    room_no = parts[1]
                    curr_no = parts[2]
                    update_time = parts[5]
                    message_list += f"目前{room_no}診號: {curr_no}（更新時間: {update_time}）\n"
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=message_list or "目前無資料"))

        elif user_msg == "醫生":
            message_list = ""
            doc_list = gd(url_doctor)
            for i in doc_list.split(',,'):
                segs = i.split(',')
                if len(segs) >= 2:
                    if '-' in segs[0]:
                        curr_date, room1, room2 = segs[:3]
                        message_list += f"日期: {curr_date}\n早珍\n一診: {room1}\n二診: {room2}\n"
                    else:
                        # afternoon or night shift
                        if len(segs) == 2:
                            room1, room2 = segs
                            message_list += f"午珍\n一診: {room1}\n二診: {room2}\n"
                        else:
                            room1, room2 = segs[0], segs[1]
                            message_list += f"晚珍\n一診: {room1}\n二診: {room2}\n"
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=message_list or "目前無資料"))

        elif user_msg == "提醒掛號號碼":
            # Start registration process
            table.put_item(Item={
                'user_id': user_id,
                'state': 'waiting_room',
                'timestamp': int(__import__('time').time())
            })
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="請問要提醒哪個診室？"))

        else:
            # Check if user is in the middle of registration
            response = table.get_item(Key={'user_id': user_id})
            item = response.get('Item')

            if item and 'state' in item:
                if item['state'] == 'waiting_room':
                    # User replied with room number
                    table.update_item(
                        Key={'user_id': user_id},
                        UpdateExpression="SET #s=:s, room_no=:r",
                        ExpressionAttributeNames={'#s': 'state'},
                        ExpressionAttributeValues={
                            ':r': user_msg.strip(),
                            ':s': 'waiting_number'
                        }
                    )
                    line_bot_api.reply_message(event.reply_token, TextSendMessage(text="請輸入想要提醒的號碼"))

                elif item['state'] == 'waiting_number':
                    try:
                        queue_no = int(user_msg.strip())
                        room_no = item['room_no']

                        # Store final reminder and clean up temporary state
                        table.put_item(Item={
                            'user_id': user_id,
                            'room_no': room_no,
                            'queue_no': queue_no,
                            'timestamp': int(__import__('time').time())
                        })
                        table.delete_item(Key={'user_id': user_id})

                        line_bot_api.reply_message(
                            event.reply_token,
                            TextSendMessage(text=f"✅ 已登記通知：當 {room_no} 診接近號碼 {queue_no} 時我會提醒你！")
                        )
                    except ValueError:
                        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="請輸入有效號碼"))
            else:
                # Fallback echo
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text=user_msg))

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        return {'statusCode': 502, 'body': json.dumps("Invalid signature.")}

    return {'statusCode': 200, 'body': json.dumps("OK")}
