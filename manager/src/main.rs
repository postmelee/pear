//! Stage 2 command surface. No runtime launch command exists before supervision approval.
use pear_manager::{
    contract::Bundle,
    fs::{require, Error, Result, Root},
    json::J,
};
use std::collections::BTreeMap;
fn execute() -> Result<()> {
    let args: Vec<String> = std::env::args().skip(1).collect();
    require(!args.is_empty(), "cli_misuse")?;
    let command = args[0].as_str();
    require(
        ["inspect", "evaluate", "activate"].contains(&command),
        "cli_misuse",
    )?;
    require(args.len() % 2 == 1, "cli_misuse")?;
    let mut options = BTreeMap::new();
    for pair in args[1..].chunks(2) {
        require(
            options.insert(pair[0].as_str(), pair[1].as_str()).is_none(),
            "cli_misuse",
        )?;
    }
    let allowed = if command == "activate" {
        vec![
            "--bundle-root",
            "--entry",
            "--context",
            "--state-root",
            "--policy",
        ]
    } else {
        vec![
            "--bundle-root",
            "--entry",
            "--context",
            "--purpose",
            "--policy",
        ]
    };
    require(options.keys().all(|k| allowed.contains(k)), "cli_misuse")?;
    let get = |k| options.get(k).copied().ok_or(Error::code("cli_misuse"));
    let root = get("--bundle-root")?;
    let entry = get("--entry")?;
    let context = get("--context")?;
    let b = Bundle::inspect(Root::open(root)?, entry, context)?;
    let mut policy_hash = String::new();
    let policy = if let Some(path) = options.get("--policy") {
        let (parent, name) = path.rsplit_once('/').ok_or(Error::code("invalid_path"))?;
        let (bytes, hash, _) = Root::open(parent)?.read_record(name, 262144)?;
        policy_hash = hash;
        Some(pear_manager::json::parse(&bytes)?)
    } else {
        None
    };
    let purpose = if command == "inspect" {
        "inspect"
    } else if command == "activate" {
        b.request(entry)?.get("purpose")?.s()?
    } else {
        get("--purpose")?
    };
    let now = unsafe { libc::time(std::ptr::null_mut()) };
    let codes = b.eligibility(entry, purpose, policy.as_ref(), now)?;
    if command == "activate" {
        require(codes.is_empty(), "ineligible")?;
        let p = policy
            .as_ref()
            .ok_or(Error::code("external_policy_required"))?;
        let admitted = pear_manager::activation::Admitted::new(b, entry, p, &policy_hash)?;
        let state = Root::open(get("--state-root")?)?;
        pear_manager::activation::activate(&state, &admitted, root, entry)?;
        println!("{{\"diagnostic_version\":1,\"phase\":\"activation\",\"reason\":\"selection_committed\",\"runtime_eligible\":false}}");
    } else {
        let codes = pear_manager::encoding::encode(&J::Arr(
            codes.iter().take(32).map(|c| J::Str((*c).into())).collect(),
        ));
        println!("{{\"record_valid\":true,\"eligible\":{},\"outcome_codes\":{},\"record_count\":{},\"evaluation_only\":true}}",codes=="[]",codes,b.records.len());
    }
    Ok(())
}
fn main() {
    if let Err(e) = execute() {
        println!("{{\"record_valid\":false,\"eligible\":false,\"outcome_codes\":[\"{}\"],\"native_error\":{},\"evaluation_only\":true}}",e.code,e.errno.map_or("null".into(),|n|n.to_string()));
        std::process::exit(if e.code == "cli_misuse" {
            2
        } else if [
            "ineligible",
            "runtime_authorization_unavailable",
            "payload_not_readonly",
            "state_busy",
        ]
        .contains(&e.code)
        {
            3
        } else {
            1
        });
    }
}
