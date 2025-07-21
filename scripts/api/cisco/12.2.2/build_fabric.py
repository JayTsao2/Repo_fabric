import yaml
import json
import os

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
    return mapped_config

def build_data_center_VXLAN_EVPN(fabric_site_name: str):
    """
    Builds a fabric configuration for a given site.

    Args:
        fabric_site_name: The name of the fabric site (e.g., "Site3-test").
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(script_dir, '..', '..', '..', '..'))

    # --- Configuration (paths are relative to the project root) ---
    fabric_config_path = os.path.join(project_root, 'network_configs', '1_vxlan_evpn', 'fabric', f'{fabric_site_name}.yaml')
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
    mapped_config = apply_field_mapping(flat_config, flatten_config(field_mapping))

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
    
    vrf_template = final_config.get('Advanced', {}).get('VRF Template')
    network_template = final_config.get('Advanced', {}).get('Network Template')
    vrf_extension_template = final_config.get('Advanced', {}).get('VRF Extension Template')
    network_extension_template = final_config.get('Advanced', {}).get('Network Extension Template')

    if vrf_template and 'vrfTemplate' in mapped_config:
        del mapped_config['vrfTemplate']
    if network_template and 'networkTemplate' in mapped_config:
        del mapped_config['networkTemplate']
    if vrf_extension_template and 'vrfExtensionTemplate' in mapped_config:
        del mapped_config['vrfExtensionTemplate']
    if network_extension_template and 'networkExtensionTemplate' in mapped_config:
        del mapped_config['networkExtensionTemplate']

    mapped_config["FABRIC_NAME"] = fabric_name
    mapped_config["FF"] = template_name

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
    fabric_freeform_dir = os.path.join(freeform_base_path, f"{fabric_name}_FreeForm")
    resources_freeform_base_path = os.path.join(project_root, 'scripts', 'api', 'cisco', '12.2.2', 'resources', 'freeform')

    aaa_freeform_path = os.path.join(resources_freeform_base_path, "AAA Freeform Config.sh")
    leaf_freeform_path = os.path.join(resources_freeform_base_path, "Leaf Freeform Config.sh")
    spine_freeform_path = os.path.join(resources_freeform_base_path, "Spine Freeform Config.sh")
    banner_freeform_path = os.path.join(resources_freeform_base_path, "Banner.sh")

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
    
    temp_payload_file = "temp_fabric_payload.json"
    with open(temp_payload_file, 'w') as f:
        json.dump(api_payload, f, indent=4)

    print(f"Payload saved to {temp_payload_file}")
    print("\nCalling create_fabric API...")
    fabric_api.create_fabric(
        filename=temp_payload_file,
        template_name=template_name,
        leaf_freeform_config_file=leaf_freeform_path,
        spine_freeform_config_file=spine_freeform_path,
        aaa_freeform_config_file=aaa_freeform_path,
        banner_freeform_config_file=banner_freeform_path
    )

    os.remove(temp_payload_file)
    print(f"Cleaned up temporary file: {temp_payload_file}")

def main():
    """
    Main function to run the fabric build process.
    You can change the site name here to build a different fabric.
    """
    fabric_site_to_build = "Site3-test" 
    build_data_center_VXLAN_EVPN(fabric_site_to_build)

if __name__ == "__main__":
    main()