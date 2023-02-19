import os
import secrets

from dotenv import load_dotenv

load_dotenv()

known_utm_tags = {"utm_source", "utm_campaign"}

secret_key = os.getenv("SECRET_KEY").encode("utf-8")
jwt_expiration_in_seconds = 600

model_embeddings = "text-embedding-ada-002"
openai_key = os.getenv("OPENAI_API_KEY")
min_similarity_score = 0.85

redis_host = os.getenv("REDIS_HOST")
redis_port = int(os.getenv("REDIS_PORT"))
redis_password = os.getenv("REDIS_PASSWORD")

# Vector dimension, "text-embedding-ada-002" returns 1536
dim = 1536


def create_id(prefix=None, length=10):
    id = secrets.token_hex(length // 2)
    return prefix + id if prefix else id
