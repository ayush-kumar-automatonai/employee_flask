import os
from dotenv import load_dotenv

from flask import Flask, jsonify, request
from pymongo import MongoClient
from bson import ObjectId
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

# MongoDB Atlas Connection
client = MongoClient(os.getenv("MONGO_URI"))

# Database
db = client["employee_db"]

# Collections
employees = db["employees"]
users = db["users"]


# HOME ROUTE
@app.route('/')
def home():
    return "Employee Management System Running"


# GET ALL EMPLOYEES
@app.route('/employees', methods=['GET'])
@jwt_required()
def get_employees():

    employee_list = []

    for emp in employees.find():

        employee_list.append({
            "_id": str(emp["_id"]),
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

    employee = {
        "name": data["name"],
        "age": data["age"],
        "department": data["department"],
        "salary": data["salary"]
    }

    result = employees.insert_one(employee)

    return jsonify({
        "message": "Employee added successfully",
        "id": str(result.inserted_id)
    })


# GET EMPLOYEE BY DEPARTMENT
@app.route('/employees/department/<department>', methods=['GET'])
@jwt_required()
def get_employee_by_department(department):

    employee_list = []

    employee_data = employees.find({
        "department": department
    })

    for emp in employee_data:

        employee_list.append({
            "_id": str(emp["_id"]),
            "name": emp["name"],
            "age": emp["age"],
            "department": emp["department"],
            "salary": emp["salary"]
        })

    return jsonify(employee_list)


# GET SINGLE EMPLOYEE
@app.route('/employees/<string:id>', methods=['GET'])
@jwt_required()
def get_employee(id):

    try:

        employee = employees.find_one({
            "_id": ObjectId(id)
        })

        if employee:

            return jsonify({
                "_id": str(employee["_id"]),
                "name": employee["name"],
                "age": employee["age"],
                "department": employee["department"],
                "salary": employee["salary"]
            })

        return jsonify({
            "message": "Employee not found"
        }), 404

    except:

        return jsonify({
            "message": "Invalid employee id"
        }), 400


# UPDATE EMPLOYEE
@app.route('/employees/<string:id>', methods=['PUT'])
@jwt_required()
def update_employee(id):

    try:

        data = request.get_json()

        updated_data = {
            "name": data["name"],
            "age": data["age"],
            "department": data["department"],
            "salary": data["salary"]
        }

        employees.update_one(
            {"_id": ObjectId(id)},
            {"$set": updated_data}
        )

        return jsonify({
            "message": "Employee updated successfully"
        })

    except:

        return jsonify({
            "message": "Invalid employee id"
        }), 400


# DELETE EMPLOYEE
@app.route('/employees/<string:id>', methods=['DELETE'])
@jwt_required()
def delete_employee(id):

    try:

        employees.delete_one({
            "_id": ObjectId(id)
        })

        return jsonify({
            "message": "Employee deleted successfully"
        })

    except:

        return jsonify({
            "message": "Invalid employee id"
        }), 400


# REGISTER USER
@app.route('/register', methods=['POST'])
def register():

    data = request.get_json()

    existing_user = users.find_one({
        "username": data["username"]
    })

    if existing_user:

        return jsonify({
            "message": "User already exists"
        }), 400

    user = {
        "username": data["username"],
        "password": data["password"]
    }

    users.insert_one(user)

    return jsonify({
        "message": "User registered successfully"
    })


# LOGIN USER
@app.route('/login', methods=['POST'])
def login():

    data = request.get_json()

    user = users.find_one({
        "username": data["username"]
    })

    if not user:

        return jsonify({
            "message": "User not found"
        }), 404

    if user["password"] != data["password"]:

        return jsonify({
            "message": "Invalid password"
        }), 401

    access_token = create_access_token(
        identity=data["username"]
    )

    return jsonify({
        "token": access_token
    })


if __name__ == '__main__':
    app.run(debug=True)