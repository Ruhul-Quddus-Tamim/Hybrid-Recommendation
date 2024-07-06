from .utils import get_user_ratings, calculate_similarity
import logging
import pickle
import os

logger = logging.getLogger(__name__)

class CollaborativeFiltering:
    def __init__(self, connection):
        self.connection = connection
        self.model = self.load_model()

    def load_model(self):
        model_path = './models/svd_model.pkl'
        with open(model_path, 'rb') as f:
            model = pickle.load(f)
        logger.info("Trained SVD model loaded.")
        return model

    def user_based_recommendations(self, user_id, limit=20):
        """
        Generate movie recommendations for a user based on user-based collaborative filtering.
        
        :param user_id: Target user ID
        :param limit: Number of recommendations to return
        :return: List of recommended movies with details and predicted ratings
        """
        user_ratings = get_user_ratings(self.connection, user_id)
        if not user_ratings:
            return []
        
        similar_users = self.find_similar_users(user_id, user_ratings)
        recommendations = self.aggregate_user_recommendations(similar_users, user_id, limit)
        return recommendations

    def find_similar_users(self, user_id, user_ratings, top_n=10):
        """
        Find users similar to the target user based on rating profiles.
        
        :param user_id: Target user ID
        :param user_ratings: Ratings of the target user
        :param top_n: Number of similar users to find
        :return: List of tuples (similar_user_id, similarity_score)
        """
        query = """
        MATCH (u:User)-[r:RATED]->(m:Movie)
        WHERE u.userId <> $user_id
        RETURN u.userId AS userId, collect(m.movieId) AS movieIds, collect(r.rating) AS ratings
        """
        result = self.connection.query(query, parameters={"user_id": user_id})

        similarities = []
        for record in result:
            other_user_id = record["userId"]
            other_user_ratings = list(zip(record["movieIds"], record["ratings"]))
            similarity = calculate_similarity(user_ratings, other_user_ratings)
            similarities.append((other_user_id, similarity))

        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_n]

    def aggregate_user_recommendations(self, similar_users, user_id, limit=10):
        """
        Aggregate recommendations from similar users.
        
        :param similar_users: List of tuples (similar_user_id, similarity_score)
        :param user_id: Target user ID
        :param limit: Number of recommendations to return
        :return: List of recommended movies with details
        """
        recommended_movies = {}

        for similar_user_id, similarity in similar_users:
            user_ratings = get_user_ratings(self.connection, similar_user_id)
            
            for movie_id, rating in user_ratings:
                try:
                    # Use the trained model to predict ratings
                    prediction = self.model.predict(int(user_id), int(movie_id))
                    predicted_rating = prediction.est
                    logger.debug(f"User: {user_id}, Movie: {movie_id}, Predicted: {predicted_rating}, Actual: {rating}")
                except Exception as e:
                    logger.error(f"Error predicting rating for user {user_id} and movie {movie_id}: {e}")
                    predicted_rating = None

                if predicted_rating is not None:
                    if movie_id not in recommended_movies:
                        recommended_movies[movie_id] = (predicted_rating * similarity, similarity)
                    else:
                        current_rating, current_similarity = recommended_movies[movie_id]
                        recommended_movies[movie_id] = (current_rating + predicted_rating * similarity, current_similarity + similarity)

        for movie_id in recommended_movies:
            total_rating, total_similarity = recommended_movies[movie_id]
            recommended_movies[movie_id] = total_rating / total_similarity

        sorted_recommendations = sorted(recommended_movies.items(), key=lambda x: x[1], reverse=True)
        top_recommendations = sorted_recommendations[:limit]

        # Fetch movie details for the top recommendations
        movie_details = self.get_movie_details([movie_id for movie_id, _ in top_recommendations])

        recommendations_with_details = [
            {
                "movieId": movie_id,
                "title": movie_details[movie_id]["title"],
                "genres": movie_details[movie_id]["genres"],
                "predictedRating": rating
            }
            for movie_id, rating in top_recommendations
        ]

        return recommendations_with_details

    def get_movie_details(self, movie_ids):
        """
        Fetch movie details for the given movie IDs.
        
        :param movie_ids: List of movie IDs
        :return: Dictionary of movie details keyed by movie ID
        """
        query = """
        MATCH (m:Movie)
        WHERE m.movieId IN $movie_ids
        RETURN m.movieId AS movieId, m.title AS title, m.genres AS genres
        """
        result = self.connection.query(query, parameters={"movie_ids": movie_ids})

        movie_details = {record["movieId"]: {"title": record["title"], "genres": record["genres"]} for record in result}
        return movie_details