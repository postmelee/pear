// SPDX-FileCopyrightText: 2026 Pear contributors
// SPDX-License-Identifier: GPL-3.0-or-later
import Foundation

struct SetupInfo: Decodable {
    let version: String
    let runtime_id: String
    let runtime_bytes: UInt64
    let steam_bytes: UInt64
    let runtime_present: Bool
    let steam_present: Bool
    let ready: Bool
}

// Pipe reads can split a UTF-8 scalar or contain several complete updates.
struct OutputLines {
    private var pending = Data()
    mutating func append(_ data: Data) -> [String] {
        pending.append(data)
        var lines: [String] = []
        while let end = pending.firstIndex(of: 10) {
            lines.append(String(decoding: pending[..<end], as: UTF8.self))
            pending.removeSubrange(...end)
        }
        if pending.count > 65_536 {
            pending.removeAll()
            lines.append("Preparation output exceeded its limit. Close Pear and retry.")
        }
        return lines
    }
    mutating func finish() -> [String] {
        guard !pending.isEmpty else { return [] }
        defer { pending.removeAll() }
        return [String(decoding: pending, as: UTF8.self)]
    }
}

enum SetupUpdate {
    case status(String)
    case download(received: UInt64, total: UInt64, name: String)
    init(_ line: String) {
        let parts = line.split(separator: "\t", omittingEmptySubsequences: false)
        if parts.count == 4, parts[0] == "@download",
           let received = UInt64(parts[1]), let total = UInt64(parts[2]), total > 0 {
            self = .download(received: received, total: total, name: String(parts[3]))
        } else {
            self = .status(line)
        }
    }
}

func downloadSize(_ bytes: UInt64) -> String {
    String(format: "%.1f MB", Double(bytes) / 1_000_000)
}


// A window observation is not proof of authentication or a responsive library.
enum SteamOpening: Equatable {
    case waiting, delayed, visible, unconfirmed
    static func state(elapsed: TimeInterval, visible: Bool) -> Self {
        if visible { return .visible }
        if elapsed >= 120 { return .unconfirmed }
        return elapsed >= 30 ? .delayed : .waiting
    }
    var observing: Bool { self == .waiting || self == .delayed }
    var retryEnabled: Bool { self != .waiting }
    var title: String {
        switch self {
        case .waiting, .delayed: return "Opening Steam…"
        case .visible: return "Steam window is open"
        case .unconfirmed: return "Check Steam"
        }
    }
    var message: String {
        switch self {
        case .waiting:
            return "This may take a little while, especially while Steam updates. Its window will appear separately."
        case .delayed:
            return "Steam is taking longer than usual. It may still be updating. If no Steam window appears, you can try opening it again."
        case .visible:
            return "Continue in the Steam window. It may still be updating or loading. You can close Pear; Steam and your games stay open."
        case .unconfirmed:
            return "Pear could not confirm a visible Steam window. Check Steam in the Dock. If no window appears, try opening it again."
        }
    }
}

// Darwin KERN_PROCARGS2: argc, executable path, padding, argv, environment.
// Read only to identify a window owner; never log or retain the environment.
func steamProcessMatches(_ data: Data, executable: String, prefix: String) -> Bool {
    let bytes = [UInt8](data)
    guard bytes.count >= 4 else { return false }
    let argc = bytes.withUnsafeBytes { $0.loadUnaligned(as: Int32.self) }
    guard argc > 0, argc <= 4096 else { return false }
    var at = 4
    func take() -> String? {
        guard at < bytes.count, let end = bytes[at...].firstIndex(of: 0) else { return nil }
        defer { at = end + 1 }
        return String(bytes: bytes[at..<end], encoding: .utf8)
    }
    guard take() == executable else { return false }
    while at < bytes.count && bytes[at] == 0 { at += 1 }
    var steam = false
    for _ in 0..<argc {
        guard let argument = take() else { return false }
        let name = argument.lowercased().replacingOccurrences(of: "/", with: "\\")
        if name == "c:\\program files (x86)\\steam\\steam.exe" ||
           name == "c:\\program files (x86)\\steam\\bin\\cef\\cef.win64\\steamwebhelper.exe" {
            steam = true
        }
    }
    guard steam else { return false }
    // Wine rewrites argv and leaves NUL padding before the original environment.
    while at < bytes.count && bytes[at] == 0 { at += 1 }
    var prefixes: [String] = []
    while at < bytes.count {
        guard let entry = take() else { return false }
        if entry.isEmpty { break }
        if entry.hasPrefix("WINEPREFIX=") { prefixes.append(String(entry.dropFirst(11))) }
    }
    return prefixes == [prefix]
}
