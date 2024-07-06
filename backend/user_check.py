from recommendations.utils import get_user_ratings

def is_new_user(connection, user_id):
    # Check if user has ratings
    query = """
    MATCH (u:User {userId: $user_id})-[:RATED]->(m:Movie)
    RETURN COUNT(*) AS rating_count
    """
    result = connection.query(query, parameters={"user_id": user_id})
    rating_count = result[0]['rating_count']
    print(f"User {user_id} rating count: {rating_count}")  # Debug log

    if rating_count > 0:
        return False

    # Check if user has genres
    query = """
    MATCH (u:User {userId: $user_id})-[:LIKES]->(g:Genre)
    RETURN COUNT(*) AS genre_count
    """
    result = connection.query(query, parameters={"user_id": user_id})
    genre_count = result[0]['genre_count']
    print(f"User {user_id} genre count: {genre_count}")  # Debug log

    if genre_count > 0:
        return False

    # Check if user has tags
    query = """
    MATCH (u:User {userId: $user_id})-[:TAGGED]->(t:Tag)
    RETURN COUNT(*) AS tag_count
    """
    result = connection.query(query, parameters={"user_id": user_id})
    tag_count = result[0]['tag_count']
    print(f"User {user_id} tag count: {tag_count}")  # Debug log

    return tag_count == 0