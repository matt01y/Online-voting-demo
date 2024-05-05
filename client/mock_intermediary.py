import json
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Debug Intermediary server")


class Vote(BaseModel):
    name: str | None
    party: str | None


@app.get("/init")
async def init():
    with open("./parties.json", "r", encoding="utf") as f:
        parties = json.loads("\n".join(f.readlines()))

    return {
        "auth_server": {"host": "127.0.0.1", "port": 7878},
        "backend_key": "",
        "intermediary_key": "",
        "parties": parties
    }


@app.post("/vote")
async def vote(user_vote: Vote):
    if user_vote.party is None and user_vote.name is not None:
        raise HTTPException(status_code=422, detail="Invalid party. Party cannot be None when name is provided")

    if user_vote.party is not None and user_vote.name is None:
        raise HTTPException(status_code=422, detail="Invalid name. Name cannot be None when party is provided")

    print(user_vote)
