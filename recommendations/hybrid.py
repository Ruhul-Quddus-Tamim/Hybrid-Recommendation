from .collaborative_filtering import CollaborativeFiltering
from .content_based import ContentBasedFiltering
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HybridRecommender:
    def __init__(self, connection):
        self.collaborative_filtering = CollaborativeFiltering(connection)
        self.content_based_filtering = ContentBasedFiltering(connection)

    def recommend_for_existing_user(self, user_id, limit=12):
        logger.info(f"Generating recommendations for user {user_id} with limit {limit}")
        
        user_recs = self.collaborative_filtering.user_based_recommendations(user_id, limit)
        content_recs = self.content_based_filtering.content_based_recommendations(user_id, limit)
        
        logger.debug(f"User-based recommendations: {user_recs}")
        logger.debug(f"Content-based recommendations: {content_recs}")

        combined_recs = self.combine_recommendations(user_recs, content_recs, limit=limit)
        logger.info(f"Combined recommendations for user {user_id}: {combined_recs}")
        return combined_recs

    def combine_recommendations(self, user_recs, content_recs, *, limit):
        seen = set()
        combined = []

        for rec_list in (user_recs, content_recs):
            for rec in rec_list:
                if rec['movieId'] not in seen:
                    seen.add(rec['movieId'])
                    combined.append(rec)
                    if len(combined) >= limit:
                        return combined  # Return early if limit is reached

        return combined[:limit]  # Ensure the combined list respects the limit