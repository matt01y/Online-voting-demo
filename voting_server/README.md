# Voting Server

## Description
The tally server, the place where the votes get decrypted and counted.

## Usage
First make sure you have cargo installed.
Also make that gpg is installed on your system.
And that you have the correct private key in your gpg keyring.

To start the server, run the following command:
```bash
cargo run
```

### Intermediate
The intermediate can get the public key at the following endpoint:
```bash
curl 127.0.0.1/public_key
```

The encrypted votes can be sent to the following endpoint:
```bash
curl 'http://127.0.0.1:7879/vote' -X POST -H 'Content-Type: application/json' --data-raw '{"encrypted_vote": "-----BEGIN%20PGP%20MESSAGE----- ... -----END%20PGP%20MESSAGE-----"}'
```
make sure that the data sent is url encoded.

to see the current tally
```bash
curl 127.0.0.1:7879/votes
```