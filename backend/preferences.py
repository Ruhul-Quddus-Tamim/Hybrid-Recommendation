import logging
from neo4j import GraphDatabase
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

def get_preferences():
    logger.debug("Fetching preferences")
    try:
        with driver.session(database=database) as session:
            # Fetch unique movie titles
            movies_result = session.run("MATCH (m:Movie) RETURN DISTINCT m.title AS movie ORDER BY movie")
            # Fetch unique tags
            tags_result = session.run("MATCH (t:Tag) RETURN DISTINCT t.tag AS tag ORDER BY tag")

            movies = [record["movie"] for record in movies_result]
            tags = [record["tag"] for record in tags_result]

            preferences_data = {
                "movies": movies,
                "tags": tags
            }
            logger.debug(f"Preferences data: {preferences_data}")
            return preferences_data
    except Exception as e:
        logger.error(f"Error fetching preferences: {e}")
        raise e

def save_preferences(user_id, ratings, tags):
    logger.debug(f"Saving preferences for user {user_id}")
    try:
        with driver.session(database=database) as session:
            for rating in ratings:
                movie = rating['movie']
                rating_value = int(rating['rating'])
                logger.debug(f"Rating: user_id={user_id}, movie={movie}, rating={rating_value}")
                session.run(
                    """
                    MATCH (u:User {userId: $user_id}), (m:Movie {title: $movie})
                    MERGE (u)-[r:RATED]->(m)
                    SET r.rating = $rating
                    """,
                    user_id=int(user_id), movie=movie, rating=rating_value
                )
            for tag in tags:
                movie = tag['movie']
                tag_value = tag['tag']
                logger.debug(f"Tag: user_id={user_id}, movie={movie}, tag={tag_value}")
                session.run(
                    """
                    MATCH (u:User {userId: $user_id}), (m:Movie {title: $movie})
                    MERGE (u)-[t:TAGGED]->(m)
                    SET t.tag = $tag
                    """,
                    user_id=int(user_id), movie=movie, tag=tag_value
                )
        logger.debug(f"Preferences saved for user {user_id}")
    except Exception as e:
        logger.error(f"Error saving preferences for user {user_id}: {e}")
        raise e