use std::collections::HashMap;
use std::fs;
use std::process::{Command, Stdio};
use std::sync::{Arc, Mutex};

use axum::{Extension, Json, Router};
use axum::routing::{get, post};
use tower::ServiceBuilder;
use tower_http::add_extension::AddExtensionLayer;

const PUB_KEY_FILE: &str = "public_key.asc";


#[tokio::main]
async fn main() {
    let votes: Arc<Mutex<HashMap<String, HashMap<String, i64>>>> = Arc::new(Mutex::new(HashMap::new()));
    // create a new instance of the application
    let app = Router::new()
        // the route for the public key
        .route("/public_key", get(public_key))
        .route("/vote", post(vote))
        .layer(ServiceBuilder::new().layer(AddExtensionLayer::new(votes)));

    // start the server
    let listener = tokio::net::TcpListener::bind("0.0.0.0:7879").await.unwrap();
    axum::serve(listener, app).await.unwrap();
}

#[derive(serde::Serialize)]
struct PublicKeyResponse {
    public_key: String,
}

async fn public_key() -> Json<PublicKeyResponse> {
    // Load the PGP key from a file
    let key_data = fs::read_to_string(PUB_KEY_FILE).expect("Unable to read key file");
    // and return it
    Json(PublicKeyResponse {
        public_key: key_data
    })
}

#[derive(serde::Deserialize)]
struct VoteRequest {
    encrypted_vote: String,
}

#[derive(serde::Serialize, serde::Deserialize, Debug)]
struct VoteNonce {
    nonce: u64,
    vote: Vote,
}

#[derive(serde::Serialize, serde::Deserialize, Debug)]
struct Vote {
    name: String,
    party: String,
}

async fn vote(
    Extension(votes): Extension<Arc<Mutex<HashMap<String, HashMap<String, i64>>>>>,
    Json(VoteRequest { encrypted_vote }): Json<VoteRequest>
) {
    // change it into a normal string
    let encrypted_vote = urlencoding::decode(&encrypted_vote).expect("utf-8").into_owned();
    let cmd  = Command::new("echo")
        .arg(encrypted_vote)
        // pipe this output into the gpg command
        .stdout(Stdio::piped())
        .spawn()
        .expect("Failed to execute command");
    let encrypted_vote = Command::new("gpg")
        .arg("--decrypt")
        // read the output of the previous command
        .stdin(cmd.stdout.unwrap())
        // pipe this output
        .stdout(Stdio::piped())
        // remove extra output
        .stderr(Stdio::null())
        .spawn()
        .expect("Failed to execute command 2");
    // gets the output of the previous command
    let encrypted_vote = encrypted_vote.wait_with_output().expect("Failed to wait on child");
    // convert the output to a string
    // this is thus the decrypted vote
    let vote = std::str::from_utf8(&encrypted_vote.stdout).unwrap();
    // parse the vote
    let vote_n: VoteNonce = serde_json::from_str(vote).expect("Failed to parse vote");

    // add the vote
    votes.lock().unwrap()
        // get the party
        .entry(vote_n.vote.party.clone())
        // if the party does not exist, create a new hashmap
        .or_insert(HashMap::new())
        // get the party member
        .entry(vote_n.vote.name.clone())
        // if the party member does not exist, give em 0 votes
        .or_insert(0);

    // add 1 vote
    *votes.lock().unwrap()
        .get_mut(&vote_n.vote.party)
        .unwrap()
        .get_mut(&vote_n.vote.name)
        .unwrap() += 1;

    // debug print
    println!("cur_state: {:?}", votes.lock().unwrap());
}