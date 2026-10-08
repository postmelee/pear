//! Native manager foundation. No runtime execution or admission is implemented here.
#[cfg(not(all(target_os = "macos", target_arch = "aarch64")))]
compile_error!("the current manager foundation requires native ARM64 macOS");
pub mod diagnostics;
pub mod json;
pub mod native;
