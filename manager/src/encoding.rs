//! Encoding of bounded local metadata and closed diagnostic values.
use crate::json::J;
pub fn encode(v: &J) -> String {
    match v {
        J::Null => "null".into(),
        J::Bool(v) => v.to_string(),
        J::Int(v) => v.to_string(),
        J::Str(s) => {
            let mut out = String::from("\"");
            for c in s.chars() {
                match c {
                    '"' => out.push_str("\\\""),
                    '\\' => out.push_str("\\\\"),
                    c if c < ' ' => out.push_str(&format!("\\u{:04x}", c as u32)),
                    c => out.push(c),
                }
            }
            out.push('"');
            out
        }
        J::Arr(a) => format!("[{}]", a.iter().map(encode).collect::<Vec<_>>().join(",")),
        J::Obj(o) => format!(
            "{{{}}}",
            o.iter()
                .map(|(k, v)| format!("{}:{}", encode(&J::Str(k.clone())), encode(v)))
                .collect::<Vec<_>>()
                .join(",")
        ),
    }
}
