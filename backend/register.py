import os
from neo4j import GraphDatabase
from dotenv import load_dotenv
import logging

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(filename='register.log', level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Neo4j connection (update with your credentials)
uri = os.getenv('NEO4J_URI')
username = os.getenv('NEO4J_USERNAME')
password = os.getenv('NEO4J_PASSWORD')
database = os.getenv('NEO4J_DATABASE')

logger.info(f"Connecting to Neo4j at {uri} with user {username}")

driver = GraphDatabase.driver(uri, auth=(username, password))

def create_user(tx, user_id, name, email):
    logger.debug(f"Running CREATE (u:User {{userId: {user_id}, name: {name}, email: {email}}})")
    result = tx.run("CREATE (u:User {userId: $user_id, name: $name, email: $email})",
           user_id=int(user_id), name=name, email=email)
    summary = result.consume().counters
    logger.info(f"Transaction summary: {summary}")

def register_user(user_id, name, email):
    logger.debug(f"Starting session to register user {user_id}")
    with driver.session(database=database) as session:
        logger.debug(f"Executing create_user transaction for {user_id}")
        session.execute_write(create_user, user_id, name, email)
        logger.info(f"User {user_id} registered successfully with name: {name} and email: {email}")

if __name__ == '__main__':
    import sys
    logger.debug(f"Script started with arguments: {sys.argv}")
    if len(sys.argv) != 4:
        logger.error("Invalid number of arguments. Expected 3 arguments: user_id, name, email")
        sys.exit(1)
    user_id = sys.argv[1]
    name = sys.argv[2]
    email = sys.argv[3]
    logger.info(f"Registering user with ID: {user_id}, Name: {name}, Email: {email}")
    register_user(user_id, name, email)
    logger.info(f"Finished registering user with ID: {user_id}")