#!/usr/bin/env python3

import argparse
import ipaddress
import logging
import sys
import time
from typing import Dict, Optional, List

import requests
import yaml


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


# SCM API Configuration
SCM_BASE_URL = "https://api.strata.paloaltonetworks.com/config/objects/v1"
ADDRESS_OBJECTS_ENDPOINT = f"{SCM_BASE_URL}/addresses"


class TokenManager:
    def __init__(self, auth_config: Optional[Dict] = None, static_token: Optional[str] = None):
        self.auth_config = auth_config
        self.token = static_token
        self.token_expiry = 0

    def get_token(self) -> str:
        if self.token and not self.auth_config:
            return self.token

        if self.auth_config:
            current_time = time.time()
            if current_time >= self.token_expiry - 60:
                self.token = self._generate_token()

        if not self.token:
            raise ValueError("No valid token available")

        return self.token

    def _generate_token(self) -> str:
        logger.info("Generating new access token...")

        token_url = self.auth_config.get("token_url")
        client_id = self.auth_config.get("client_id")
        client_secret = self.auth_config.get("client_secret")
        scope = self.auth_config.get("scope")

        if not all([token_url, client_id, client_secret]):
            raise ValueError("Missing auth fields: token_url, client_id, client_secret")

        data = {
            "grant_type": "client_credentials"
        }

        if scope:
            data["scope"] = scope

        response = requests.post(
            token_url,
            auth=(client_id, client_secret),
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=30
        )

        response.raise_for_status()

        token_data = response.json()
        access_token = token_data.get("access_token")
        expires_in = token_data.get("expires_in", 900)

        if not access_token:
            raise ValueError("No access_token in token response")

        self.token_expiry = time.time() + expires_in

        logger.info(f"Access token generated successfully, expires in {expires_in} seconds")
        return access_token

    def invalidate_token(self):
        logger.info("Invalidating current token")
        self.token_expiry = 0


def load_config(filepath: str) -> Dict:
    logger.info(f"Loading configuration from {filepath}")

    try:
        with open(filepath, "r") as f:
            config = yaml.safe_load(f)

    except FileNotFoundError:
        logger.error(f"Configuration file not found: {filepath}")
        raise

    except yaml.YAMLError as e:
        logger.error(f"Error parsing configuration file: {e}")
        raise

    if not isinstance(config, dict):
        raise ValueError("Config YAML must contain a dictionary")

    has_static_token = bool(config.get("token"))
    has_auth_config = bool(config.get("auth"))

    if not has_static_token and not has_auth_config:
        raise ValueError("Provide either 'token' or 'auth' in config.yaml")

    if has_auth_config:
        auth_required_fields = ["client_id", "client_secret", "token_url"]
        auth_config = config["auth"]

        missing_auth_fields = [
            field for field in auth_required_fields
            if not auth_config.get(field)
        ]

        if missing_auth_fields:
            raise ValueError(
                f"Missing required auth fields: {', '.join(missing_auth_fields)}"
            )

        if not auth_config.get("scope"):
            logger.warning("No scope provided. Recommended format: tsg_id:<your-tsg-id>")

    if not config.get("objects_file"):
        raise ValueError("Missing required field in config.yaml: objects_file")

    logger.info("Configuration loaded successfully")
    return config


def load_objects_yaml(filepath: str) -> List[Dict]:
    logger.info(f"Loading address objects from {filepath}")

    try:
        with open(filepath, "r") as f:
            data = yaml.safe_load(f)

    except FileNotFoundError:
        logger.error(f"Objects file not found: {filepath}")
        raise

    except yaml.YAMLError as e:
        logger.error(f"Error parsing objects YAML file: {e}")
        raise

    if not isinstance(data, dict):
        raise ValueError("Objects YAML root must be a dictionary")

    if "objects" not in data:
        raise ValueError("Objects YAML missing required key: objects")

    objects = data["objects"]

    if not isinstance(objects, list):
        raise ValueError("'objects' must be a list")

    required_fields = ["name", "folder", "ip_netmask"]

    for index, obj in enumerate(objects, start=1):
        if not isinstance(obj, dict):
            raise ValueError(f"Object #{index} must be a dictionary")

        missing_fields = [
            field for field in required_fields
            if field not in obj or obj[field] in [None, ""]
        ]

        if missing_fields:
            raise ValueError(
                f"Object #{index} missing required fields: {', '.join(missing_fields)}"
            )

        try:
            ipaddress.ip_network(obj["ip_netmask"], strict=False)
        except ValueError:
            raise ValueError(
                f"Object #{index} has invalid ip_netmask: {obj['ip_netmask']}"
            )

    logger.info(f"Successfully loaded {len(objects)} address objects")
    return objects


def create_address_object(
    token_manager: TokenManager,
    obj: Dict,
    dry_run: bool = False,
    retry_on_401: bool = True
) -> bool:

    payload = {
        "name": obj["name"],
        "folder": obj["folder"],
        "ip_netmask": obj["ip_netmask"]
    }

    if dry_run:
        logger.info(f"[DRY RUN] Would create address object: {payload}")
        return True

    token = token_manager.get_token()

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": f"Bearer {token}"
    }

    logger.info(
        f"Creating address object '{obj['name']}' "
        f"in folder '{obj['folder']}' "
        f"with IP '{obj['ip_netmask']}'"
    )

    try:
        response = requests.post(
            ADDRESS_OBJECTS_ENDPOINT,
            json=payload,
            headers=headers,
            timeout=30
        )

        if response.status_code == 401 and retry_on_401:
            logger.warning("Received 401 Unauthorized. Regenerating token and retrying...")
            token_manager.invalidate_token()
            return create_address_object(
                token_manager,
                obj,
                dry_run=dry_run,
                retry_on_401=False
            )

        if response.status_code == 429:
            retry_after = int(response.headers.get("Retry-After", 5))
            logger.warning(f"Rate limited. Retrying after {retry_after} seconds...")
            time.sleep(retry_after)
            return create_address_object(
                token_manager,
                obj,
                dry_run=dry_run,
                retry_on_401=retry_on_401
            )

        if response.ok:
            logger.info(f"Successfully created address object '{obj['name']}'")
            return True

        logger.error(
            f"Failed to create address object '{obj['name']}' "
            f"({response.status_code}) {response.text}"
        )
        return False

    except requests.RequestException as e:
        logger.error(f"Request failed for object '{obj['name']}': {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Create address objects in Strata Cloud Manager"
    )

    parser.add_argument(
        "--config",
        required=True,
        help="Path to config YAML file"
    )

    parser.add_argument(
        "--objects",
        help="Optional path to objects YAML file. Overrides objects_file from config.yaml"
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate and show payloads without sending API requests"
    )

    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable debug logging"
    )

    args = parser.parse_args()

    if args.verbose:
        logger.setLevel(logging.DEBUG)

    try:
        config = load_config(args.config)

        objects_file = args.objects or config["objects_file"]

        static_token = config.get("token")
        auth_config = config.get("auth")

        token_manager = TokenManager(
            auth_config=auth_config,
            static_token=static_token
        )

        objects = load_objects_yaml(objects_file)

        total_objects = len(objects)
        success_count = 0

        logger.info(f"Starting address object creation for {total_objects} objects")

        for obj in objects:
            if create_address_object(token_manager, obj, dry_run=args.dry_run):
                success_count += 1

        logger.info(
            f"Completed: {success_count}/{total_objects} objects successful"
        )

        if success_count < total_objects:
            sys.exit(1)

    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
        sys.exit(1)

    except Exception as e:
        logger.error(f"Error: {e}")

        if args.verbose:
            import traceback
            traceback.print_exc()

        sys.exit(1)


if __name__ == "__main__":
    main()