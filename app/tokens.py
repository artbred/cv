import time

import jwt
from settings import jwt_expiration_in_seconds, secret_key
from storage import jwt_token_is_revoked, revoke_jwt_token

# This makes very little sense


def encrypt_label_id(label_id: str):
    payload = {"exp": int(time.time_ns() + jwt_expiration_in_seconds), "label_id": label_id}
    return jwt.encode(payload, secret_key, algorithm="HS256")


def decrypt_label_id(token) -> str:
    if jwt_token_is_revoked(token):
        raise ValueError("Your token has already been used, you need to generate new one by entering position")

    revoke_jwt_token(token)

    try:
        decoded_payload = jwt.decode(token, secret_key, algorithms=["HS256"])
        return decoded_payload["label_id"]
    except jwt.ExpiredSignatureError:
        raise ValueError("Your download link has expired, send request once more")
    except Exception:
        raise ValueError("Invalid Token")
