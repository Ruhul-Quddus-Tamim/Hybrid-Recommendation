import logging
import random

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ColdStartRecommender:
    def __init__(self, connection):
        self.connection = connection

    def recommend_for_new_user(self, limit=10):
        logger.info("Generating recommendations for a new user")
        
        popular_recs = self.get_popular_items(limit * 7)
        trending_recs = self.get_trending_items(limit * 7)
        diverse_recs = self.get_diverse_items(limit * 7)
        
        logger.debug(f"Popular recommendations: {popular_recs}")
        logger.debug(f"Trending recommendations: {trending_recs}")
        logger.debug(f"Diverse recommendations: {diverse_recs}")

        combined_recs = self.combine_recommendations(popular_recs, trending_recs, diverse_recs, limit=limit)
        logger.info(f"Combined recommendations for new user: {combined_recs}")
        return combined_recs

    def combine_recommendations(self, *rec_lists, limit):
        seen = set()
        combined = []

        for rec_list in rec_lists:
            random.shuffle(rec_list)  # Shuffle each list to add randomness
            for rec in rec_list:
                if rec['movieId'] not in seen:
                    seen.add(rec['movieId'])
                    combined.append(rec)
                    if len(combined) >= limit:
                        return combined  # Return early if limit is reached

        return combined[:limit]  # Ensure the combined list respects the limit

    def get_popular_items(self, limit=70):
        query = """
        MATCH (m:Movie)<-[r:RATED]-()
        RETURN m.movieId AS movieId, m.title AS title, m.genres AS genres, AVG(r.rating) AS avgRating, COUNT(r) AS ratingCount
        ORDER BY avgRating DESC, ratingCount DESC
        LIMIT $limit
        """
        result = self.connection.query(query, parameters={"limit": limit})
        return [{"movieId": record["movieId"], "title": record["title"], "genres": record["genres"]} for record in result]

    def get_trending_items(self, limit=70):
        query = """
        MATCH (m:Movie)<-[r:RATED]-()
        WHERE r.timestamp > timestamp() - 30 * 24 * 60 * 60 * 1000  // last 30 days
        RETURN m.movieId AS movieId, m.title AS title, m.genres AS genres, COUNT(r) AS ratingCount
        ORDER BY ratingCount DESC
        LIMIT $limit
        """
        result = self.connection.query(query, parameters={"limit": limit})
        return [{"movieId": record["movieId"], "title": record["title"], "genres": record["genres"]} for record in result]

    def get_diverse_items(self, limit=70):
        query = """
        MATCH (m:Movie)
        RETURN m.movieId AS movieId, m.title AS title, m.genres AS genres
        ORDER BY m.genres
        LIMIT $limit
        """
        result = self.connection.query(query, parameters={"limit": limit})
        return [{"movieId": record["movieId"], "title": record["title"], "genres": record["genres"]} for record in result]