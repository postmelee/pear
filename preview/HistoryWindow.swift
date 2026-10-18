// SPDX-FileCopyrightText: 2026 Pear contributors
// SPDX-License-Identifier: GPL-3.0-or-later
import AppKit
import UniformTypeIdentifiers

@MainActor private final class HistoryBadge: NSView {
    private let tint: NSColor
    init(_ title: String, symbol: String, tint: NSColor) {
        self.tint = tint
        super.init(frame: .zero)
        wantsLayer = true
        let icon = NSImageView(image: NSImage(systemSymbolName: symbol, accessibilityDescription: nil) ?? NSImage())
        icon.contentTintColor = tint
        let label = NSTextField(labelWithString: title)
        label.font = .systemFont(ofSize: 12, weight: .medium)
        label.textColor = PearStyle.foreground
        let row = NSStackView(views: [icon, label]); row.spacing = 5; row.alignment = .centerY
        row.translatesAutoresizingMaskIntoConstraints = false
        addSubview(row)
        NSLayoutConstraint.activate([
            icon.widthAnchor.constraint(equalToConstant: 13), icon.heightAnchor.constraint(equalToConstant: 13),
            row.leadingAnchor.constraint(equalTo: leadingAnchor, constant: 8),
            row.trailingAnchor.constraint(equalTo: trailingAnchor, constant: -8),
            row.topAnchor.constraint(equalTo: topAnchor, constant: 5),
            row.bottomAnchor.constraint(equalTo: bottomAnchor, constant: -5)])
        setAccessibilityElement(true); setAccessibilityLabel(title)
    }
    required init?(coder: NSCoder) { fatalError("init(coder:) is unavailable") }
    override var wantsUpdateLayer: Bool { true }
    override func updateLayer() { layer?.backgroundColor = tint.withAlphaComponent(0.13).cgColor; layer?.cornerRadius = 6 }
    override func viewDidChangeEffectiveAppearance() { super.viewDidChangeEffectiveAppearance(); needsDisplay = true }
}

@MainActor final class HistoryWindow: NSObject, NSTableViewDataSource, NSTableViewDelegate {
    let store: ReportingStore
    var configureSharing: ((SharingMode, Set<ReportField>) throws -> Void)?
    var retryReport: ((UUID) throws -> Void)?
    var deleteLocalRecord: ((UUID) throws -> Void)?
    var deleteServerReport: ((UUID, @escaping (Bool) -> Void) -> Void)?
    var enableNotifications: (() -> Void)?
    var submit: ((RunObservation, Bool) throws -> Void)?
    private var window: NSWindow!
    private let table = NSTableView()
    private let modeLabel = NSTextField(labelWithString: "")
    private let selectedTitle = NSTextField(labelWithString: "Selected run")
    private let emptyLabel = NSTextField(labelWithString: "No runs yet. Games opened through Pear will appear here.")
    private let details = NSTextField(wrappingLabelWithString: "Choose a run to see its details.")
    private let result = NSPopUpButton()
    private let note = NSTextView()
    private let shareNote = NSButton(checkboxWithTitle: "Include this note when I share", target: nil, action: nil)
    private let shareButton = NSButton()
    private var openRunButton: NSButton!
    private let retryButton = NSButton()
    private var listPage: NSStackView!
    private var detailPage: NSStackView!
    private let runDate = PearStyle.label("", muted: true)
    private let disableButton = NSButton()
    private let more = NSPopUpButton(frame: .zero, pullsDown: true)
    private let sharedSummary = PearStyle.label("", muted: true)
    var isVisible: Bool { window?.isVisible ?? false }
    private let availability = NSTextField(wrappingLabelWithString: "")
    private var pendingFinished: [UUID] = []
    private var showingFinished = false
    private var displayedID: UUID?
    private var reloading = false
    private var selection: UUID?
    private var rows: [RunObservation] { store.snapshot.runs.sorted { $0.startedAt > $1.startedAt } }

    init(store: ReportingStore) { self.store = store; super.init() }
    private func text(_ value: String, bold: Bool = false) -> NSTextField {
        PearStyle.label(value, size: bold ? 15 : 13, weight: bold ? .semibold : .regular)
    }
    private func button(_ title: String, _ action: Selector) -> NSButton {
        PearStyle.button(title, target: self, action: action)
    }
    private func stack(_ views: [NSView], horizontal: Bool = false) -> NSStackView {
        PearStyle.stack(views, horizontal: horizontal)
    }
    func show() {
        if window == nil { build() }
        refresh(); window.makeKeyAndOrderFront(nil); NSApp.activate(ignoringOtherApps:true)
    }
    private func build() {
        window = NSWindow(contentRect:NSRect(x:0,y:0,width:800,height:600),
                          styleMask:[.titled,.closable,.miniaturizable,.resizable],backing:.buffered,defer:false)
        window.title = "Pear · Run history"; window.isReleasedWhenClosed = false
        window.minSize = NSSize(width:760,height:600); PearStyle.window(window)
        modeLabel.font = .systemFont(ofSize: 12, weight: .medium); modeLabel.textColor = PearStyle.muted
        disableButton.title = "Turn off automatic sharing"; disableButton.bezelStyle = .rounded
        disableButton.target = self; disableButton.action = #selector(disableSharing)
        let sharing = stack([modeLabel, NSView(), button("Sharing settings…",#selector(settings)), disableButton], horizontal: true)
        for (id,title,width) in [("game","Game",205.0),("date","Date · time open",190.0),
                                  ("result","Your result",165.0),("shared","Sharing",160.0)] {
            let column = NSTableColumn(identifier:NSUserInterfaceItemIdentifier(id)); column.title=title; column.width=width
            column.minWidth = id == "game" ? 140 : 130
            table.addTableColumn(column)
        }
        table.dataSource=self; table.delegate=self; table.rowHeight=54; table.style = .fullWidth
        table.backgroundColor = PearStyle.background; table.usesAlternatingRowBackgroundColors = false
        table.target = self; table.action = #selector(openSelected)
        table.setAccessibilityLabel("Game runs. Select a run to add a result or note.")
        let list = NSScrollView(); list.documentView=table; list.hasVerticalScroller=true
        list.backgroundColor = PearStyle.background
        list.heightAnchor.constraint(greaterThanOrEqualToConstant:200).isActive=true
        emptyLabel.textColor = PearStyle.muted
        availability.font = .systemFont(ofSize: 12); availability.textColor = PearStyle.muted
        openRunButton=button("Open selected run",#selector(openSelected));openRunButton.keyEquivalent="\r"
        let footer = stack([button("Shared reports…",#selector(manageSharedReports)), NSView(), openRunButton!],horizontal:true)
        listPage = stack([PearStyle.label("Run history",size:28,weight:.semibold),
                          PearStyle.label("Your recent games. Share what worked, or help us fix a problem.", muted:true),
                          sharing, list, emptyLabel, availability, footer])
        listPage.spacing = 16
        for view in [sharing,list,footer] { view.widthAnchor.constraint(equalTo:listPage.widthAnchor).isActive=true }
        PearStyle.pin(listPage,in:window.contentView!)

        selectedTitle.font = .systemFont(ofSize:26,weight:.semibold); selectedTitle.textColor = PearStyle.foreground
        details.font = .systemFont(ofSize:13); details.textColor = PearStyle.muted
        result.addItems(withTitles:["Not confirmed","Worked normally","Had problems"])
        result.controlSize = .large
        let notes = PearStyle.editor(note, height:100)
        shareButton.title="Share result"; shareButton.target=self; shareButton.action = #selector(share)
        shareButton.bezelStyle = .rounded; shareButton.bezelColor = PearStyle.buttonFill; shareButton.controlSize = .large
        retryButton.title = "Retry sending"; retryButton.target = self; retryButton.action = #selector(retrySending)
        retryButton.bezelStyle = .rounded
        more.addItem(withTitle:"More…");more.menu?.autoenablesItems=false
        for (title, action) in [("Environment & versions…", #selector(showEnvironment)),
                                ("Add test details…", #selector(editSupplemental)),
                                ("Export…", #selector(exportRecord)),
                                ("View shared content…", #selector(viewShared)),
                                ("Delete local record…", #selector(deleteLocal)),
                                ("Manage shared reports…", #selector(manageSharedReports))] {
            let item = NSMenuItem(title:title,action:action,keyEquivalent:""); item.target=self; more.menu?.addItem(item)
        }
        let navigation = stack([button("← All runs",#selector(showList)),NSView(),more],horizontal:true)
        let actions = stack([button("Save on this Mac",#selector(save)),retryButton,NSView(),shareButton],horizontal:true)
        let resultRow = stack([text("How did it run?",bold:true),result],horizontal:true)
        detailPage = stack([navigation,selectedTitle,runDate,resultRow,
                            PearStyle.label("Note (optional)",size:15,weight:.semibold), notes,shareNote,
                            PearStyle.label("Your note stays on this Mac unless you include it when sharing.",size:12,muted:true),
                            NSView(),sharedSummary,actions])
        detailPage.spacing = 16
        for view in [navigation,notes,actions,sharedSummary] { view.widthAnchor.constraint(equalTo:detailPage.widthAnchor).isActive=true }
        PearStyle.pin(detailPage,in:window.contentView!)
        detailPage.isHidden = true
        window.center()
    }
    @objc private func openSelected() {
        guard selection != nil else { return }
        listPage.isHidden = true; detailPage.isHidden = false
        window.makeFirstResponder(result)
    }
    @objc private func showList() {
        // Navigation saves only the local draft, never a network report.
        if let draft=editedRun() {
            do { try store.record(draft) } catch { failure(error); return }
        }
        detailPage.isHidden = true; listPage.isHidden = false; refresh(); window.makeFirstResponder(table)
    }
    @objc private func showEnvironment() {
        let alert=NSAlert();alert.messageText="Environment & versions"
        alert.informativeText=details.stringValue + "\n\nTime open measures the game process, not active play. An observed exit is not a confirmed successful result."
        alert.beginSheetModal(for:window)
    }
    func tableView(_ tableView: NSTableView, rowViewForRow row: Int) -> NSTableRowView? { PearHistoryRow() }
    func refresh() {
        guard window != nil else { return }
        let modes: [SharingMode:String] = [.localOnly:"Not sharing",.askAfterExit:"Ask after each game",.automatic:"Automatic sharing"]
        modeLabel.stringValue = modes[store.snapshot.policy.consent.mode]!
        disableButton.isHidden = store.snapshot.policy.consent.mode != .automatic
        availability.stringValue = !store.available ? "Local storage is unavailable. Sharing is stopped; reopen Pear after resolving the storage problem." : submit == nil ? "Local records and export are available. Report sharing is not connected in this development build." : "Shared results help improve Pear. Publication follows review."
        emptyLabel.isHidden = !rows.isEmpty
        openRunButton.isEnabled = selection != nil
        reloading = true
        table.reloadData()
        reloading = false

        if let selection, let row=rows.firstIndex(where:{$0.id==selection}) { table.selectRowIndexes(IndexSet(integer:row),byExtendingSelection:false) }
        shareButton.isEnabled = submit != nil && selection != nil && store.available && selection.map { store.snapshot.serverDeletions?[$0] == nil } == true
        retryButton.isEnabled = retryReport != nil && store.snapshot.policy.pending.contains { $0.payload.reportID == selection }
        retryButton.isHidden = !retryButton.isEnabled
        updateSharingSummary()
    }
    func numberOfRows(in tableView: NSTableView) -> Int { rows.count }
    func tableView(_ tableView: NSTableView, viewFor tableColumn: NSTableColumn?, row: Int) -> NSView? {
        let run = rows[row]
        let cell = NSTableCellView()
        let value: NSView
        switch tableColumn?.identifier.rawValue {
        case "game":
            let label = NSTextField(labelWithString: run.gameName ?? run.appID.map { "Steam App \($0)" } ?? "Unidentified game")
            label.font = .systemFont(ofSize: 14, weight: .medium); label.textColor = PearStyle.foreground; value = label
        case "date":
            let date = DateFormatter.localizedString(from:run.startedAt,dateStyle:.medium,timeStyle:.none)
            let minutes=run.endedAt.map { max(0,Int($0.timeIntervalSince(run.startedAt)/60)) }
            let label = NSTextField(labelWithString: date + " · " + (minutes.map { "\($0) min open" } ?? "Unknown duration"))
            label.font = .systemFont(ofSize: 12); label.textColor = PearStyle.muted; value = label
        case "result":
            value = HistoryBadge(resultTitle(run.result),
                symbol: run.result == .normal ? "checkmark.circle.fill" : run.result == .problems ? "exclamationmark.circle.fill" : "questionmark.circle",
                tint: run.result == .normal ? PearStyle.accent : run.result == .problems ? PearStyle.negative : PearStyle.muted)
        default:
            let request = store.snapshot.policy.pending.first { $0.payload.reportID == run.id }
            let pending = request != nil
            let failed = request.map { (store.snapshot.delivery?[$0.requestID]?.failures ?? 0) > 0 } ?? false
            let expired = request.map { Date().timeIntervalSince($0.createdAt ?? .distantPast) >= 14 * 86400 } ?? false
            let shared = store.snapshot.shared[run.id] != nil
            let deletion = store.snapshot.serverDeletions?[run.id]
            value = HistoryBadge(deletion == true ? "Deleted from server" : deletion == false ? "Deletion needs retry" : failed ? "Send failed" : expired ? "Retry needed" : pending ? "Pending" : shared ? "Shared" : "Not shared",
                symbol: pending ? "clock" : shared ? "arrow.up.circle.fill" : "lock",
                tint: pending ? .systemOrange : shared ? PearStyle.accent : PearStyle.muted)
        }
        value.translatesAutoresizingMaskIntoConstraints = false; cell.addSubview(value)
        NSLayoutConstraint.activate([value.leadingAnchor.constraint(equalTo:cell.leadingAnchor,constant:4),
            value.centerYAnchor.constraint(equalTo:cell.centerYAnchor),
            value.trailingAnchor.constraint(lessThanOrEqualTo:cell.trailingAnchor,constant:-4)])
        return cell
    }
    private func resultTitle(_ value: UserRunResult) -> String {
        switch value { case .unknown:return "Not confirmed"; case .normal:return "Worked normally"; case .problems:return "Had problems" }
    }
    func tableViewSelectionDidChange(_ notification: Notification) {
        guard !reloading else { return }
        guard rows.indices.contains(table.selectedRow) else { selection=nil; return }
        let run=rows[table.selectedRow]
        // Preserve a local draft when selecting another run; never upload on navigation.
        if selection != run.id, let draft=editedRun() {
            do { try store.record(draft) } catch { failure(error); return }
        }
        selection=run.id
        openRunButton.isEnabled=true
        runDate.stringValue = DateFormatter.localizedString(from:run.startedAt,dateStyle:.long,timeStyle:.short)
            + " · " + (run.endedAt.map { "\(max(0,Int($0.timeIntervalSince(run.startedAt)/60))) min open" } ?? "End not observed")
        selectedTitle.stringValue = run.gameName ?? run.appID.map { "Steam App \($0)" } ?? "Unidentified game"
        details.stringValue = "\(run.macOS.map { "macOS \($0)" } ?? "macOS unknown") · \(run.chip ?? "Chip unknown") · \(run.memoryGiB.map { "\($0) GB" } ?? "Memory unknown")\nPear \(run.pear) · Wine \(run.wine) · DXMT \(run.dxmt)\nGame build: \(run.gameBuild ?? "Unknown") · Observed exit: \(run.observedExit.rawValue)"
        if displayedID != run.id {
            result.selectItem(at:run.result == .normal ? 1 : run.result == .problems ? 2 : 0)
            note.string=run.note; shareNote.state = .off
            displayedID=run.id
        }
        shareButton.isEnabled = submit != nil && store.available && store.snapshot.serverDeletions?[run.id] == nil
        retryButton.isEnabled = retryReport != nil && store.snapshot.policy.pending.contains { $0.payload.reportID == run.id }
        retryButton.isHidden = !retryButton.isEnabled
        updateSharingSummary()
    }
    private func updateSharingSummary() {
        let shared = selection.map { store.snapshot.shared[$0] != nil } ?? false
        shareButton.title = shared ? "Update shared result" : "Share result"
        sharedSummary.stringValue = shared ? "Already shared. Sharing changes updates this report." : "Only on this Mac. Nothing is sent until you choose to share."
        if !shared && store.snapshot.policy.consent.mode == .automatic {
            sharedSummary.stringValue = "Selected fields are shared automatically after a run. Notes are only sent when you include them."
        }
        more.item(at:4)?.isEnabled = shared
        if let id=selection,store.snapshot.policy.pending.contains(where:{$0.payload.reportID == id}) {
            sharedSummary.stringValue = "Waiting to send. You can retry if the connection was interrupted."
        }
        if let id=selection,let deleted=store.snapshot.serverDeletions?[id] {
            sharedSummary.stringValue = deleted ? "Deleted from the server. Your local record is kept." : "Server deletion needs a retry. This report will not be sent again."
        }
    }
    private func editedRun() -> RunObservation? {
        guard let id=selection,var run=rows.first(where:{$0.id==id}) else { return nil }
        run.result = result.indexOfSelectedItem == 1 ? .normal : result.indexOfSelectedItem == 2 ? .problems : .unknown
        run.note=note.string; return run
    }
    @objc private func editSupplemental() {
        guard let run = editedRun() else { return }
        let old = run.supplemental ?? SupplementalReport()
        let alert = NSAlert(); alert.messageText = "Optional test details"
        alert.informativeText = "Leave anything you did not check as Unknown. These are your observations, not automatic checks. Details are included only when you manually share and may be published after review. Do not include account information or paths."
        let outcomes = ["unknown", "observed", "failed", "not-tested"]
        func picker(_ values: [String], _ value: String) -> NSPopUpButton {
            let p = NSPopUpButton(); p.addItems(withTitles: values); p.selectItem(withTitle: value); return p
        }
        let stage = picker(["unknown", "launch-failed", "launched-unusable", "menu-interactive", "active-gameplay", "regression"], old.furthestResult)
        let checks = [old.input,old.audio,old.saveReload,old.recovery].map { picker(outcomes,$0) }
        let minutes = NSTextField(string: old.activePlayMinutes.map(String.init) ?? "")
        minutes.placeholderString = "Optional · actual active play, not process time"
        let settings = NSTextField(string: old.settings); settings.placeholderString = "Optional · resolution and graphics settings"
        var views: [NSView] = [text("Furthest result",bold:true),stage,text("Active play minutes",bold:true),minutes]
        for (name,p) in zip(["Input","Audio","Save / reload","Recovery"],checks) { views += [stack([text(name),p],horizontal:true)] }
        views += [text("Game settings",bold:true),settings]
        let options=stack(views); options.frame=NSRect(x:0,y:0,width:540,height:310)
        alert.accessoryView=options;alert.addButton(withTitle:"Save details");alert.addButton(withTitle:"Cancel")
        alert.beginSheetModal(for:window) { response in
            guard response == .alertFirstButtonReturn else { return }
            let raw=minutes.stringValue.trimmingCharacters(in:.whitespaces)
            guard raw.isEmpty || (Int(raw).map { $0 >= 0 && $0 <= 1440 } ?? false), settings.stringValue.count <= 500 else { self.failure(ReportingStoreError.unavailable); return }
            var updated=run
            updated.supplemental=SupplementalReport(furthestResult:stage.titleOfSelectedItem ?? "unknown",activePlayMinutes:Int(raw),input:checks[0].titleOfSelectedItem!,audio:checks[1].titleOfSelectedItem!,saveReload:checks[2].titleOfSelectedItem!,recovery:checks[3].titleOfSelectedItem!,settings:settings.stringValue)
            do { try self.store.record(updated);self.refresh() } catch { self.failure(error) }
        }
    }
    private func failure(_ error: Error) {
        let alert=NSAlert(); alert.messageText="Could not save this change"
        alert.informativeText="No further reports will be sent if local storage is unavailable. \(error.localizedDescription)"
        alert.beginSheetModal(for:window)
    }
    @objc private func save() {
        guard let run=editedRun() else { return }
        do {
            try store.record(run); refresh()
            sharedSummary.stringValue = store.snapshot.shared[run.id] == nil
                ? "Saved on this Mac. You can share this result when you’re ready."
                : "Saved on this Mac. Choose Update shared result to send your changes."
        } catch { failure(error) }
    }
    @objc private func share() {
        guard store.snapshot.policy.consent.disclosureVersion == 2, !store.snapshot.policy.consent.fields.isEmpty else { settings(); return }
        guard let run=editedRun(),let submit else { return }
        do { try store.record(run); try submit(run,shareNote.state == .on); refresh() } catch { failure(error) }
    }
    @objc private func retrySending() {
        guard let selection, let retryReport else { return }
        do { try retryReport(selection); refresh() } catch { failure(error) }
    }
    @objc private func deleteLocal() {
        guard let id = selection else { return }
        let alert = NSAlert(); alert.messageText = "Delete this local run?"
        alert.informativeText = "This removes the local run and its queued transmissions. Reports already sent and their shared-content receipts remain. This does not delete a report from the server."
        alert.addButton(withTitle: "Cancel"); alert.addButton(withTitle: "Delete local record")
        alert.beginSheetModal(for: window) { response in
            guard response == .alertSecondButtonReturn else { return }
            do {
                if let remove = self.deleteLocalRecord { try remove(id) }
                else {
                    // No transport exists in this local-only development mode.
                    try self.store.transaction {
                        $0.policy.removePending(reportID: id)
                        $0.runs.removeAll { $0.id == id }
                    }
                }
                self.selection = nil; self.displayedID = nil
                self.selectedTitle.stringValue = "Selected run"; self.details.stringValue = "Choose a run to see its details."
                self.note.string = ""; self.showList(); self.refresh()
            } catch { self.failure(error) }
        }
    }
    @objc private func disableSharing() {
        do {
            if let configureSharing { try configureSharing(.localOnly,store.snapshot.policy.consent.fields) }
            else { try store.transaction { $0.policy.disableAutomaticSharing() } }
            refresh()
            availability.stringValue = "Sharing is off. Local records and reports already sent are kept."
        } catch { failure(error) }
    }
    @objc private func exportRecord() {
        guard let run=editedRun() else { return }
        let panel=NSSavePanel();panel.allowedContentTypes=[.json];panel.nameFieldStringValue="pear-run-\(run.id.uuidString).json"
        panel.beginSheetModal(for:window) { response in
            guard response == .OK,let url=panel.url else { return }
            do {
                let encoder=JSONEncoder();encoder.outputFormatting=[.prettyPrinted,.sortedKeys]
                // Export only the explicit sharing projection, not exact timestamps.
                try encoder.encode(run.payload(fields:Set(ReportField.allCases),shareNote:self.shareNote.state == .on)).write(to:url,options:.atomic)
            } catch { self.failure(error) }
        }
    }
    @objc private func manageSharedReports() {
        let ids = Set(store.snapshot.shared.keys).union(store.snapshot.serverDeletions?.filter { !$0.value }.map { $0.key } ?? []).sorted { $0.uuidString < $1.uuidString }
        let alert = NSAlert(); alert.messageText = "Shared reports"
        guard !ids.isEmpty else {
            alert.informativeText = "No shared reports or pending deletions on this Mac. Local records are separate."
            alert.beginSheetModal(for: window); return
        }
        alert.informativeText = "Delete a report from Pear’s server. This keeps your local record, stops its queued sends and prevents resending the same record. Public removal follows the next successful catalog update. Backups, GitHub originals and external copies are separate."
        let picker = NSPopUpButton()
        picker.addItems(withTitles: ids.map { id in
            let r = store.snapshot.shared[id]
            return (r?.appID.map { "Steam App \($0)" } ?? "Report") + " · " + (r?.dateUTC ?? "Date not shared") + " · " + id.uuidString
        })
        picker.frame = NSRect(x:0,y:0,width:590,height:30)
        alert.accessoryView = picker
        alert.addButton(withTitle: "Cancel"); alert.addButton(withTitle: "Delete from server")
        alert.beginSheetModal(for: window) { response in
            guard response == .alertSecondButtonReturn, ids.indices.contains(picker.indexOfSelectedItem), let remove = self.deleteServerReport else { return }
            remove(ids[picker.indexOfSelectedItem]) { success in
                let result = NSAlert(); result.messageText = success ? "Server report deleted" : "Deletion not confirmed"
                result.informativeText = success ? "Your local history is kept. Published catalog removal follows the next successful update." : "The report may still be on the server. Its pending uploads are stopped. Use Shared reports to retry deletion when online."
                self.refresh(); result.beginSheetModal(for:self.window)
            }
        }
    }

    @objc private func viewShared() {
        guard let id=selection,let shared=store.snapshot.shared[id] else { return }
        let alert=NSAlert();alert.messageText="Last shared content"
        let encoder=JSONEncoder();encoder.outputFormatting=[.prettyPrinted,.sortedKeys]
        alert.informativeText=(try? String(data:encoder.encode(shared),encoding:.utf8)) ?? "Unavailable"
        alert.beginSheetModal(for:window)
    }
    func confirmFinished(_ id: UUID) {
        guard store.snapshot.policy.shouldShowExitPrompt else { return }
        pendingFinished.append(id)
        showNextFinished()
    }
    private func showNextFinished() {
        guard !showingFinished, !pendingFinished.isEmpty else { return }
        guard store.snapshot.policy.shouldShowExitPrompt else { pendingFinished.removeAll(); return }
        let id = pendingFinished.removeFirst()
        guard let run = store.snapshot.runs.first(where: { $0.id == id }) else { showNextFinished(); return }
        show(); showingFinished = true
        let alert = NSAlert(); alert.messageText = "How did the game run?"
        alert.informativeText = "Share your experience to help improve Pear. You can also skip and add a result later."
        let outcome = NSPopUpButton(); outcome.addItems(withTitles: ["Not confirmed", "Worked normally", "Had problems"])
        outcome.selectItem(at:run.result == .normal ? 1 : run.result == .problems ? 2 : 0)
        let notes = NSTextView(); notes.string = run.note; notes.isRichText = false; notes.font = .systemFont(ofSize: 13)
        let scroll = PearStyle.editor(notes, height:90)
        scroll.widthAnchor.constraint(equalToConstant: 440).isActive = true
        notes.isVerticallyResizable = true; notes.textContainer?.widthTracksTextView = true
        let suppress = NSButton(checkboxWithTitle: "Do not show this window after games", target: nil, action: nil)
        let game = PearStyle.label(run.gameName ?? run.appID.map { "Steam App \($0)" } ?? "Unidentified game",size:23,weight:.semibold)
        let content = stack([game, text("Your result", bold: true), outcome, text("Note (optional)", bold: true), scroll,
                             PearStyle.label("Share result sends this note privately. Skip keeps it on this Mac.",size:12,muted:true), suppress,
                             PearStyle.label("Hiding this window does not turn on automatic sharing.",size:12,muted:true)])
        content.frame = NSRect(x: 0, y: 0, width: 440, height: 310)
        alert.accessoryView = content
        alert.addButton(withTitle: "Share result").isEnabled = submit != nil
        alert.addButton(withTitle: "Skip this time")
        alert.beginSheetModal(for: window) { response in
            var updated = run
            updated.result = outcome.indexOfSelectedItem == 1 ? .normal : outcome.indexOfSelectedItem == 2 ? .problems : .unknown
            updated.note = notes.string
            do {
                try self.store.record(updated)
                if suppress.state == .on { try self.store.transaction { $0.policy.suppressExitPrompt() } }
                if response == .alertFirstButtonReturn { try self.submit?(updated, true) }
            } catch { self.failure(error) }
            self.displayedID = nil
            self.showingFinished = false; self.refresh(); self.showNextFinished()
        }
    }
    func showSharingIntroductionIfNeeded() {
        if store.snapshot.policy.consent.disclosureVersion != 2 { show(); settings() }
    }
    @objc private func settings() {
        let consent=store.snapshot.policy.consent
        let alert=NSAlert();alert.messageText="Sharing settings"
        alert.informativeText="Help improve support for more games. Your reports help Pear investigate problems and work with contributors. Sharing is optional; Pear works without it.\n\nSelected fields, your result and manually added test details may be published on the catalog and GitHub after private review. Approval is not a compatibility certification."
        let mode=NSPopUpButton();mode.addItems(withTitles:["Do not share — local records and manual sharing only","Ask after each game","Automatically share selected fields"])
        mode.selectItem(at:consent.disclosureVersion != 2 || consent.mode == .localOnly ? 0 : consent.mode == .askAfterExit ? 1 : 2)
        let fields:[(ReportField,String)] = [(.environment,"macOS version, chip and memory"),(.components,"Pear, Wine and DXMT versions"),(.game,"Steam App ID and available game build"),(.execution,"Date, process minutes and observed exit status")]
        let checks=fields.map { field,title in
            let check=NSButton(checkboxWithTitle:title,target:nil,action:nil);check.state=consent.fields.contains(field) ? .on : .off;return check
        }
        let prompt=NSButton(checkboxWithTitle:"Show the result window in ask mode",target:nil,action:nil);prompt.state=consent.showExitPrompt ? .on : .off
        let notify=NSButton(checkboxWithTitle:"Notify me after games in automatic mode",target:nil,action:nil);notify.state=consent.notifyAutomaticCompletion ? .on : .off
        let privacy = PearStyle.label("Notes stay private and are sent only when explicitly included. Accounts, credentials, saves, paths and raw logs are excluded. Exact timestamps stay on this Mac.",size:12,muted:true)
        let retention = PearStyle.label("You can stop sharing at any time. Local history: 90 days. Server reports: up to 180 days, or 365 days after the latest update for published reports. Delete shared reports separately from local records; external copies may remain. Cloudflare operates the service; network processing is not completely anonymous.",size:12,muted:true)
        let options=stack([text("When to share",bold:true), mode, text("Choose what to share",bold:true)] + checks
                          + [privacy,text("After a game",bold:true),prompt,notify,retention])
        options.spacing=10
        options.frame=NSRect(x:0,y:0,width:560,height:430)
        for label in [privacy,retention] { label.widthAnchor.constraint(equalToConstant:560).isActive=true }
        alert.accessoryView=options
        alert.addButton(withTitle:"Save settings").bezelColor=PearStyle.buttonFill
        alert.addButton(withTitle:"Cancel")
        alert.beginSheetModal(for:window) { response in
            guard response == .alertFirstButtonReturn else { return }
            let selected=Set(zip(fields,checks).filter{$0.1.state == .on}.map{$0.0.0})
            let selectedMode:SharingMode = mode.indexOfSelectedItem == 0 ? .localOnly : mode.indexOfSelectedItem == 1 ? .askAfterExit : .automatic
            guard selectedMode == .localOnly || !selected.isEmpty else {
                let explanation = NSAlert(); explanation.messageText = "Choose at least one field"
                explanation.informativeText = "No sharing setting was changed. Choose which fields to share in Sharing settings."
                explanation.beginSheetModal(for:self.window); return
            }
            do {
                if let configure=self.configureSharing { try configure(selectedMode,selected) }
                else { try self.store.transaction { $0.policy.configure(mode:selectedMode,fields:selected) } }
                try self.store.transaction {
                    $0.policy.setExitPrompt(prompt.state == .on)
                    $0.policy.setExitNotifications(notify.state == .on)
                }
                if notify.state == .on && !consent.notifyAutomaticCompletion { self.enableNotifications?() }
                self.refresh()
            } catch { self.failure(error) }
        }
    }
}
