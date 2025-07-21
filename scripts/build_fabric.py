
import yaml
import json
import os
import sys

# Dynamically add the path containing the fabric.py module to sys.path
# This is necessary because '12.2.2' is not a valid Python package name for direct import
module_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'api', 'cisco', '12.2.2'))
if module_path not in sys.path:
    sys.path.append(module_path)

import fabric as fabric_api

def load_yaml_file(filepath):
    """Loads a YAML file and returns its content."""
    try:
        with open(filepath, 'r') as file:
            return yaml.safe_load(file)
    except FileNotFoundError:
        print(f"Error: File not found at {filepath}")
        return None
    except yaml.YAMLError as e:
        print(f"Error parsing YAML file {filepath}: {e}")
        return None

def merge_configs(base_config, override_config):
    """Merges two configurations. The override_config takes precedence."""
    merged = base_config.copy()
    for key, value in override_config.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = merge_configs(merged[key], value)
        else:
            merged[key] = value
    return merged

def get_template_name(fabric_type, template_mapping_file):
    """Gets the template name from the mapping file based on fabric type."""
    templates = load_yaml_file(template_mapping_file)
    if templates:
        return templates.get(fabric_type)
    return None

def read_freeform_config(file_path):
    """Reads the content of a freeform configuration file."""
    try:
        with open(file_path, 'r') as f:
            return f.read()
    except FileNotFoundError:
        print(f"Warning: Freeform config file not found at {file_path}")
        return ""

def flatten_config(nested_config, parent_key='', sep='_'):
    items = []
    for k, v in nested_config.items():
        new_key = parent_key + sep + k if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_config(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)

def apply_field_mapping(config, mapping):
    mapped_config = {}
    for key, value in config.items():
        if key in mapping and mapping[key] is not None:
            mapped_config[mapping[key]] = value
        # Keep unmapped keys for now, might be needed for template logic
        # else:
        #     mapped_config[key] = value
    return mapped_config

def main():
    # Get the absolute path of the directory where the script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)

    # --- Configuration (paths are relative to the project root) ---
    fabric_config_path = os.path.join(project_root, 'network_configs', '1_vxlan_evpn', 'fabric', 'Site3-test.yaml')
    defaults_path = os.path.join(project_root, 'scripts', 'api', 'cisco', '12.2.2', 'resources', 'corp_defaults', 'cisco_vxlan.yaml')
    template_map_path = os.path.join(project_root, 'scripts', 'api', 'cisco', '12.2.2', 'resources', 'fabric_template.yaml')
    field_mapping_path = os.path.join(project_root, 'scripts', 'api', 'cisco', '12.2.2', 'resources', '_field_mapping', 'cisco_vxlan.yaml')
    freeform_base_path = os.path.join(project_root, 'network_configs', '1_vxlan_evpn', 'fabric')

    # --- Load Configurations ---
    fabric_config = load_yaml_file(fabric_config_path)
    defaults_config = load_yaml_file(defaults_path)
    field_mapping = load_yaml_file(field_mapping_path)

    if not fabric_config or not defaults_config or not field_mapping:
        print("Could not load initial configurations or mappings. Exiting.")
        return

    # --- Merge, Flatten, and Map Configurations ---
    final_config = {}
    for key in defaults_config:
        if key in fabric_config:
            final_config[key] = merge_configs(defaults_config[key], fabric_config[key])
        else:
            final_config[key] = defaults_config[key]

    flat_config = flatten_config(final_config)
    mapped_config = apply_field_mapping(flat_config, flatten_config(field_mapping)) # Flatten the mapping file as well

    # --- Get Template Name ---
    fabric_type = fabric_config.get('Fabric', {}).get('type')
    if not fabric_type:
        print("Fabric type not specified in the config. Exiting.")
        return

    template_name = get_template_name(fabric_type, template_map_path)
    if not template_name:
        print(f"Could not find a template for fabric type '{fabric_type}'. Exiting.")
        return

    # --- Prepare Payload for API ---
    fabric_name = fabric_config.get('Fabric', {}).get('name')
    
    # Extract template names that should be outside nvPairs
    vrf_template = final_config.get('Advanced', {}).get('VRF Template')
    network_template = final_config.get('Advanced', {}).get('Network Template')
    vrf_extension_template = final_config.get('Advanced', {}).get('VRF Extension Template')
    network_extension_template = final_config.get('Advanced', {}).get('Network Extension Template')

    # Remove these from mapped_config as they will be top-level
    if vrf_template:
        del mapped_config['vrfTemplate']
    if network_template:
        del mapped_config['networkTemplate']
    if vrf_extension_template:
        del mapped_config['vrfExtensionTemplate']
    if network_extension_template:
        del mapped_config['networkExtensionTemplate']

    # The API expects a flat nvPairs dictionary with mapped keys
    mapped_config["FABRIC_NAME"] = fabric_name
    mapped_config["FF"] = template_name

    # Ensure SITE_ID uses the value of BGP_AS
    if "BGP_AS" in mapped_config:
        mapped_config["SITE_ID"] = mapped_config["BGP_AS"]

    api_payload = {
        "fabricName": fabric_name,
        "nvPairs": mapped_config,
        "vrfTemplate": vrf_template,
        "networkTemplate": network_template,
        "vrfExtensionTemplate": vrf_extension_template,
        "networkExtensionTemplate": network_extension_template
    }

    # --- Read and Add Freeform Configs ---
    # Determine freeform config paths based on fabric_name or corp_defaults
    fabric_freeform_dir = os.path.join(freeform_base_path, f"{fabric_name}_FreeForm")

    # Get default paths from the merged config (which includes corp_defaults)
    default_aaa_path_rel = fabric_config.get('Manageability', {}).get('AAA Freeform Config', {}).get('Freeform')
    default_leaf_path_rel = fabric_config.get('Advanced', {}).get('Leaf Freeform Config', {}).get('Freeform')
    default_spine_path_rel = fabric_config.get('Advanced', {}).get('Spine Freeform Config', {}).get('Freeform')
    default_banner_path_rel = fabric_config.get('Manageability', {}).get('Banner', {}).get('Freeform')

    # Initialize paths with defaults
    aaa_freeform_path = os.path.join(freeform_base_path, *default_aaa_path_rel.split('/')) if default_aaa_path_rel else ""
    leaf_freeform_path = os.path.join(freeform_base_path, *default_leaf_path_rel.split('/')) if default_leaf_path_rel else ""
    spine_freeform_path = os.path.join(freeform_base_path, *default_spine_path_rel.split('/')) if default_spine_path_rel else ""
    banner_freeform_path = os.path.join(project_root, 'scripts', 'api', 'cisco', '12.2.2', 'resources', 'freeform', 'Banner.sh')

    # Check for fabric-specific freeform files and override if they exist
    if os.path.isdir(fabric_freeform_dir):
        temp_aaa_path = os.path.join(fabric_freeform_dir, "AAA Freeform Config.sh")
        if os.path.exists(temp_aaa_path):
            aaa_freeform_path = temp_aaa_path

        temp_leaf_path = os.path.join(fabric_freeform_dir, "Leaf Freeform Config.sh")
        if os.path.exists(temp_leaf_path):
            leaf_freeform_path = temp_leaf_path

        temp_spine_path = os.path.join(fabric_freeform_dir, "Spine Freeform Config.sh")
        if os.path.exists(temp_spine_path):
            spine_freeform_path = temp_spine_path

        temp_banner_path = os.path.join(fabric_freeform_dir, "Banner.sh")
        if os.path.exists(temp_banner_path):
            banner_freeform_path = temp_banner_path
    
    # --- Save the payload to a temporary file to pass to create_fabric ---
    temp_payload_file = "temp_fabric_payload.json"
    with open(temp_payload_file, 'w') as f:
        json.dump(api_payload, f, indent=4)

    print(f"Payload saved to {temp_payload_file}")
    # --- Call Create Fabric ---
    print("\nCalling create_fabric API...")
    fabric_api.create_fabric(
        filename=temp_payload_file,
        template_name=template_name,
        leaf_freeform_config_file=leaf_freeform_path,
        spine_freeform_config_file=spine_freeform_path,
        aaa_freeform_config_file=aaa_freeform_path,
        banner_freeform_config_file=banner_freeform_path
    )

    # --- Cleanup ---
    os.remove(temp_payload_file)
    print(f"Cleaned up temporary file: {temp_payload_file}")


if __name__ == "__main__":
    main()
