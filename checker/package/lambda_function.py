from linebot import LineBotApi
from linebot.models import TextSendMessage
from get_data import get_current_data as gd
import os
import boto3

line_bot_api = LineBotApi(os.environ['Channel_access_token'])
table_name = os.environ.get('DYNAMO_TABLE', 'line_queue_watch')
url_progress = "https://houchihlung.com/hzlnum.php"

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(table_name)

def lambda_handler(event, context):
    current_data = gd(url_progress)
    if not current_data:
        print("No current data fetched.")
        return {'statusCode': 200, 'body': 'No data'}

    # Parse current numbers
    room_status = {}
    for i in current_data.split(';'):
        parts = i.split('-')
        if len(parts) > 2:
            room_no = parts[1]
            curr_no = int(parts[2])
            room_status[room_no] = curr_no

    items = table.scan().get('Items', [])
    print(f"Checking {len(items)} active watchers...")

    for item in items:
        user_id = item['user_id']
        room_no = str(item['room_no'])
        queue_no = int(item['queue_no'])

        curr_no = room_status.get(room_no)
        if curr_no is None:
            continue

        # Trigger alert if within 10 numbers
        if curr_no >= (queue_no - 10):
            msg = f"⚠️ 目前 {room_no} 診已看至 {curr_no} 號，快要輪到你囉！"
            try:
                line_bot_api.push_message(user_id, TextSendMessage(text=msg))
                print(f"Sent alert to {user_id} for room {room_no}")
                table.delete_item(Key={'user_id': user_id})
            except Exception as e:
                print(f"Failed to send to {user_id}: {e}")

    return {'statusCode': 200, 'body': 'Check complete'}
