# Palo Alto SCM Address Object Automation

This project provides a Python-based automation script for creating Address Objects in Palo Alto Networks Strata Cloud Manager (SCM) through the SCM API.
The initial version of the script required manually defining each Address Object directly in the Python code. The current implementation improves this approach by reading object definitions from a YAML file, making the solution more scalable, maintainable, and suitable for larger deployments.

## Features

* Create Address Objects through the SCM API
* Read object definitions from an external YAML file
* Validate YAML structure and required fields
* Validate IP/netmask values before execution
* OAuth Service Account authentication support
* Automatic access token generation and refresh
* Detailed logging and error handling
* Dry-run mode for validation before deployment
* Support for static tokens if required

## Repository Contents

| File                            | Description                             |
| ------------------------------- | --------------------------------------- |
| `create_address_objects.py`     | Current automated implementation        |
| `create_address_objects_old.py` | Original manual implementation          |
| `config.yaml.example`           | Example configuration file              |
| `devices.yaml.example`          | Example Address Objects definition file |

The original manual implementation has been preserved with the `_old` suffix to demonstrate the evolution of the solution from a manually maintained script to a fully data-driven approach.

## Requirements

Python 3.9+

Install dependencies:

```bash
pip install requests pyyaml
```

## Configuration

Create a `config.yaml` file based on the provided example:

```yaml
auth:
  client_id: "your-service-account@your-tsg-id.iam.panserviceaccount.com"
  client_secret: "your-client-secret"
  token_url: "https://auth.apps.paloaltonetworks.com/auth/v1/oauth2/access_token"
  scope: "tsg_id:your-tsg-id"

objects_file: "devices.yaml"
```

Alternatively, a static token can be used:

```yaml
token: "your-access-token"

objects_file: "devices.yaml"
```

## Address Object Definition File

Example `devices.yaml`:

```yaml
objects:
  - name: Internal_1
    folder: Azure-SEE
    ip_netmask: 10.10.10.1/32

  - name: Internal_2
    folder: Azure-SEE
    ip_netmask: 10.10.10.2/32
```

## Usage

Create Address Objects:

```bash
python create_address_objects.py --config config.yaml
```

Run validation without creating objects:

```bash
python create_address_objects.py --config config.yaml --dry-run
```

Enable verbose logging:

```bash
python create_address_objects.py --config config.yaml --verbose
```

## Example Workflow

1. Define Address Objects in `devices.yaml`
2. Configure authentication in `config.yaml`
3. Run the script
4. Review logs for successful object creation

## Why This Project?

The main goal of this project is to reduce repetitive manual work when creating large numbers of Address Objects.

Instead of modifying Python code every time a new object is required, object definitions can simply be added to a YAML file while the automation handles the API interactions.

This approach provides:

* Better scalability
* Reduced risk of human error
* Easier maintenance
* Cleaner separation between data and code

## Disclaimer

This project is provided as-is for educational and automation purposes. Test thoroughly in your own environment before using it in production.

## Contributions

Feedback, suggestions, and improvements are always welcome.

