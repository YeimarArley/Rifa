import hashlib
password = "root123"
hash_result = hashlib.sha256(password.encode()).hexdigest()
print(hash_result)