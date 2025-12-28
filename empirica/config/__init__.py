"""
Empirica Configuration Module

Centralized configuration management for:
- API credentials (credentials_loader)
- Model selection
- Adapter configuration
- Investigation profiles
- Threshold profiles (MCO cascade styles)
"""

from .credentials_loader import get_credentials_loader, CredentialsLoader
from .profile_loader import load_profile, InvestigationProfile, InvestigationConstraints
from .threshold_loader import (
    ThresholdLoader,
    get_threshold_config,
    load_profile as load_threshold_profile,
    get_threshold,
    override_threshold
)
from .mco_loader import (
    MCOLoader,
    get_mco_config
)

__all__ = [
    'get_credentials_loader',
    'CredentialsLoader',
    'load_profile',
    'InvestigationProfile',
    'InvestigationConstraints',
    'ThresholdLoader',
    'get_threshold_config',
    'load_threshold_profile',
    'get_threshold',
    'override_threshold',
    'MCOLoader',
    'get_mco_config',
]
