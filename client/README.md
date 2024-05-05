# Client

## Description
The client stands in for interaction with the user. 
They log in to the system through the client and cast their vote. The client makes a first 
request to the intermediary on **intermediary ip**/init. The client expects the following:
```json
{
  "auth server": {
    "host": "host ip of auth server",
    "port": port number of auth server as a positive integer
  }
  "intermediary key": "public key of intermediary",
  "backend key": "public key of backend",
  "parties": [
    {
      "name": "name of politician",
      "party": "party of politician"
    },
    ...
  ]
}

```

## Dependencies
The client depends on:
* requests: this package makes it easier to make get/post/... requests to a URL
* json: to parse the config file
* python-gnupg: for the encryption part
* [DEBUG]: fastapi, this is only used for the debug server to test out the client

## Usage
to run the client, simply run `python client.py` in a shell. To execute the debug server as well, run the shell script
`./run_debug.sh`. This will start the debug server on 127.0.0.1:9000.
