use std::sync::{Arc, Mutex};

use axum::{extract::Json, routing::get, routing::post, Extension, Router};
use tower::ServiceBuilder;
use tower_http::add_extension::AddExtensionLayer;

const EID_PREFIX: &str = "BE-";

struct Voter {
    e_id: String,
    public_key: String,
}

#[tokio::main]
async fn main() {
    // This is our state of registered voters, a list of voters
    // We use Arc<Mutex<...>> to share it between requests thread safe
    let voters: Arc<Mutex<Vec<Voter>>> = Arc::new(Mutex::new(Vec::new()));

    let app = Router::new()
        // This routes post request to /login to the login function
        .route("/login", post(login))
        // This makes it possible to use the voters in the login function
        .layer(ServiceBuilder::new().layer(AddExtensionLayer::new(voters.clone())))
        .route("/validate_voter", get(validate_voter))
        .layer(ServiceBuilder::new().layer(AddExtensionLayer::new(voters)));

    let listener = tokio::net::TcpListener::bind("0.0.0.0:7878").await.unwrap();
    axum::serve(listener, app).await.unwrap();
}

#[derive(serde::Deserialize)]
struct LoginRequest {
    e_id: String,
    public_key: String,
}

#[derive(serde::Serialize)]
struct LoginResponse {
    voter_id: Option<u64>,
    message: String,
}

async fn login(
    // This is so that we can access the voters in the function that was passed in the router
    Extension(voters): Extension<Arc<Mutex<Vec<Voter>>>>,
    // This parses the request body as json into the LoginRequest struct (sends error response if it fails)
    Json(LoginRequest { e_id, public_key }): Json<LoginRequest>,
) -> Json<LoginResponse> {
    // We answer with a json that is serialized from LoginResponse
    // this is a demo implementation, so we will just take a number as eID value
    // login with eID, and also send public key
    // responds with voter_id if good request.

    // check if eID is valid
    if !e_id.starts_with(EID_PREFIX) {
        return Json(LoginResponse {
            voter_id: None,
            message: "Invalid eID".to_string(),
        });
    }

    // claim the voters mutex
    let mut voters = voters.lock().unwrap();
    // check if eID is already registered
    if let Some((index, _)) = voters
        .iter()
        .enumerate()
        .find(|(_, voter)| voter.e_id == e_id)
    {
        return Json(LoginResponse {
            voter_id: Some(index as u64),
            message: "eID already registered".to_string(),
        });
    }
    // register the voter
    voters.push(Voter {
        e_id,
        public_key: public_key.clone(),
    });
    Json(LoginResponse {
        voter_id: Some((voters.len() - 1) as u64),
        message: "Successfully registered".to_string(),
    })
}

#[derive(serde::Deserialize)]
struct ValidateVoteRequest {
    voter_id: u64,
}

#[derive(serde::Serialize)]
struct ValidateVoterResponse {
    message: ValidateVoterResponseMessage,
}

#[derive(serde::Serialize)]
enum ValidateVoterResponseMessage {
    PublicKey(String),
    InvalidVoterID,
}

async fn validate_voter(
    Extension(voters): Extension<Arc<Mutex<Vec<Voter>>>>,
    Json(ValidateVoteRequest {
        voter_id,
    }): Json<ValidateVoteRequest>,
) -> Json<ValidateVoterResponse> {
    let voters = voters.lock().unwrap();
    // check if voter_id is valid
    if let Some(voter) = voters.get(voter_id as usize) {
        // send this voter's public key
        return Json(ValidateVoterResponse {
            message: ValidateVoterResponseMessage::PublicKey(voter.public_key.clone()),
        });
    }
    // Let em know that the voter_id is invalid
    Json(ValidateVoterResponse {
        message: ValidateVoterResponseMessage::InvalidVoterID,
    })
}
