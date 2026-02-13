"""
Empirica Configuration Module

Centralized configuration management for:
- API credentials (credentials_loader)
- Model selection
- Adapter configuration
- Investigation profiles
- Threshold profiles (MCO cascade styles)
"""

# Lazy imports — submodules loaded on first access only.
# path_resolver consumers (statusline, hooks) should not pay for
# credentials_loader, profile_loader, threshold_loader, mco_loader.

_LAZY_IMPORTS = {
    'get_credentials_loader': ('.credentials_loader', 'get_credentials_loader'),
    'CredentialsLoader': ('.credentials_loader', 'CredentialsLoader'),
    'load_profile': ('.profile_loader', 'load_profile'),
    'InvestigationProfile': ('.profile_loader', 'InvestigationProfile'),
    'InvestigationConstraints': ('.profile_loader', 'InvestigationConstraints'),
    'ThresholdLoader': ('.threshold_loader', 'ThresholdLoader'),
    'get_threshold_config': ('.threshold_loader', 'get_threshold_config'),
    'load_threshold_profile': ('.threshold_loader', 'load_profile'),
    'get_threshold': ('.threshold_loader', 'get_threshold'),
    'override_threshold': ('.threshold_loader', 'override_threshold'),
    'MCOLoader': ('.mco_loader', 'MCOLoader'),
    'get_mco_config': ('.mco_loader', 'get_mco_config'),
}


def __getattr__(name):
    if name in _LAZY_IMPORTS:
        module_path, attr_name = _LAZY_IMPORTS[name]
        import importlib
        mod = importlib.import_module(module_path, __package__)
        return getattr(mod, attr_name)
    raise AttributeError(f"module 'empirica.config' has no attribute {name!r}")


__all__ = list(_LAZY_IMPORTS.keys())
