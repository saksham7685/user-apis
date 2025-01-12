import re
import uuid
import hashlib
from flask import Flask, request, jsonify
from flask_mysqldb import MySQL
from datetime import datetime

crud_app = Flask(__name__)

# MySQL Configuration
crud_app.config['MYSQL_HOST'] = 'localhost'
crud_app.config['MYSQL_USER'] = 'root'
crud_app.config['MYSQL_PASSWORD'] = 'rootroot'  # Replace with your MySQL password
crud_app.config['MYSQL_DB'] = 'flask_crud'

mysql = MySQL(crud_app)

# Utility Functions
def validate_password(password):
    if len(password) < 8 or not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False
    return True

def validate_email(email):
    return re.match(r"[^@]+@[^@]+\.[^@]+", email)

# CREATE Operation
@crud_app.route('/users', methods=['POST'])
def create_user():
    data = request.json
    name = data.get('name')
    password = data.get('password')
    email = data.get('email')
    address = data.get('address', '')

    errors = []

    if not name:
        errors.append("Name is required")
    if not password:
        errors.append("Password is required")
    elif not validate_password(password):
        errors.append("Password must be at least 8 characters long and contain one special character")
    if not email:
        errors.append("Email is required")
    elif not validate_email(email):
        errors.append("Invalid email format")

    if errors:
        return jsonify({"errors": errors}), 400

    hashed_password = hashlib.md5(password.encode()).hexdigest()
    user_id = str(uuid.uuid4())
    created_at = updated_at = datetime.now()

    cursor = mysql.connection.cursor()
    cursor.execute(
        """
        INSERT INTO users (id, name, password, email, address, createdAt, updatedAt) 
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """,
        (user_id, name, hashed_password, email, address, created_at, updated_at),
    )
    mysql.connection.commit()
    return jsonify({"message":"created!!"}) ,201

# READ Operation
@crud_app.route('/users', methods=['GET'])
def get_users():
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT id, name, email, address, createdAt, updatedAt FROM users")
    rows = cursor.fetchall()
    users = [
        {
            "id": row[0],
            "name": row[1],
            "email": row[2],
            "address": row[3],
            "createdAt": row[4],
            "updatedAt": row[5],
        }
        for row in rows
    ]
    return jsonify(users), 200

@crud_app.route('/users/<string:user_id>', methods=['GET'])
def get_user(user_id):
    cursor = mysql.connection.cursor()
    cursor.execute(
        "SELECT id, name, email, address, createdAt, updatedAt FROM users WHERE id = %s",
        (user_id,),
    )
    row = cursor.fetchone()
    if row:
        user = {
            "id": row[0],
            "name": row[1],
            "email": row[2],
            "address": row[3],
            "createdAt": row[4],
            "updatedAt": row[5],
        }
        return jsonify(user), 200
    return jsonify({"error": "User not found"}), 404

# UPDATE Operation
@crud_app.route('/users/<string:user_id>', methods=['PUT'])
def update_user(user_id):
    data = request.json
    name = data.get('name')
    password = data.get('password')
    email = data.get('email')
    address = data.get('address', '')

    errors = []

    if not name:
        errors.append("Name is required")
    if not password:
        errors.append("Password is required")
    elif not validate_password(password):
        errors.append("Password must be at least 8 characters long and contain one special character")
    if not email:
        errors.append("Email is required")
    elif not validate_email(email):
        errors.append("Invalid email format")

    if errors:
        return jsonify({"errors": errors}), 400

    hashed_password = hashlib.md5(password.encode()).hexdigest()
    updated_at = datetime.now()

    cursor = mysql.connection.cursor()
    cursor.execute(
        """
        UPDATE users 
        SET name = %s, password = %s, email = %s, address = %s, updatedAt = %s 
        WHERE id = %s
        """,
        (name, hashed_password, email, address, updated_at, user_id),
    )
    mysql.connection.commit()

    if cursor.rowcount == 0:
        return jsonify({"error": "User not found"}), 404

    return jsonify({"message": "User updated successfully!"}), 200

# DELETE Operation
@crud_app.route('/users/<string:user_id>', methods=['DELETE'])
def delete_user(user_id):
    cursor = mysql.connection.cursor()
    cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
    mysql.connection.commit()

    if cursor.rowcount == 0:
        return jsonify({"error": "User not found"}), 404

    return jsonify({"message": "User deleted successfully!"}), 200


@crud_app.route('/users/<string:user_id>', methods=['PATCH'])
def patch_user(user_id):
    data = request.json
    fields_to_update = []
    errors=[]

    # Generate the dynamic SQL update query based on provided fields
    if 'name' in data and not data['name']:
        errors.append("Name cannot be empty")
    if 'password' in data:
        if not data['password']:
            errors.append("Password cannot be empty")
        elif not validate_password(data['password']):
            errors.append("Password must be at least 8 characters long and contain one special character")
        else:
            hashed_password = hashlib.md5(data['password'].encode()).hexdigest()
            fields_to_update.append("password = '{}'".format(hashed_password))
    if 'email' in data:
        if not data['email']:
            errors.append("Email cannot be empty")
        elif not validate_email(data['email']):
            errors.append("Invalid email format")
        else:
            fields_to_update.append("email = '{}'".format(data['email']))
    if 'address' in data:
        if not data['address']:
            errors.append("Address cannot be empty")
        else:
            fields_to_update.append("address = '{}'".format(data['address']))

    # If there are validation errors, return them
    if errors:
        return jsonify({"errors": errors}), 400

    if not fields_to_update:
        return jsonify({"error": "No valid fields provided for update"}), 400

    # Update the updatedAt timestamp
    updated_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    fields_to_update.append("updatedAt = '{}'".format(updated_at))

    update_query = "UPDATE users SET {} WHERE id = '{}'".format(", ".join(fields_to_update), user_id)

    cursor = mysql.connection.cursor()
    cursor.execute(update_query)
    mysql.connection.commit()

    if cursor.rowcount == 0:
        return jsonify({"error": "User not found"}), 404

    return jsonify({"message": "User updated successfully!"}), 200


if __name__ == '__main__':
    crud_app.run(debug=True)
