//! Closed public errors; never accept parser input, paths or raw streams as text.
#[derive(Clone, Copy, Debug)]
pub enum Phase {
    Parse,
    Native,
}
#[derive(Clone, Copy, Debug)]
pub enum Reason {
    InvalidInput,
    NativeFailure,
}
#[derive(Clone, Copy, Debug)]
pub struct Diagnostic {
    pub phase: Phase,
    pub reason: Reason,
    pub native_error: Option<i32>,
}
impl Diagnostic {
    pub fn to_json(self) -> String {
        let phase = match self.phase {
            Phase::Parse => "parse",
            Phase::Native => "native",
        };
        let reason = match self.reason {
            Reason::InvalidInput => "invalid_input",
            Reason::NativeFailure => "native_failure",
        };
        let code = self
            .native_error
            .map_or_else(|| "null".into(), |v| v.to_string());
        format!("{{\"diagnostic_version\":1,\"phase\":\"{phase}\",\"reason\":\"{reason}\",\"native_error\":{code}}}")
    }
}
