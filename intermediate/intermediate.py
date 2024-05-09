import json
import sqlite3
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Intermediary server")

def create_sqlite_database(filename):
    """ create a database connection to an SQLite database """
    conn = None
    sql_statements = [ 
        """CREATE TABLE IF NOT EXISTS votes
                (id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                party TEXT);"""]
    try:
        conn = sqlite3.connect(filename)
        cursor = conn.cursor()
        for statement in sql_statements:
            cursor.execute(statement)
        conn.commit()
        print(f"sqlite version: {sqlite3.sqlite_version}")
    except sqlite3.Error as e:
        print(f"Error occured: {e}")
    return conn

# Create a SQLite database connection
conn = create_sqlite_database('db.sqlite')
cursor = conn.cursor()

class Vote(BaseModel):
    name: str | None
    party: str | None

@app.on_event("shutdown")
def shutdown_event():
    # Close the database connection when the application shuts down
    conn.close()


@app.get("/init")
async def init():
    with open("./parties.json", "r", encoding="utf") as f:
        parties = json.loads("\n".join(f.readlines()))

    return {
        "auth_server": {"host": "127.0.0.1", "port": 7878},
        "backend_key": "",
        "parties": parties
    }


@app.post("/vote")
async def vote(user_vote: Vote):
    if user_vote.party is None and user_vote.name is not None:
        raise HTTPException(status_code=422, detail="Invalid party. Party cannot be None when name is provided")

    if user_vote.party is not None and user_vote.name is None:
        raise HTTPException(status_code=422, detail="Invalid name. Name cannot be None when party is provided")

    print(user_vote)

    # Insert the vote into the database
    cursor.execute("INSERT INTO votes (name, party) VALUES (?, ?)", (user_vote.name, user_vote.party))
    conn.commit()

    # Fetch all votes from the database
    cursor.execute("SELECT * FROM votes")
    all_votes = cursor.fetchall()
    print("All votes in the database:")
    for vote in all_votes:
        print(vote)

    return {"message": "Vote recorded successfully."}
