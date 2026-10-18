// SPDX-FileCopyrightText: 2026 Pear contributors
// SPDX-License-Identifier: GPL-3.0-or-later
import AppKit
import UserNotifications

// Presentation only. The same Rust binary serves this window and the CLI.
@MainActor final class PreviewApp: NSObject, NSApplicationDelegate, UNUserNotificationCenterDelegate {
    var window: NSWindow!
    var titleLabel: NSTextField!
    var label: NSTextField!
    var downloads: NSGridView!
    var downloadHost: NSStackView!
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
    var reporting: ReportingCoordinator?
    var reportingTransport: URLSessionReportTransport?
    var serverDeletes: [UUID: ReportTransfer] = [:]
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

    @objc func showSharingSettings() {
        guard let history else { showHistory(); return }
        history.showSharingSettings()
    }

    func prepareHistory(_ setup: SetupInfo) {
        guard historyStore == nil, historyError == nil else { return }
        let env = ProcessInfo.processInfo.environment
        let root = URL(fileURLWithPath: env["PEAR_PREVIEW_ROOT"] ??
            NSHomeDirectory() + "/Library/Application Support/Pear Preview").standardizedFileURL.resolvingSymlinksInPath()
        do {
            let directory = root.appendingPathComponent("history")
            // Acquire ownership before decoding or migrating any persistent state.
            let owner = try ReportingSessionOwner(directory: directory)
            let store = try ReportingStore(directory: directory)
            // Reopening cannot establish the end of an observation interrupted by Quit.
            try store.transaction { state in
                for i in state.runs.indices where state.runs[i].endedAt == nil {
                    state.runs[i].observedExit = .unknown
                }
            }
            let transport = try URLSessionReportTransport(endpoint: URL(string: "https://pear-reports.postmelee.workers.dev/reports")!, capabilities: KeychainReportCapabilities())
            let coordinator = ReportingCoordinator(store: store, transport: transport)
            try coordinator.pruneLocalHistory()
            let view = HistoryWindow(store: store)
            historyOwner = owner; historyStore = store; history = view
            reporting = coordinator; reportingTransport = transport
            view.submit = { run, note in try coordinator.enqueue(run, origin: .manual, shareNote: note) }
            view.configureSharing = { mode, fields in try coordinator.configure(mode: mode, fields: fields) }
            view.retryReport = { id in try coordinator.retry(reportID: id) }
            view.deleteLocalRecord = { id in try coordinator.deleteLocal(reportID: id) }
            view.deleteServerReport = { [weak self] id, done in
                guard let self, self.serverDeletes[id] == nil else { return }
                do {
                    try coordinator.prepareServerDeletion(reportID: id)
                    self.serverDeletes[id] = transport.delete(reportID: id) { [weak self] success in
                        self?.serverDeletes.removeValue(forKey: id)
                        do {
                            if success { try coordinator.confirmServerDeletion(reportID: id) }
                            done(success)
                        } catch { done(false) }
                    }
                } catch { done(false) }
            }
            view.enableNotifications = { UNUserNotificationCenter.current().requestAuthorization(options: [.alert, .sound]) { _, _ in } }
            coordinator.changed = { [weak view] in view?.refresh() }
            view.showSharingIntroductionIfNeeded()
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
                        let identity = installedGameIdentity(root: probe.root, appID: session.appID)
                        let run = RunObservation(id: session.id, startedAt: session.began,
                            macOS: "\(version.majorVersion).\(version.minorVersion).\(version.patchVersion)",
                            chip: reportingChipName(), memoryGiB: Int(ProcessInfo.processInfo.physicalMemory / (1024 * 1024 * 1024)),
                            pear: Bundle.main.object(forInfoDictionaryKey: "CFBundleShortVersionString") as? String ?? self.info?.version ?? "Unknown", wine: "11.0", dxmt: "0.80", appID: session.appID, gameBuild: identity.build, gameName: identity.name)
                        try store.record(run)
                    }
                    for finish in finished {
                        guard var run = store.snapshot.runs.first(where: { $0.id == finish.session.id }) else { continue }
                        run.endedAt = finish.observedEnd; run.observedExit = finish.exit
                        try store.record(run)
                        if store.snapshot.policy.consent.mode == .automatic {
                            try self.reporting?.enqueue(run, origin: .automatic)
                            if store.snapshot.policy.shouldNotifyExit {
                                let content = UNMutableNotificationContent()
                                content.title = "Run recorded"
                                content.body = "Open Pear’s Run history to add a result or note."
                                UNUserNotificationCenter.current().add(UNNotificationRequest(identifier: run.id.uuidString, content: content, trigger: nil))
                            }
                        } else { self.history?.confirmFinished(run.id) }
                    }
                    self.history?.refresh()
                    self.reporting?.sendNext()
                } catch {
                    self.reporting?.stop()
                    self.historyError = "Run history could not be saved. Sharing is stopped."
                }
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

    nonisolated func userNotificationCenter(_ center: UNUserNotificationCenter, willPresent notification: UNNotification, withCompletionHandler completionHandler: @escaping (UNNotificationPresentationOptions) -> Void) {
        completionHandler([.banner, .sound])
    }
    nonisolated func userNotificationCenter(_ center: UNUserNotificationCenter, didReceive response: UNNotificationResponse, withCompletionHandler completionHandler: @escaping () -> Void) {
        Task { @MainActor in self.showHistory() }
        completionHandler()
    }

    func applicationDidFinishLaunching(_ notification: Notification) {
        UNUserNotificationCenter.current().delegate = self
        buildMainWindow()
        window.center(); window.makeKeyAndOrderFront(nil)
        NSApp.activate(ignoringOtherApps: true)
        let menu = NSMenu()
        let appItem = NSMenuItem(); let appMenu = NSMenu()
        let runsItem = NSMenuItem(title: "Run history", action: #selector(showHistory), keyEquivalent: "h"); runsItem.target = self
        let aboutItem = NSMenuItem(title: "About Pear", action: #selector(showAbout), keyEquivalent: ""); aboutItem.target = self
        appMenu.addItem(aboutItem); appMenu.addItem(.separator())
        let sharingItem = NSMenuItem(title:"Settings…",action:#selector(showSharingSettings),keyEquivalent:",");sharingItem.target=self
        appMenu.addItem(sharingItem); appMenu.addItem(.separator())
        appMenu.addItem(NSMenuItem(title: "Quit Pear", action: #selector(NSApplication.terminate(_:)), keyEquivalent: "q"))
        appItem.submenu = appMenu; menu.addItem(appItem)
        let windowItem=NSMenuItem(title:"Window",action:nil,keyEquivalent:"")
        let windowMenu=NSMenu(title:"Window");windowMenu.addItem(runsItem)
        runsItem.keyEquivalentModifierMask=[.command,.shift]
        windowItem.submenu=windowMenu;menu.addItem(windowItem);NSApp.windowsMenu=windowMenu
        NSApp.mainMenu = menu
        inspectSetup()
    }

    // Shared by the shipped launcher and the isolated, network-free UI review.
    func buildMainWindow() {
        window = NSWindow(contentRect:NSRect(x:0,y:0,width:600,height:340),
                          styleMask:[.titled,.closable,.miniaturizable],backing:.buffered,defer:false)
        window.title = "Pear"; window.isReleasedWhenClosed = false; PearStyle.window(window)
        let titlebar = NSTitlebarAccessoryViewController()
        let mark = NSImageView(image:Bundle.main.url(forResource:"PearMark",withExtension:"png").flatMap { NSImage(contentsOf:$0) } ?? NSApp.applicationIconImage)
        mark.widthAnchor.constraint(equalToConstant:16).isActive=true
        mark.heightAnchor.constraint(equalToConstant:16).isActive=true
        let titleContent = PearStyle.stack([mark,PearStyle.label("Pear",size:13,weight:.semibold)],horizontal:true,spacing:6)
        titleContent.frame = NSRect(x:0,y:0,width:72,height:24)
        titlebar.view=titleContent;titlebar.layoutAttribute = .left
        window.titleVisibility = .hidden;window.addTitlebarAccessoryViewController(titlebar)
        titleLabel = PearStyle.label("Set up Pear",size:28,weight:.semibold)
        label = PearStyle.label("Checking your installation…",size:14,muted:true)
        downloadHost = PearStyle.stack([])
        progress = NSProgressIndicator();progress.style = .bar;progress.isIndeterminate=false
        progress.setAccessibilityLabel("Setup progress");progress.isHidden=true
        busy = NSProgressIndicator();busy.style = .spinning;busy.isIndeterminate=true
        busy.controlSize = .small;busy.setAccessibilityLabel("Preparing");busy.isHidden=true
        let status = PearStyle.stack([busy!,progress!],horizontal:true)
        button = PearStyle.button("Download and install",target:self,action:#selector(start),primary:true)
        button.keyEquivalent="\r";button.isEnabled=false
        cancelButton = PearStyle.button("Cancel",target:self,action:#selector(cancelSetup));cancelButton.isHidden=true
        let actions = PearStyle.stack([NSView(),cancelButton!,button!],horizontal:true,spacing:16)
        let page=PearStyle.stack([titleLabel!,label!,downloadHost,status,NSView(),actions],spacing:16)
        page.setCustomSpacing(8,after:titleLabel!)
        page.setCustomSpacing(26,after:label!)
        PearStyle.pin(page,in:window.contentView!)
        for view in [label!,downloadHost!,status,actions] {
            view.widthAnchor.constraint(equalTo:page.widthAnchor).isActive=true
        }
        busy.widthAnchor.constraint(equalToConstant:18).isActive=true
        busy.heightAnchor.constraint(equalToConstant:18).isActive=true
        progress.widthAnchor.constraint(equalTo:status.widthAnchor).isActive=true
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
        if let historyError {
            label.stringValue = historyError
            button.isEnabled = false
            return
        }
        if value.ready {
            start()
            return
        }
        label.stringValue = "Install the files below to get started. Steam updates and games download separately."
        downloads?.removeFromSuperview()
        downloads = NSGridView(views: [
            [NSTextField(labelWithString: "Required files"), NSTextField(labelWithString: "Download")],
            [NSTextField(labelWithString: "Runtime · Wine 11.0 + DXMT 0.80"),
             NSTextField(labelWithString: value.runtime_present ? "Installed" : downloadSize(value.runtime_bytes))],
            [NSTextField(labelWithString: "Steam installer"),
             NSTextField(labelWithString: value.steam_present ? "Installed" : downloadSize(value.steam_bytes))]
        ])
        downloads.columnSpacing = 30
        downloads.rowSpacing = 12
        downloads.column(at: 1).xPlacement = .trailing
        for row in 0..<downloads.numberOfRows {
            for col in 0..<downloads.numberOfColumns {
                if let text=downloads.cell(atColumnIndex:col,rowIndex:row).contentView as? NSTextField {
                    text.font = .systemFont(ofSize:12,weight:row == 0 ? .medium : .regular)
                    text.textColor = row == 0 ? PearStyle.muted : PearStyle.foreground
                }
            }
        }
        downloadHost.addArrangedSubview(downloads)
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
        reporting?.stop()
        for transfer in serverDeletes.values { transfer.cancel() }
        closing = true
        observationGeneration += 1
        openingGeneration += 1
        guard let task, task.isRunning else { return .terminateNow }
        task.interrupt()
        return .terminateLater
    }
}

#if !PEAR_UI_REVIEW
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

#endif
