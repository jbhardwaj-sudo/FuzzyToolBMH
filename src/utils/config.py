from typing import Dict, Any
import json
import os

class Config:
    """
    Configuration management for the fuzzy matching tool.
    """
    
    DEFAULT_CONFIG = {
        'matching': {
            'algorithm': 'ratio',
            'threshold': 80,
            'max_matches': 5
        },
        'weights': {},
        'preprocessing': {
            'clean_text': True,
            'handle_missing': 'fill_empty'
        },
        'output': {
            'format': 'xlsx',
            'include_scores': True
        }
    }
    
    def __init__(self, config_path: str = None):
        """
        Initialize configuration, optionally loading from a file.
        
        Args:
            config_path: Path to configuration JSON file
        """
        self._config = self.DEFAULT_CONFIG.copy()
        if config_path and os.path.exists(config_path):
            self.load_config(config_path)
    
    def load_config(self, config_path: str) -> None:
        """
        Load configuration from JSON file.
        
        Args:
            config_path: Path to configuration file
        """
        try:
            with open(config_path, 'r') as f:
                loaded_config = json.load(f)
                self._config.update(loaded_config)
        except Exception as e:
            raise ValueError(f"Error loading configuration: {str(e)}")
    
    def save_config(self, config_path: str) -> None:
        """
        Save current configuration to JSON file.
        
        Args:
            config_path: Path to save configuration file
        """
        try:
            with open(config_path, 'w') as f:
                json.dump(self._config, f, indent=4)
        except Exception as e:
            raise ValueError(f"Error saving configuration: {str(e)}")
    
    def update_config(self, updates: Dict[str, Any]) -> None:
        """
        Update configuration with new values.
        
        Args:
            updates: Dictionary of configuration updates
        """
        def deep_update(d: Dict[str, Any], u: Dict[str, Any]) -> Dict[str, Any]:
            for k, v in u.items():
                if isinstance(v, dict) and k in d and isinstance(d[k], dict):
                    deep_update(d[k], v)
                else:
                    d[k] = v
            return d
        
        self._config = deep_update(self._config, updates)
    
    def get_config(self) -> Dict[str, Any]:
        """
        Get current configuration.
        
        Returns:
            Dictionary containing current configuration
        """
        return self._config.copy()
    
    def get_matching_config(self) -> Dict[str, Any]:
        """Get matching-specific configuration."""
        return self._config['matching'].copy()
    
    def get_weights(self) -> Dict[str, float]:
        """Get field weights configuration."""
        return self._config['weights'].copy()
    
    def set_weights(self, weights: Dict[str, float]) -> None:
        """
        Set field weights configuration.
        
        Args:
            weights: Dictionary mapping field names to weights
        """
        # Validate weights
        if not all(isinstance(w, (int, float)) and w >= 0 for w in weights.values()):
            raise ValueError("All weights must be non-negative numbers")
        
        self._config['weights'] = weights.copy()
    
    def validate_config(self) -> bool:
        """
        Validate current configuration.
        
        Returns:
            True if valid, raises ValueError if not
        """
        # Validate matching config
        matching = self._config.get('matching', {})
        if not all(k in matching for k in ['algorithm', 'threshold', 'max_matches']):
            raise ValueError("Missing required matching configuration parameters")
        
        if not isinstance(matching['threshold'], (int, float)) or \
           not 0 <= matching['threshold'] <= 100:
            raise ValueError("Threshold must be a number between 0 and 100")
        
        if not isinstance(matching['max_matches'], int) or matching['max_matches'] < 1:
            raise ValueError("max_matches must be a positive integer")
        
        # Validate weights
        weights = self._config.get('weights', {})
        if not all(isinstance(w, (int, float)) and w >= 0 for w in weights.values()):
            raise ValueError("All weights must be non-negative numbers")
        
        return True
