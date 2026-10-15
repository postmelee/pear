// SPDX-FileCopyrightText: 2026 Pear contributors
// SPDX-License-Identifier: GPL-3.0-or-later
import AppKit
import Darwin

// No pixels, window titles, Accessibility APIs or stored process environments.
// Failure to read metadata means unknown, not successful Steam startup.
struct SteamWindowProbe {
    let root: URL
    let runtime: String

    func visible() -> Bool {
        let executable = root.appendingPathComponent("runtimes/\(runtime)/Libraries/Wine/lib/wine/x86_64-unix/wine").path
        let prefix = root.appendingPathComponent("private/prefix").path
        guard let windows = CGWindowListCopyWindowInfo([.optionOnScreenOnly, .excludeDesktopElements], kCGNullWindowID) as? [[String: Any]] else { return false }
        var owners: [pid_t: Bool] = [:]
        for window in windows {
            guard let pid = (window[kCGWindowOwnerPID as String] as? NSNumber)?.int32Value,
                  pid > 0,
                  (window[kCGWindowLayer as String] as? NSNumber)?.intValue == 0,
                  (window[kCGWindowAlpha as String] as? NSNumber)?.doubleValue ?? 0 > 0,
                  let bounds = window[kCGWindowBounds as String] as? [String: Any],
                  let width = bounds["Width"] as? NSNumber, width.doubleValue > 1,
                  let height = bounds["Height"] as? NSNumber, height.doubleValue > 1 else { continue }
            if owners[pid] == nil {
                owners[pid] = matches(pid: pid, executable: executable, prefix: prefix)
            }
            if owners[pid] == true { return true }
        }
        return false
    }

    private func matches(pid: pid_t, executable: String, prefix: String) -> Bool {
        var path = [CChar](repeating: 0, count: 4 * Int(MAXPATHLEN))
        guard proc_pidpath(pid, &path, UInt32(path.count)) > 0,
              String(cString: path) == executable else { return false }
        var query: [Int32] = [CTL_KERN, KERN_PROCARGS2, pid]
        var bytes = [UInt8](repeating: 0, count: 262_144)
        var size = bytes.count
        let status = bytes.withUnsafeMutableBytes {
            sysctl(&query, u_int(query.count), $0.baseAddress, &size, nil, 0)
        }
        guard status == 0, size <= bytes.count else { return false }
        let matched = steamProcessMatches(Data(bytes.prefix(size)), executable: executable, prefix: prefix)
        // Recheck the executable after reading arguments; PIDs are not persistent identities.
        guard matched, proc_pidpath(pid, &path, UInt32(path.count)) > 0 else { return false }
        return String(cString: path) == executable
    }
}
