// SPDX-FileCopyrightText: 2026 Pear contributors
// SPDX-License-Identifier: GPL-3.0-or-later
import AppKit

// Presentation only. The same Rust binary serves this window and the CLI.
final class PreviewApp: NSObject, NSApplicationDelegate {
    var window: NSWindow!
    var label: NSTextField!
    var button: NSButton!
    var task: Process?
    var closing = false
    func applicationDidFinishLaunching(_ notification: Notification) {
        window = NSWindow(contentRect: NSRect(x: 0, y: 0, width: 520, height: 220),
                          styleMask: [.titled, .closable, .miniaturizable], backing: .buffered, defer: false)
        window.title = "Pear Preview"
        window.isReleasedWhenClosed = false
        let title = NSTextField(labelWithString: "Windows Steam · Preview")
        title.font = .boldSystemFont(ofSize: 21)
        title.frame = NSRect(x: 24, y: 164, width: 472, height: 30)
        label = NSTextField(wrappingLabelWithString: "Preparing…")
        label.frame = NSRect(x: 24, y: 58, width: 472, height: 96)
        button = NSButton(title: "Open Steam again", target: self, action: #selector(start))
        button.frame = NSRect(x: 304, y: 16, width: 192, height: 32)
        for view in [title, label!, button!] { window.contentView!.addSubview(view) }
        window.center(); window.makeKeyAndOrderFront(nil)
        NSApp.activate(ignoringOtherApps: true)
        start()
    }
    @objc func start() {
        guard task == nil else { return }
        button.isEnabled = false
        label.stringValue = "Preparing…"
        let process = Process()
        process.executableURL = Bundle.main.resourceURL!.appendingPathComponent("pear-preview")
        process.arguments = ["steam"]
        // The child inherits PEAR_PREVIEW_RUNTIME_ARCHIVE for a pinned local candidate.
        // A developer may select an isolated test root without changing shared core logic.
        if let root = ProcessInfo.processInfo.environment["PEAR_PREVIEW_ROOT"] {
            process.arguments! += ["--root", root]
        }
        let pipe = Pipe()
        process.standardInput = FileHandle.nullDevice
        process.standardOutput = pipe
        process.standardError = pipe
        pipe.fileHandleForReading.readabilityHandler = { handle in
            let data = handle.availableData
            guard !data.isEmpty else { handle.readabilityHandler = nil; return }
            let value = String(decoding: data, as: UTF8.self).trimmingCharacters(in: .whitespacesAndNewlines)
            DispatchQueue.main.async {
                self.label.stringValue = value
            }
        }
        process.terminationHandler = { process in
            DispatchQueue.main.async {
                self.task = nil
                self.button.title = process.terminationStatus == 0 ? "Open Steam again" : "Retry"
                self.button.isEnabled = true
                if self.closing { NSApp.reply(toApplicationShouldTerminate: true) }
            }
        }
        do { try process.run(); task = process }
        catch { label.stringValue = "Cannot start Pear Preview: \(error.localizedDescription)"; button.isEnabled = true }
    }
    func applicationShouldTerminateAfterLastWindowClosed(_ sender: NSApplication) -> Bool { true }
    func applicationShouldTerminate(_ sender: NSApplication) -> NSApplication.TerminateReply {
        guard let task, task.isRunning else { return .terminateNow }
        closing = true
        task.interrupt()
        return .terminateLater
    }
}
let app = NSApplication.shared
let delegate = PreviewApp()
app.delegate = delegate
app.setActivationPolicy(.regular)
app.run()
