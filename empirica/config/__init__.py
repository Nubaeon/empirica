"""
Empirica Configuration Module

Centralized configuration management for:
- API credentials (credentials_loader)
- Model selection
- Adapter configuration
- Investigation profiles
"""

from .credentials_loader import get_credentials_loader, CredentialsLoader
from .profile_loader import load_profile, InvestigationProfile, InvestigationConstraints

__all__ = [
    'get_credentials_loader',
    'CredentialsLoader',
    'load_profile',
    'InvestigationProfile',
    'InvestigationConstraints',
]
