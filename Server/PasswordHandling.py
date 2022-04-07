import bcrypt

def CheckPW(password, hashedPassword):
    if bcrypt.checkpw(password.encode("utf-8"), hashedPassword):
        return True
    else:
        return False

def GenHash(password):
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())

password = "Password0"
hashed = GenHash(password)

print(CheckPW(password, hashed))
