import hashlib

def make_pw_hash(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def check_pw_hash(password, db_hash):
    if make_pw_hash(password) == db_hash:
        return True
    
    return False