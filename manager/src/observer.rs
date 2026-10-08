//! Bounded, nonblocking observer framing; transport is not observation authority.
use crate::{
    encoding::encode,
    fs::{Error, Result, require},
    json::{self, J},
};
use std::{
    collections::VecDeque,
    os::fd::{AsRawFd, FromRawFd, OwnedFd},
    time::{Duration, Instant},
};
pub const FRAME_LIMIT: usize = 262144;
pub const QUEUE_LIMIT: usize = 524288;
pub const DEADLINE: Duration = Duration::from_millis(1500);
const PASS_LIMIT: usize = 65536;
struct Pending {
    bytes: Vec<u8>,
    offset: usize,
    started: Instant,
}
pub struct Observer {
    fd: OwnedFd,
    header: [u8; 4],
    header_count: usize,
    body: Vec<u8>,
    wanted: usize,
    partial: Option<Instant>,
    queue: VecDeque<Pending>,
    queued: usize,
    pub received_bytes: usize,
    pub sent_bytes: usize,
}
impl Observer {
    /// Duplicate only an explicitly selected connected stream socket; never claim
    /// ownership of a caller's arbitrary integer or accept regular-file readiness.
    pub fn from_inherited(fd: i32) -> Result<Self> {
        require(fd >= 3, "invalid_observer_fd")?;
        fn call(value: i32) -> Result<i32> {
            if value < 0 {
                Err(std::io::Error::last_os_error().into())
            } else {
                Ok(value)
            }
        }
        let duplicate = call(unsafe { libc::fcntl(fd, libc::F_DUPFD_CLOEXEC, 3) })?;
        let owned = unsafe { OwnedFd::from_raw_fd(duplicate) };
        let original_flags = call(unsafe { libc::fcntl(fd, libc::F_GETFD) })?;
        call(unsafe { libc::fcntl(fd, libc::F_SETFD, original_flags | libc::FD_CLOEXEC) })?;
        let mut kind = 0i32;
        let mut size = std::mem::size_of::<i32>() as libc::socklen_t;
        call(unsafe {
            libc::getsockopt(
                duplicate,
                libc::SOL_SOCKET,
                libc::SO_TYPE,
                (&mut kind as *mut i32).cast(),
                &mut size,
            )
        })?;
        require(kind == libc::SOCK_STREAM, "invalid_observer_fd")?;
        let mut address = unsafe { std::mem::zeroed::<libc::sockaddr_storage>() };
        let mut len = std::mem::size_of_val(&address) as libc::socklen_t;
        call(unsafe {
            libc::getpeername(
                duplicate,
                (&mut address as *mut libc::sockaddr_storage).cast(),
                &mut len,
            )
        })?;
        let flag = 1i32;
        call(unsafe {
            libc::setsockopt(
                duplicate,
                libc::SOL_SOCKET,
                libc::SO_NOSIGPIPE,
                (&flag as *const i32).cast(),
                std::mem::size_of_val(&flag) as libc::socklen_t,
            )
        })?;
        let flags = call(unsafe { libc::fcntl(duplicate, libc::F_GETFL) })?;
        call(unsafe { libc::fcntl(duplicate, libc::F_SETFL, flags | libc::O_NONBLOCK) })?;
        Ok(Self {
            fd: owned,
            header: [0; 4],
            header_count: 0,
            body: Vec::new(),
            wanted: 0,
            partial: None,
            queue: VecDeque::new(),
            queued: 0,
            received_bytes: 0,
            sent_bytes: 0,
        })
    }
    pub fn enqueue(&mut self, value: &J) -> Result<()> {
        let size =
            crate::encoding::size(value, FRAME_LIMIT).ok_or(Error::code("observer_frame_size"))?;
        require(size > 0, "observer_frame_size")?;
        require(
            self.queued + size + 4 <= QUEUE_LIMIT,
            "observer_queue_limit",
        )?;
        let mut text = String::new();
        text.try_reserve_exact(size + 4)
            .map_err(|_| Error::code("observer_allocation"))?;
        text.push_str("\0\0\0\0");
        crate::encoding::write(&mut text, value).map_err(|_| Error::code("observer_encoding"))?;
        let mut bytes = text.into_bytes();
        require(
            self.queued + bytes.capacity() <= QUEUE_LIMIT,
            "observer_queue_limit",
        )?;
        bytes[..4].copy_from_slice(&(size as u32).to_be_bytes());
        self.queued += bytes.capacity();
        self.queue.push_back(Pending {
            bytes,
            offset: 0,
            started: Instant::now(),
        });
        Ok(())
    }
    pub fn pending(&self) -> bool {
        !self.queue.is_empty()
    }
    pub fn buffered(&self) -> usize {
        self.queued + self.body.capacity() + self.header.len() + 8192
    }
    /// At most one delivered frame and 64 KiB per direction per pass. The caller
    /// services child pipes, cancellation, deadlines and cleanup between passes.
    pub fn service(&mut self) -> Result<Option<J>> {
        let now = Instant::now();
        require(
            self.partial
                .is_none_or(|s| now.duration_since(s) < DEADLINE)
                && self
                    .queue
                    .front()
                    .is_none_or(|q| now.duration_since(q.started) < DEADLINE),
            "observer_deadline",
        )?;
        let mut sent = 0;
        while sent < PASS_LIMIT {
            let Some(front) = self.queue.front_mut() else {
                break;
            };
            let count = (front.bytes.len() - front.offset).min(PASS_LIMIT - sent);
            let n = unsafe {
                libc::send(
                    self.fd.as_raw_fd(),
                    front.bytes[front.offset..].as_ptr().cast(),
                    count,
                    0,
                )
            };
            if n < 0 {
                let e = std::io::Error::last_os_error();
                match e.kind() {
                    std::io::ErrorKind::WouldBlock => break,
                    std::io::ErrorKind::Interrupted => continue,
                    _ => return Err(e.into()),
                }
            }
            require(n > 0, "observer_disconnected")?;
            let n = n as usize;
            front.offset += n;
            sent += n;
            self.sent_bytes += n;
            if front.offset == front.bytes.len() {
                self.queued -= front.bytes.capacity();
                self.queue.pop_front();
            }
        }
        let mut received = 0;
        while received < PASS_LIMIT {
            let mut buffer = [0u8; 8192];
            let remain = if self.header_count < 4 {
                4 - self.header_count
            } else {
                self.wanted - self.body.len()
            };
            let count = remain.min(buffer.len()).min(PASS_LIMIT - received);
            let n =
                unsafe { libc::recv(self.fd.as_raw_fd(), buffer.as_mut_ptr().cast(), count, 0) };
            if n < 0 {
                let e = std::io::Error::last_os_error();
                match e.kind() {
                    std::io::ErrorKind::WouldBlock => break,
                    std::io::ErrorKind::Interrupted => continue,
                    _ => return Err(e.into()),
                }
            }
            require(
                n > 0,
                if self.partial.is_some() {
                    "observer_partial_eof"
                } else {
                    "observer_disconnected"
                },
            )?;
            let n = n as usize;
            received += n;
            self.received_bytes += n;
            if self.partial.is_none() {
                self.partial = Some(Instant::now());
            }
            if self.header_count < 4 {
                self.header[self.header_count..self.header_count + n].copy_from_slice(&buffer[..n]);
                self.header_count += n;
                if self.header_count == 4 {
                    self.wanted = u32::from_be_bytes(self.header) as usize;
                    require(
                        self.wanted > 0 && self.wanted <= FRAME_LIMIT,
                        "observer_frame_size",
                    )?;
                    self.body
                        .try_reserve_exact(self.wanted)
                        .map_err(|_| Error::code("observer_allocation"))?;
                }
            } else {
                self.body.extend_from_slice(&buffer[..n]);
            }
            if self.header_count == 4 && self.body.len() == self.wanted {
                let message =
                    json::parse(&self.body).map_err(|_| Error::code("observer_invalid_json"))?;
                self.body.clear();
                self.header_count = 0;
                self.wanted = 0;
                self.partial = None;
                return Ok(Some(message));
            }
        }
        require(self.buffered() <= 1048576, "observer_buffer_limit")?;
        Ok(None)
    }
}

use crate::{contract, fs, native};
fn object(fields: impl IntoIterator<Item = (&'static str, J)>) -> J {
    J::Obj(fields.into_iter().map(|(k, v)| (k.into(), v)).collect())
}
fn string(s: &str) -> J {
    J::Str(s.into())
}
fn reference(record: &J, path: &str) -> Result<J> {
    let bytes = encode(record);
    Ok(object([
        ("ref_type", string("record")),
        ("path", string(path)),
        ("record_kind", string("launch")),
        ("schema_version", record.get("schema_version")?.clone()),
        (
            "digest",
            object([
                ("algorithm", string("sha256")),
                ("scope", string("exact_utf8_file_bytes")),
                (
                    "value",
                    string(&fs::hex(&native::sha256_bytes(bytes.as_bytes())?)),
                ),
            ]),
        ),
    ]))
}
/// Exact-request/capture-bound finite fixture session. Runtime observation authority
/// is deliberately unavailable; these messages cannot qualify real game execution.
pub struct Session {
    pub transport: Observer,
    request: J,
    request_ref: J,
    hash: String,
    capture: String,
    started: Instant,
    ready_ref: Option<J>,
    spawn_ref: Option<J>,
    exit_ref: Option<J>,
    process: Option<J>,
    pub complete: bool,
    pub failure: Option<Error>,
    pub events: Vec<J>,
    observer_sequence: i64,
}
impl Session {
    pub fn new(fd: i32, request: &J, path: &str, hash: &str, capture: &str) -> Result<Self> {
        let mut request_ref = reference(request, path)?;
        if let J::Obj(ref mut o) = request_ref {
            if let Some(J::Obj(d)) = o.get_mut("digest") {
                d.insert("value".into(), string(hash));
            }
        }
        let mut result = Self {
            transport: Observer::from_inherited(fd)?,
            request: request.clone(),
            request_ref,
            hash: hash.into(),
            capture: capture.into(),
            started: Instant::now(),
            ready_ref: None,
            spawn_ref: None,
            exit_ref: None,
            process: None,
            complete: false,
            failure: None,
            events: Vec::new(),
            observer_sequence: 0,
        };
        result.transport.enqueue(&result.packet(request.clone()))?;
        Ok(result)
    }
    fn packet(&self, record: J) -> J {
        object([
            ("protocol_version", J::Int(1)),
            ("scope", string("synthetic")),
            ("capture_id", string(&self.capture)),
            ("request_sha256", string(&self.hash)),
            ("record", record),
        ])
    }
    fn envelope(&self, packet: &J) -> Result<J> {
        packet.keys(&[
            "protocol_version",
            "scope",
            "capture_id",
            "request_sha256",
            "record",
        ])?;
        require(
            packet.get("protocol_version")?.i()? == 1
                && packet.get("scope")?.s()? == "synthetic"
                && packet.get("capture_id")?.s()? == self.capture
                && packet.get("request_sha256")?.s()? == self.hash,
            "observer_identity_mismatch",
        )?;
        let record = packet.get("record")?;
        contract::shape(record, self.request.get("schema_version")?.i()?)?;
        require(
            record.get("record_kind")?.s()? == "launch"
                && record.get("variant")?.s()? == "event"
                && record.get("record_context")? == self.request.get("record_context")?
                && record.get("producer")?.s()? == "observer"
                && record.get("request")? == &self.request_ref
                && record.get("run_id")? == self.request.get("run_id")?
                && record.get("clock_id")?.s()? == self.capture
                && record.get("sequence")?.i()? == self.observer_sequence
                && *record.get("process")? == J::Null
                && *record.get("ready_ack")? == J::Null,
            "observer_event_mismatch",
        )?;
        Ok(record.clone())
    }
    fn accept(&mut self, packet: J) -> Result<()> {
        let r = self.envelope(&packet)?;
        require(
            r.get("status")?.s()? != "unsupported",
            "observer_scope_incomplete",
        )?;
        require(
            r.get("status")?.s()? == "passed" && r.get("event")?.s()? != "gap",
            "observer_gap",
        )?;
        if self.ready_ref.is_none() {
            require(
                r.get("event")?.s()? == "observer_ready"
                    && *r.get("previous")? == J::Null
                    && r.get("elapsed_ns")?.i()? == 0
                    && r.get("covers")?.a()?.is_empty()
                    && r.get("completed_exits")?.a()?.is_empty(),
                "observer_not_ready",
            )?;
            self.ready_ref = Some(reference(&r, "observer/0.json")?);
        } else {
            require(
                !self.complete
                    && self.exit_ref.is_some()
                    && r.get("event")?.s()? == "observer_complete"
                    && r.get("previous")? == self.ready_ref.as_ref().unwrap(),
                "observer_completion_basis",
            )?;
            let process = self
                .process
                .as_ref()
                .ok_or(Error::code("observer_completion_basis"))?;
            require(
                r.get("covers")?.a()? == [process.get("token")?.clone()]
                    && r.get("completed_exits")?.a()? == [self.exit_ref.as_ref().unwrap().clone()],
                "observer_completion_basis",
            )?;
            let last = self
                .events
                .iter()
                .rev()
                .find(|e| e.get("event").and_then(J::s) == Ok("exited"))
                .ok_or(Error::code("observer_completion_basis"))?;
            require(
                r.get("elapsed_ns")?.i()? > last.get("elapsed_ns")?.i()?,
                "observer_completion_order",
            )?;
            self.complete = true;
        }
        self.observer_sequence += 1;
        require(self.events.len() < 8, "observer_event_limit")?;
        self.events.push(r);
        Ok(())
    }
    pub fn service(&mut self) {
        if self.failure.is_some() || (self.complete && !self.transport.pending()) {
            return;
        }
        let result = self.transport.service().and_then(|message| {
            if let Some(v) = message {
                self.accept(v)
            } else {
                Ok(())
            }
        });
        if let Err(e) = result {
            self.failure = Some(e);
        }
    }
    pub fn ready(&mut self, cancelled: impl Fn() -> bool, limit: Duration) -> Result<()> {
        let deadline = Instant::now() + limit.min(DEADLINE);
        loop {
            if cancelled() {
                return Err(Error::code("cancelled"));
            }
            self.service();
            if let Some(e) = self.failure.take() {
                return Err(e);
            }
            if self.ready_ref.is_some() && !self.transport.pending() {
                return Ok(());
            }
            require(Instant::now() < deadline, "observer_not_ready")?;
            std::thread::sleep(Duration::from_millis(2));
        }
    }
    fn event(&self, name: &str, sequence: i64, previous: J, process: J, ready: J) -> Result<J> {
        Ok(object([
            ("record_kind", string("launch")),
            (
                "schema_version",
                self.request.get("schema_version")?.clone(),
            ),
            (
                "record_context",
                self.request.get("record_context")?.clone(),
            ),
            (
                "record_id",
                string(&format!("{}-supervisor-{sequence}", self.capture)),
            ),
            (
                "disclosure",
                object([
                    ("mode", string("full")),
                    ("withheld", J::Arr(Vec::new())),
                    ("origin_token", J::Null),
                ]),
            ),
            ("variant", string("event")),
            ("request", self.request_ref.clone()),
            ("run_id", self.request.get("run_id")?.clone()),
            ("producer", string("supervisor")),
            ("sequence", J::Int(sequence)),
            ("previous", previous),
            ("event", string(name)),
            ("clock_id", string(&self.capture)),
            (
                "elapsed_ns",
                J::Int(self.started.elapsed().as_nanos().min(9007199254740991) as i64),
            ),
            ("process", process),
            ("status", string("passed")),
            ("covers", J::Arr(Vec::new())),
            ("ready_ack", ready),
            ("completed_exits", J::Arr(Vec::new())),
        ]))
    }
    pub fn spawned(&mut self, pid: i32, identity: (u64, u64)) -> Result<()> {
        let process = object([
            ("token", string("owned-main")),
            ("pid", J::Int(pid as i64)),
            (
                "generation",
                string(&format!("{}-{}", identity.0, identity.1)),
            ),
        ]);
        let event = self.event(
            "spawned",
            0,
            J::Null,
            process.clone(),
            self.ready_ref
                .clone()
                .ok_or(Error::code("observer_not_ready"))?,
        )?;
        self.spawn_ref = Some(reference(&event, "supervisor/0.json")?);
        self.process = Some(process);
        self.transport.enqueue(&self.packet(event.clone()))?;
        self.events.push(event);
        Ok(())
    }
    pub fn exited(&mut self) -> Result<()> {
        let event = self.event(
            "exited",
            1,
            self.spawn_ref
                .clone()
                .ok_or(Error::code("observer_spawn_missing"))?,
            self.process
                .clone()
                .ok_or(Error::code("observer_spawn_missing"))?,
            J::Null,
        )?;
        self.exit_ref = Some(reference(&event, "supervisor/1.json")?);
        self.transport.enqueue(&self.packet(event.clone()))?;
        self.events.push(event);
        Ok(())
    }
}

#[cfg(test)]
impl Session {
    // Transport-only fault setup, compiled out of all production binaries.
    pub(crate) fn pressure_fixture(fd: i32, overflow: bool) -> Self {
        let request=json::parse(br#"{"record_kind":"launch","schema_version":1,"record_context":"fixture","run_id":"pressure-fixture"}"#).unwrap();
        let mut session = Self::new(
            fd,
            &request,
            "records/request.json",
            &"0".repeat(64),
            "capture-pressure",
        )
        .unwrap();
        session.ready_ref = Some(J::Null);
        let large = J::Arr((0..127).map(|_| J::Str("x".repeat(2048))).collect());
        session.transport.enqueue(&large).unwrap();
        session.transport.enqueue(&large).unwrap();
        assert!(session.transport.queued <= QUEUE_LIMIT);
        assert!(session.transport.buffered() <= 1048576);
        if overflow {
            let error = session.transport.enqueue(&large).unwrap_err();
            assert_eq!(error.code, "observer_queue_limit");
            session.failure = Some(error);
        }
        session
    }
}
