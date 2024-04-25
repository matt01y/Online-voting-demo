# Login Server / Auth Server

## Description
This is the login server for our voting service. The user can log in with the eID or ItsMe.
When logging in they also give us their public key, which we the intermediate uses to check if it was signed by them.
The intermediate can then check when it gets a vote if the signature is valid. And if it is the first vote of the user.

## Usage
First make sure you have cargo installed.

To start the server, run the following command:
```bash
cargo run
```

### Client
The (user / client) can (log in / register) with the following request:
```bash
curl --data '{"e_id":"BE-64", "public_key":"aaaaa"}' --header 'Content-Type: application/json' --request POST 127.0.0.1:7878/login
```
In which they fill in their eID and public key in the respective fields. In the demo the eID is a "unique" number representing
their identity. The public key is the key they use to sign their votes.

The response from the server will be a json with the following format:
```json
{
    "voter_id": 0,
    "message": "Successfully registered"
}
```
In which the voter_id is the id of the voter in the database. This is used to identify the voter when they vote.
They have to pass this to the intermediate when they vote.

Message can also be `"eID already registered"` if the eID is already in the database.

`voter_id` will be `null` and `message` will be `"Invalid eID"` when the given `e_id` doesnt start with the `EID_PREFIX`.

If the passed data is in a wrong format, the response will be a `422` error.

### Intermediate
The intermediate can check if a vote is valid with the following request:
```bash
curl --data '{"voter_id":0, "public_key":"aaaaa"}' --header 'Content-Type: application/json' --request GET 127.0.0.1:7878/validate_voter
```

The response will either be:
```json
{
    "message": "ValidVoter"
}
```
or
```json
{
    "message": "InvalidVoter"
}
```

If the passed data is in a wrong format, the response will be a `422` error.
