//! Finite owned publication/lease fault harness; absent from the product CLI.
use pear_manager::{
    activation::Admitted,
    contract::Bundle,
    fs::{Error, Result, Root, require},
    json, state,
};
use std::io::{self, Read, Write};
fn barrier(point: &str) -> Result<()> {
    println!("{point}");
    io::stdout().flush()?;
    let mut byte = [0];
    io::stdin().read_exact(&mut byte)?;
    Ok(())
}
fn run() -> Result<()> {
    let args: Vec<String> = std::env::args().collect();
    require(args.len() == 7, "probe_usage")?;
    let root = Root::open(&args[1])?;
    let selection = root.json("selection.json")?;
    let bundle = Bundle::inspect(
        Root::open(selection.get("bundle_root")?.s()?)?,
        selection.get("request")?.s()?,
        "fixture",
    )?;
    let (parent, name) = args[3].rsplit_once('/').ok_or(Error::code("probe_usage"))?;
    let (bytes, hash, _) = Root::open(parent)?.read_record(name, 262144)?;
    let admitted = Admitted::new(
        bundle,
        selection.get("request")?.s()?,
        &json::parse(&bytes)?,
        &hash,
    )?;
    state::prepare_with(&root, &args[2], &selection, &admitted, |point| {
        if point == args[4] {
            barrier(point)?;
            if args[5] == "fail" {
                return Err(Error {
                    code: "injected_failure",
                    errno: Some(libc::EIO),
                });
            }
        }
        Ok(())
    })
}
fn main() {
    if let Err(error) = run() {
        println!(
            "{{\"reason\":\"{}\",\"native_error\":{}}}",
            error.code,
            error.errno.map_or("null".into(), |v| v.to_string())
        );
        std::process::exit(1);
    }
}
