import yaml
import json
import os
from typing import List, Dict, Any, Tuple

import fabric as fabric_api

# --- Helper Functions ---

def load_yaml_file(filepath: str) -> Dict[str, Any]:
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

def merge_configs(base_config: Dict[str, Any], override_config: Dict[str, Any]) -> Dict[str, Any]:
    """Merges two configurations. The override_config takes precedence."""
    merged = base_config.copy()
    for key, value in override_config.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = merge_configs(merged[key], value)
        else:
            merged[key] = value
    return merged

def get_template_name(fabric_type: str, template_mapping_file: str) -> str:
    """Gets the template name from the mapping file based on fabric type."""
    templates = load_yaml_file(template_mapping_file)
    if templates:
        return templates.get(fabric_type)
    return None

def read_freeform_config(file_path: str) -> str:
    """Reads the content of a freeform configuration file."""
    try:
        with open(file_path, 'r') as f:
            return f.read()
    except FileNotFoundError:
        print(f"Warning: Freeform config file not found at {file_path}")
        return ""

def flatten_config(nested_config: Dict[str, Any], parent_key: str = '', sep: str = '_') -> Dict[str, Any]:
    """Flattens a nested dictionary."""
    items = []
    for k, v in nested_config.items():
        new_key = parent_key + sep + k if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_config(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)

def apply_field_mapping(config: Dict[str, Any], mapping: Dict[str, Any]) -> Dict[str, Any]:
    """Applies field mapping to a configuration dictionary."""
    mapped_config = {}
    for key, value in config.items():
        if key in mapping and mapping[key] is not None:
            mapped_config[mapping[key]] = value
    return mapped_config

def get_nested_value(config_dict: Dict[str, Any], keys: Tuple[str, ...]) -> Any:
    """Gets a nested value from a dictionary using a tuple of keys."""
    value = config_dict
    for key in keys:
        if isinstance(value, dict) and key in value:
            value = value[key]
        else:
            return None
    return value

# --- Core Logic ---

def prepare_fabric_payload(
    config_path: str,
    defaults_path: str,
    field_mapping_path: str,
    template_map_path: str,
    type_keys: Tuple[str, ...],
    name_keys: Tuple[str, ...]
) -> Tuple[Dict[str, Any], str]:
    """
    Prepares the API payload for creating a fabric-like entity.
    """
    # --- Load Configurations ---
    fabric_config = load_yaml_file(config_path)
    defaults_config = load_yaml_file(defaults_path)
    field_mapping = load_yaml_file(field_mapping_path)

    if not fabric_config or not defaults_config or not field_mapping:
        print("Could not load initial configurations or mappings. Exiting.")
        return None, None

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
    fabric_type = get_nested_value(fabric_config, type_keys)
    if not fabric_type:
        print(f"Fabric type not specified at '{'.'.join(type_keys)}' in the config. Exiting.")
        return None, None

    template_name = get_template_name(fabric_type, template_map_path)
    if not template_name:
        print(f"Could not find a template for fabric type '{fabric_type}'. Exiting.")
        return None, None

    # --- Prepare Payload for API ---
    fabric_name = get_nested_value(fabric_config, name_keys)
    
    vrf_template = final_config.get('Advanced', {}).get('VRF Template', "Default_VRF_Universal")
    network_template = final_config.get('Advanced', {}).get('Network Template', "Default_Network_Universal")
    vrf_extension_template = final_config.get('Advanced', {}).get('VRF Extension Template', "Default_VRF_Extension_Universal")
    network_extension_template = final_config.get('Advanced', {}).get('Network Extension Template', "Default_Network_Extension_Universal")

    if vrf_template and 'vrfTemplate' in mapped_config:
        del mapped_config['vrfTemplate']
    if network_template and 'networkTemplate' in mapped_config:
        del mapped_config['networkTemplate']
    if vrf_extension_template and 'vrfExtensionTemplate' in mapped_config:
        del mapped_config['vrfExtensionTemplate']
    if network_extension_template and 'networkExtensionTemplate' in mapped_config:
        del mapped_config['networkExtensionTemplate']

    mapped_config["FABRIC_NAME"] = fabric_name
    mapped_config["FABRIC_TYPE"] = template_name

    if "BGP_AS" in mapped_config:
        mapped_config["SITE_ID"] = mapped_config["BGP_AS"]
        
    api_payload = {
        "nvPairs": mapped_config,
        "vrfTemplate": vrf_template,
        "networkTemplate": network_template,
        "vrfExtensionTemplate": vrf_extension_template,
        "networkExtensionTemplate": network_extension_template
    }
    
    return api_payload, template_name

# --- Builders ---

def build_data_center_VXLAN_EVPN(fabric_site_name: str):
    """
    Builds a fabric configuration for a given site.
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(script_dir, '..', '..', '..', '..'))

    # --- Configuration ---
    fabric_config_path = os.path.join(project_root, 'network_configs', '1_vxlan_evpn', 'fabric', f'{fabric_site_name}.yaml')
    defaults_path = os.path.join(project_root, 'scripts', 'api', 'cisco', '12.2.2', 'resources', 'corp_defaults', 'cisco_vxlan.yaml')
    template_map_path = os.path.join(project_root, 'scripts', 'api', 'cisco', '12.2.2', 'resources', 'fabric_template.yaml')
    field_mapping_path = os.path.join(project_root, 'scripts', 'api', 'cisco', '12.2.2', 'resources', '_field_mapping', 'cisco_vxlan.yaml')
    
    api_payload, template_name = prepare_fabric_payload(
        config_path=fabric_config_path,
        defaults_path=defaults_path,
        field_mapping_path=field_mapping_path,
        template_map_path=template_map_path,
        type_keys=('Fabric', 'type'),
        name_keys=('Fabric', 'name')
    )

    if not api_payload or not template_name:
        return

    # --- Read and Add Freeform Configs ---
    fabric_name = api_payload["fabricName"]
    freeform_base_path = os.path.join(project_root, 'network_configs', '1_vxlan_evpn', 'fabric')
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
    
    temp_payload_file = f"temp_payload_{fabric_name}.json"
    with open(temp_payload_file, 'w') as f:
        json.dump(api_payload, f, indent=4)

    print(f"Payload saved to {temp_payload_file}")
    print("\nCalling create_fabric API for VXLAN EVPN Fabric...")
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

def build_multi_site_domain(msd_name: str):
    """
    Builds a Multi-Site Domain (MSD) configuration.
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(script_dir, '..', '..', '..', '..'))

    # --- Configuration ---
    config_path = os.path.join(project_root, 'network_configs', '1_vxlan_evpn', 'multisite_deployment', f'{msd_name}.yaml')
    defaults_path = os.path.join(project_root, 'scripts', 'api', 'cisco', '12.2.2', 'resources', 'corp_defaults', 'cisco_multi-site.yaml')
    template_map_path = os.path.join(project_root, 'scripts', 'api', 'cisco', '12.2.2', 'resources', 'fabric_template.yaml')
    field_mapping_path = os.path.join(project_root, 'scripts', 'api', 'cisco', '12.2.2', 'resources', '_field_mapping', 'cisco_multi-site.yaml')

    api_payload, template_name = prepare_fabric_payload(
        config_path=config_path,
        defaults_path=defaults_path,
        field_mapping_path=field_mapping_path,
        template_map_path=template_map_path,
        type_keys=('Fabric', 'type'),
        name_keys=('Fabric', 'name')
    )

    if not api_payload or not template_name:
        return
    api_payload["nvPairs"]["FABRIC_TYPE"] = "MFD"  # Set the fabric type to MFD
    api_payload["nvPairs"]["FF"] = "MSD"

    temp_payload_file = f"temp_payload_{msd_name}.json"
    with open(temp_payload_file, 'w') as f:
        json.dump(api_payload, f, indent=4)
    
    print(f"Payload saved to {temp_payload_file}")
    print("\nCalling create_fabric API for Multi-Site Domain...")
    fabric_api.create_fabric(
        filename=temp_payload_file,
        template_name=template_name
    )

    os.remove(temp_payload_file)
    print(f"Cleaned up temporary file: {temp_payload_file}")

def build_inter_site_network(isn_name: str):
    """
    Builds an Inter-Site Network (ISN) configuration.
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(script_dir, '..', '..', '..', '..'))

    # --- Configuration ---
    config_path = os.path.join(project_root, 'network_configs', '1_vxlan_evpn', 'inter-site_network', f'{isn_name}.yaml')
    defaults_path = os.path.join(project_root, 'scripts', 'api', 'cisco', '12.2.2', 'resources', 'corp_defaults', 'cisco_inter-site.yaml')
    template_map_path = os.path.join(project_root, 'scripts', 'api', 'cisco', '12.2.2', 'resources', 'fabric_template.yaml')
    field_mapping_path = os.path.join(project_root, 'scripts', 'api', 'cisco', '12.2.2', 'resources', '_field_mapping', 'cisco_inter-site.yaml')

    api_payload, template_name = prepare_fabric_payload(
        config_path=config_path,
        defaults_path=defaults_path,
        field_mapping_path=field_mapping_path,
        template_map_path=template_map_path,
        type_keys=('Fabric', 'type'),
        name_keys=('Fabric', 'name')
    )

    if not api_payload or not template_name:
        return
    del api_payload["nvPairs"]["SITE_ID"]  # Remove SITE_ID if it exists
    api_payload["nvPairs"]["FABRIC_TYPE"] = "External"  # Set the fabric type to ISN
    api_payload["nvPairs"]["EXT_FABRIC_TYPE"] = "Multi-Site External Network"  
    temp_payload_file = f"temp_payload_{isn_name}.json"
    with open(temp_payload_file, 'w') as f:
        json.dump(api_payload, f, indent=4)

    print(f"Payload saved to {temp_payload_file}")
    print("\nCalling create_fabric API for Inter-Site Network...")
    fabric_api.create_fabric(
        filename=temp_payload_file,
        template_name=template_name
    )

    os.remove(temp_payload_file)
    print(f"Cleaned up temporary file: {temp_payload_file}")

def link_fabrics(parent_fabric: str, child_fabric: str):
    """
    Links a child fabric to a parent fabric.
    """
    print(f"\nLinking {child_fabric} to {parent_fabric}...")
    fabric_api.add_MSD(parent_fabric_name=parent_fabric, child_fabric_name=child_fabric)

def main():
    """
    Main function to run the fabric build process.
    Uncomment the section you want to run.
    """
    # --- Build Data Center VXLAN EVPN Fabric ---
    # You can change the site name here to build a different fabric.
    fabric_site_to_build = "Site3-test" 
    # build_data_center_VXLAN_EVPN(fabric_site_to_build)

    # --- Build Multi-Site Domain ---
    msd_to_build = "MSD-Test"
    # build_multi_site_domain(msd_to_build)

    # --- Build Inter-Site Network ---
    isn_to_build = "ISN-Test" # Assuming the file is ISN.yaml
    build_inter_site_network(isn_to_build)

    # --- Link Fabrics ---
    # link_fabrics(parent_fabric=msd_to_build, child_fabric=isn_to_build)

if __name__ == "__main__":
    main()
