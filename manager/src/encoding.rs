//! Encoding of bounded local metadata and closed diagnostic values.
use crate::json::J;
use std::fmt::{self, Write};

fn quoted(out: &mut impl Write, text: &str) -> fmt::Result {
    out.write_char('"')?;
    for c in text.chars() {
        match c {
            '"' => out.write_str("\\\"")?,
            '\\' => out.write_str("\\\\")?,
            c if c < ' ' => write!(out, "\\u{:04x}", c as u32)?,
            c => out.write_char(c)?,
        }
    }
    out.write_char('"')
}
/// Write directly into the caller's single buffer; no joined temporary strings.
pub(crate) fn write(out: &mut impl Write, value: &J) -> fmt::Result {
    match value {
        J::Null => out.write_str("null"),
        J::Bool(value) => write!(out, "{value}"),
        J::Int(value) => write!(out, "{value}"),
        J::Str(value) => quoted(out, value),
        J::Arr(values) => {
            out.write_char('[')?;
            for (index, value) in values.iter().enumerate() {
                if index != 0 {
                    out.write_char(',')?;
                }
                write(out, value)?;
            }
            out.write_char(']')
        }
        J::Obj(values) => {
            out.write_char('{')?;
            for (index, (key, value)) in values.iter().enumerate() {
                if index != 0 {
                    out.write_char(',')?;
                }
                quoted(out, key)?;
                out.write_char(':')?;
                write(out, value)?;
            }
            out.write_char('}')
        }
    }
}
pub(crate) fn size(value: &J, limit: usize) -> Option<usize> {
    struct Count {
        bytes: usize,
        limit: usize,
    }
    impl Write for Count {
        fn write_str(&mut self, text: &str) -> fmt::Result {
            self.bytes = self.bytes.checked_add(text.len()).ok_or(fmt::Error)?;
            if self.bytes > self.limit {
                Err(fmt::Error)
            } else {
                Ok(())
            }
        }
    }
    let mut count = Count { bytes: 0, limit };
    write(&mut count, value).ok()?;
    Some(count.bytes)
}
pub fn encode(value: &J) -> String {
    let mut out = String::new();
    write(&mut out, value).expect("String formatting is infallible");
    out
}
