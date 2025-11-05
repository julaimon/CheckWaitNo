from PIL import Image
import io

from PIL import Image
import io

def compress_image_to_jpeg(input_path, max_bytes=1_000_000, target_size=(2500, 1686)):
    img = Image.open(input_path)
    img = img.resize(target_size, Image.Resampling.LANCZOS)

    quality = 95
    while quality > 10:
        img_bytes = io.BytesIO()
        img.convert("RGB").save(img_bytes, format="JPEG", quality=quality)
        if img_bytes.getbuffer().nbytes <= max_bytes:
            return img_bytes.getvalue()
        quality -= 5
    raise ValueError("Cannot compress image under 1 MB")


from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    MessagingApiBlob,
    RichMenuRequest,
    RichMenuArea,
    RichMenuSize,
    RichMenuBounds,
    MessageAction
)
import os

# === 設定 LINE Channel Access Token ===
channel_access_token = ""

config = Configuration(access_token=channel_access_token)

with ApiClient(config) as api_client:
    messaging_api = MessagingApi(api_client)
    messaging_api_blob = MessagingApiBlob(api_client)

    # === 步驟 1: 刪除舊的 Rich Menu ===
    rich_menus = messaging_api.get_rich_menu_list()
    if rich_menus.richmenus:
        for rm in rich_menus.richmenus:
            print(f"🗑 刪除舊的 Rich Menu: {rm.rich_menu_id}")
            messaging_api.delete_rich_menu(rm.rich_menu_id)
    else:
        print("ℹ️ 沒有舊的 Rich Menu。")

    # === 步驟 2: 定義新的 Rich Menu ===
    rich_menu_request = RichMenuRequest(
        size=RichMenuSize(width=2500, height=1686),
        selected=True,
        name="MainMenu",
        chat_bar_text="請點擊選單",
        areas=[
            RichMenuArea(
                bounds=RichMenuBounds(x=0, y=0, width=833, height=1686),
                action=MessageAction(label="看診進度", text="看診進度")
            ),
            RichMenuArea(
                bounds=RichMenuBounds(x=833, y=0, width=834, height=1686),
                action=MessageAction(label="醫生", text="醫生")
            ),
            RichMenuArea(
                bounds=RichMenuBounds(x=1667, y=0, width=833, height=1686),
                action=MessageAction(label="提醒掛號號碼", text="提醒掛號號碼")
            )
        ]
    )

    # === 步驟 3: 建立新的 Rich Menu ===
    response = messaging_api.create_rich_menu(rich_menu_request=rich_menu_request)
    rich_menu_id = response.rich_menu_id
    print(f"✅ 成功建立 Rich Menu！ID: {rich_menu_id}")

    # === 步驟 4: 上傳圖片 ===
    image_bytes = compress_image_to_jpeg("image.png")
    messaging_api_blob.set_rich_menu_image(
    rich_menu_id=rich_menu_id,
    body=image_bytes,
    _headers={"Content-Type": "image/jpeg"}
    )
    #with open("image.png", "rb") as f:
    #    image_bytes = f.read()
    #    messaging_api_blob.set_rich_menu_image(
    #        rich_menu_id=rich_menu_id,
    #        body=image_bytes,
    #        _headers={"Content-Type": "image/png"}
    #    )

    print("✅ 成功上傳 Rich Menu 圖片！")

    # === 步驟 5: 設為預設選單 ===
    messaging_api.set_default_rich_menu(rich_menu_id)
    print("✅ 已設為預設 Rich Menu！")
