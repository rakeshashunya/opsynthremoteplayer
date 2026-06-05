import os

def main():
    config_path = os.path.join('libs', 'hbb_common', 'src', 'config.rs')
    if not os.path.exists(config_path):
        print(f"Error: {config_path} does not exist. Make sure submodules are checked out.")
        return

    print(f"Reading {config_path}...")
    with open(config_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Define the modifications
    replacements = [
        # Hardcoding the rendezvous servers
        (
            'pub const RENDEZVOUS_SERVERS: &[&str] = &["router.rustdesk.com"];',
            'pub const RENDEZVOUS_SERVERS: &[&str] = &["opsynth.ashunya.com"];'
        ),
        # Hardcoding the public encryption key
        (
            'pub const RS_PUB_KEY: &str = "";',
            'pub const RS_PUB_KEY: &str = "2xobsb9zEqBv81w2AZ5r7RuKOtJ9H23ZT3RzOWjGnBE=";'
        ),
        # Enforcing connection mode: client host-only (is_incoming_only returns true unless launched with connect/play args)
        (
            'pub fn is_incoming_only() -> bool {\n    HARD_SETTINGS\n        .read()\n        .unwrap()\n        .get("conn-type")\n        .map_or(false, |x| x == ("incoming"))\n}',
            'pub fn is_incoming_only() -> bool {\n    let args: Vec<String> = std::env::args().collect();\n    for arg in args {\n        let arg_lower = arg.to_lowercase();\n        if arg_lower.starts_with("opsynthremoteplayer://")\n            || arg_lower.starts_with("rustdesk://")\n            || arg_lower == "--connect"\n            || arg_lower == "--play"\n            || arg_lower == "--file-transfer"\n            || arg_lower == "--view-camera"\n        {\n            return false;\n        }\n    }\n    true\n}'
        ),
        # Enforcing is_disable_settings to return true
        (
            'pub fn is_disable_settings() -> bool {\n    is_some_hard_opton("disable-settings")\n}',
            'pub fn is_disable_settings() -> bool {\n    true\n}'
        ),
        # Setting the app name RwLock default to OpsynthRemotePlayer
        (
            'pub static ref APP_NAME: RwLock<String> = RwLock::new("RustDesk".to_owned());',
            'pub static ref APP_NAME: RwLock<String> = RwLock::new("OpsynthRemotePlayer".to_owned());'
        )
    ]

    modified = False
    for old, new in replacements:
        if old in content:
            content = content.replace(old, new)
            print(f"Applied replacement: {old.splitlines()[0]} -> {new.splitlines()[0]}")
            modified = True
        else:
            # Check if it was already applied
            if new in content:
                print(f"Skipping (already applied): {new.splitlines()[0]}")
            else:
                print(f"Warning: Target string not found (was it modified elsewhere?): {old.splitlines()[0]}")

    if modified:
        with open(config_path, 'w', encoding='utf-8', newline='\n') as f:
            f.write(content)
        print("Successfully updated config.rs")
    else:
        print("No changes were made to config.rs")

if __name__ == '__main__':
    main()
