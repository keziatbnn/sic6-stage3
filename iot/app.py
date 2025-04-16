from flask import Flask, request, jsonify
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from datetime import datetime
import os
import logging
from dotenv import load_dotenv

# Konfigurasi logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Konfigurasi MongoDB
mongodb_uri = os.environ.get('MONGODB_URI', 
                             "mongodb+srv://keziatbn:bswUIk16XbObVg4N@cluster0.pkum2.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")

try:
    client = MongoClient(mongodb_uri, server_api=ServerApi('1'))
    client.admin.command('ping')
    logger.info("Pinged your deployment. Successfully connected to MongoDB!")
    
    db = client['iot_project']
    collection = db['sensor_data']
except Exception as e:
    logger.error(f"Error connecting to MongoDB: {e}")

@app.route('/api/data', methods=['POST'])
def receive_data():
    try:
        if not request.is_json:
            logger.warning("Received request is not JSON")
            return jsonify({"success": False, "message": "Invalid request, JSON expected"}), 400

        data = request.json
        logger.info(f"Received data: {data}")

        # Validasi data
        required_fields = ['device_id']
        for field in required_fields:
            if field not in data:
                logger.warning(f"Missing required field: {field}")
                return jsonify({"success": False, "message": f"Missing required field: {field}"}), 400

        if 'timestamp' not in data:
            data['timestamp'] = datetime.now().isoformat()

        try:
            result = collection.insert_one(data)
            logger.info(f"Data saved successfully with ID: {result.inserted_id}")
            return jsonify({"success": True, "message": "Data saved successfully", "id": str(result.inserted_id)}), 201
        except Exception as db_error:
            logger.error(f"MongoDB Insert Error: {db_error}")
            return jsonify({"success": False, "message": f"Database error: {str(db_error)}"}), 500

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return jsonify({"success": False, "message": f"Error saving data: {str(e)}"}), 500


@app.route('/api/data', methods=['GET'])
def get_data():
    try:
        device_id = request.args.get('device_id')
        limit = request.args.get('limit')
        
        # Validasi limit
        if limit:
            try:
                limit = int(limit)
                if limit <= 0:
                    return jsonify({"success": False, "message": "Limit must be a positive integer"}), 400
            except ValueError:
                return jsonify({"success": False, "message": "Limit must be a valid integer"}), 400
        else:
            limit = 100  # Default limit
        
        query = {}
        if device_id:
            query['device_id'] = device_id
        
        # Ambil data dari MongoDB
        cursor = collection.find(query).sort('timestamp', -1).limit(limit)
        data = list(cursor)
        
        # Konversi ObjectId menjadi string untuk JSON
        for item in data:
            item['_id'] = str(item['_id'])
        
        return jsonify({
            "success": True,
            "count": len(data),
            "data": data
        })
    
    except Exception as e:
        logger.error(f"Error retrieving data: {e}")
        return jsonify({"success": False, "message": f"Error retrieving data: {str(e)}"}), 500

# Endpoint untuk pengecekan API health
@app.route('/health', methods=['GET'])
def health_check():
    try:
        # Periksa koneksi ke MongoDB
        client.admin.command('ping')
        return jsonify({"status": "healthy", "database": "connected"}), 200
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({"status": "unhealthy", "database": "disconnected", "error": str(e)}), 500

if __name__ == '__main__':
    from waitress import serve
    port = int(os.environ.get('PORT', 5000))
    print(f"Starting server on port {port}")
    serve(app, host='0.0.0.0', port=port)