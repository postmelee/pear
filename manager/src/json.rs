//! Strict bounded JSON for the explicitly limited native fixture contract.
use std::collections::BTreeMap;

#[derive(Clone, Debug, PartialEq)]
pub enum J {
    Null,
    Bool(bool),
    Int(i64),
    Str(String),
    Arr(Vec<J>),
    Obj(BTreeMap<String, J>),
}
pub type R<T> = Result<T, ()>;
impl J {
    pub fn get(&self, key: &str) -> R<&J> {
        if let J::Obj(o) = self {
            o.get(key).ok_or(())
        } else {
            Err(())
        }
    }
    pub fn s(&self) -> R<&str> {
        if let J::Str(s) = self {
            Ok(s)
        } else {
            Err(())
        }
    }
    pub fn a(&self) -> R<&[J]> {
        if let J::Arr(a) = self {
            Ok(a)
        } else {
            Err(())
        }
    }
    pub fn i(&self) -> R<i64> {
        if let J::Int(i) = self {
            Ok(*i)
        } else {
            Err(())
        }
    }
    pub fn b(&self) -> R<bool> {
        if let J::Bool(b) = self {
            Ok(*b)
        } else {
            Err(())
        }
    }
    pub fn keys(&self, keys: &[&str]) -> R<()> {
        if let J::Obj(o) = self {
            if o.len() == keys.len() && keys.iter().all(|k| o.contains_key(*k)) {
                return Ok(());
            }
        }
        Err(())
    }
    pub fn eqs(&self, s: &str) -> R<()> {
        if self.s()? == s {
            Ok(())
        } else {
            Err(())
        }
    }
    pub fn text(&self) -> R<()> {
        let s = self.s()?;
        if !s.is_empty() && s.len() <= 4096 && !s.chars().any(|c| c <= '\u{1f}' || c == '\u{7f}') {
            Ok(())
        } else {
            Err(())
        }
    }
}
pub fn ensure(b: bool) -> R<()> {
    if b {
        Ok(())
    } else {
        Err(())
    }
}
pub fn parse(data: &[u8]) -> R<J> {
    ensure(data.len() <= 262144)?;
    let text = std::str::from_utf8(data).map_err(|_| ())?;
    let mut p = Parser {
        s: text.as_bytes(),
        at: 0,
        nodes: 0,
    };
    let v = p.value(0)?;
    p.ws();
    ensure(p.at == p.s.len())?;
    Ok(v)
}
struct Parser<'a> {
    s: &'a [u8],
    at: usize,
    nodes: usize,
}
impl Parser<'_> {
    fn ws(&mut self) {
        while self.s.get(self.at).is_some_and(|c| b" \t\r\n".contains(c)) {
            self.at += 1
        }
    }
    fn byte(&mut self) -> R<u8> {
        let b = *self.s.get(self.at).ok_or(())?;
        self.at += 1;
        Ok(b)
    }
    fn take(&mut self, x: u8) -> R<()> {
        ensure(self.byte()? == x)
    }
    fn literal(&mut self, x: &[u8]) -> R<()> {
        ensure(self.s.get(self.at..self.at + x.len()) == Some(x))?;
        self.at += x.len();
        Ok(())
    }
    fn hex(&mut self) -> R<u32> {
        let mut n = 0;
        for _ in 0..4 {
            n = n * 16 + (self.byte()? as char).to_digit(16).ok_or(())?;
        }
        Ok(n)
    }
    fn string(&mut self) -> R<String> {
        self.take(b'"')?;
        let mut out = String::new();
        let mut scalar_count = 0;
        loop {
            let b = self.byte()?;
            match b {
                b'"' => return Ok(out),
                b'\\' => match self.byte()? {
                    b'"' => out.push('"'),
                    b'\\' => out.push('\\'),
                    b'/' => out.push('/'),
                    b'b' | b'f' | b'n' | b'r' | b't' => return Err(()),
                    b'u' => {
                        let a = self.hex()?;
                        let c = if (0xd800..=0xdbff).contains(&a) {
                            self.take(b'\\')?;
                            self.take(b'u')?;
                            let b = self.hex()?;
                            ensure((0xdc00..=0xdfff).contains(&b))?;
                            0x10000 + ((a - 0xd800) << 10) + (b - 0xdc00)
                        } else {
                            a
                        };
                        ensure(c >= 32)?;
                        out.push(char::from_u32(c).ok_or(())?);
                    }
                    _ => return Err(()),
                },
                0..=31 => return Err(()),
                0x20..=0x7f => out.push(b as char),
                _ => {
                    self.at -= 1;
                    // The whole document was already UTF-8 checked. Decode only
                    // this scalar to keep large Unicode strings linear in size.
                    let width = if b < 0xe0 {
                        2
                    } else if b < 0xf0 {
                        3
                    } else {
                        4
                    };
                    let scalar = self.s.get(self.at..self.at + width).ok_or(())?;
                    let c = std::str::from_utf8(scalar)
                        .map_err(|_| ())?
                        .chars()
                        .next()
                        .ok_or(())?;
                    self.at += width;
                    out.push(c)
                }
            }
            scalar_count += 1;
            ensure(scalar_count <= 2048)?;
        }
    }
    fn value(&mut self, depth: usize) -> R<J> {
        ensure(depth <= 32)?;
        self.nodes += 1;
        ensure(self.nodes <= 8192)?;
        self.ws();
        match *self.s.get(self.at).ok_or(())? {
            b'n' => {
                self.literal(b"null")?;
                Ok(J::Null)
            }
            b't' => {
                self.literal(b"true")?;
                Ok(J::Bool(true))
            }
            b'f' => {
                self.literal(b"false")?;
                Ok(J::Bool(false))
            }
            b'"' => Ok(J::Str(self.string()?)),
            b'[' => {
                ensure(depth < 32)?;
                self.at += 1;
                self.ws();
                let mut a = Vec::new();
                if self.s.get(self.at) == Some(&b']') {
                    self.at += 1;
                    return Ok(J::Arr(a));
                }
                loop {
                    a.push(self.value(depth + 1)?);
                    self.ws();
                    match self.byte()? {
                        b']' => break,
                        b',' => (),
                        _ => return Err(()),
                    }
                }
                Ok(J::Arr(a))
            }
            b'{' => {
                ensure(depth < 32)?;
                self.at += 1;
                self.ws();
                let mut o = BTreeMap::new();
                if self.s.get(self.at) == Some(&b'}') {
                    self.at += 1;
                    return Ok(J::Obj(o));
                }
                loop {
                    self.ws();
                    self.nodes += 1;
                    ensure(self.nodes <= 8192)?;
                    let k = self.string()?;
                    ensure(k.chars().count() <= 96)?;
                    self.ws();
                    self.take(b':')?;
                    let v = self.value(depth + 1)?;
                    ensure(o.insert(k, v).is_none())?;
                    self.ws();
                    match self.byte()? {
                        b'}' => break,
                        b',' => (),
                        _ => return Err(()),
                    }
                }
                Ok(J::Obj(o))
            }
            b'-' | b'0'..=b'9' => {
                let start = self.at;
                if self.s[self.at] == b'-' {
                    self.at += 1;
                }
                let b = self.byte()?;
                if b != b'0' {
                    ensure((b'1'..=b'9').contains(&b))?;
                    while self.s.get(self.at).is_some_and(|c| c.is_ascii_digit()) {
                        self.at += 1;
                    }
                }
                let n = std::str::from_utf8(&self.s[start..self.at])
                    .map_err(|_| ())?
                    .parse::<i64>()
                    .map_err(|_| ())?;
                ensure(n.abs_diff(0) <= 9007199254740991)?;
                Ok(J::Int(n))
            }
            _ => Err(()),
        }
    }
}
