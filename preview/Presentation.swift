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
