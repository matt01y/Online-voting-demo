use std::sync::{Arc, Mutex};

use axum::{Extension, extract::Json, Router, routing::post, routing::get};
use tower::ServiceBuilder;
use tower_http::add_extension::AddExtensionLayer;

struct Voter {
    e_id: u64,
    public_key: String,
}

#[tokio::main]
async fn main() {
    let voters: Arc<Mutex<Vec<Voter>>> = Arc::new(Mutex::new(Vec::new()));

    let app = Router::new()
        .route("/login", post(login))
        .layer(ServiceBuilder::new().layer(AddExtensionLayer::new(voters.clone())))
        .route("/validate_voter", get(validate_voter))
        .layer(ServiceBuilder::new().layer(AddExtensionLayer::new(voters)));

    let listener = tokio::net::TcpListener::bind("0.0.0.0:7878").await.unwrap();
    axum::serve(listener, app).await.unwrap();
}

#[derive(serde::Deserialize)]
struct LoginRequest {
    e_id: u64,
    public_key: String,
}

#[derive(serde::Serialize)]
struct LoginResponse {
    voter_id: u64,
    message: String,
}


async fn login(
    Extension(voters): Extension<Arc<Mutex<Vec<Voter>>>>,
    Json(LoginRequest { e_id, public_key }): Json<LoginRequest>,
) -> Json<LoginResponse> {
    // this is a demo implementation, so we will just take a number as eID value
    // login with eID, and also send public key
    // responds with voter_id if good request.
    let mut voters = voters.lock().unwrap();
    if let Some(invoter) = voters.iter().enumerate().find(|invoter| invoter.1.e_id == e_id) {
        return Json(LoginResponse { voter_id: invoter.0 as u64, message: "eID already registered".to_string() });
    }
    voters.push(Voter { e_id, public_key: public_key.clone() });
    Json(LoginResponse { voter_id: (voters.len() - 1) as u64, message: "Successfully registered".to_string() })
}


#[derive(serde::Deserialize)]
struct ValidateVoteRequest {
    voter_id: u64,
    public_key: String,
}

#[derive(serde::Serialize)]
struct ValidateVoterResponse {
    message: ValidateVoterResponseMessage,
}

#[derive(serde::Serialize)]
enum ValidateVoterResponseMessage {
    ValidVoter,
    InvalidVoter,
}

async fn validate_voter(
    Extension(voters): Extension<Arc<Mutex<Vec<Voter>>>>,
    Json(ValidateVoteRequest { voter_id, public_key }): Json<ValidateVoteRequest>,
) -> Json<ValidateVoterResponse> {
    let voters = voters.lock().unwrap();
    if let Some(voter) = voters.get(voter_id as usize) {
        if voter.public_key == public_key {
            return Json(ValidateVoterResponse { message: ValidateVoterResponseMessage::ValidVoter });
        }
    }
    Json(ValidateVoterResponse { message: ValidateVoterResponseMessage::InvalidVoter })
}


