"""
Configuration Utilities - High-level utilities for fabric configuration management
Contains YAML/JSON processing, config merging, and build-specific functions.
Used by build_fabric.py for configuration processing.
"""
import yaml
import json
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path

def load_yaml_file(filepath: str) -> Optional[Dict[str, Any]]:
    """Load a YAML file and return its content."""
    try:
        with open(filepath, 'r', encoding='utf-8') as file:
            return yaml.safe_load(file)
    except FileNotFoundError:
        print(f"Error: YAML file not found at {filepath}")
        return None
    except yaml.YAMLError as e:
        print(f"Error parsing YAML file {filepath}: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error loading YAML file {filepath}: {e}")
        return None

def load_json_file(filepath: str) -> Optional[Dict[str, Any]]:
    """Load a JSON file and return its content."""
    try:
        with open(filepath, 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        print(f"Error: JSON file not found at {filepath}")
        return None
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON file {filepath}: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error loading JSON file {filepath}: {e}")
        return None

def save_yaml_file(data: Dict[str, Any], filepath: str) -> bool:
    """Save data to a YAML file."""
    try:
        with open(filepath, 'w', encoding='utf-8') as file:
            yaml.dump(data, file, default_flow_style=False, indent=2)
        return True
    except Exception as e:
        print(f"Error saving YAML file {filepath}: {e}")
        return False

def save_json_file(data: Dict[str, Any], filepath: str, indent: int = 2) -> bool:
    """Save data to a JSON file."""
    try:
        with open(filepath, 'w', encoding='utf-8') as file:
            json.dump(data, file, indent=indent)
        return True
    except Exception as e:
        print(f"Error saving JSON file {filepath}: {e}")
        return False

def merge_configs(base_config: Dict[str, Any], override_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Recursively merge two configurations with override taking precedence.
    Used for merging default configs with specific fabric configurations.
    """
    if not isinstance(base_config, dict) or not isinstance(override_config, dict):
        return override_config if override_config else base_config
    
    merged = base_config.copy()
    for key, value in override_config.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = merge_configs(merged[key], value)
        else:
            merged[key] = value
    return merged

def flatten_config(nested_config: Dict[str, Any], parent_key: str = '', separator: str = '_') -> Dict[str, Any]:
    """
    Flatten a nested dictionary into a single-level dictionary.
    Used for converting hierarchical YAML configs to API-ready format.
    """
    if not isinstance(nested_config, dict):
        return {parent_key: nested_config} if parent_key else {}
    
    items = []
    for key, value in nested_config.items():
        new_key = f"{parent_key}{separator}{key}" if parent_key else key
        if isinstance(value, dict):
            items.extend(flatten_config(value, new_key, separator).items())
        else:
            items.append((new_key, value))
    return dict(items)

def apply_field_mapping(config: Dict[str, Any], mapping: Dict[str, Any]) -> Dict[str, Any]:
    """
    Apply field mapping to transform configuration keys to API format.
    Maps YAML configuration keys to NDFC API field names.
    """
    if not isinstance(mapping, dict):
        return config
    
    mapped_config = {}
    for key, value in config.items():
        if key in mapping and mapping[key] is not None:
            mapped_config[mapping[key]] = value
        elif key not in mapping:
            # Keep unmapped fields as-is
            mapped_config[key] = value
    return mapped_config

def get_nested_value(config_dict: Dict[str, Any], keys: Tuple[str, ...]) -> Any:
    """
    Get a nested value from a dictionary using a tuple of keys.
    Safely traverses nested dictionary structures.
    """
    if not isinstance(config_dict, dict) or not keys:
        return None
    
    value = config_dict
    for key in keys:
        if isinstance(value, dict) and key in value:
            value = value[key]
        else:
            return None
    return value

def get_template_name(fabric_type: str, template_mapping_file: str) -> Optional[str]:
    """
    Get the template name from the mapping file based on fabric type.
    Maps fabric types to their corresponding NDFC templates.
    """
    templates = load_yaml_file(template_mapping_file)
    if templates:
        return templates.get(fabric_type)
    return None

def validate_file_exists(filepath: str) -> bool:
    """Check if a file exists."""
    return Path(filepath).exists()

def validate_configuration_files(file_paths: List[str]) -> Tuple[bool, List[str]]:
    """
    Validate that all required configuration files exist.
    Returns tuple of (all_exist, missing_files).
    """
    missing_files = [f for f in file_paths if not Path(f).exists()]
    return len(missing_files) == 0, missing_files

def read_freeform_config(file_path: str) -> str:
    """
    Read the content of a freeform configuration file.
    Handles special formatting for banner configurations.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Special handling for banner files
        if "Banner.sh" in file_path:
            content = "`" + content + "`"
            
        return content
    except FileNotFoundError:
        print(f"Warning: Freeform config file not found at {file_path}")
        return ""
    except Exception as e:
        print(f"Error reading freeform config {file_path}: {e}")
        return ""

def parse_freeform_config(file_path: str) -> str:
    """
    Legacy alias for read_freeform_config for backward compatibility.
    Use read_freeform_config instead.
    """
    return read_freeform_config(file_path)

def create_backup_config(original_config: Dict[str, Any], backup_dir: str = "backups") -> str:
    """
    Create a backup of configuration before modifications.
    Returns the backup file path.
    """
    import datetime
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"config_backup_{timestamp}.json"
    
    Path(backup_dir).mkdir(exist_ok=True)
    backup_path = Path(backup_dir) / backup_filename
    
    if save_json_file(original_config, str(backup_path)):
        print(f"Configuration backed up to: {backup_path}")
        return str(backup_path)
    else:
        print("Failed to create configuration backup")
        return ""

def extract_child_fabrics_config(config_dict: Dict[str, Any]) -> Dict[str, List[str]]:
    """
    Extract child fabric information from MSD configuration.
    Returns dictionary with 'regular_fabrics' and 'isn_fabrics' keys.
    """
    child_fabric_config = config_dict.get("Child Fabric", {})
    
    # Extract regular fabrics
    regular_fabrics = child_fabric_config.get("Fabric", [])
    if isinstance(regular_fabrics, str):
        regular_fabrics = [regular_fabrics]
    elif not isinstance(regular_fabrics, list):
        regular_fabrics = []
    
    # Extract ISN fabrics
    isn_fabrics = child_fabric_config.get("ISN", [])
    if isinstance(isn_fabrics, str):
        isn_fabrics = [isn_fabrics]
    elif not isinstance(isn_fabrics, list):
        isn_fabrics = []
    
    return {
        "regular_fabrics": regular_fabrics,
        "isn_fabrics": isn_fabrics
    }

def print_build_summary(fabric_type: str, fabric_name: str, success: bool, operation: str = "created") -> None:
    """Print a formatted build summary message."""
    status = "✅ SUCCESS" if success else "❌ FAILED"
    print(f"{status}: {fabric_type} - {fabric_name}")
    if success:
        print(f"   Fabric '{fabric_name}' has been {operation} successfully")
    else:
        operation_verb = "create" if operation == "created" else "update" if operation == "updated" else operation.replace("ed", "e")
        print(f"   Failed to {operation_verb} fabric '{fabric_name}'")
