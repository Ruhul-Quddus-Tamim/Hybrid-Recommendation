from flask import Flask, jsonify, request, render_template
from backend.register import register_user
from backend.profile import profile_bp
from backend.preferences import get_preferences, save_preferences
from recommendations.hybrid import HybridRecommender
from recommendations.cold_start import ColdStartRecommender
from backend.user_check import is_new_user
import logging
import os
from dotenv import load_dotenv
from recommendations.utils import Neo4jConnection

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.register_blueprint(profile_bp)

# Neo4j connection
uri = os.getenv('NEO4J_URI')
username = os.getenv('NEO4J_USERNAME')
password = os.getenv('NEO4J_PASSWORD')
database = os.getenv('NEO4J_DATABASE')
connection = Neo4jConnection(uri, username, password)

hybrid_recommender = HybridRecommender(connection)
cold_start_recommender = ColdStartRecommender(connection)

@app.route('/')
def home():
    logger.debug("Rendering home page")
    return render_template('index.html')

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    user_id = data['userId']
    name = data['name']
    email = data['email']
    
    logger.info(f"Received registration for userId: {user_id}, name: {name}, email: {email}")
    
    try:
        register_user(user_id, name, email)
        logger.info(f"User {user_id} registered successfully in the database.")
        return jsonify({"message": "User registered successfully!"}), 201
    except Exception as e:
        logger.error(f"Error registering user {user_id}: {e}")
        return jsonify({"message": "Failed to register user."}), 500

@app.route('/recommendations', methods=['GET'])
def recommendations():
    user_id = request.args.get('user_id')
    try:
        logger.debug(f"Getting recommendations for user {user_id}")
        if is_new_user(connection, int(user_id)):
            logger.info(f"User {user_id} is new.")
            recommendations = cold_start_recommender.recommend_for_new_user()
            return jsonify({"is_new_user": True, "recommendations": recommendations}), 200
        else:
            recommendations = hybrid_recommender.recommend_for_existing_user(int(user_id))
            return jsonify({"is_new_user": False, "recommendations": recommendations}), 200
    except Exception as e:
        logger.error(f"Error getting recommendations for user {user_id}: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/recommendations_page', methods=['GET'])
def recommendations_page():
    user_id = request.args.get('user_id')
    is_new = request.args.get('is_new') == 'true'
    logger.debug(f"Rendering recommendations page for user {user_id}, is_new={is_new}")
    return render_template('recommendations.html', user_id=user_id, is_new=is_new)

@app.route('/user_preferences', methods=['GET'])
def user_preferences_page():
    logger.debug("Rendering user preferences page")
    return render_template('user_preferences.html')

@app.route('/preferences', methods=['GET'])
def preferences():
    try:
        preferences_data = get_preferences()
        return jsonify(preferences_data), 200
    except Exception as e:
        logger.error(f"Error fetching preferences: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/preferences', methods=['POST'])
def update_preferences():
    data = request.get_json()
    user_id = data['userId']
    ratings = data.get('ratings', [])
    tags = data.get('tags', [])

    logger.debug(f"Received preferences for user {user_id}: ratings={ratings}, tags={tags}")
    
    try:
        save_preferences(user_id, ratings, tags)
        return jsonify({"message": "Preferences updated successfully!"}), 200
    except Exception as e:
        logger.error(f"Error saving preferences for user {user_id}: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    logger.debug("Starting Flask application")
    app.run(debug=True, port=5001)