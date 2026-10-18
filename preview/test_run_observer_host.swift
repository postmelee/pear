// SPDX-FileCopyrightText: 2026 Pear contributors
// SPDX-License-Identifier: GPL-3.0-or-later
import Foundation
import Darwin
@main struct HostObserverTests {
    static func main() throws {
        if CommandLine.arguments.contains("--child") { Thread.sleep(forTimeInterval: 4); return }
        let root = FileManager.default.temporaryDirectory.resolvingSymlinksInPath().appendingPathComponent(UUID().uuidString)
        defer { try? FileManager.default.removeItem(at: root) }
        let executable = root.appendingPathComponent("runtimes/fixture/Libraries/Wine/lib/wine/x86_64-unix/wine64")
        try FileManager.default.createDirectory(at: executable.deletingLastPathComponent(), withIntermediateDirectories: true)
        try FileManager.default.copyItem(at: URL(fileURLWithPath: CommandLine.arguments[0]), to: executable)
        try FileManager.default.createDirectory(at: root.appendingPathComponent("private/prefix"), withIntermediateDirectories: true)
        let child = Process(); child.executableURL = executable; child.arguments = ["--child"]
        child.environment = ["WINEPREFIX":root.appendingPathComponent("private/prefix").path,"SteamAppId":"3405340"]
        try child.run()
        defer { if child.isRunning { child.terminate(); child.waitUntilExit() } }
        Thread.sleep(forTimeInterval:0.2)
        let probe = OwnedProcessProbe(root:root,runtime:"fixture")
        let first = probe.snapshot(previous:[])
        guard first.complete && first.processes.contains(where: { $0.pid == child.processIdentifier && $0.appID == 3405340 }) else { throw CocoaError(.fileReadUnknown) }
        let other = OwnedProcessProbe(root:root.appendingPathComponent("other"),runtime:"fixture").snapshot(previous:[])
        precondition(other.processes.isEmpty)
        var state = RunObserverState()
        let started = state.consume(first,now:Date(),monotonic:ProcessInfo.processInfo.systemUptime)
        precondition(started.0.count == 1)
        child.waitUntilExit()
        let last = probe.snapshot(previous:first.processes)
        let ended = state.consume(last,now:Date(),monotonic:ProcessInfo.processInfo.systemUptime)
        precondition(ended.1.count == 1 && ended.1[0].exit == .exited)
        print("PASS: real macOS PID/start/argv/prefix observation and natural exit; synthetic executable, no Wine/game execution")
    }
}
