# Doppler Secrets Management Guide for AI Agents

## Overview
This document provides guidance for AI agents on using Doppler for secrets management in this environment. Doppler is integrated into the project workflow to securely manage environment variables and secrets.

## Core Commands

### Running Applications with Secrets
Use `doppler run` to execute applications with secrets injected from Doppler:

```bash
# Run a command with Doppler secrets
doppler run -- your-command-here

# Example: Run a Python application with secrets
doppler run -- python app.py

# Example: Run a shell script with secrets
doppler run -- bash deploy.sh
```

### Project Setup
Each project is configured to work with Doppler through the `.doppler.yaml` configuration file:

```bash
# Initialize Doppler for a new project
doppler setup --project <project-name> --config <config-name>

# Example setup for a development environment
doppler setup --project my-project --config dev
```

## Project Integration

### Git Repository Integration
Doppler is tied to git repositories with the following structure:
- Each git repository has its own Doppler project
- Configuration environments (dev/stage/prod) map to git branches or deployment targets
- The `.doppler.yaml` file in each repository specifies the project and configuration to use

### Environment Variables
- Secrets are accessed through environment variables automatically
- No need to manually manage environment variable files
- Automatic fallback handling when running outside configured environments

## Security Best Practices for AI Agents

### 1. Don't Hardcode Secrets
- Never write secrets to files, code, or logs
- Always use `doppler run` to access secrets in environment variables
- If you need to reference secrets in output, they will be automatically masked

### 2. Use Appropriate Scopes
- Only access Doppler projects that are relevant to your assigned tasks
- Don't attempt to access secrets for projects outside your scope
- Respect the principle of least privilege

### 3. Log Management
- Avoid including secret values in logs, error messages, or output
- Doppler automatically masks secrets in output when possible
- Be cautious when echoing or printing environment variables

### 4. Session Management
- Secrets are only accessible during a `doppler run` session
- Don't attempt to extract or cache secrets outside of Doppler's secure context
- Each command execution should be a new `doppler run` invocation when secrets are needed

## Common Use Cases

### Starting Services
```bash
# Start your application with secrets
doppler run -- npm start
doppler run -- python manage.py runserver
doppler run -- ./start-service.sh
```

### Running Scripts
```bash
# Execute scripts that need secrets
doppler run -- python script.py
doppler run -- bash automation.sh
```

### Development Workflow
```bash
# Set up a new project with Doppler
doppler setup --project my-repo-name --config dev
doppler run -- make setup
doppler run -- make test
```

## Troubleshooting

### Missing Secrets Error
If you encounter "environment variable not found" errors:
1. Ensure you're using `doppler run -- your-command`
2. Verify the `.doppler.yaml` file exists and is properly configured
3. Confirm you have access to the specified project and config

### Configuration Issues
If Doppler configuration seems incorrect:
1. Check the `.doppler.yaml` file in the project root
2. Verify the project and config names match Doppler setup
3. Contact system administrators to confirm access permissions

## Important Notes
- Always use `doppler run` when your commands need to access secrets
- Secrets are never stored in the git repository itself
- The system will automatically use the correct configuration based on the project context
- For local development, make sure to run `doppler setup` first to configure your local environment