use std::fs;

use axum::{Json, Router};
use axum::routing::get;

const PGP_KEY_FILE: &str = "key.asc";
const PUB_KEY_FILE: &str = "public_key.asc";



#[tokio::main]
async fn main() {
    // create a new instance of the application
    let app = Router::new()
        // the route for the public key
        .route("/public_key", get(public_key));

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

    Json(PublicKeyResponse {
        public_key: key_data
    })
}