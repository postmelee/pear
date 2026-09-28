import Foundation
import Darwin

@_silgen_name("CC_SHA256")
private func ccSHA256(_ data: UnsafeRawPointer?, _ count: UInt32, _ output: UnsafeMutablePointer<UInt8>?) -> UnsafeMutablePointer<UInt8>?

func sha256(_ data: Data) -> String {
    var output = [UInt8](repeating: 0, count: 32)
    _ = data.withUnsafeBytes { bytes in ccSHA256(bytes.baseAddress, UInt32(bytes.count), &output) }
    return output.map { String(format: "%02x", $0) }.joined()
}
func isHash(_ value: String) -> Bool {
    value.utf8.count == 64 && value.utf8.allSatisfy { (48...57).contains($0) || (97...102).contains($0) }
}
func relativePath(_ value: String) throws -> [String] {
    try require(!value.isEmpty && value.utf8.count <= 512 && !value.hasPrefix("/") && !value.hasPrefix("~") && !value.contains("%") && !value.contains("\\") && !value.contains(":"))
    let pieces = value.split(separator: "/", omittingEmptySubsequences: false).map(String.init)
    try require(pieces.count <= 32 && pieces.allSatisfy { !$0.isEmpty && $0 != "." && $0 != ".." && $0.utf8.allSatisfy { $0 >= 32 && $0 != 127 } })
    return pieces
}
final class OpenedFile {
    let fd: Int32
    let data: Data
    let info: stat
    init(_ fd: Int32, _ data: Data, _ info: stat) { self.fd = fd; self.data = data; self.info = info }
    deinit { close(fd) }
}
final class BundleFiles {
    let root: Int32
    var blobBytes = 0
    var aliases: [String: String] = [:]
    init(_ path: String) throws {
        try require(path.hasPrefix("/") && path.utf8.count <= 4096 && !path.contains("\0"))
        var fd = open("/", O_RDONLY | O_DIRECTORY | O_CLOEXEC)
        guard fd >= 0 else { throw Failure.invalid }
        do {
            let pieces = path.dropFirst().split(separator: "/", omittingEmptySubsequences: false).map(String.init)
            try require(!pieces.isEmpty && pieces.allSatisfy { !$0.isEmpty && $0 != "." && $0 != ".." })
            for piece in pieces {
                let next = openat(fd, piece, O_RDONLY | O_DIRECTORY | O_NOFOLLOW | O_CLOEXEC)
                guard next >= 0 else { throw Failure.invalid }
                close(fd); fd = next
            }
            root = fd
        } catch { close(fd); throw error }
    }
    deinit { close(root) }
    func read(_ path: String, max: Int) throws -> OpenedFile {
        let pieces = try relativePath(path)
        var directory = dup(root)
        guard directory >= 0 else { throw Failure.invalid }
        defer { close(directory) }
        for piece in pieces.dropLast() {
            let next = openat(directory, piece, O_RDONLY | O_DIRECTORY | O_NOFOLLOW | O_CLOEXEC)
            guard next >= 0 else { throw Failure.invalid }
            close(directory); directory = next
        }
        let fd = openat(directory, pieces.last!, O_RDONLY | O_NONBLOCK | O_NOFOLLOW | O_CLOEXEC)
        guard fd >= 0 else { throw Failure.invalid }
        do {
            var before = stat()
            try require(fstat(fd, &before) == 0 && (before.st_mode & S_IFMT) == S_IFREG && before.st_size >= 0 && before.st_size <= max)
            var data = Data()
            var chunk = [UInt8](repeating: 0, count: 16384)
            while true {
                let count = Darwin.read(fd, &chunk, chunk.count)
                if count < 0 && errno == EINTR { continue }
                guard count >= 0 else { throw Failure.invalid }
                if count == 0 { break }
                try require(data.count + count <= max)
                data.append(contentsOf: chunk.prefix(count))
            }
            var after = stat()
            try require(fstat(fd, &after) == 0 && sameFile(before, after) && data.count == before.st_size)
            let identity = "\(before.st_dev):\(before.st_ino)"
            if let oldPath = aliases[identity] { try require(oldPath == path) }
            aliases[identity] = path
            return OpenedFile(fd, data, before)
        } catch { close(fd); throw error }
    }
}
func sameFile(_ a: stat, _ b: stat) -> Bool {
    a.st_dev == b.st_dev && a.st_ino == b.st_ino && a.st_size == b.st_size &&
    a.st_mtimespec.tv_sec == b.st_mtimespec.tv_sec && a.st_mtimespec.tv_nsec == b.st_mtimespec.tv_nsec &&
    a.st_ctimespec.tv_sec == b.st_ctimespec.tv_sec && a.st_ctimespec.tv_nsec == b.st_ctimespec.tv_nsec
}
