from flask import Flask, request, jsonify, make_response
from pymongo import MongoClient
from bson import ObjectId
from flask_cors import CORS


app = Flask(__name__)

CORS(app)

#For security, permission to specifi ports should be specified.
# example: CORS(app, origins=["http://localhost:4200"])



#MongoDB connection and instantiation-----------------------------
client = MongoClient("mongodb://localhost:27017")
db = client.DTPWebAPP
#This travelData collection contains all the travel plan information
travelPlans = db.travelData 

#The dtpUserAuth collection contains all the data related to user authentication
userAuthCollection = db.dtpUserAuth


# Functions without routing------------------------------------------
def email_exists(email):
    # Checking if the email exists in the userAuthCollection
    return userAuthCollection.find_one({'emailId': email}) is not None

def update_travel_plan_by_id(plan_id, updated_data):
    try:
        # Convert the plan_id to ObjectId
        plan_id = ObjectId(plan_id)
        result = travelPlans.update_one({'_id': plan_id}, {'$set': updated_data})

        if result.modified_count > 0:
            # Plan document updated successfully
            return True
        else:
            # No matching document found for the provided ID
            return False
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return False


# All functions with routing---------------------------------------

@app.route("/api/v1.0/travelplans/<string:plan_id>", methods=["GET"])
def get_travel_plan(plan_id):
    try:
        plan = travelPlans.find_one({'_id': ObjectId(plan_id)})
        if plan:
            plan['_id'] = str(plan['_id'])
            return make_response(jsonify(plan), 200)
        else:
            return make_response(jsonify({'error': 'Plan not found'}), 404)
    except Exception as e:
        return make_response(jsonify({'error': str(e)}), 500)

# ---------------------------GET------------------------------
@app.route("/api/v1.0/travelplans/all", methods=["GET"])
def get_travel_plans():
    try:
        # Get optional query parameters
        departure_location = request.args.get('departure_location')
        destination_location = request.args.get('destination_location')
        travel_date = request.args.get('travel_date')

        # Construct the query based on provided parameters
        query = {}
        if departure_location:
            query['departureLocation'] = departure_location
        if destination_location:
            query['destinationLocation'] = destination_location
        if travel_date:
            query['travelDate'] = travel_date

        # Execute the query
        travel_plans = list(travelPlans.find(query))

        # Convert _id to string for JSON serialization
        for plan in travel_plans:
            plan['_id'] = str(plan['_id'])

        return make_response(jsonify(travel_plans), 200)

    except Exception as e:
        return make_response(jsonify({'error': str(e)}), 500)
# ------------------------------------------------------------------
    
# @app.route("/api/v1.0/travelplans/all", methods=["GET"])
# def get_all_travel_plans():
#     travel_plans = [] 
#     for plan in travelPlans.find():
#         plan['_id'] = str(plan['_id'])
#         travel_plans.append(plan)
#     return make_response(jsonify(travel_plans), 200)


# ------------------------------POST----------------------------------------
@app.route("/api/v1.0/UserAuthentication/login", methods=["POST"])
def login_user():
    user_data = request.get_json()
    # print('Login Data:', user_data)

    email = user_data.get('emailId')
    password = user_data.get('password')

    try:
        # Checking if the user with the given email and password exists
        user = userAuthCollection.find_one({'emailId': email, 'password': password})

        if user:
            # Returning success response as the user has found
            return make_response(jsonify({'message': 'Login successful'}), 200)
        else:
            # User not found
            return make_response(jsonify({'error': 'Invalid email or password'}), 401)
        
    except Exception as e:
        return make_response(jsonify({'error': str(e)}), 500)


@app.route("/api/v1.0/travelplans/addnewplan", methods=["POST"])
def add_new_plan():
    data = request.get_json()

    # print('Obtained Data ===============', data)

    # Extracting values from JSON data
    travelDate = data.get('travelDate')
    leavingTime = data.get('leavingTime')
    arrivingTime = data.get('arrivingTime')
    departureLocation = data.get('departureLocation')
    destinationLocation = data.get('destinationLocation')
    travelReason = data.get('travelReason')
    description = data.get('description') 

    if travelDate and leavingTime and arrivingTime and departureLocation and destinationLocation and travelReason:
        new_plan = {
            "travelDate": travelDate,
            "leavingTime": leavingTime,
            "arrivingTime": arrivingTime,
            "departureLocation": departureLocation,
            "destinationLocation": destinationLocation,
            "description": description,
            "travelReason": travelReason, 
        }
        new_plan_id = travelPlans.insert_one(new_plan)
        new_plan_link = "http://127.0.0.1:5000/api/v1.0/travelplans/addnewplan/" + str(new_plan_id.inserted_id)
        return make_response( jsonify({"url": new_plan_link} ), 201)
    else:
        return make_response( jsonify({"error":"Missing form data"} ), 404)


# ================ User registration logics =========================
@app.route("/api/v1.0/UserAuthentication/register", methods=["POST"])
def register_user():
    user_data = request.get_json()

    accountName = user_data.get('accountName')
    emailId = user_data.get('emailId')
    password = user_data.get('password')

    try:
        if emailId and password:
            # Check if the email already exists
            if email_exists(emailId):
                return make_response(jsonify({'Error': 'Email already exists'}), 409)
            new_user = {
                'accountName': accountName,
                'emailId': emailId,
                'password': password
            }
            new_user_id = userAuthCollection.insert_one(new_user)
            new_user_link = "http://127.0.0.1:5000/api/v1.0/UserAuthentication/register/" + str(new_user_id.inserted_id)
            return make_response(jsonify({'url': new_user_link}), 201)
        else:
            return make_response(jsonify({'Error': 'Data missing'}), 404)
    
    except Exception as e:
        return make_response(jsonify({'An error occurred: ': str(e)}), 404)

# --------------------------------------------------------------------------------

# -----------------------------------PUT or UPDATE--------------------------------------
@app.route("/api/v1.0/travelplans/update/<string:plan_id>", methods=["PUT"])
def update_travel_plan(plan_id):
    data = request.get_json()
    updated_plan = update_travel_plan_by_id(plan_id, data)
    if updated_plan:
        return jsonify({"message": "Travel plan updated successfully"}), 200
    else:
        return jsonify({"error": "Failed to update travel plan"}), 500


# -----------------------------------DELETE--------------------------------------

@app.route("/api/v1.0/travelplans/all/<string:id>", methods=["DELETE"])
def delete_travelPlan(id):
    # print('-----------------------------------------------', id)
    result = travelPlans.delete_one({'_id': ObjectId(id)})
    if result.deleted_count == 1:
        return make_response(jsonify({"Message: ": "You have successfully deleted the travel plan"}), 204)
    else:
        return make_response(jsonify({"error": "Invalid business ID"}), 404)


@app.route("/api/v1.0/travelplans/clear", methods=["DELETE"])
def clear_all_travel_plans():
    try:
        result = travelPlans.delete_many({})
        return jsonify({"message": f"Cleared {result.deleted_count} travel plans"}), 200

    except Exception as e:
        return make_response(jsonify({'error': str(e)}), 500)
# =======================================================================================



if (__name__) == "__main__":
    app.run(debug=True)


