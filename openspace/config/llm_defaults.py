"""LLM default configuration.

Centralized default model configuration for OpenSpace.
All modules should import defaults from here instead of hardcoding.
"""

import os
from typing import Optional


def get_default_model() -> str:
    """Get the default LLM model name.
    
    Resolution order (highest -> lowest priority):
    1. OPENSPACE_MODEL environment variable
    2. openspace_config.json (llm.default_model with env var support)
    3. Built-in fallback: minimax/MiniMax-M2.7
    
    Returns:
        Default model identifier string
    """
    # 1. Check environment variable first
    env_model = os.environ.get("OPENSPACE_MODEL", "").strip()
    if env_model:
        return env_model
    
    # 2. Try to load from openspace_config.json
    try:
        from pathlib import Path
        import json
        
        # Look for openspace_config.json in project root
        project_root = Path(__file__).resolve().parent.parent.parent
        config_path = project_root / "openspace_config.json"
        
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            llm_config = config.get("llm", {})
            default_model = llm_config.get("default_model", "")
            
            # Handle ${ENV_VAR:-default} syntax
            if default_model.startswith("${") and default_model.endswith("}"):
                # Extract ENV_VAR and default value
                inner = default_model[2:-1]  # Remove ${ and }
                if ":-" in inner:
                    env_var, default_val = inner.split(":-", 1)
                elif ":" in inner:
                    env_var, default_val = inner.split(":", 1)
                else:
                    env_var, default_val = inner, ""
                
                env_value = os.environ.get(env_var, "").strip()
                if env_value:
                    return env_value
                return default_val
            elif default_model:
                return default_model
    except Exception:
        pass
    
    # 3. Built-in fallback
    return "minimax/MiniMax-M2.7"


def get_default_api_key() -> Optional[str]:
    """Get the default API key from environment or config."""
    # Check environment variable first
    env_key = os.environ.get("MINIMAX_API_KEY", "").strip()
    if env_key:
        return env_key
    
    # Try to load from openspace_config.json
    try:
        from pathlib import Path
        import json
        
        project_root = Path(__file__).resolve().parent.parent.parent
        config_path = project_root / "openspace_config.json"
        
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            llm_config = config.get("llm", {})
            api_key_config = llm_config.get("default_api_key", "")
            
            # Handle ${ENV_VAR} syntax
            if api_key_config.startswith("${") and api_key_config.endswith("}"):
                env_var = api_key_config[2:-1]
                return os.environ.get(env_var) or None
            elif api_key_config:
                return api_key_config
    except Exception:
        pass
    
    return None


def get_default_api_base() -> str:
    """Get the default API base URL from environment or config."""
    # Check environment variable first
    env_base = os.environ.get("MINIMAX_API_BASE", "").strip()
    if env_base:
        return env_base
    
    # Try to load from openspace_config.json
    try:
        from pathlib import Path
        import json
        
        project_root = Path(__file__).resolve().parent.parent.parent
        config_path = project_root / "openspace_config.json"
        
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            llm_config = config.get("llm", {})
            api_base_config = llm_config.get("default_api_base", "")
            
            # Handle ${ENV_VAR:-default} syntax
            if api_base_config.startswith("${") and api_base_config.endswith("}"):
                inner = api_base_config[2:-1]
                if ":-" in inner:
                    env_var, default_val = inner.split(":-", 1)
                elif ":" in inner:
                    env_var, default_val = inner.split(":", 1)
                else:
                    env_var, default_val = inner, ""
                
                env_value = os.environ.get(env_var, "").strip()
                if env_value:
                    return env_value
                return default_val
            elif api_base_config:
                return api_base_config
    except Exception:
        pass
    
    return "https://api.minimaxi.chat/v1"


# Module-level constants for convenience
# These are resolved at import time based on current environment
DEFAULT_MODEL = get_default_model()
DEFAULT_API_KEY = get_default_api_key()
DEFAULT_API_BASE = get_default_api_base()


__all__ = [
    "get_default_model",
    "get_default_api_key",
    "get_default_api_base",
    "DEFAULT_MODEL",
    "DEFAULT_API_KEY",
    "DEFAULT_API_BASE",
]
