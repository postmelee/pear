// SPDX-FileCopyrightText: 2026 Pear contributors
// SPDX-License-Identifier: GPL-3.0-or-later
import AppKit

// Presentation only. The same Rust binary serves this window and the CLI.
@MainActor final class PreviewApp: NSObject, NSApplicationDelegate {
    var window: NSWindow!
    var titleLabel: NSTextField!
    var label: NSTextField!
    var downloads: NSGridView!
    var progress: NSProgressIndicator!
    var busy: NSProgressIndicator!
    var button: NSButton!
    var cancelButton: NSButton!
    var task: Process?
    var info: SetupInfo?
    var lines = OutputLines()
    var closing = false
    var stopping = false
    var openingGeneration = 0
    var history: HistoryWindow?
    var historyStore: ReportingStore?
    var historyOwner: ReportingSessionOwner?
    var runObserver = RunObserverState()
    var observationGeneration = 0
    var observedOwnedSession = false
    var observerStarted = Date()
    var sawOwnedSession = false
    var historyError: String?

    @objc func showHistory() {
        if let history { history.show(); return }
        let alert = NSAlert(); alert.messageText = "Run history is unavailable"
        alert.informativeText = historyError ?? "Wait for Pear to check the installation."
        alert.beginSheetModal(for: window)
    }

    func prepareHistory(_ setup: SetupInfo) {
        guard historyStore == nil, historyError == nil else { return }
        let env = ProcessInfo.processInfo.environment
        let root = URL(fileURLWithPath: env["PEAR_PREVIEW_ROOT"] ??
            NSHomeDirectory() + "/Library/Application Support/Pear Preview").standardizedFileURL.resolvingSymlinksInPath()
        do {
            let directory = root.appendingPathComponent("history")
            let store = try ReportingStore(directory: directory)
            let owner = try ReportingSessionOwner(directory: directory)
            // Reopening cannot establish the end of an observation interrupted by Quit.
            try store.transaction { state in
                for i in state.runs.indices where state.runs[i].endedAt == nil {
                    state.runs[i].observedExit = .unknown
                }
            }
            historyOwner = owner; historyStore = store; history = HistoryWindow(store: store)
            observationGeneration += 1
            pollRuns(OwnedProcessProbe(root: root, runtime: setup.runtime_id), generation: observationGeneration)
        } catch { historyError = "Another Pear observer may be running, or local storage is unavailable. No reports will be sent." }
    }

    func pollRuns(_ probe: OwnedProcessProbe, generation: Int) {
        guard !closing, generation == observationGeneration else { return }
        let previous = runObserver.previous
        windowQueue.async {
            let snapshot = probe.snapshot(previous: previous)
            DispatchQueue.main.async {
                guard !self.closing, generation == self.observationGeneration, let store = self.historyStore else { return }
                self.observedOwnedSession = !snapshot.complete || !snapshot.processes.isEmpty
                if !snapshot.processes.isEmpty { self.sawOwnedSession = true }
                let (started, finished) = self.runObserver.consume(snapshot, now: Date(), monotonic: ProcessInfo.processInfo.systemUptime)
                do {
                    for session in started {
                        let version = ProcessInfo.processInfo.operatingSystemVersion
                        let run = RunObservation(id: session.id, startedAt: session.began,
                            macOS: "\(version.majorVersion).\(version.minorVersion).\(version.patchVersion)",
                            memoryGiB: Int(ProcessInfo.processInfo.physicalMemory / (1024 * 1024 * 1024)),
                            pear: self.info?.version ?? "Unknown", wine: "11.0", dxmt: "0.80", appID: session.appID)
                        try store.record(run)
                    }
                    for finish in finished {
                        guard var run = store.snapshot.runs.first(where: { $0.id == finish.session.id }) else { continue }
                        run.endedAt = finish.observedEnd; run.observedExit = finish.exit
                        try store.record(run)
                        self.history?.confirmFinished(run.id)
                    }
                    self.history?.refresh()
                } catch { self.historyError = "Run history could not be saved. Sharing is stopped." }
                if snapshot.complete, snapshot.processes.isEmpty, self.task == nil,
                   !self.window.isVisible, !(self.history?.isVisible ?? false),
                   self.sawOwnedSession || Date().timeIntervalSince(self.observerStarted) > 120 {
                    NSApp.terminate(nil); return
                }
                DispatchQueue.main.asyncAfter(deadline: .now() + 2) { [weak self] in
                    self?.pollRuns(probe, generation: generation)
                }
            }
        }
    }
    let windowQueue = DispatchQueue(label: "org.pear.steam-window", qos: .utility)

    func observeSteam() {
        openingGeneration += 1
        let generation = openingGeneration
        let env = ProcessInfo.processInfo.environment
        let root = URL(fileURLWithPath: env["PEAR_PREVIEW_ROOT"] ??
            (env["HOME"] ?? NSHomeDirectory()) + "/Library/Application Support/Pear Preview")
            .standardizedFileURL.resolvingSymlinksInPath()
        let probe = SteamWindowProbe(root: root, runtime: info!.runtime_id)
        let began = ProcessInfo.processInfo.systemUptime
        showOpening(.waiting)
        pollSteam(probe, began: began, generation: generation)
    }

    func showOpening(_ state: SteamOpening) {
        titleLabel.stringValue = state.title
        label.stringValue = state.message
        button.title = "Open Steam again"
        button.isEnabled = state.retryEnabled
        busy.setAccessibilityLabel("Opening Steam")
        busy.isHidden = !state.observing
        if state.observing { busy.startAnimation(nil) } else { busy.stopAnimation(nil) }
    }

    func pollSteam(_ probe: SteamWindowProbe, began: TimeInterval, generation: Int) {
        guard !closing, generation == openingGeneration else { return }
        windowQueue.async {
            let visible = probe.visible()
            DispatchQueue.main.async {
                guard !self.closing, generation == self.openingGeneration else { return }
                let state = SteamOpening.state(elapsed: ProcessInfo.processInfo.systemUptime - began, visible: visible)
                self.showOpening(state)
                if state.observing {
                    DispatchQueue.main.asyncAfter(deadline: .now() + 1) { [weak self] in
                        self?.pollSteam(probe, began: began, generation: generation)
                    }
                }
            }
        }
    }

    func applicationDidFinishLaunching(_ notification: Notification) {
        window = NSWindow(contentRect: NSRect(x: 0, y: 0, width: 580, height: 370),
                          styleMask: [.titled, .closable, .miniaturizable], backing: .buffered, defer: false)
        window.title = "Pear"
        window.isReleasedWhenClosed = false
        titleLabel = NSTextField(labelWithString: "Set up Pear")
        titleLabel.font = .boldSystemFont(ofSize: 23)
        titleLabel.frame = NSRect(x: 24, y: 306, width: 532, height: 34)
        label = NSTextField(wrappingLabelWithString: "Checking your installation…")
        label.frame = NSRect(x: 24, y: 218, width: 532, height: 78)
        progress = NSProgressIndicator(frame: NSRect(x: 24, y: 83, width: 532, height: 18))
        progress.style = .bar
        progress.isIndeterminate = false
        progress.setAccessibilityLabel("Setup progress")
        progress.isHidden = true
        busy = NSProgressIndicator(frame: NSRect(x: 24, y: 83, width: 18, height: 18))
        busy.style = .spinning
        busy.isIndeterminate = true
        busy.setAccessibilityLabel("Preparing")
        busy.isHidden = true
        button = NSButton(title: "Download and install", target: self, action: #selector(start))
        button.frame = NSRect(x: 342, y: 24, width: 214, height: 32)
        button.keyEquivalent = "\r"
        button.isEnabled = false
        cancelButton = NSButton(title: "Cancel", target: self, action: #selector(cancelSetup))
        cancelButton.frame = NSRect(x: 238, y: 24, width: 96, height: 32)
        cancelButton.isHidden = true
        let about = NSButton(title: "About Pear", target: self, action: #selector(showAbout))
        about.frame = NSRect(x: 24, y: 24, width: 116, height: 32)
        let historyButton = NSButton(title: "Run history", target: self, action: #selector(showHistory))
        historyButton.frame = NSRect(x: 145, y: 24, width: 94, height: 32)
        for view in [historyButton, titleLabel!, label!, progress!, busy!, button!, cancelButton!, about] {
            window.contentView!.addSubview(view)
        }
        window.center(); window.makeKeyAndOrderFront(nil)
        NSApp.activate(ignoringOtherApps: true)
        inspectSetup()
    }

    func process(_ command: String) -> Process {
        let child = Process()
        child.executableURL = Bundle.main.resourceURL!.appendingPathComponent("pear-preview")
        child.arguments = [command]
        if command != "setup-info" { child.arguments! += ["--output", "events"] }
        if let root = ProcessInfo.processInfo.environment["PEAR_PREVIEW_ROOT"] {
            child.arguments! += ["--root", root]
        }
        child.standardInput = FileHandle.nullDevice
        return child
    }

    // No state creation or network: only the core's read-only metadata command.
    func inspectSetup() {
        launch(process("setup-info"), inspecting: true)
    }

    func showSetup(_ value: SetupInfo) {
        info = value
        prepareHistory(value)
        if value.ready {
            start()
            return
        }
        label.stringValue = "Pear needs these files to open Windows Steam. Download sizes are shown below. Steam updates and games download separately; their sizes vary."
        downloads?.removeFromSuperview()
        downloads = NSGridView(views: [
            [NSTextField(labelWithString: "Required files"), NSTextField(labelWithString: "Download")],
            [NSTextField(labelWithString: "Runtime · Wine 11.0 + DXMT 0.80"),
             NSTextField(labelWithString: value.runtime_present ? "Installed" : downloadSize(value.runtime_bytes))],
            [NSTextField(labelWithString: "Steam installer"),
             NSTextField(labelWithString: value.steam_present ? "Installed" : downloadSize(value.steam_bytes))]
        ])
        downloads.frame = NSRect(x: 24, y: 113, width: 532, height: 90)
        downloads.columnSpacing = 30
        downloads.rowSpacing = 12
        downloads.column(at: 1).xPlacement = .trailing
        window.contentView!.addSubview(downloads)
        button.title = "Download and install"
        button.isEnabled = true
    }

    @objc func showAbout() {
        let alert = NSAlert()
        alert.messageText = "Pear"
        let version = info?.version ?? "0.1.0"
        alert.informativeText = "Version \(version)\nRuntime: Wine 11.0 · DXMT 0.80\nRosetta required\n\nFree and open source · GPL-3.0-or-later\n\nSteam, games and saves are kept in your user’s Library/Application Support/Pear Preview folder."
        alert.addButton(withTitle: "OK")
        alert.beginSheetModal(for: window)
    }

    @objc func start() {
        guard task == nil else { return }
        // Retry a failed metadata inspection before offering any download action.
        guard info != nil else { inspectSetup(); return }
        openingGeneration += 1
        button.isEnabled = false
        downloads?.isHidden = true
        titleLabel.stringValue = "Preparing Steam"
        label.stringValue = "Checking the installed files…"
        progress.isHidden = true
        busy.isHidden = false
        busy.startAnimation(nil)
        cancelButton.isHidden = false
        cancelButton.isEnabled = true
        stopping = false
        lines = OutputLines()
        launch(process("steam"), inspecting: false)
    }

    @objc func cancelSetup() {
        guard let task, task.isRunning else { return }
        stopping = true
        cancelButton.isEnabled = false
        label.stringValue = "Stopping setup. Existing games and saves will be kept."
        task.interrupt()
    }

    func display(_ line: String) {
        guard !stopping, !line.isEmpty else { return }
        switch SetupUpdate(line) {
        case let .download(received, total, name):
            busy.stopAnimation(nil)
            busy.isHidden = true
            progress.isHidden = false
            progress.minValue = 0
            progress.maxValue = 1
            progress.doubleValue = Double(min(received, total)) / Double(total)
            let item = name == "SteamSetup.exe" ? "Steam installer" : "Pear runtime"
            label.stringValue = "Downloading \(item)…\n\(downloadSize(received)) of \(downloadSize(total))"
        case let .status(message):
            progress.isHidden = true
            busy.isHidden = false
            busy.startAnimation(nil)
            label.stringValue = message
        }
    }

    func launch(_ child: Process, inspecting: Bool) {
        let pipe = Pipe()
        child.standardOutput = pipe
        child.standardError = pipe
        do {
            try child.run()
            task = child
        } catch {
            label.stringValue = "Cannot start Pear: \(error.localizedDescription)"
            button.title = "Retry"
            button.isEnabled = true
            progress.isHidden = true
            busy.stopAnimation(nil)
            busy.isHidden = true
            cancelButton.isHidden = true
            return
        }
        // One reader preserves ordering through EOF, then delivers termination.
        DispatchQueue.global(qos: .userInitiated).async {
            var metadata = Data()
            while true {
                let data = pipe.fileHandleForReading.availableData
                if data.isEmpty { break }
                if inspecting {
                    if metadata.count < 65_536 { metadata.append(data) }
                } else {
                    DispatchQueue.main.async {
                        for line in self.lines.append(data) { self.display(line) }
                    }
                }
            }
            child.waitUntilExit()
            let result = metadata
            DispatchQueue.main.async {
                self.task = nil
                self.busy.stopAnimation(nil)
                self.busy.isHidden = true
                self.progress.isHidden = true
                self.cancelButton.isHidden = true
                if self.closing {
                    NSApp.reply(toApplicationShouldTerminate: true)
                    return
                }
                if inspecting {
                    if child.terminationStatus == 0,
                       let value = try? JSONDecoder().decode(SetupInfo.self, from: result) {
                        self.showSetup(value)
                    } else {
                        self.label.stringValue = "Cannot check installation. Close Pear and try again."
                        self.button.title = "Retry"
                        self.button.isEnabled = true
                    }
                } else {
                    for line in self.lines.finish() { self.display(line) }
                    self.busy.stopAnimation(nil)
                    self.busy.isHidden = true
                    self.progress.isHidden = true
                    self.titleLabel.stringValue = child.terminationStatus == 0 ? "Windows Steam" : "Setup paused"
                    self.button.title = child.terminationStatus == 0 ? "Open Steam again" : "Retry"
                    self.button.isEnabled = true
                    if child.terminationStatus == 0 && !self.stopping { self.observeSteam() }
                    if self.stopping { self.label.stringValue = "Setup stopped. Existing games and saves were kept. Select Retry to continue." }
                }
                if self.closing { NSApp.reply(toApplicationShouldTerminate: true) }
            }
        }
    }

    func applicationShouldHandleReopen(_ sender: NSApplication, hasVisibleWindows flag: Bool) -> Bool {
        window.makeKeyAndOrderFront(nil); return true
    }

    func applicationShouldTerminateAfterLastWindowClosed(_ sender: NSApplication) -> Bool {
        // Retain the observation owner after the window closes; explicit Quit
        // still leaves Steam and games running. No global Wine termination.
        return historyOwner == nil
    }
    func applicationShouldTerminate(_ sender: NSApplication) -> NSApplication.TerminateReply {
        closing = true
        observationGeneration += 1
        openingGeneration += 1
        guard let task, task.isRunning else { return .terminateNow }
        task.interrupt()
        return .terminateLater
    }
}

@main
struct PearMain {
    static func main() {
        let app = NSApplication.shared
        let delegate = PreviewApp()
        app.delegate = delegate
        app.setActivationPolicy(.regular)
        app.run()
    }
}
