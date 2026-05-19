import os
import bcrypt
from dotenv import load_dotenv

from flask import Flask, jsonify, request
from pymongo import MongoClient
from flask_jwt_extended import (
    JWTManager,
    create_access_token,
    jwt_required
)

# Load environment variables
load_dotenv()

app = Flask(__name__)

# JWT Configuration
app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY")

jwt = JWTManager(app)

# MongoDB Connection
client = MongoClient(os.getenv("MONGO_URI"))

# Database
db = client["employee_db"]

# Collections
employees = db["employees"]
users = db["users"]


# HOME ROUTE
@app.route('/')
def home():
    return "Employee Management System"


# GET EMPLOYEES
@app.route('/employees', methods=['GET'])
@jwt_required()
def get_employees():

    search = request.args.get("search")

    # Return All Employees
    if not search:

        employee_list = []

        employee_data = employees.find()

        for emp in employee_data:

            employee_list.append({
                "id": emp["id"],
                "name": emp["name"],
                "age": emp["age"],
                "department": emp["department"],
                "salary": emp["salary"]
            })

        return jsonify(employee_list)

    # Dynamic Global Search Query
    query = {
        "$or": [
            {"name": search},
            {"department": search}
        ]
    }

    # If numeric search
    if search.isdigit():

        numeric_search = int(search)

        query["$or"].extend([
            {"id": numeric_search},
            {"age": numeric_search},
            {"salary": numeric_search}
        ])

    employee_data = list(
        employees.find(query)
    )

    # No Employee Found
    if not employee_data:

        return jsonify({
            "message": "Employee does not exist"
        }), 404

    # Single Employee Response
    if len(employee_data) == 1:

        emp = employee_data[0]

        return jsonify({
            "id": emp["id"],
            "name": emp["name"],
            "age": emp["age"],
            "department": emp["department"],
            "salary": emp["salary"]
        })

    # Multiple Employee Response
    employee_list = []

    for emp in employee_data:

        employee_list.append({
            "id": emp["id"],
            "name": emp["name"],
            "age": emp["age"],
            "department": emp["department"],
            "salary": emp["salary"]
        })

    return jsonify(employee_list)
# ADD EMPLOYEE
@app.route('/employees', methods=['POST'])
@jwt_required()
def add_employee():

    data = request.get_json()

    # Validation
    required_fields = ["name", "age", "department", "salary"]

    for field in required_fields:

        if field not in data:
            return jsonify({
                "message": f"{field} is required"
            }), 400

    # Auto Increment ID
    last_employee = employees.find_one(
        sort=[("id", -1)]
    )

    if last_employee:
        new_id = last_employee["id"] + 1
    else:
        new_id = 1

    employee = {
        "id": new_id,
        "name": data["name"],
        "age": data["age"],
        "department": data["department"],
        "salary": data["salary"]
    }

    employees.insert_one(employee)

    return jsonify({
        "message": f'{data["name"]} added successfully'
    })


# UPDATE EMPLOYEE
@app.route('/employees', methods=['PUT'])
@jwt_required()
def update_employee():

    employee_id = request.args.get("id")

    if not employee_id:
        return jsonify({
            "message": "Employee id is required"
        }), 400

    employee = employees.find_one({
        "id": int(employee_id)
    })

    if not employee:
        return jsonify({
            "message": "Employee does not exist"
        }), 404

    data = request.get_json()

    updated_data = {}

    allowed_fields = [
        "name",
        "age",
        "department",
        "salary"
    ]

    for field in allowed_fields:

        if field in data:
            updated_data[field] = data[field]

    employees.update_one(
        {"id": int(employee_id)},
        {"$set": updated_data}
    )

    return jsonify({
        "message": f'Employee {employee_id} updated successfully'
    })


# DELETE EMPLOYEE
@app.route('/employees', methods=['DELETE'])
@jwt_required()
def delete_employee():

    employee_id = request.args.get("id")

    if not employee_id:
        return jsonify({
            "message": "Employee id is required"
        }), 400

    employee = employees.find_one({
        "id": int(employee_id)
    })

    if not employee:
        return jsonify({
            "message": "Employee does not exist"
        }), 404

    employees.delete_one({
        "id": int(employee_id)
    })

    return jsonify({
        "message": f'Employee {employee_id} deleted successfully'
    })


# REGISTER USER
@app.route('/register', methods=['POST'])
def register():

    data = request.get_json()

    required_fields = [
        "username",
        "password"
    ]

    for field in required_fields:

        if field not in data:
            return jsonify({
                "message": f"{field} is required"
            }), 400

    existing_user = users.find_one({
        "username": data["username"]
    })

    if existing_user:

        return jsonify({
            "message":"User already exists"
        }), 400

    # Encrypt Password
    hashed_password = bcrypt.hashpw(
        data["password"].encode('utf-8'),
        bcrypt.gensalt()
    )

    user = {
        "username": data["username"],
        "password": hashed_password
    }

    users.insert_one(user)

    return jsonify({
        "message": f'{data["username"]} registered successfully'
    })


# LOGIN USER
@app.route('/login', methods=['POST'])
def login():

    data = request.get_json()

    required_fields = [
        "username",
        "password"
    ]

    for field in required_fields:

        if field not in data:
            return jsonify({
                "message": f"{field} is required"
            }), 400

    user = users.find_one({
        "username": data["username"]
    })

    if not user:

        return jsonify({
            "message": "User not found"
        }), 404

    # Password Verification
    password_correct = bcrypt.checkpw(
        data["password"].encode('utf-8'),
        user["password"]
    )

    if not password_correct:

        return jsonify({
            "message": "Invalid password"
        }), 401

    access_token = create_access_token(
        identity=data["username"]
    )

    return jsonify({
        "message": f'{data["username"]} logged in successfully',
        "token": access_token
    })


if __name__ == '__main__':
    app.run(debug=True)