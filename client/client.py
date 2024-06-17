import argparse
import json
import os
import random
import shutil

import gnupg
import requests as req


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


def authenticate(host: str, port: int, auth_data: dict[str, str]) -> int:
    auth = req.post(f"http://{host}:{port}/login", json=auth_data).json()
    vote_id = auth["voter_id"]

    if vote_id is None:
        raise AssertionError(f"[ERROR] {auth['message']}")

    return vote_id


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


def send_vote(vote_id: int, vote: tuple[str, str] | None, address: str, user_key, encryption_key,
              encryptor: gnupg.GPG) -> None:
    # (vote_id, sign(vote_id, backend_key(nonce, vote)))
    if vote is None:
        vote_json = {
            "name": "None",
            "party": "None"
        }
    else:
        vote_json = {
            "name": vote[0],
            "party": vote[1]
        }

    nonce = random.randint(100000, 999999)
    vote_encrypted = gpg.encrypt(json.dumps({"nonce": nonce, "vote": vote_json}),
                                 recipients=encryption_key["fingerprint"], always_trust=True).data.decode("utf-8")

    signed = encryptor.sign(json.dumps({"vote_id": vote_id, "vote": vote_encrypted}),
                            keyid=user_key.fingerprint).data.decode("utf-8")
    response = req.post(f"{address}/vote",
                        json={
                            "vote_id": vote_id,
                            "plain": vote_encrypted,
                            "signed": signed})

    if response.status_code != 200:
        print(f"[ERROR]: {response.status_code} - {response.json()['detail']}")
        return

    print(response.json()["message"])


def cleanup(fingerprint, gnu_path, secret=True, passphrase=""):
    gpg.delete_keys(fingerprint, secret=secret, passphrase=passphrase)
    shutil.rmtree(gnu_path)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--eid", type=str, default="BE-63963937392")
    args = parser.parse_args()

    path = os.path.join(os.getcwd(), args.eid)

    if os.path.exists(path):
        shutil.rmtree(path)

    os.mkdir(path)
    gpg = gnupg.GPG(gnupghome=path)

    # take the first entry as for proof of concept, in a real application, load balancing will be performed
    config = load_config("./client_config.json")
    intermediary = config["intermediaries"][0]

    # contact the intermediary, result will be list of parties and people, and ip of auth server
    # the public keys of the backend server and intermediary server
    intermediary_address = f"http://{intermediary['host']}:{intermediary['port']}"
    data = init_connection(intermediary_address)

    backend_key = gpg.import_keys(data["backend_key"]).results[0]

    key_gen_data = gpg.gen_key_input(key_type="RSA", key_length=2048, no_protection=True)
    key = gpg.gen_key(key_gen_data)

    user_data = {
        "e_id": args.eid,
        "public_key": gpg.export_keys(key.fingerprint)
    }

    try:
        voter_id = authenticate(data["auth_server"]["host"], data["auth_server"]["port"], user_data)
    except AssertionError as e:
        cleanup(key.fingerprint, path)
        raise e

    user_vote = user_vote(data["parties"])
    send_vote(voter_id, user_vote, intermediary_address, key, encryption_key=backend_key, encryptor=gpg)

    cleanup(key.fingerprint, path)
