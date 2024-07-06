from neo4j import GraphDatabase
import os
from dotenv import load_dotenv
import math

# Load environment variables from .env file
load_dotenv()

# Neo4j connection details
uri = os.getenv('NEO4J_URI')
username = os.getenv('NEO4J_USERNAME')
password = os.getenv('NEO4J_PASSWORD')
database = os.getenv('NEO4J_DATABASE')

class Neo4jConnection:
    def __init__(self, uri, user, pwd):
        self.driver = GraphDatabase.driver(uri, auth=(user, pwd))

    def close(self):
        self.driver.close()

    def query(self, query, parameters=None, db=None):
        """
        Execute a query in the Neo4j database.
        
        :param query: Cypher query string
        :param parameters: Parameters for the query
        :param db: Database name
        :return: List of records
        """
        assert query is not None
        session = None
        response = None
        try:
            session = self.driver.session(database=db) if db is not None else self.driver.session()
            response = list(session.run(query, parameters))
        except Exception as e:
            print("Query failed:", e)
        finally:
            if session is not None:
                session.close()
        return response

# def get_user_ratings(connection, user_id):
#     """
#     Retrieve all ratings made by a user and normalize them.
    
#     :param connection: Neo4jConnection instance
#     :param user_id: User ID
#     :return: List of tuples (movieId, normalized_rating)
#     """
#     query = """
#     MATCH (u:User {userId: $user_id})-[r:RATED]->(m:Movie)
#     RETURN m.movieId AS movieId, r.rating AS rating
#     """
#     result = connection.query(query, parameters={"user_id": user_id})
#     ratings = [(record["movieId"], record["rating"]) for record in result]
    
#     if not ratings:
#         return []
    
#     avg_rating = sum(rating for _, rating in ratings) / len(ratings)
#     normalized_ratings = [(movie_id, rating - avg_rating) for movie_id, rating in ratings]
#     return normalized_ratings

def get_user_ratings(connection, user_id):
    """
    Retrieve all ratings made by a user.
    
    :param connection: Neo4jConnection instance
    :param user_id: User ID
    :return: List of tuples (movieId, rating)
    """
    query = """
    MATCH (u:User {userId: $user_id})-[r:RATED]->(m:Movie)
    RETURN m.movieId AS movieId, r.rating AS rating
    """
    result = connection.query(query, parameters={"user_id": user_id})
    ratings = [(record["movieId"], record["rating"]) for record in result]
    
    return ratings

def get_movie_ratings(connection, movie_id):
    """
    Retrieve all ratings for a movie.

    :param connection: Neo4jConnection instance
    :param movie_id: Movie ID
    :return: List of tuples (userId, rating)
    """
    query = """
    MATCH (m:Movie {movieId: $movie_id})<-[r:RATED]-(u:User)
    RETURN u.userId AS userId, r.rating AS rating
    """
    result = connection.query(query, parameters={"movie_id": movie_id})
    return [(record["userId"], record["rating"]) for record in result]

def calculate_similarity(ratings1, ratings2):
    """
    Calculate the cosine similarity between two sets of normalized ratings.
    
    :param ratings1: List of tuples (movieId, normalized_rating) for user 1
    :param ratings2: List of tuples (movieId, normalized_rating) for user 2
    :return: Cosine similarity
    """
    ratings1_dict = dict(ratings1)
    ratings2_dict = dict(ratings2)

    common_movies = set(ratings1_dict.keys()).intersection(set(ratings2_dict.keys()))
    
    if not common_movies:
        return 0.0

    numerator = sum(ratings1_dict[movie] * ratings2_dict[movie] for movie in common_movies)
    denominator1 = math.sqrt(sum(ratings1_dict[movie] ** 2 for movie in common_movies))
    denominator2 = math.sqrt(sum(ratings2_dict[movie] ** 2 for movie in common_movies))
    
    if denominator1 == 0 or denominator2 == 0:
        return 0.0

    return numerator / (denominator1 * denominator2)