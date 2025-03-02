from flask import Flask, jsonify, request
from mindee import Client, product, AsyncPredictResponse
import os
from flask import Flask, request, jsonify
from mindee import Client, product, AsyncPredictResponse
import os
import firebase_admin
from dotenv import load_dotenv
from firebase_admin import auth, credentials, firestore
import json 
import base64
load_dotenv()


app = Flask(__name__)

mindee_client = Client(api_key=os.getenv("ocr"))
encoded_data = os.getenv("fb")

if encoded_data:
    decoded_data = base64.b64decode(encoded_data).decode()
    json_data = json.loads(decoded_data)

    # Save as a temporary file
    with open("secrets.json", "w") as f:
        f.write(decoded_data)

    # Load credentials from the temporary file
    cred = credentials.Certificate("secrets.json")


# firebase_credentials_base64 = os.getenv("fb")
# cred = credentials.Certificate("./secrets.json")
firebase_admin.initialize_app(cred)
db = firestore.client()


@app.route('/extractFromOCR', methods=['POST'])
def upload_image():
    if 'image' not in request.files:
        return jsonify({'error': 'No image file provided'}), 400
    
    image = request.files['image']
    file_path = f"/tmp/{image.filename}"
    image.save(file_path)
    
    input_doc = mindee_client.source_from_path(file_path)
    result: AsyncPredictResponse = mindee_client.enqueue_and_parse(
        product.NutritionFactsLabelV1,
        input_doc,
    )
    
    os.remove(file_path)
    
    return jsonify({'parsed_data': str(result.document )})


@app.route('/add_condition', methods=['POST'])
def add_condition():
    description = request.form.get("description")
    code = request.form.get("code")
    status = request.form.get("status")

    if not description or not code or not status:
        return jsonify({"error": "Missing required fields"}), 400
    
    condition_data = {
        "description": description,
        "code": code,
        "status": status
    }
    
    db.collection("diagnoses").add(condition_data)
    return jsonify({"message": "Medical condition added successfully", "data": condition_data})

@app.route('/delete_condition', methods=['POST'])
def delete_condition():
    condition_id = request.form.get("id")  # Get condition ID from query parameters

    if not condition_id:
        return jsonify({"error": "Condition ID is required"}), 400

    try:
        condition_ref = db.collection("diagnoses").document(condition_id)
        if not condition_ref.get().exists:
            return jsonify({"error": "Condition not found"}), 404
        
        condition_ref.delete()
        return jsonify({"message": "Condition deleted successfully"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 

@app.route('/get_conditions', methods=['GET'])
def get_conditions():
    try:
        conditions_ref = db.collection("conditions").stream()
        conditions = []

        for doc in conditions_ref:
            condition_data = doc.to_dict()
            condition_data["id"] = doc.id  # Include document ID
            conditions.append(condition_data)

        return jsonify({"conditions": conditions}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/add_allergy', methods=['POST'])
def add_allergy():
    name = request.form.get("name")
    type_ = request.form.get("type_")
    reaction = request.form.get("reaction")
    severity = request.form.get("severity")


    if not name or not type_ or not reaction or not severity:
        return jsonify({"error": "Missing required fields"}), 400

    allergy_data = {
        "name": name,
        "type": type_,
        "reaction": reaction,
        "severity": severity
    }

    try:
        db.collection("allergies").add(allergy_data)
        return jsonify({"message": "Allergy added successfully", "data": allergy_data}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/get_allergies', methods=['GET'])
def get_allergies():
    try:
        allergies_ref = db.collection("allergies").stream()
        allergies = []

        for doc in allergies_ref:
            allergy_data = doc.to_dict()
            allergy_data["id"] = doc.id  # Include document ID
            allergies.append(allergy_data)

        return jsonify({"allergies": allergies}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/delete_allergy', methods=['POST'])
def delete_allergy():
    allergy_id = request.form.get("id")  # Get allergy ID from query params

    if not allergy_id:
        return jsonify({"error": "Allergy ID is required"}), 400

    try:
        allergy_ref = db.collection("allergies").document(allergy_id)
        if not allergy_ref.get().exists:
            return jsonify({"error": "Allergy not found"}), 404

        allergy_ref.delete()
        return jsonify({"message": "Allergy deleted successfully"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/add_drug', methods=['POST'])
def add_drug():
    name = request.form.get("name")
    dose = request.form.get("dose")
    frequency = request.form.get("frequency")
    start_date = request.form.get("start_date")


    if not name or not dose or not frequency or not start_date:
        return jsonify({"error": "Missing required fields"}), 400

    drug_data = {
        "name": name,
        "dose": dose,
        "frequency": frequency,
        "start_date":start_date
    }

    try:
        db.collection("medications").add(drug_data)
        return jsonify({"message": "Drug added successfully", "data": drug_data}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/get_drugs', methods=['GET'])
def get_drugs():
    try:
        drugs_ref = db.collection("medications").stream()
        drugs = []

        for doc in drugs_ref:
            drug_data = doc.to_dict()
            drug_data["id"] = doc.id  # Include document ID
            drugs.append(drug_data)

        return jsonify({"drugs": drugs}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/delete_drug', methods=['POST'])
def delete_drug():
    drug_id = request.form.get("id")  # Get drug ID from query params

    if not drug_id:
        return jsonify({"error": "Drug ID is required"}), 400

    try:
        drug_ref = db.collection("medications").document(drug_id)
        if not drug_ref.get().exists:
            return jsonify({"error": "Drug not found"}), 404

        drug_ref.delete()
        return jsonify({"message": "Drug deleted successfully"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/addselffact', methods=['POST'])
def add_self_fact():
    fact = request.form.get("fact")

    if not fact:
        return jsonify({"error": "Missing required field: fact"}), 400

    fact_data = {"fact": fact}

    try:
        db.collection("selffacts").add(fact_data)
        return jsonify({"message": "Self-fact added successfully", "data": fact_data}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/get_self_facts', methods=['GET'])
def get_self_facts():
    try:
        facts_ref = db.collection("selffacts").stream()
        facts = []

        for doc in facts_ref:
            fact_data = doc.to_dict()
            fact_data["id"] = doc.id  # Include document ID
            facts.append(fact_data)

        return jsonify({"self_facts": facts}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/delete_self_fact', methods=['POST'])
def delete_self_fact():
    fact_id = request.form.get("id")  # Get self-fact ID from query params

    if not fact_id:
        return jsonify({"error": "Self-fact ID is required"}), 400

    try:
        fact_ref = db.collection("selffacts").document(fact_id)
        if not fact_ref.get().exists:
            return jsonify({"error": "Self-fact not found"}), 404

        fact_ref.delete()
        return jsonify({"message": "Self-fact deleted successfully"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500



@app.route('/set_account', methods=['POST'])
def set_account():
    name = request.form.get("name")
    dob = request.form.get("dob")
    sex = request.form.get("sex")

    if not name or not dob or not gender:
        return jsonify({"error": "Missing required fields"}), 400

    account_data = {
        "name": name,
        "age": dob,
        "sex": sex
    }

    try:
        # Always overwrite the single account document
        db.collection("demographics").document("singleton").set(account_data)
        return jsonify({"message": "Account updated successfully", "data": account_data}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/get_account', methods=['GET'])
def get_account():
    try:
        account_ref = db.collection("demographics").document("singleton").get()

        if not account_ref.exists:
            return jsonify({"error": "Account not found"}), 404

        account_data = account_ref.to_dict()
        return jsonify({"account": account_data}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run()

#google-crc32c==1.6.0