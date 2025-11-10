from linebot import LineBotApi
from linebot.models import TextSendMessage
from get_data import get_current_data as gd
import os
import boto3
from datetime import datetime, time as dtime, timedelta, timezone

line_bot_api = LineBotApi(os.environ['Channel_access_token'])
table_name = os.environ.get('DYNAMO_TABLE', 'line_queue_watch')
url_progress = "https://houchihlung.com/hzlnum.php"

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(table_name)

# === Timezone UTC+8 ===
tz = timezone(timedelta(hours=8))

# === Session definitions ===
SESSIONS = {
    "早診": (dtime(8, 30), dtime(12, 0)),
    "午診": (dtime(15, 0), dtime(17, 45)),
    "晚診": (dtime(18, 30), dtime(22, 0)),
}

# Allowable time buffer (15 minutes early/late)
TOLERANCE = timedelta(minutes=15)

def is_in_session(session_name):
    """Return True if current time within ±15 min of a session."""
    now = datetime.now(tz)
    sname = session_name.replace("診", "")
    for full, (start, end) in SESSIONS.items():
        if sname in full:  # match '早', '午', '晚'
            start_dt = datetime.combine(now.date(), start, tzinfo=tz)
            end_dt = datetime.combine(now.date(), end, tzinfo=tz)
            if start_dt - TOLERANCE <= now <= end_dt + TOLERANCE:
                return True
    return False

def lambda_handler(event, context):
    current_data = gd(url_progress)
    if not current_data:
        print("No current data fetched.")
        return {'statusCode': 200, 'body': 'No data'}

    # Parse room and current number
    room_status = {}
    for i in current_data.split(';'):
        parts = i.split('-')
        if len(parts) > 2:
            room_no = parts[1]
            try:
                curr_no = int(parts[2])
                room_status[room_no] = curr_no
            except ValueError:
                continue

    items = table.scan().get('Items', [])
    print(f"Checking {len(items)} active watchers...")

    for item in items:
        user_id = item['user_id']
        room_no = str(item.get('room_no', ''))
        queue_no = int(item.get('queue_no', 0))
        session = item.get('session', '早診')

        # Check time window
        if not is_in_session(session):
            print(f"⏸ Skipping {user_id}: not within {session} time window.")
            continue

        curr_no = room_status.get(room_no)
        if curr_no is None:
            print(f"⚠️ Room {room_no} not found in progress data.")
            continue

        # Send "start reminder" if not notified yet
        if not item.get('notified_start'):
            start_msg = f"🕒 開始提醒您 {session} 的掛號號碼 {queue_no}（診室 {room_no}）"
            try:
                line_bot_api.push_message(user_id, TextSendMessage(text=start_msg))
                print(f"✅ Start reminder sent to {user_id}")
                table.update_item(
                    Key={'user_id': user_id},
                    UpdateExpression="SET #n = :t, #s = :v",
                    ExpressionAttributeNames={'#n': 'notified_time', '#s': 'notified_start'},
                    ExpressionAttributeValues={':t': int(datetime.now().timestamp()), ':v': True}
                )
            except Exception as e:
                print(f"❌ Failed to send start reminder to {user_id}: {e}")

        # Continue with queue number checking
        if curr_no >= (queue_no - 10):
            msg = f"⚠️ 目前 {session} {room_no} 診已看至 {curr_no} 號，快要輪到你囉！"
            try:
                line_bot_api.push_message(user_id, TextSendMessage(text=msg))
                print(f"📢 Alert sent to {user_id} for {session} {room_no}")
                table.delete_item(Key={'user_id': user_id})
            except Exception as e:
                print(f"❌ Failed to send alert to {user_id}: {e}")

    return {'statusCode': 200, 'body': 'Check complete'}
