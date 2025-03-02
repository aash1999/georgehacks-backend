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
import re
import os
from groq import Groq
from flask_cors import CORS

# from google.cloud import firestore


load_dotenv()


app = Flask(__name__)
CORS(app)

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
        conditions_ref = db.collection("diagnoses").stream()
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

    if not name or not dob or not sex:
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

#========= AI Routes


class Custom_LLM:

  def __init__(self, model_name="qwen-2.5-32b"):
    self.model_name = model_name
    self.groq_client = Groq()

  # Mock database function (replace with actual implementation)
  def get_patient_from_db(self, patient_id: str) -> dict:

    # Example mock data matching the JSON structure from previous answer
    """return {
        "demographics": {
            "name": "Jane A. Doe",
            "age": 38,
            "sex": "Female"
        },
        "medications": [
                {
                    "name": "Metformin",
                    "dose": "500 mg",
                    "frequency": "BID",
                    "start_date": "03/01/2023"
                },
                {
                    "name": "Lisinopril",
                    "dose": "10 mg",
                    "frequency": "Daily",
                    "start_date": "03/01/2023"
                }
            ],
        "diagnoses": [
                {
                    "description": "Type 2 Diabetes Mellitus",
                    "code": "E11.9",
                    "status": "Active"
                },
                {
                    "description": "Hypertension",
                    "code": "I10",
                    "status": "Active"
                }
            ],
        "allergies": [
            {
                "name": "Shellfish",
                "type": "Food",
                "reaction": "Anaphylaxis",
                "severity": "High"
            },
            {
                "name": "Peanut",
                "type": "Food",
                "reaction": "Anaphylaxis",
                "severity": "High"
            }
        ],
        "laboratory_results": [
            {
                "test": "Hemoglobin A1c",
                "result": 7.2,
                "units": "%",
                "date": "03/05/2023"
            },
            {
                "test": "LDL Cholesterol",
                "result": 145,
                "units": "mg/dL",
                "date": "03/05/2023"
            }
        ]
    }"""
    # print(get_account().json())
    acc,_ =get_account()
    dru,_ =get_drugs()
    con,_ =get_conditions()
    alle,_ =get_allergies()
    
    print(acc.get_json())
    data = {
        "demographics": acc.get_json()["account"],
        "medications": dru.get_json()["drugs"],
        "diagnoses": con.get_json()["conditions"],
        "allergies": alle.get_json()["allergies"],
        "laboratory_results": [
            {
                "test": "Hemoglobin A1c",
                "result": 7.2,
                "units": "%",
                "date": "03/05/2023"
            },
            {
                "test": "LDL Cholesterol",
                "result": 145,
                "units": "mg/dL",
                "date": "03/05/2023"
            }
        ]
    }
    return data

  def call_groq(self, prompt):
    client = self.groq_client
    completion = client.chat.completions.create(
        model=self.model_name,
        messages=[
            {
                "role": "user",
                "content": prompt if isinstance(prompt, str) else str(prompt)
            }
        ],
        temperature=0.6,
        max_completion_tokens=4096,
        top_p=0.95,
        stream=True,
        stop=None,
    )

    response = ''
    for chunk in completion:
        response += chunk.choices[0].delta.content or ""

    return response

  def parse_output(self, response, return_reasons=False):

    food_pattern = r'\[([^\]]+)\]'
    foods = re.findall(food_pattern, response)

    if return_reasons:
        reason_pattern = r'\(([^)]+)\)'
        reasons = re.findall(reason_pattern, response)

    return (foods, reasons) if return_reasons else foods, []

  def create_medical_prompt(self, patient_id: str, user_query: str) -> str:
    """
    Creates a medical context prompt for LLM using patient EHR data

    Args:
        patient_id: Unique identifier for the patient
        user_query: User's medication-related question

    Returns:
        Formatted prompt string with patient context and query

    Raises:
        ValueError: If patient not found or data is incomplete
    """

    # 1. Retrieve patient document from database (mock implementation)
    patient_data = self.get_patient_from_db(patient_id)  # Replace with actual DB call

    if not patient_data:
        raise ValueError(f"Patient {patient_id} not found in database")

    # 2. Extract relevant medical context
    try:
        demographics = patient_data.get('demographics', {})
        medications = patient_data.get('medications', {})
        conditions = patient_data.get('diagnoses', {})
        labs = patient_data.get('laboratory_results', [])

        # 3. Construct structured prompt
        prompt_parts = [
            "You're a helpful medical assistant. Given a patient's medical history you will answer their question."
            "\n=== Demographics ===",
            #f"Patient: {demographics.get('name', 'N/A')}",
            f"Age: {demographics.get('age', 'N/A')}",
            f"Sex: {demographics.get('sex', 'N/A')}",

            "\n== Current Medications ==",
            *[f"- {med['name']} ({med['dose']}, {med['frequency']}) since {med['start_date']}"
              for med in medications],

            "\n== Medical Conditions ==",
            *[f"- {cond['description']} ({cond['code']}) - {cond['status']}"
              for cond in conditions],

            "\n== Recent Lab Results ==",
            *[f"- {lab['test']}: {lab['result']} {lab.get('units', '')} ({lab['date']})"
              for lab in labs[:3]],  # Show last 3 relevant labs

            "\n=== Instructions ===",
            "As a medical assistant, consider:",
            "1. Current medications and potential interactions with patient history",
            "2. Patient's medical conditions and contraindications",
            "3. Recent lab values that might affect safety",
            "4. Provide dosage warnings if suggesting OTC medications",
            "5. Highlight urgent concerns requiring physician consultation",

            "\n=== User Query ===",
            user_query,

            "\n=== Response ===",
            "Answer:"
        ]

        return "\n".join(prompt_parts)

    except KeyError as e:
        raise ValueError(f"Invalid patient data structure: {str(e)}") from e

  def create_dietary_prompt(self, patient_id: str, location: str) -> str:
    """
    Creates a dietary recommendation prompt based on medical history

    Args:
        patient_id: Unique patient identifier
        location: Patient's current location (city/country)

    Returns:
        Formatted prompt for dietary recommendations

    Raises:
        ValueError: For missing patient data or invalid structure
    """
    # 1. Retrieve patient data
    patient_data = self.get_patient_from_db(patient_id)
    if not patient_data:
        raise ValueError(f"Patient {patient_id} not found")

    try:
        # 2. Extract relevant medical information
        demographics = patient_data.get('demographics', {})
        conditions = patient_data.get('diagnoses', {})
        medications = patient_data.get('medications', {})
        allergies = patient_data.get('allergies', [])  # Assume allergies structure exists
        labs = patient_data.get('laboratory_results', [])

        # 3. Construct prompt sections
        prompt_parts = [
            "You are a clinical nutritionist. Analyze this patient profile and:",
            "1. List top five foods to avoid with reasons.",
            "2. Consider location-specific food availability.",

            "\n=== Patient Profile ===",
            f"Age: {demographics.get('age', 'N/A')}",
            f"Sex: {demographics.get('sex', 'N/A')}",
            f"Location: {location}",

            "\n== Medical Conditions ==",
            *[f"- {cond['description']} ({cond.get('code', '')})"
              for cond in conditions],

            "\n== Medications ==",
            *[f"- {med['name']} ({med['dose']})" for med in medications],

            "\n== Allergies ==",
            *( [f"- {allergy['name']} ({allergy.get('reaction', '')})" for allergy in allergies]
              if allergies else ["- No known food allergies"] ),

            "\n== Relevant Lab Results ==",
            *[f"- {lab['test']}: {lab['result']} {lab.get('units', '')} (Normal: {lab.get('normal_range', '')})"
              for lab in labs if self.is_relevant_lab(lab['test'])],  # Implement relevance filtering

            "\n=== Instructions ===",
            "Prioritize recommendations based on:",
            "1. Direct contraindications from medical conditions",
            "2. Medication interactions (e.g., MAOIs & aged cheeses)",
            "3. Allergy safety",
            "4. Lab values indicating dietary needs (e.g., high LDL → limit saturated fats)",
            "5. Regional food common in {location}",

            "\n=== Response Format ===",
            "Your response must be in ENGLISH language and only contain the list and nothing else like explainations. Structure your response like this:",
            "-> [Food](Reason)."
        ]

        return "\n".join(prompt_parts)

    except KeyError as e:
        raise ValueError(f"Invalid data structure: {str(e)}") from e

  # Helper function (implement based on your lab test taxonomy)
  def is_relevant_lab(self, test_name: str) -> bool:
      """Determine if lab test is relevant for dietary recommendations"""
      relevant_tests = {
          'Hemoglobin A1c', 'LDL Cholesterol',
          'Serum Potassium', 'Renal Function Tests'
      }
      return test_name in relevant_tests

  def create_medical_risk_prompt(self, patient_id: str) -> dict:
    """
    Creates a structured medical risk prompt for LLM to analyze patient's medical history
    and autonomously assess potential risks and wellness strategies.

    Args:
        patient_id: Unique identifier for the patient
        user_query: User's query related to long-term health and wellness

    Returns:
        A structured dictionary prompt instructing the LLM to analyze patient health data and respond in a conversational tone.

    Raises:
        ValueError: If patient data is missing or incomplete.
    """

    # 1. Retrieve patient document from database (mock implementation)
    patient_data = self.get_patient_from_db(patient_id)  # Replace with actual DB call

    if not patient_data:
        raise ValueError(f"Patient {patient_id} not found in database")

    # 2. Extract relevant medical context
    try:
        demographics = patient_data.get('demographics', {})
        medications = patient_data.get('medications', {})
        conditions = patient_data.get('diagnoses', {})
        labs = patient_data.get('laboratory_results', [])

        # 3. Construct structured AI prompt
        prompt = {
            "introduction": (
                "You are an AI-powered health assistant. Your role is to analyze the patient's medical data "
                "and provide a **friendly, supportive, and insightful** assessment. "
                "Speak naturally, like a trusted health advisor, and keep the response **encouraging and constructive**."
            ),
            "patient_overview": {
                "Age": demographics.get('age', 'N/A'),
                "Sex": demographics.get('sex', 'N/A'),
            },
            "current_medications": [
                {"name": med["name"], "dose": med["dose"], "frequency": med["frequency"], "start_date": med["start_date"]}
                for med in medications
            ],
            "medical_conditions": [
                {"description": cond["description"], "code": cond["code"], "status": cond["status"]}
                for cond in conditions
            ],
            "recent_lab_results": [
                {"test": lab["test"], "result": lab["result"], "units": lab.get("units", ""), "date": lab["date"]}
                for lab in labs[:5]  # Show last 5 relevant labs
            ],
            "ai_instructions": [
                "Analyze the patient's medical history, medications, and lab results.",
                "Identify **long-term health risks** with a focus on potential complications while keeping the response **non-alarming and supportive.**",
                "Clearly explain **risk factors** related to their conditions and medications, using a calm and reassuring tone.",
                "Provide **early warning signs** to be mindful of, based on their health profile.",
                "Offer **a few practical wellness suggestions** but keep the focus on risk assessment.",
                "Speak naturally and conversationally, like a friendly but knowledgeable health advisor.",
                "If necessary, **suggest a routine check-up** in a way that encourages proactive care without creating fear.",
                "Ensure the response is **concise**, **informative**, and within **35-50 words**."
            ],
          "ai_response_format": (
              "Provide a structured response that includes each sentence in a square bracket:\n"
              "**A direct but non-intimidating summary** of potential health risks.\n"
              "**Key long-term considerations** related to their conditions and medications.\n"
              "**Early warning signs** they should pay attention to.\n"
              "**A few friendly, practical wellness tips** without shifting focus away from risk awareness.\n"
              "**Encouragement to stay proactive** without making them feel alarmed."
          )

        }

        return prompt  # Return structured JSON-style dictionary

    except KeyError as e:
        raise ValueError(f"Invalid patient data structure: {str(e)}") from e


  """
  ***APIs***
  """

  def med_question_answer(self, patient_id: str, user_query: str):

    prompt = self.create_medical_prompt(patient_id, user_query)
    response = self.call_groq(prompt)

    return response

  def get_dietary_recommendations(self, patient_id: str, location: str):

    prompt = self.create_dietary_prompt(patient_id, location)
    response = self.call_groq(prompt)
    final_response = self.parse_output(response, return_reasons=False)

    return final_response

  def get_future_risk(self, patient_id: str):
    prompt = self.create_medical_risk_prompt(patient_id)
    response = self.call_groq(prompt)
    final_response = self.parse_output(response, return_reasons=False)

    return final_response

llm = Custom_LLM()

@app.route('/get_med_answer', methods=['GET'])
def get_med_answer():
    try:
        query = request.form.get("query")
        response = llm.med_question_answer("123", query)
        return jsonify(response), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/get_diet', methods=['GET'])
def get_diet():
    try:
        diet_rec, reasons = llm.get_dietary_recommendations("123", "New York")
        return jsonify({"diet_rec":diet_rec, "reasons":reasons}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/get_risks', methods=['GET'])
def get_risks():
    try:
        risk, _ = llm.get_future_risk("123")
        return jsonify(risk), 200
    except:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run()

#google-crc32c==1.6.0