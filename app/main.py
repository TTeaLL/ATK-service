from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel, condecimal, validator
import re
import mysql.connector
from mysql.connector import Error
import bcrypt
from typing import Optional, List
import os
from dotenv import load_dotenv
from pydantic import field_validator

load_dotenv()

app = FastAPI()
security = HTTPBasic()


DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'database': os.getenv('DB_DATABASE', 'atk'),
    'user': os.getenv('DB_USER', 'user'),
    'password': os.getenv('DB_PASSWORD', 'userpassword')
}


class ContainerCreate(BaseModel):
    container_number: str
    cost: condecimal(decimal_places=2, gt=0)

    @field_validator('container_number')
    @classmethod
    def validate_container_number(cls, v):
        pattern = r'^[A-Z]{3}U\d{7}$'
        if not re.match(pattern, v):
            raise ValueError('Container number must be in format: ABCU1234567')
        return v


class ContainerResponse(BaseModel):
    id: int
    container_number: str
    cost: float

    class Config:
        orm_mode = True


def get_db_connection():
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        return connection
    except Error as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database connection failed: {e}"
        )


def verify_password(plain_password, hashed_password):
    try:
        if hashed_password.startswith(('$2a$', '$2b$', '$2y$')):
            plain_bytes = plain_password.encode('utf-8')
            hash_bytes = hashed_password.encode('utf-8')
            return bcrypt.checkpw(plain_bytes, hash_bytes)
        return False
    except Exception as e:
        print(f"Password verification error: {e}")
        print(f"Plain: {plain_password}, Hash: {hashed_password}")
        return False


def authenticate_user(credentials: HTTPBasicCredentials = Depends(security)):
    print(f"Auth attempt: {credentials.username}:{credentials.password}")

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute("SELECT * FROM users WHERE username = %s", (credentials.username,))
    user = cursor.fetchone()

    if user:
        print(f"User found: {user['username']}")
        print(f"Stored hash: {user['password_hash']}")
        print(f"Hash type: {type(user['password_hash'])}")
        print(f"Hash length: {len(user['password_hash'])}")

        # Проверка пароля
        is_valid = verify_password(credentials.password, user['password_hash'])
        print(f"Password valid: {is_valid}")
    else:
        print("User not found")
        cursor.close()
        connection.close()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )

    if not is_valid:
        print("Authentication failed")
        cursor.close()
        connection.close()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )

    cursor.close()
    connection.close()
    print("Authentication successful")
    return credentials.username


@app.get("/api/containers", response_model=List[ContainerResponse])
def get_containers(
        q: Optional[str] = None,
        username: str = Depends(authenticate_user)
):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    if q:
        cursor.execute(
            "SELECT id, container_number, cost FROM containers WHERE container_number LIKE %s LIMIT 50",
            (f'%{q}%',)
        )
    else:
        cursor.execute("SELECT id, container_number, cost FROM containers LIMIT 50")

    containers = cursor.fetchall()
    cursor.close()
    connection.close()

    return containers


@app.get("/api/containers/by-cost", response_model=List[ContainerResponse])
def get_containers_by_cost(
        cost: Optional[float] = None,
        min_cost: Optional[float] = None,
        max_cost: Optional[float] = None,
        username: str = Depends(authenticate_user)
):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    if cost:
        cursor.execute(
            "SELECT id, container_number, cost FROM containers WHERE cost = %s",
            (cost,)
        )
    elif min_cost is not None or max_cost is not None:
        min_val = min_cost if min_cost is not None else 0
        max_val = max_cost if max_cost is not None else float('inf')

        cursor.execute(
            "SELECT id, container_number, cost FROM containers WHERE cost BETWEEN %s AND %s",
            (min_val, max_val)
        )
    else:
        cursor.execute("SELECT id, container_number, cost FROM containers LIMIT 50")

    containers = cursor.fetchall()
    cursor.close()
    connection.close()

    return containers


@app.post("/api/containers", response_model=ContainerResponse)
def create_container(
        container: ContainerCreate,
        username: str = Depends(authenticate_user)
):
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        cursor.execute(
            "INSERT INTO containers (container_number, cost) VALUES (%s, %s)",
            (container.container_number, float(container.cost))
        )
        connection.commit()

        cursor.execute(
            "SELECT id, container_number, cost FROM containers WHERE id = LAST_INSERT_ID()"
        )
        new_container = cursor.fetchone()

    except Error as e:
        if e.errno == 1062:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Container with this number already exists"
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {e}"
        )
    finally:
        cursor.close()
        connection.close()

    return dict(zip(['id', 'container_number', 'cost'], new_container))


@app.get("/")
def read_root():
    return {"message": "ATK Container Service API"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)