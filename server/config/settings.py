# config/settings.py
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    raise ValueError("OpenAI API key not found in environment variables")

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
