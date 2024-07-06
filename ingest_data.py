import pandas as pd
from neo4j import GraphDatabase
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load the datasets from the data folder
movies_path = os.getenv('MOVIES_PATH')
tags_path = os.getenv('TAGS_PATH')
links_path = os.getenv('LINKS_PATH')
ratings_path = os.getenv('RATINGS_PATH')

movies = pd.read_csv(movies_path)
tags = pd.read_csv(tags_path)
links = pd.read_csv(links_path)
ratings = pd.read_csv(ratings_path)

# Neo4j connection (update with your credentials)
uri = os.getenv('NEO4J_URI')
username = os.getenv('NEO4J_USERNAME')
password = os.getenv('NEO4J_PASSWORD')
database = os.getenv('NEO4J_DATABASE')

driver = GraphDatabase.driver(uri, auth=(username, password))

checkpoint_file = 'checkpoint.txt'

def read_checkpoint():
    if os.path.exists(checkpoint_file):
        with open(checkpoint_file, 'r') as f:
            return int(f.read().strip())
    return 0

def write_checkpoint(index):
    with open(checkpoint_file, 'w') as f:
        f.write(str(index))

def clear_existing_data():
    with driver.session(database=database) as session:
        session.run("MATCH (u:User) DETACH DELETE u")
        session.run("MATCH (m:Movie) DETACH DELETE m")
        session.run("MATCH ()-[r:TAGGED]->() DELETE r")
        session.run("MATCH ()-[r:RATED]->() DELETE r")
    logger.info("Cleared existing user, movie, and relationship data.")

def create_user(tx, user_id):
    tx.run("MERGE (u:User {userId: $user_id})", user_id=user_id)

def create_movie(tx, movie_id, title, genres):
    tx.run("MERGE (m:Movie {movieId: $movie_id, title: $title, genres: $genres})",
           movie_id=movie_id, title=title, genres=genres)

def create_tag(tx, user_id, movie_id, tag, timestamp):
    tx.run("""
        MATCH (u:User {userId: $user_id})
        MATCH (m:Movie {movieId: $movie_id})
        CREATE (u)-[:TAGGED {tag: $tag, timestamp: $timestamp}]->(m)
    """, user_id=user_id, movie_id=movie_id, tag=tag, timestamp=timestamp)

def create_link(tx, movie_id, imdb_id, tmdb_id):
    tx.run("MATCH (m:Movie {movieId: $movie_id}) SET m.imdbId = $imdb_id, m.tmdbId = $tmdb_id",
           movie_id=movie_id, imdb_id=imdb_id, tmdb_id=tmdb_id)

def create_rating(tx, user_id, movie_id, rating, timestamp):
    tx.run("""
        MATCH (u:User {userId: $user_id})
        MATCH (m:Movie {movieId: $movie_id})
        CREATE (u)-[:RATED {rating: $rating, timestamp: $timestamp}]->(m)
    """, user_id=user_id, movie_id=movie_id, rating=rating, timestamp=timestamp)

def ingest_data(data, ingest_function):
    with ThreadPoolExecutor() as executor:
        futures = [executor.submit(ingest_function, *row) for row in data.itertuples(index=False, name=None)]
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                logger.error(f"Error during data ingestion: {e}")

def ingest_movies():
    logger.info("Ingesting movies...")
    def ingest_movie_row(row):
        with driver.session(database=database) as session:
            session.write_transaction(create_movie, row.movieId, row.title, row.genres)
    ingest_data(movies.itertuples(index=False, name=None), ingest_movie_row)

def ingest_users():
    logger.info("Ingesting users...")
    unique_user_ids = set(pd.concat([tags['userId'], ratings['userId']]).unique())
    def ingest_user_row(user_id):
        with driver.session(database=database) as session:
            session.write_transaction(create_user, user_id)
    ingest_data(pd.DataFrame(unique_user_ids, columns=['userId']).itertuples(index=False, name=None), ingest_user_row)

def ingest_tags():
    logger.info("Ingesting tags...")
    def ingest_tag_row(row):
        with driver.session(database=database) as session:
            session.write_transaction(create_tag, row.userId, row.movieId, row.tag, row.timestamp)
    ingest_data(tags.itertuples(index=False, name=None), ingest_tag_row)

def ingest_links():
    logger.info("Ingesting links...")
    def ingest_link_row(row):
        with driver.session(database=database) as session:
            session.write_transaction(create_link, row.movieId, row.imdbId, row.tmdbId)
    ingest_data(links.itertuples(index=False, name=None), ingest_link_row)

def ingest_ratings():
    logger.info("Ingesting ratings...")
    def ingest_rating_row(row):
        with driver.session(database=database) as session:
            session.write_transaction(create_rating, row.userId, row.movieId, row.rating, row.timestamp)
    ingest_data(ratings.iloc[:500000].itertuples(index=False, name=None), ingest_rating_row)

if __name__ == '__main__':
    logger.info("Starting data ingestion...")
    clear_existing_data()
    ingest_movies()
    ingest_users()
    ingest_tags()
    ingest_links()
    ingest_ratings()
    driver.close()
    logger.info("Data ingestion completed.")
