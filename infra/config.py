import os

from dotenv import load_dotenv


load_dotenv()

AWS_DEFAULT_REGION = os.getenv("AWS_DEFAULT_REGION", "ap-southeast-2")
STAGE = os.getenv("STAGE", "dev")
