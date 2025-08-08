#!/usr/bin/env python3
"""
Build Script Factory - Dynamically loads builder based on YAML config
"""
import sys
import os
import yaml
import importlib.util

def get_root_dir():
    """Get the root directory of the repository."""
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def load_fabric_config():
    """Load and return fabric builder configuration."""
    config_path = os.path.join(get_root_dir(), 'network_configs', 'fabric_builder.yaml')
    
    try:
        with open(config_path, 'r') as file:
            config = yaml.safe_load(file)
            return config['Cisco']['NDFC']
    except (FileNotFoundError, KeyError) as e:
        print(f"Config error: {e}.")
        exit(1)

def get_available_versions():
    """Get list of available builder versions."""
    cisco_path = os.path.join(get_root_dir(), 'scripts', 'cisco')
    available_versions = []
    
    if os.path.exists(cisco_path):
        for item in os.listdir(cisco_path):
            version_path = os.path.join(cisco_path, item)
            build_file = os.path.join(version_path, 'build.py')
            if os.path.isdir(version_path) and os.path.exists(build_file):
                available_versions.append(item)
    
    return sorted(available_versions)

def create_builder(version):
    """Factory function to create appropriate builder instance."""
    # Check if version exists
    version_path = os.path.join(get_root_dir(), 'scripts', 'cisco', version)
    build_file_path = os.path.join(version_path, 'build.py')
    
    if not os.path.exists(version_path):
        available = get_available_versions()
        raise FileNotFoundError(
            f"Version {version} not found. Available versions: {', '.join(available)}"
        )
    
    if not os.path.exists(build_file_path):
        raise FileNotFoundError(
            f"build.py not found for version {version} at {build_file_path}"
        )
    
    try:
        # Use importlib to dynamically import the module
        spec = importlib.util.spec_from_file_location(f"build_{version}", build_file_path)
        build_module = importlib.util.module_from_spec(spec)
        
        # Add version path to sys.path temporarily for any module dependencies
        if version_path not in sys.path:
            sys.path.insert(0, version_path)
        
        try:
            spec.loader.exec_module(build_module)
            return build_module.FabricBuilder()
        finally:
            # Clean up sys.path
            if version_path in sys.path:
                sys.path.remove(version_path)
                
    except AttributeError:
        raise ImportError(f"FabricBuilder class not found in version {version}")
    except Exception as e:
        raise ImportError(f"Error importing FabricBuilder for version {version}: {e}")

def validate_version_compatibility(version):
    """Validate that the version is supported and compatible."""
    available_versions = get_available_versions()
    
    if not available_versions:
        raise RuntimeError("No builder versions found in scripts/cisco/")
    
    if version not in available_versions:
        print(f"Warning: Version {version} not found.")
        print(f"Available versions: {', '.join(available_versions)}")
        exit(1)
    
    return version

def main():
    """Main execution function."""
    # Load configuration
    ndfc_config = load_fabric_config()
    requested_version = ndfc_config['version']
    ip = ndfc_config['ip']
    
    print(f"Requested NDFC Builder v{requested_version} for {ip}")
    
    try:
        # Validate and get actual version to use
        validate_version_compatibility(requested_version)

        # Create builder instance
        builder = create_builder(requested_version)

        # Execute build process
        builder.build()
        
        # print("Starting fabric delete process...")
        # builder.delete()
        # print("Delete process completed.")
        
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0

if __name__ == '__main__':
    exit(main())