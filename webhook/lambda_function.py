from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from get_data import get_current_data as gd
import os
import json
import boto3
import time

# === LINE BOT & AWS CONFIG ===
line_bot_api = LineBotApi(os.environ['Channel_access_token'])
handler = WebhookHandler(os.environ['Channel_secret'])
bot_id = os.environ['bot_id']
table_name = os.environ.get('DYNAMO_TABLE', 'line_queue_watch')

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(table_name)

# === Data sources ===
url_progress = "https://houchihlung.com/hzlnum.php"
url_doctor = "https://houchihlung.com/shift/today.php"

# === Lambda entry ===
def lambda_handler(event, context):
    signature = event['headers'].get('x-line-signature')
    body = event['body']

    @handler.add(MessageEvent, message=TextMessage)
    def handle_message(event):
        user_msg = event.message.text.strip()
        user_id = event.source.user_id

        # === 看診進度 ===
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
            return

        # === 醫生值班 ===
        elif user_msg == "醫生":
            message_list = ""
            doc_list = gd(url_doctor)
            for i in doc_list.split(',,'):
                segs = i.split(',')
                if len(segs) >= 2:
                    if '-' in segs[0]:
                        curr_date, room1, room2 = segs[:3]
                        message_list += f"日期: {curr_date}\n早診\n一診: {room1}\n二診: {room2}\n"
                    else:
                        if len(segs) == 2:
                            room1, room2 = segs
                            message_list += f"午診\n一診: {room1}\n二診: {room2}\n"
                        else:
                            room1, room2 = segs[0], segs[1]
                            message_list += f"晚診\n一診: {room1}\n二診: {room2}\n"
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=message_list or "目前無資料"))
            return

        # === 提醒掛號號碼 (start flow) ===
        elif user_msg == "提醒掛號號碼":
            table.put_item(Item={
                'user_id': user_id,
                'state': 'waiting_time',
                'timestamp': int(time.time())
            })
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="請問要提醒哪個時段？（早診／午診／晚診）")
            )
            return

        # === CONTINUE EXISTING STATE ===
        response = table.get_item(Key={'user_id': user_id})
        item = response.get('Item')

        if not item or 'state' not in item:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=user_msg))
            return

        state = item['state']

        # Step 1: select session (早診/午診/晚診)
        if state == 'waiting_time':
            session = user_msg.strip()
            if session not in ["早診", "午診", "晚診"]:
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text="請輸入 早診／午診／晚診"))
                return

            table.update_item(
                Key={'user_id': user_id},
                UpdateExpression="SET #s=:s, #sess=:sess",
                ExpressionAttributeNames={
                    '#s': 'state',
                    '#sess': 'session'
                },
                ExpressionAttributeValues={
                    ':s': 'waiting_room',
                    ':sess': session
                }
            )
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="請問要提醒哪個診室？"))
            return

        # Step 2: select room
        elif state == 'waiting_room':
            room_no = user_msg.strip()
            table.update_item(
                Key={'user_id': user_id},
                UpdateExpression="SET #s=:s, room_no=:r",
                ExpressionAttributeNames={'#s': 'state'},
                ExpressionAttributeValues={
                    ':s': 'waiting_number',
                    ':r': room_no
                }
            )
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="請輸入想要提醒的號碼"))
            return

        # Step 3: select queue number
        elif state == 'waiting_number':
            try:
                queue_no = int(user_msg.strip())
                room_no = item.get('room_no')
                session = item.get('session')

                # Final save (no delete needed)
                final_item = {
                    'user_id': user_id,
                    'room_no': room_no,
                    'queue_no': queue_no,
                    'session': session,
                    'timestamp': int(time.time())
                }
                print(">>> DEBUG: Writing final reminder to DynamoDB:", final_item)
                table.put_item(Item=final_item)

                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(
                        text=f"✅ 已登記通知：{session} 當 {room_no} 診接近號碼 {queue_no} 時我會提醒你！"
                    )
                )
            except ValueError:
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text="請輸入有效號碼"))
            return

        # fallback
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=user_msg))

    # === Handle signature ===
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        return {'statusCode': 502, 'body': json.dumps("Invalid signature.")}

    return {'statusCode': 200, 'body': json.dumps("OK")}
