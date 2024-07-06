import logging
from neo4j import GraphDatabase
from flask import Blueprint, jsonify, request, render_template
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Neo4j connection (update with your credentials)
uri = os.getenv('NEO4J_URI')
username = os.getenv('NEO4J_USERNAME')
password = os.getenv('NEO4J_PASSWORD')
database = os.getenv('NEO4J_DATABASE')

logger.info(f"Connecting to Neo4j at {uri} with user {username}")

driver = GraphDatabase.driver(uri, auth=(username, password))

profile_bp = Blueprint('profile', __name__)

@profile_bp.route('/profile/', methods=['GET'])
def profile_page():
    return render_template('profile.html')

@profile_bp.route('/profile/<int:user_id>', methods=['GET'])
def get_profile(user_id):
    logger.debug(f"Fetching profile for user_id: {user_id}")
    try:
        with driver.session(database=database) as session:
            user_result = session.run(
                "MATCH (u:User {userId: $user_id}) RETURN u.userId AS userId, u.name AS name, u.email AS email",
                user_id=user_id
            )
            user = user_result.single()
            if not user:
                logger.debug(f"No user found with user_id: {user_id}")
                return jsonify({"error": "User not found"}), 404

            ratings_result = session.run(
                "MATCH (u:User {userId: $user_id})-[r:RATED]->(m:Movie) RETURN m.title AS movie, r.rating AS rating",
                user_id=user_id
            )
            tags_result = session.run(
                "MATCH (u:User {userId: $user_id})-[t:TAGGED]->(m:Movie) RETURN m.title AS movie, t.tag AS tag",
                user_id=user_id
            )

            ratings_dict = {}
            for record in ratings_result:
                movie = record["movie"]
                rating = record["rating"]
                if movie not in ratings_dict:
                    ratings_dict[movie] = []
                ratings_dict[movie].append(rating)

            tags_dict = {}
            for record in tags_result:
                movie = record["movie"]
                tag = record["tag"]
                if movie not in tags_dict:
                    tags_dict[movie] = []
                tags_dict[movie].append(tag)

            profile_data = {
                "userId": user["userId"],
                "name": user["name"],
                "email": user["email"],
                "ratings": [{"movie": movie, "rating": ratings[0]} for movie, ratings in ratings_dict.items()],
                "tags": [{"movie": movie, "tag": tags[0]} for movie, tags in tags_dict.items()]
            }

            logger.debug(f"Profile data: {profile_data}")

            return jsonify(profile_data), 200
    except Exception as e:
        logger.error(f"Error fetching profile for user {user_id}: {e}")
        return jsonify({"error": str(e)}), 500