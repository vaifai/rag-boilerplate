from dotenv import load_dotenv, find_dotenv
import os

load_dotenv(find_dotenv())

from app.core.config import settings

print(os.getenv("MONGO_DB"))
