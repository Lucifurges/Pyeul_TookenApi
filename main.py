from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import hashlib
import uuid
import random
import string
import logging

app = Flask(__name__)

# Enable CORS for all routes
CORS(app)

# Configure logging
logging.basicConfig(level=logging.INFO)

def random_string(length):
    characters = string.ascii_lowercase + "0123456789"
    return ''.join(random.choice(characters) for _ in range(length))

def encode_sig(data):
    sorted_data = {k: data[k] for k in sorted(data)}
    data_str = ''.join(f"{key}={value}" for key, value in sorted_data.items())
    return hashlib.md5((data_str + '62f8ce9f74b12f84c123cc23437a4a32').encode()).hexdigest()

def generate_token(email, password):
    device_id = str(uuid.uuid4())
    adid = str(uuid.uuid4())
    random_str = random_string(24)

    form = {
        'adid': adid,
        'email': email,
        'password': password,
        'format': 'json',
        'device_id': device_id,
        'cpl': 'true',
        'family_device_id': device_id,
        'locale': 'en_US',
        'client_country_code': 'US',
        'credentials_type': 'device_based_login_password',
        'generate_session_cookies': '1',
        'generate_analytics_claim': '1',
        'generate_machine_id': '1',
        'source': 'login',
        'machine_id': random_str,
        'api_key': '882a8490361da98702bf97a021ddc14d',
        'access_token': '350685531728%7C62f8ce9f74b12f84c123cc23437a4a32',
    }

    form['sig'] = encode_sig(form)
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36',
    }

    url = 'https://b-graph.facebook.com/auth/login'

    try:
        response = requests.post(url, data=form, headers=headers, timeout=10)
        data = response.json()

        logging.info(f"Facebook API response: {data}")

        if response.status_code == 200 and 'access_token' in data:
            return {'success': True, 'token': data['access_token']}
        else:
            return {
                'success': False,
                'error': data.get('error', {}).get('message', 'Failed to generate token. Check credentials.')
            }
    except requests.exceptions.Timeout:
        return {'success': False, 'error': 'Request timed out. Try again later.'}
    except requests.exceptions.RequestException as e:
        logging.error(f"Request error: {e}")
        return {'success': False, 'error': 'An error occurred while processing your request.'}

@app.route('/get_token', methods=['POST'])
def get_token():
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')

        if not email or not password:
            return jsonify({'success': False, 'error': 'Email and password are required'}), 400

        result = generate_token(email, password)
        return jsonify(result)

    except Exception as e:
        logging.error(f"Internal Server Error: {e}")
        return jsonify({'success': False, 'error': 'Internal Server Error'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
