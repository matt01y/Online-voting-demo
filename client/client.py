import requests as req
import json


# packet:
# voter_id, user_private_key_sign(backend_key(vote + nonce), voter_id)

# 1. Client sends eid and public key to auth
# 2. Auth generates a random number, stores them together with eid and public key in a list
# 3. Client receives voter_id and random number from auth
# 4. Client sends voter_id + encrypted random number + encrypted (vote + nonce) to intermediary

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


if __name__ == '__main__':
    # take the first entry as for proof of concept, in a real application, load balancing will be performed
    config = load_config("./client_config.json")

    intermediary = config["intermediaries"][0]
    data = init_connection(intermediary["host"], intermediary["port"])
    voter_id = authenticate(data["auth_server"]["host"], data["auth_server"]["port"], get_user_data())
    print(voter_id)
