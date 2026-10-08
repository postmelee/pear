//! Native manager foundation. No runtime execution or admission is implemented here.
#[cfg(not(all(target_os = "macos", target_arch = "aarch64")))]
compile_error!("the current manager foundation requires native ARM64 macOS");
pub mod diagnostics;
pub mod fs;
pub mod json;
pub mod native;

pub mod activation;
pub mod contract;
pub mod encoding;
pub mod launch;
pub mod observer;
pub mod policy;
pub mod state;
pub mod supervisor;
mod tools;
