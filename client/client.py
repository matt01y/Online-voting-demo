import requests as req
import json
import gnupg
import os
import shutil


def init_connection(address: str) -> dict:
    response = req.get(f"{address}/init").json()
    auth_server = response["auth_server"]
    backend_key = response["backend_key"]
    parties = response["parties"]["politicians"]

    return {
        "auth_server": auth_server,
        "backend_key": backend_key,
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


def send_vote(vote_id: int, vote: tuple[str, str] | None, address: str, user_key, backend_key,
              encryptor: gnupg.GPG) -> None:
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

    signed = encryptor.sign(json.dumps(vote_json))
    print(signed)
    response = req.post(f"{address}/vote", data=signed.data)
    if response.status_code != 200:
        print(f"[ERROR]: {response.status_code} - {response.text}")


if __name__ == '__main__':
    path = os.path.join(os.getcwd(), "tempkeys")

    if os.path.exists(path):
        shutil.rmtree(path)

    os.mkdir(path)
    gpg = gnupg.GPG(gnupghome=path)

    # take the first entry as for proof of concept, in a real application, load balancing will be performed
    config = load_config("./client_config.json")
    intermediary = config["intermediaries"][0]

    key_gen_data = gpg.gen_key_input(key_type="RSA", key_length=2048, no_protection=True)
    key = gpg.gen_key(key_gen_data)
    # print(key.)

    user_data = {
        "e_id": "BE-63963937393",
        "public_key": "heyditiseenkey:)"
    }

    # contact the intermediary, result will be list of parties and people, and ip of auth server
    # the public keys of the backend server and intermediary server
    intermediary_address = f"http://{intermediary['host']}:{intermediary['port']}"
    data = init_connection(intermediary_address)
    voter_id = authenticate(data["auth_server"]["host"], data["auth_server"]["port"], user_data)

    user_vote = user_vote(data["parties"])
    send_vote(voter_id, user_vote, intermediary_address, key, backend_key=data["backend_key"], encryptor=gpg)

    gpg.delete_keys(key.fingerprint, secret=True, passphrase="")
    shutil.rmtree(path)
