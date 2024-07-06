import logging
from recommendations.utils import get_user_ratings

# Configure logging
logging.basicConfig(level=logging.INFO)  # Set to INFO to suppress debug logs
logger = logging.getLogger(__name__)

# Set Neo4j driver logging level to INFO
logging.getLogger("neo4j").setLevel(logging.INFO)

class ContentBasedFiltering:
    def __init__(self, connection, high_rating_threshold=4.0):
        self.connection = connection
        self.high_rating_threshold = high_rating_threshold

    def content_based_recommendations(self, user_id, limit=10):
        """
        Generate movie recommendations for a user based on content-based filtering.
        
        :param user_id: Target user ID
        :param limit: Number of recommendations to return
        :return: List of recommended movies with details
        """
        user_ratings = get_user_ratings(self.connection, user_id)
        logger.info(f"User {user_id} ratings: {user_ratings}")
        
        # Extract raw ratings
        high_rated_movies = [
            movie_id for movie_id, rating in user_ratings
            if rating >= self.high_rating_threshold
        ]
        logger.info(f"High-rated movie IDs: {high_rated_movies}")
        
        if not high_rated_movies:
            logger.info("No high-rated movies found.")
            return []
        
        similar_movies = self.find_similar_movies(high_rated_movies, user_id)
        logger.info(f"Similar movies for user {user_id}: {similar_movies}")
        
        return similar_movies[:limit]

    def find_similar_movies(self, high_rated_movies, user_id):
        query = """
        MATCH (m:Movie)
        WHERE m.movieId IN $rated_movie_ids
        RETURN m.genres AS genres
        """
        genres_result = self.connection.query(query, parameters={"rated_movie_ids": high_rated_movies})
        logger.info(f"Genres result: {genres_result}")
        
        genres = set()
        for record in genres_result:
            genres.update(record["genres"].split("|"))
        logger.info(f"Extracted genres: {genres}")

        query = """
        MATCH (similar:Movie)
        WHERE any(genre IN $genres WHERE genre IN split(similar.genres, '|'))
        AND NOT EXISTS((:User {userId: $user_id})-[:RATED]->(similar))
        RETURN similar.movieId AS movieId, similar.title AS title, similar.genres AS genres
        LIMIT 50
        """
        result = self.connection.query(query, parameters={"genres": list(genres), "user_id": user_id})
        logger.info(f"Similar movies result: {result}")

        return [{"movieId": record["movieId"], "title": record["title"], "genres": record["genres"]} for record in result]