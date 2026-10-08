//! Bounded test probe for Stage 1 APIs, not the product CLI or a runtime launcher.
use pear_manager::{
    diagnostics::{Diagnostic, Phase, Reason},
    json, native,
};
use std::{
    fs::OpenOptions,
    io::{self, Read, Write},
    os::unix::fs::OpenOptionsExt,
};
fn run(args: &[String]) -> io::Result<()> {
    match args.get(1).map(String::as_str) {
        Some("parse") => {
            let mut bytes = Vec::new();
            io::stdin().take(262145).read_to_end(&mut bytes)?;
            if json::parse(&bytes).is_err() {
                println!(
                    "{}",
                    Diagnostic {
                        phase: Phase::Parse,
                        reason: Reason::InvalidInput,
                        native_error: None
                    }
                    .to_json()
                );
                std::process::exit(1);
            }
            println!("{{\"parsed\":true}}");
        }
        Some("hash") if args.len() == 4 => {
            let file = OpenOptions::new()
                .read(true)
                .custom_flags(libc::O_NOFOLLOW | libc::O_NONBLOCK)
                .open(&args[2])?;
            let limit = args[3]
                .parse()
                .map_err(|_| io::Error::from_raw_os_error(libc::EINVAL))?;
            let (digest, bytes) = native::sha256(&file, limit)?;
            println!(
                "{{\"sha256\":\"{}\",\"bytes\":{bytes}}}",
                digest
                    .iter()
                    .map(|b| format!("{b:02x}"))
                    .collect::<String>()
            );
        }
        Some("stage") if args.len() == 3 => {
            let parent = OpenOptions::new()
                .read(true)
                .custom_flags(libc::O_DIRECTORY | libc::O_NOFOLLOW)
                .open(&args[2])?;
            let name = native::stage_directory(&parent)?;
            println!("{}", name.to_str().expect("native ASCII template"));
        }
        Some("identity") => {
            let pid = args
                .get(2)
                .and_then(|v| v.parse().ok())
                .unwrap_or(std::process::id() as i32);
            let (seconds, micros) = native::process_identity(pid)?;
            println!("{{\"seconds\":{seconds},\"micros\":{micros}}}");
        }
        Some("lock") if args.len() == 4 => {
            let file = OpenOptions::new()
                .read(true)
                .write(true)
                .custom_flags(libc::O_NOFOLLOW)
                .open(&args[2])?;
            let shared = args[3].starts_with("shared");
            let result = if shared {
                file.try_lock_shared()
            } else {
                file.try_lock()
            };
            match result {
                Err(std::fs::TryLockError::WouldBlock) => {
                    println!("busy");
                    return Ok(());
                }
                Err(std::fs::TryLockError::Error(error)) => return Err(error),
                Ok(()) => (),
            }
            println!("locked");
            io::stdout().flush()?;
            if args[3].ends_with("hold") {
                let mut byte = [0];
                io::stdin().read_exact(&mut byte)?;
            }
            if args[3] != "exclusive-drop" {
                file.unlock()?;
            }
        }
        Some("diagnostic") => println!(
            "{}",
            Diagnostic {
                phase: Phase::Native,
                reason: Reason::NativeFailure,
                native_error: Some(libc::EBADF)
            }
            .to_json()
        ),
        _ => return Err(io::Error::from_raw_os_error(libc::EINVAL)),
    }
    Ok(())
}
fn main() {
    if let Err(error) = run(&std::env::args().collect::<Vec<_>>()) {
        println!(
            "{}",
            Diagnostic {
                phase: Phase::Native,
                reason: Reason::NativeFailure,
                native_error: error.raw_os_error()
            }
            .to_json()
        );
        std::process::exit(1);
    }
}
