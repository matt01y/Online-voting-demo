import requests as req
import json


def init_connection(host: str, port: int) -> dict:
    response = req.get(f"http://{host}:{port}/init").json()
    auth_server = response["auth_server"]
    backend_key = response["backend_key"]
    intermediary_key = response["intermediary_key"]
    parties = response["parties"]["politicians"]

    return {
        "auth_server": auth_server,
        "backend_key": backend_key,
        "intermediary_key": intermediary_key,
        "parties": parties
    }


def authenticate(host: str, port: int, auth_data: dict[str, str]) -> int | None:
    auth = req.post(f"http://{host}:{port}/login", json=auth_data).json()

    if "success" in auth["message"].lower():
        return auth["voter_id"]


def load_config(path: str) -> dict:
    with open(path, "r", encoding="UTF-8") as file:
        read_data = "\n".join(file.readlines())
        config_data = json.loads(read_data)
    return config_data


def get_user_data():
    return {
        "e_id": "BE-878",
        "public_key": "888888888"
    }


def user_vote(parties: list[dict[str, str]]) -> tuple[str, str] | None:
    parties_sorted = sorted(parties, key=lambda p: p["party"])
    print(f"{'Nr':^5} {'Name':^25} Party")
    for i, option in enumerate(parties_sorted):
        print(f"{i + 1:>5}. {option['name']:<25} {option['party']}")
    print("\ncast your vote (leave empty to vote blank, press enter to confirm)")

    while True:
        decision = input("Number: ")
        if decision == "":
            return None

        try:
            index = int(decision) - 1
            vote = parties_sorted[index]
            return vote["name"], vote["party"]
        except ValueError:
            print("[ERROR]: could not cast the input to a number")


def send_vote(vote_id: int, vote: tuple[str, str] | None, host: str, port: int) -> None:
    # (vote_id, sign(vote_id, backend_key(nonce, vote)))
    if vote is None:
        vote_json = {
            "name": None,
            "party": None
        }
    else:
        vote_json = {
            "name": vote[0],
            "party": vote[1]
        }
    response = req.post(f"http://{host}:{port}/vote", json=vote_json)
    if response.status_code != 200:
        print(f"[ERROR]: {response.status_code} - {response.text}")


if __name__ == '__main__':
    # take the first entry as for proof of concept, in a real application, load balancing will be performed
    config = load_config("./client_config.json")
    intermediary = config["intermediaries"][0]

    # contact the intermediary, result will be list of parties and people, and ip of auth server
    # the public keys of the backend server and intermediary server
    data = init_connection(intermediary["host"], intermediary["port"])
    voter_id = authenticate(data["auth_server"]["host"], data["auth_server"]["port"], get_user_data())

    user_vote = user_vote(data["parties"])
    send_vote(user_vote, intermediary["host"], intermediary["port"])
