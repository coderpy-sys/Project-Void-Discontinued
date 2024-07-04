from dotenv import load_dotenv
import os
from discord_webhook import DiscordWebhook
from datetime import datetime

load_dotenv()
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

DB_PATHS = [
    "db/economy.db",
    "db/giveaways.db",
    "db/configs.db"
]

webhook = DiscordWebhook(
    url=WEBHOOK_URL,
    content=f"Timestamp: <t:{round(datetime.now().timestamp())}:f>"
)

for db_path in DB_PATHS:
    with open(db_path, "rb") as f:
        webhook.add_file(file=f.read(), filename=os.path.basename(db_path))

response = webhook.execute()
