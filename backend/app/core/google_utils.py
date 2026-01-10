import os
import logging
import json

logger = logging.getLogger("uvicorn.info")

def setup_google_credentials():
    """
    Restores Google Credentials files from environment variables.
    Useful for production environments (like Railway) where file-based secrets
    should not be committed to the repo.
    """
    logger.info("Initializing Google Credentials...")

    # 1. Restore Service Account JSON (For Google Cloud Services: STT, etc.)
    service_account_json = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")
    if service_account_json:
        try:
            logger.info("Found GOOGLE_SERVICE_ACCOUNT_JSON. Restoring 'google_credentials.json'...")
            # Validate JSON first
            try:
                if isinstance(service_account_json, str):
                     # Check if it's a stringified JSON or just the JSON content
                     # If it starts with {, it's likely content
                     if not service_account_json.strip().startswith('{'):
                         # If it's base64 or something else, we might need decoding, 
                         # but usually in Railway it's the raw JSON text.
                         pass
                     
                     # Simple check if it's parseable
                     json.loads(service_account_json)

            except json.JSONDecodeError:
                logger.warning("GOOGLE_SERVICE_ACCOUNT_JSON env var might not be valid JSON.")
            
            with open("backend/google_credentials.json", "w") as f:
                f.write(service_account_json)
            
            # Set GOOGLE_APPLICATION_CREDENTIALS to point to this file
            # This is what google.auth.default() looks for by default
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.path.abspath("backend/google_credentials.json")
            logger.info(f"Set GOOGLE_APPLICATION_CREDENTIALS to {os.environ['GOOGLE_APPLICATION_CREDENTIALS']}")
            
        except Exception as e:
            logger.error(f"Failed to restore google_credentials.json: {e}")
    else:
        logger.info("No GOOGLE_SERVICE_ACCOUNT_JSON env var found.")

    # 2. Restore User Token JSON (For Calendar OAuth delegation)
    token_json = os.environ.get("GOOGLE_TOKEN_JSON")
    if token_json:
        try:
            logger.info("Found GOOGLE_TOKEN_JSON. Restoring 'token.json'...")
            with open("token.json", "w") as f:
                f.write(token_json)
        except Exception as e:
            logger.error(f"Failed to restore token.json: {e}")
    else:
        logger.info("No GOOGLE_TOKEN_JSON env var found.")
