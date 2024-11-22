import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Update DATABASE_URL for the new location
DATABASE_URL = os.getenv("DATABASE_URL")
