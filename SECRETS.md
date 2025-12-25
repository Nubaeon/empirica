# Secrets Management

This project uses [Doppler](https://www.doppler.com/) for secrets management.

## Running Commands with Secrets

To run commands that need access to secrets:

```bash
doppler run -- your-command-here
```

## Examples

```bash
# Run Python application with secrets
doppler run -- python app.py

# Run tests with secrets
doppler run -- python -m pytest

# Run shell script with secrets
doppler run -- bash deploy.sh
```

## Configuration

This project is configured to use:
- Project: `test-doppler-project`
- Config: `dev`

## Adding New Secrets

To add new secrets, visit the Doppler dashboard for this project and add them there.
Do not commit secrets to the repository directly.
