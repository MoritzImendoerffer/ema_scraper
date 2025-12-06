"""Load configuration from YAML file."""

from pathlib import Path
import yaml

def load_config(config_path: Path) -> dict:
    """Load config from YAML file."""
    if config_path is None:
        config_path = Path(__file__).parent / "config.yaml"
    
    with open(config_path) as f:
        return yaml.safe_load(f)