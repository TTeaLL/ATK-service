import mysql.connector
from mysql.connector import Error
import bcrypt
import os
from dotenv import load_dotenv

load_dotenv()


def create_tables():
    try:
        connection = mysql.connector.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            user=os.getenv('DB_USER', 'root'),
            password=os.getenv('DB_PASSWORD', '')
        )

        cursor = connection.cursor()

        # Create database
        cursor.execute("CREATE DATABASE IF NOT EXISTS atk")
        cursor.execute("USE atk")

        # Create tables
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS containers (
                id INT AUTO_INCREMENT PRIMARY KEY,
                container_number CHAR(11) UNIQUE NOT NULL,
                cost DECIMAL(10, 2) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_container_number (container_number),
                INDEX idx_cost (cost)
            )
        """)

        # Hash passwords and insert users
        hashed_password = bcrypt.hashpw('password1'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        users = [
            ('user1', hashed_password),
            ('user2', hashed_password),
            ('user3', hashed_password)
        ]

        cursor.executemany(
            "INSERT IGNORE INTO users (username, password_hash) VALUES (%s, %s)",
            users
        )

        # Insert sample containers
        containers = [
            ('ABCU1234567', 100.50),
            ('XYZU7654321', 200.75),
            ('DEFU9876543', 150.25),
            ('GHIU1239876', 300.00),
            ('JKLMU4567890', 250.50),
            ('NOPQU6789012', 175.25),
            ('RSTU3456789', 225.75),
            ('VWXU2345678', 275.00),
            ('YZAU8765432', 125.50),
            ('BCDU1098765', 350.25)
        ]

        cursor.executemany(
            "INSERT IGNORE INTO containers (container_number, cost) VALUES (%s, %s)",
            containers
        )

        connection.commit()
        print("Database and tables created successfully!")

    except Error as e:
        print(f"Error: {e}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


if __name__ == "__main__":
    create_tables()