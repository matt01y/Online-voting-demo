import json
import os
import shutil
import sqlite3

import gnupg
import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Intermediary server")

path = os.path.join(os.getcwd(), "tempkeys")

if os.path.exists(path):
    shutil.rmtree(path)

os.mkdir(path)

# gpg = gnupg.GPG(gnupghome=os.path.join(os.getcwd(), "tempkeys"))
gpg = gnupg.GPG()


def create_sqlite_database(filename):
    """ create a database connection to an SQLite database """
    conn = None
    sql_statements = [
        """CREATE TABLE IF NOT EXISTS votes
                (voter_id INTEGER PRIMARY KEY);"""]
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
backend_public = requests.get("http://127.0.0.1:7879/public_key").json()['public_key']


class Vote(BaseModel):
    vote_id: int
    plain: str
    signed: str


@app.on_event("shutdown")
def shutdown_event():
    # Close the database connection when the application shuts down
    conn.close()
    os.rmdir(path)


@app.get("/init")
async def init():
    with open("./parties.json", "r", encoding="utf") as f:
        parties = json.loads("\n".join(f.readlines()))

    return {
        "auth_server": {"host": "127.0.0.1", "port": 7878},
        "backend_key": backend_public,
        "parties": parties
    }


@app.post("/vote")
async def vote(user_vote: Vote):
    voter_id = user_vote.vote_id

    # Fetch vote(s) from the database with the given voter_id
    cursor.execute("SELECT * FROM votes WHERE voter_id = ?", (voter_id,))
    votes_with_id = cursor.fetchall()

    # Check if any votes were found with the given voter_id
    if not votes_with_id:
        # No votes found with the given voter_id
        # Insert the vote into the database
        cursor.execute("INSERT INTO votes (voter_id) VALUES (?)", (voter_id,))
        conn.commit()

        # Fetch all votes from the database
        cursor.execute("SELECT * FROM votes")
        all_votes = cursor.fetchall()
        print("All votes in the database:")
        for vote in all_votes:
            print(vote)

        try:
            public_key = requests.get("http://localhost:7878/validate_voter", headers={"Content-Type": "application/json"},
                                      data=json.dumps({"voter_id": voter_id})).json()["message"]["PublicKey"]
        except Exception as e:
            return {"message": "Not allowed: Invalid"}

        imported = gpg.import_keys(public_key).results[0]

        unsigned = gpg.verify(user_vote.signed, extra_args=["-o", "-"])

        if not unsigned.valid or (imported['fingerprint'] != unsigned.fingerprint):
            # raise HTTPException(status_code=405, detail="Not allowed: Invalid public key")
            return {"message": "Not allowed: Invalid public key"}

        _ = requests.post("http://127.0.0.1:7879/vote", json={"encrypted_vote": user_vote.plain})

        return {"message": "New vote recorded successfully."}
    else:
        # Print the vote(s) found with the given voter_id
        print(f"Votes with voter_id {voter_id}:")
        for vote in votes_with_id:
            print(vote)

        return {"message": "Vote recorded successfully."}


@app.post("/validate")
async def vote(voter_id: int):
    print(voter_id)

    # Fetch vote(s) from the database with the given voter_id
    cursor.execute("SELECT * FROM votes WHERE voter_id = ?", (voter_id,))
    votes_with_id = cursor.fetchall()

    # Check if any votes were found with the given voter_id
    if not votes_with_id:
        # No votes found with the given voter_id
        return {"message": "No vote found."}

    # Print the vote(s) found with the given voter_id
    print(f"Votes with voter_id {voter_id}:")
    for vote in votes_with_id:
        print(vote)

    return {"message": "Vote found successfully."}
