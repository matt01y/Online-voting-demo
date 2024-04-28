import requests as req
import json


# packet:
# voter_id, user_private_key_sign(backend_key(vote + nonce), voter_id)

# 1. Client sends eid and public key to auth
# 2. Auth generates a random number, stores them together with eid and public key in a list
# 3. Client receives voter_id and random number from auth
# 4. Client sends voter_id + encrypted random number + encrypted (vote + nonce) to intermediary

def main(host: str, port: int) -> None:
    response = req.get(f"http://{host}:{port}/init").json()
    auth_server = response["auth_server"]
    backend_key = response["backend_key"]
    intermediary_key = response["intermediary_key"]
    parties = response["parties"]["politicians"]

    print(f"auth server: {auth_server}")
    print(f"intermediary key:  {intermediary_key}")
    print(f"backend key: {backend_key}")
    print(f"parties: {parties}")


def load_config(path: str) -> dict:
    with open(path, "r", encoding="UTF-8") as file:
        read_data = "\n".join(file.readlines())
        data = json.loads(read_data)
    return data


if __name__ == '__main__':
    # take the first entry as for proof of concept, in a real application, load balancing will be performed
    config = load_config("./client_config.json")

    intermediary = config["intermediaries"][0]
    main(intermediary["host"], intermediary["port"])
