# LINE Bot - Queue Tracker

This is a LINE bot that tracks clinic queues and doctor schedules. Users can get real-time updates for their queue numbers and doctor assignments. The bot is implemented using **Python**, **LINE Messaging API**, **AWS Lambda**, and optionally **DynamoDB** for storing queue alerts.

---

## Features

* Query current queue status: `看診進度`
* Query doctor schedule: `醫生`
* Register for queue notifications: `診室號碼:排隊號碼` (e.g., `3:120`)
* Optional: Automated notifications when your number is near

---

## Project Structure

```
linebot/
├── webhook/                 # Webhook Lambda
│   ├── lambda_function.py
│   └── get_data.py
└── checker/                 # Checker Lambda (optional)
    ├── lambda_function.py
    └── get_data.py
requirements.txt
```

* `lambda_function.py` - Main Lambda handler
* `get_data.py` - Functions to fetch queue & doctor data
* `requirements.txt` - Python dependencies

---

## Setup

### 1. Clone the repository

```bash
git clone <repo-url>
cd linebot
```

### 2. Install dependencies

Use a Lambda-compatible folder:

```bash
pip install -r requirements.txt -t package
```

### 3. Package your Lambda

Zip the code along with dependencies:

```bash
cd package
zip -r ../lambda_webhook.zip .
cd ..
zip -g lambda_webhook.zip webhook/*.py
```

> Repeat for `checker` Lambda if needed

### 4. Deploy using AWS

You can deploy via **AWS CloudFormation** or manually:

#### Using CloudFormation

* Upload `lambda_webhook.zip` to S3
* Update `CloudFormation template` parameters:

  * `ChannelAccessToken`, `ChannelSecret`, `BotId`
  * `S3BucketName` and `WebhookLambdaZip`
* Launch the stack

#### Using AWS Console (manual)

1. Create Lambda function
2. Upload ZIP
3. Set environment variables:

   * `Channel_access_token`
   * `Channel_secret`
   * `bot_id`
4. Configure API Gateway HTTP API:

   * POST `/webhook` → Lambda integration

### 5. (Optional) DynamoDB

* Create table `line_queue_watch`

  * Partition Key: `user_id` (String)
  * Sort Key: `timestamp` (Number)
* Add IAM policy to Lambda for DynamoDB access:

```json
{
    "Effect": "Allow",
    "Action": [
        "dynamodb:PutItem",
        "dynamodb:GetItem",
        "dynamodb:Scan",
        "dynamodb:Query"
    ],
    "Resource": "arn:aws:dynamodb:<region>:<account-id>:table/line_queue_watch"
}
```

---

## Usage

1. Add your bot in LINE
2. Send messages to the bot:

   * `看診進度` → Get current queue numbers
   * `醫生` → Get today’s doctor schedule
   * `3:120` → Register queue number 120 for room 3 (receive notifications)

---

## Notes

* Make sure the Lambda webhook returns **HTTP 200**.
* Queue notifications require periodic checks, either via **CloudWatch Events** or separate Lambda.
* Free deployment is possible using **AWS Free Tier**, or alternatives like Heroku/Railway.

---

## Dependencies

* Python 3.11+
* line-bot-sdk==2.4.2
* requests==2.28.2
* boto3 (for AWS Lambda + DynamoDB)

---

## License

MIT License
