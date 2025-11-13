"""
Plugin Registry - Phase 0

Discovers and registers provider adapters dynamically.
Validates adapter interface conformance.

Usage:
    registry = PluginRegistry()
    registry.discover_adapters("path/to/adapters")
    adapter = registry.get_adapter("openai")
"""

import importlib
import importlib.util
import inspect
from pathlib import Path
from typing import Dict, Any, Protocol, Optional, List
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class AdapterPayload:
    """Standard payload sent to all adapters"""
    system: str
    state_summary: str
    user_query: str
    temperature: float = 0.2
    max_tokens: int = 800
    meta: Dict[str, Any] = None
    
    # Phase 3: Epistemic Snapshot Support (Cross-AI Context Transfer)
    epistemic_snapshot: Optional[Any] = None  # EpistemicStateSnapshot
    context_level: str = "minimal"  # minimal, standard, full
    
    def __post_init__(self):
        if self.meta is None:
            self.meta = {}
    
    def get_augmented_prompt(self) -> str:
        """
        Return prompt with epistemic context injected (if snapshot present)
        
        This method combines the user query with compressed epistemic state
        from a previous AI interaction, enabling cross-AI context continuity.
        
        Returns:
            Augmented prompt string with injected context (if snapshot present),
            otherwise returns original user_query
        """
        if not self.epistemic_snapshot:
            return self.user_query
        
        # Inject snapshot context before main prompt
        context = self.epistemic_snapshot.to_context_prompt(self.context_level)
        return f"{context}\n\n---\n\n{self.user_query}"


@dataclass
class AdapterResponse:
    """Standard response from adapters (PersonaEnforcer RESPONSE_SCHEMA)"""
    decision: str  # ACT|CHECK|INVESTIGATE|VERIFY
    confidence: float  # 0.0-1.0
    rationale: str
    vector_references: Dict[str, float]
    suggested_actions: List[str]
    fallback_needed: bool = False
    provider_meta: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.provider_meta is None:
            self.provider_meta = {}
        
        # Validate decision
        valid_decisions = {"ACT", "CHECK", "INVESTIGATE", "VERIFY"}
        if self.decision not in valid_decisions:
            raise ValueError(f"Invalid decision: {self.decision}. Must be one of {valid_decisions}")
        
        # Validate confidence
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"Invalid confidence: {self.confidence}. Must be between 0.0 and 1.0")


@dataclass
class AdapterError:
    """Error response from adapter"""
    code: str  # quota_exceeded|unauthorized|rate_limit|network|unknown
    message: str
    provider: str
    recoverable: bool = True
    meta: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.meta is None:
            self.meta = {}


class AdapterInterface(Protocol):
    """
    Protocol defining the required adapter interface.
    
    All adapters must implement these methods to be registered.
    """
    
    def health_check(self) -> bool:
        """
        Check if adapter is operational.
        
        Returns:
            bool: True if healthy, False otherwise
        """
        ...
    
    def authenticate(self, meta: Dict[str, Any]) -> Dict[str, Any]:
        """
        Request authentication from AuthManager.
        
        Args:
            meta: Metadata about the auth request (reason, scopes, etc.)
            
        Returns:
            Dict with token metadata
            
        Raises:
            Exception if authentication fails
        """
        ...
    
    def call(self, payload: AdapterPayload, token_meta: Dict[str, Any]) -> AdapterResponse | AdapterError:
        """
        Execute model call through this adapter.
        
        Args:
            payload: Standard adapter payload
            token_meta: Authentication token metadata
            
        Returns:
            AdapterResponse on success, AdapterError on failure
        """
        ...


class PluginRegistry:
    """
    Manages dynamic adapter discovery and registration.
    
    Discovers Python modules in adapter directories and validates
    they conform to the AdapterInterface protocol.
    """
    
    def __init__(self):
        self.adapters: Dict[str, Any] = {}
        self.adapter_metadata: Dict[str, Dict[str, Any]] = {}
        
    def register(self, name: str, adapter_class: type, metadata: Optional[Dict[str, Any]] = None):
        """
        Register an adapter manually.
        
        Args:
            name: Adapter identifier (e.g., "openai", "local", "copilot")
            adapter_class: Class implementing AdapterInterface
            metadata: Optional metadata (version, cost, description, etc.)
        """
        # Validate interface
        if not self._validates_interface(adapter_class):
            raise ValueError(f"Adapter {name} does not implement required interface")
        
        self.adapters[name] = adapter_class
        self.adapter_metadata[name] = metadata or {}
        logger.info(f"✅ Registered adapter: {name}")
    
    def _validates_interface(self, adapter_class: type) -> bool:
        """
        Check if adapter class implements required methods.
        
        Args:
            adapter_class: Class to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        required_methods = ['health_check', 'authenticate', 'call']
        
        for method_name in required_methods:
            if not hasattr(adapter_class, method_name):
                logger.error(f"Adapter missing required method: {method_name}")
                return False
            
            method = getattr(adapter_class, method_name)
            if not callable(method):
                logger.error(f"Adapter method not callable: {method_name}")
                return False
        
        return True
    
    def discover_adapters(self, adapter_dir: str | Path):
        """
        Discover and register adapters from a directory.
        
        Looks for Python modules matching *_adapter.py pattern.
        
        Args:
            adapter_dir: Directory to search for adapters
        """
        adapter_path = Path(adapter_dir)
        if not adapter_path.exists():
            logger.warning(f"Adapter directory not found: {adapter_dir}")
            return
        
        # Find adapter modules
        adapter_files = list(adapter_path.glob("*_adapter.py"))
        logger.info(f"🔍 Discovering adapters in {adapter_dir}")
        logger.info(f"   Found {len(adapter_files)} potential adapter modules")
        
        for adapter_file in adapter_files:
            try:
                self._load_adapter_module(adapter_file)
            except Exception as e:
                logger.error(f"Failed to load adapter {adapter_file.name}: {e}")
    
    def _load_adapter_module(self, module_path: Path):
        """
        Load a single adapter module and register it.
        
        Args:
            module_path: Path to adapter Python file
        """
        module_name = module_path.stem
        adapter_name = module_name.replace("_adapter", "")
        
        # Import module
        spec = importlib.util.spec_from_file_location(module_name, module_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Cannot load spec for {module_path}")
        
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Find adapter class (convention: {Provider}Adapter)
        adapter_class = None
        for name, obj in inspect.getmembers(module, inspect.isclass):
            if name.endswith("Adapter") and obj.__module__ == module_name:
                adapter_class = obj
                break
        
        if adapter_class is None:
            logger.warning(f"No adapter class found in {module_path.name}")
            return
        
        # Check for optional metadata
        metadata = {}
        if hasattr(module, "ADAPTER_METADATA"):
            metadata = module.ADAPTER_METADATA
        
        # Register
        self.register(adapter_name, adapter_class, metadata)
    
    def get_adapter(self, name: str, config: Optional[Dict[str, Any]] = None) -> Any:
        """
        Get an instantiated adapter by name.
        
        Args:
            name: Adapter identifier
            config: Optional configuration to pass to adapter constructor
            
        Returns:
            Instantiated adapter instance
            
        Raises:
            KeyError: If adapter not registered
        """
        if name not in self.adapters:
            raise KeyError(f"Adapter not found: {name}. Available: {list(self.adapters.keys())}")
        
        adapter_class = self.adapters[name]
        
        # Instantiate with config if constructor accepts it
        try:
            if config:
                return adapter_class(config)
            else:
                return adapter_class()
        except TypeError:
            # Constructor doesn't accept config, try without
            return adapter_class()
    
    def list_adapters(self) -> List[Dict[str, Any]]:
        """
        List all registered adapters with metadata.
        
        Returns:
            List of dicts with adapter info
        """
        result = []
        for name in self.adapters:
            info = {
                'name': name,
                'class': self.adapters[name].__name__,
                **self.adapter_metadata.get(name, {})
            }
            result.append(info)
        return result
    
    def health_check_all(self) -> Dict[str, bool]:
        """
        Run health checks on all registered adapters.
        
        Returns:
            Dict mapping adapter name to health status
        """
        results = {}
        for name in self.adapters:
            try:
                adapter = self.get_adapter(name)
                results[name] = adapter.health_check()
            except Exception as e:
                logger.error(f"Health check failed for {name}: {e}")
                results[name] = False
        return results
