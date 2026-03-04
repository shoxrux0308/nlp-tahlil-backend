import jwt, datetime
SECRET = "nlp-tizim-secret-key-2024"
ALGO = "HS256"
def create_token(data):
    p = {**data, "exp": datetime.datetime.utcnow() + datetime.timedelta(days=7)}
    return jwt.encode(p, SECRET, algorithm=ALGO)
def verify_token(token):
    try: return jwt.decode(token, SECRET, algorithms=[ALGO])
    except: return None
