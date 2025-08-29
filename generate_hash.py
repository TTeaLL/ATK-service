import bcrypt

password = "password".encode('utf-8')
hash1 = bcrypt.hashpw(password, bcrypt.gensalt()).decode('utf-8')
hash2 = bcrypt.hashpw(password, bcrypt.gensalt()).decode('utf-8')
hash3 = bcrypt.hashpw(password, bcrypt.gensalt()).decode('utf-8')

print("Хэши для пароля 'password':")
print(f"user1: {hash1}")
print(f"user2: {hash2}")
print(f"user3: {hash3}")