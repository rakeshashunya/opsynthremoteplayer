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
            'pub const RENDEZVOUS_SERVERS: &[&str] = &["rs-ny.rustdesk.com"];',
            'pub const RENDEZVOUS_SERVERS: &[&str] = &["opsynth.ashunya.com"];'
        ),
        # Hardcoding the public encryption key
        (
            'pub const RS_PUB_KEY: &str = "OeVuKk5nlHiXp+APNn0Y3pC1Iwpwn44JGqrQCsWqmBw=";',
            'pub const RS_PUB_KEY: &str = "2xobsb9zEqBv81w2AZ5r7RuKOtJ9H23ZT3RzOWjGnBE=";'
        ),
        # Enforcing connection mode: client outbound-only (is_incoming_only returns false, is_outgoing_only returns true)
        (
            'pub fn is_incoming_only() -> bool {\n    HARD_SETTINGS\n        .read()\n        .unwrap()\n        .get("conn-type")\n        .map_or(false, |x| x == ("incoming"))\n}',
            'pub fn is_incoming_only() -> bool {\n    false\n}'
        ),
        (
            'pub fn is_outgoing_only() -> bool {\n    HARD_SETTINGS\n        .read()\n        .unwrap()\n        .get("conn-type")\n        .map_or(false, |x| x == ("outgoing"))\n}',
            'pub fn is_outgoing_only() -> bool {\n    true\n}'
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
        ),
        # Remove unused import encrypt_vec_or_original
        (
            '''    password_security::{
        decrypt_str_or_original, decrypt_vec_or_original, encrypt_str_or_original,
        encrypt_vec_or_original, symmetric_crypt,
    },''',
            '''    password_security::{
        decrypt_str_or_original, decrypt_vec_or_original, encrypt_str_or_original,
        symmetric_crypt,
    },'''
        ),
        # Disable storing of peer configurations to disk (no recent sessions saved)
        (
            '''    fn store_(&self, id: &str) {
        let mut config = self.clone();
        config.password =
            encrypt_vec_or_original(&config.password, PASSWORD_ENC_VERSION, ENCRYPT_MAX_LEN);
        for opt in ["rdp_password", "os-username", "os-password"] {
            if let Some(v) = config.options.get_mut(opt) {
                *v = encrypt_str_or_original(v, PASSWORD_ENC_VERSION, ENCRYPT_MAX_LEN)
            }
        }
        if let Err(err) = store_path(Self::path(id), config) {
            log::error!("Failed to store config: {}", err);
        }
        NEW_STORED_PEER_CONFIG.lock().unwrap().insert(id.to_owned());
    }''',
            '''    fn store_(&self, _id: &str) {
        // Do not store any peer configs (connection history/settings) to disk
    }'''
        ),
        # Disable reading of peer configurations (recent sessions list is empty)
        (
            '''    pub fn get_vec_id_modified_time_path(
        id_filters: &Option<Vec<String>>,
    ) -> Vec<(String, SystemTime, PathBuf)> {
        if let Ok(peers) = Config::path(PEERS).read_dir() {
            let mut vec_id_modified_time_path = peers
                .into_iter()
                .filter_map(|res| match res {
                    Ok(res) => {
                        let p = res.path();
                        if p.is_file()
                            && p.extension().map(|p| p.to_str().unwrap_or("")) == Some("toml")
                        {
                            Some(p)
                        } else {
                            None
                        }
                    }
                    _ => None,
                })
                .map(|p| {
                    let id = p
                        .file_stem()
                        .map(|p| p.to_str().unwrap_or(""))
                        .unwrap_or("")
                        .to_owned();

                    let id_decoded_string = if id.starts_with("base64_") && id.len() != 7 {
                        let id_decoded =
                            base64::decode(&id[7..], base64::Variant::Original).unwrap_or_default();
                        String::from_utf8_lossy(&id_decoded).as_ref().to_owned()
                    } else {
                        id
                    };
                    (id_decoded_string, p)
                })
                .filter(|(id, _)| {
                    let Some(filters) = id_filters else {
                        return true;
                    };
                    filters.contains(id)
                })
                .map(|(id, p)| {
                    let t = crate::get_modified_time(&p);
                    (id, t, p)
                })
                .collect::<Vec<_>>();
            vec_id_modified_time_path.sort_unstable_by(|a, b| b.1.cmp(&a.1));
            vec_id_modified_time_path
        } else {
            vec![]
        }
    }''',
            '''    pub fn get_vec_id_modified_time_path(
        _id_filters: &Option<Vec<String>>,
    ) -> Vec<(String, SystemTime, PathBuf)> {
        vec![]
    }'''
        ),
        # Disable saving and reading the latest used remote ID
        (
            '''    pub fn set_remote_id(remote_id: &str) {
        let mut config = LOCAL_CONFIG.write().unwrap();
        if remote_id == config.remote_id {
            return;
        }
        config.remote_id = remote_id.into();
        config.store();
    }

    pub fn get_remote_id() -> String {
        LOCAL_CONFIG.read().unwrap().remote_id.clone()
    }''',
            '''    pub fn set_remote_id(_remote_id: &str) {
        // Do not store the last used remote ID
    }

    pub fn get_remote_id() -> String {
        "".to_owned()
    }'''
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
