//! Finite fixture-only Stage 2 harness; not the production launch command.
use pear_manager::{
    activation::{self, Admitted},
    contract::Bundle,
    fs::{require, Error, Result, Root},
    json,
};
use std::io::{self, Read, Write};
fn barrier(label: &str) -> Result<()> {
    println!("{label}");
    io::stdout().flush()?;
    let mut b = [0];
    io::stdin().read_exact(&mut b)?;
    Ok(())
}
fn run() -> Result<()> {
    let a: Vec<String> = std::env::args().collect();
    require(a.len() == 7, "probe_usage")?;
    let bundle = Bundle::inspect(Root::open(&a[1])?, &a[2], "fixture")?;
    let (parent, name) = a[4].rsplit_once('/').ok_or(Error::code("invalid_path"))?;
    let (bytes, hash, _) = Root::open(parent)?.read_record(name, 262144)?;
    let admitted = Admitted::new(bundle, &a[2], &json::parse(&bytes)?, &hash)?;
    let state = Root::open(&a[3])?;
    match a[5].as_str() {
        "execute" => {
            let _lease = activation::version_lease(&state, &admitted)?;
            barrier("admitted")?;
            let mut cmd = admitted.fixture_command()?;
            let status = cmd.status()?;
            require(status.success(), "fixture_failed")?;
        }
        "activate" => activation::activate_with(&state, &admitted, &a[1], &a[2], |point| {
            if a[6] == format!("{point}-enospc") {
                return Err(Error {
                    code: "filesystem_error",
                    errno: Some(libc::ENOSPC),
                });
            }
            if a[6] == format!("{point}-eio") {
                return Err(Error {
                    code: "filesystem_error",
                    errno: Some(libc::EIO),
                });
            }
            if point == a[6] {
                barrier(point)?;
                return Err(Error::code("injected_failure"));
            }
            Ok(())
        })?,
        _ => return Err(Error::code("probe_usage")),
    }
    Ok(())
}
fn main() {
    if let Err(e) = run() {
        println!(
            "{{\"reason\":\"{}\",\"native_error\":{}}}",
            e.code,
            e.errno.map_or("null".into(), |n| n.to_string())
        );
        std::process::exit(1);
    }
}
