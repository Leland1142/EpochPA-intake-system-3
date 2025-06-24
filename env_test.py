import os
from dotenv import load_dotenv
load_dotenv()
print("API_BASE:", os.getenv("API_BASE"))
