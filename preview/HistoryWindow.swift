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
        label.textColor = .labelColor
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
    private let retryButton = NSButton()
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
        let label = NSTextField(wrappingLabelWithString:value)
        label.font = bold ? .boldSystemFont(ofSize:15) : .systemFont(ofSize:13)
        return label
    }
    private func button(_ title: String, _ action: Selector) -> NSButton {
        NSButton(title:title,target:self,action:action)
    }
    private func stack(_ views: [NSView], horizontal: Bool = false) -> NSStackView {
        let stack = NSStackView(views:views); stack.orientation = horizontal ? .horizontal : .vertical
        stack.alignment = horizontal ? .centerY : .leading; stack.spacing = 12
        return stack
    }
    func show() {
        if window == nil { build() }
        refresh(); window.makeKeyAndOrderFront(nil); NSApp.activate(ignoringOtherApps:true)
    }
    private func build() {
        window = NSWindow(contentRect:NSRect(x:0,y:0,width:960,height:850),
                          styleMask:[.titled,.closable,.miniaturizable,.resizable],backing:.buffered,defer:false)
        window.title = "Pear · Run history"; window.isReleasedWhenClosed = false
        window.minSize = NSSize(width:880,height:810)
        let pageTitle = text("Run history", bold: true)
        pageTitle.font = .systemFont(ofSize: 28, weight: .bold)
        let introduction = text("See what ran on your Mac, add a result, and choose what to share.")
        introduction.textColor = .secondaryLabelColor
        modeLabel.font = .systemFont(ofSize: 13, weight: .semibold)
        let header = stack([modeLabel,button("Sharing settings",#selector(settings)),
                            button("Turn off automatic sharing",#selector(disableSharing))],horizontal:true)
        for (id,title,width) in [("game","Game",190.0),("date","Date / process time",240.0),
                                  ("result","Your result",200.0),("shared","Sharing",180.0)] {
            let column = NSTableColumn(identifier:NSUserInterfaceItemIdentifier(id)); column.title=title; column.width=width
            table.addTableColumn(column)
        }
        table.dataSource=self; table.delegate=self; table.rowHeight=42; table.usesAlternatingRowBackgroundColors=true; table.style = .fullWidth
        let list = NSScrollView(); list.documentView=table; list.hasVerticalScroller=true
        list.heightAnchor.constraint(equalToConstant:210).isActive=true
        selectedTitle.font = .systemFont(ofSize: 15, weight: .semibold)
        details.font = .systemFont(ofSize: 12)
        details.textColor = .secondaryLabelColor
        emptyLabel.font = .systemFont(ofSize: 13)
        emptyLabel.textColor = .secondaryLabelColor
        availability.font = .systemFont(ofSize: 12)
        availability.textColor = .secondaryLabelColor
        result.addItems(withTitles:["Not confirmed","Worked normally","Had problems"])
        let notes = NSScrollView(); notes.documentView=note; notes.hasVerticalScroller=true; notes.borderType = .bezelBorder
        note.isRichText=false; note.font = .systemFont(ofSize:13)
        note.isVerticallyResizable=true; note.isHorizontallyResizable=false
        note.textContainer?.widthTracksTextView=true
        notes.heightAnchor.constraint(equalToConstant:80).isActive=true
        shareButton.title="Share result"; shareButton.target=self; shareButton.action = #selector(share)
        shareButton.bezelStyle = .rounded
        shareButton.bezelColor = .controlAccentColor
        retryButton.title = "Retry sending"; retryButton.target = self; retryButton.action = #selector(retrySending)
        retryButton.bezelStyle = .rounded
        let actions = stack([button("Save changes",#selector(save)),shareButton,
                             button("Export…",#selector(exportRecord)),button("View shared content",#selector(viewShared)), retryButton],horizontal:true)
        let resultRow = stack([text("Your result", bold: true), result], horizontal: true)
        let noteHeading = stack([text("Note", bold: true), text("Optional · kept on this Mac")], horizontal: true)
        let divider = NSBox(); divider.boxType = .separator
        let privacy = text("Turning sharing off keeps local records and reports already sent.")
        privacy.font = .systemFont(ofSize: 12); privacy.textColor = .secondaryLabelColor
        let timing = text("Process time is not verified play time. Your result is separate from what Pear can observe.")
        timing.font = .systemFont(ofSize: 12); timing.textColor = .secondaryLabelColor
        let detailsHeading = text("Run details", bold: true)
        detailsHeading.font = .systemFont(ofSize: 20, weight: .semibold)
        let content = stack([pageTitle, introduction, header, privacy, availability,
                             list, emptyLabel, divider, detailsHeading, selectedTitle, details, resultRow, noteHeading,
                             notes, shareNote, button("Optional test details…", #selector(editSupplemental)), actions, button("Delete local record…", #selector(deleteLocal)), timing])
        content.spacing = 10
        content.translatesAutoresizingMaskIntoConstraints=false; window.contentView!.addSubview(content)
        NSLayoutConstraint.activate([
            content.leadingAnchor.constraint(equalTo:window.contentView!.leadingAnchor,constant:20),
            content.trailingAnchor.constraint(equalTo:window.contentView!.trailingAnchor,constant:-20),
            content.topAnchor.constraint(equalTo:window.contentView!.topAnchor,constant:20),
            content.bottomAnchor.constraint(lessThanOrEqualTo:window.contentView!.bottomAnchor,constant:-20),
            divider.widthAnchor.constraint(equalTo:content.widthAnchor),
            list.widthAnchor.constraint(equalTo:content.widthAnchor),notes.widthAnchor.constraint(equalTo:content.widthAnchor),
            details.widthAnchor.constraint(equalTo:content.widthAnchor)])
        window.center()
    }
    func refresh() {
        guard window != nil else { return }
        let modes: [SharingMode:String] = [.localOnly:"Not sharing",.askAfterExit:"Ask after each game",.automatic:"Automatic sharing"]
        modeLabel.stringValue = "Sharing: \(modes[store.snapshot.policy.consent.mode]!)"
        availability.stringValue = submit == nil ? "Local records and export are available. Report sharing is not connected in this development build." : ""
        emptyLabel.isHidden = !rows.isEmpty
        reloading = true
        table.reloadData()
        reloading = false
        if selection == nil, let first = rows.first { selection = first.id }
        if let selection, let row=rows.firstIndex(where:{$0.id==selection}) { table.selectRowIndexes(IndexSet(integer:row),byExtendingSelection:false) }
        shareButton.isEnabled = submit != nil && selection != nil && store.available
        retryButton.isEnabled = retryReport != nil && store.snapshot.policy.pending.contains { $0.payload.reportID == selection }
    }
    func numberOfRows(in tableView: NSTableView) -> Int { rows.count }
    func tableView(_ tableView: NSTableView, viewFor tableColumn: NSTableColumn?, row: Int) -> NSView? {
        let run = rows[row]
        let cell = NSTableCellView()
        let value: NSView
        switch tableColumn?.identifier.rawValue {
        case "game":
            let label = NSTextField(labelWithString: run.gameName ?? run.appID.map { "Steam App \($0)" } ?? "Unidentified game")
            label.font = .systemFont(ofSize: 14, weight: .semibold); value = label
        case "date":
            let date = DateFormatter.localizedString(from:run.startedAt,dateStyle:.medium,timeStyle:.none)
            let minutes=run.endedAt.map { max(0,Int($0.timeIntervalSince(run.startedAt)/60)) }
            let label = NSTextField(labelWithString: date + " · " + (minutes.map { "\($0) min" } ?? "Unknown duration"))
            label.font = .systemFont(ofSize: 12); label.textColor = .secondaryLabelColor; value = label
        case "result":
            value = HistoryBadge(resultTitle(run.result),
                symbol: run.result == .normal ? "checkmark.circle.fill" : run.result == .problems ? "exclamationmark.circle.fill" : "questionmark.circle",
                tint: run.result == .normal ? .systemGreen : run.result == .problems ? .systemRed : .secondaryLabelColor)
        default:
            let request = store.snapshot.policy.pending.first { $0.payload.reportID == run.id }
            let pending = request != nil
            let failed = request.map { (store.snapshot.delivery?[$0.requestID]?.failures ?? 0) > 0 } ?? false
            let expired = request.map { Date().timeIntervalSince($0.createdAt ?? .distantPast) >= 14 * 86400 } ?? false
            let shared = store.snapshot.shared[run.id] != nil
            value = HistoryBadge(failed ? "Send failed" : expired ? "Retry needed" : pending ? "Pending" : shared ? "Shared" : "Not shared",
                symbol: pending ? "clock" : shared ? "arrow.up.circle.fill" : "lock",
                tint: pending ? .systemOrange : shared ? .systemBlue : .secondaryLabelColor)
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
        let run=rows[table.selectedRow]; selection=run.id
        selectedTitle.stringValue = run.gameName ?? run.appID.map { "Steam App \($0)" } ?? "Unidentified game"
        details.stringValue = "\(run.macOS.map { "macOS \($0)" } ?? "macOS unknown") · \(run.chip ?? "Chip unknown") · \(run.memoryGiB.map { "\($0) GB" } ?? "Memory unknown")\nPear \(run.pear) · Wine \(run.wine) · DXMT \(run.dxmt)\nGame build: \(run.gameBuild ?? "Unknown") · Observed exit: \(run.observedExit.rawValue)"
        if displayedID != run.id {
            result.selectItem(at:run.result == .normal ? 1 : run.result == .problems ? 2 : 0)
            note.string=run.note; shareNote.state = .off
            displayedID=run.id
        }
        shareButton.isEnabled = submit != nil && store.available
        retryButton.isEnabled = retryReport != nil && store.snapshot.policy.pending.contains { $0.payload.reportID == run.id }
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
    @objc private func save() { guard let run=editedRun() else { return }; do { try store.record(run); refresh() } catch { failure(error) } }
    @objc private func share() {
        guard store.snapshot.policy.consent.disclosureVersion == 2 else { settings(); return }
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
                self.note.string = ""; self.refresh()
            } catch { self.failure(error) }
        }
    }
    @objc private func disableSharing() {
        do {
            if let configureSharing { try configureSharing(.localOnly,store.snapshot.policy.consent.fields) }
            else { try store.transaction { $0.policy.disableAutomaticSharing() } }
            refresh()
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
        alert.informativeText = "Your answer is separate from Pear’s automatic observation. The note stays on this Mac unless you select Share result."
        let outcome = NSPopUpButton(); outcome.addItems(withTitles: ["Not confirmed", "Worked normally", "Had problems"])
        let notes = NSTextView(); notes.isRichText = false; notes.font = .systemFont(ofSize: 13)
        let scroll = NSScrollView(); scroll.documentView = notes; scroll.hasVerticalScroller = true; scroll.borderType = .bezelBorder
        scroll.heightAnchor.constraint(equalToConstant: 90).isActive = true
        scroll.widthAnchor.constraint(equalToConstant: 440).isActive = true
        notes.isVerticallyResizable = true; notes.textContainer?.widthTracksTextView = true
        let suppress = NSButton(checkboxWithTitle: "Do not show this window after games", target: nil, action: nil)
        let content = stack([text("Your result", bold: true), outcome, text("Note (optional)", bold: true), scroll, suppress,
                             text("Hiding this window does not turn on automatic sharing.")])
        content.frame = NSRect(x: 0, y: 0, width: 440, height: 245)
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
        if store.snapshot.policy.consent.disclosureVersion != 2 { settings() }
    }
    @objc private func settings() {
        let consent=store.snapshot.policy.consent
        let alert=NSAlert();alert.messageText="Sharing settings"
        alert.informativeText="Help improve support for more games. Selected reports help Pear investigate problems and collaborate with contributors. Sharing is optional; Pear works without it.\n\nReports are reviewed privately first. Selected fields and your result may then appear on the public catalog and GitHub. Approval permits publication, not a compatibility certification.\n\nNotes are sent only when explicitly included and remain private. Accounts, credentials, saves, paths and raw logs are excluded. Exact timestamps stay on this Mac.\n\nYou can stop sharing at any time. Already published information may remain in external copies. Choose the fields below; optional test details are sent only with a manual report."
        let mode=NSPopUpButton();mode.addItems(withTitles:["Do not share — local records and manual sharing only","Ask after each game","Automatically share selected fields"])
        mode.selectItem(at:consent.disclosureVersion != 2 || consent.mode == .localOnly ? 0 : consent.mode == .askAfterExit ? 1 : 2)
        let fields:[(ReportField,String)] = [(.environment,"macOS version, chip and memory"),(.components,"Pear, Wine and DXMT versions"),(.game,"Steam App ID and available game build"),(.execution,"Date, process minutes and observed exit status")]
        let checks=fields.map { field,title in
            let check=NSButton(checkboxWithTitle:title,target:nil,action:nil);check.state=consent.fields.contains(field) ? .on : .off;return check
        }
        let prompt=NSButton(checkboxWithTitle:"Show the result window in ask mode",target:nil,action:nil);prompt.state=consent.showExitPrompt ? .on : .off
        let notify=NSButton(checkboxWithTitle:"Notify me after games in automatic mode",target:nil,action:nil);notify.state=consent.notifyAutomaticCompletion ? .on : .off
        let options=stack([mode]+checks+[prompt,notify]);options.frame=NSRect(x:0,y:0,width:480,height:240)
        alert.accessoryView=options;alert.addButton(withTitle:"Save settings");alert.addButton(withTitle:"Cancel")
        alert.beginSheetModal(for:window) { response in
            guard response == .alertFirstButtonReturn else { return }
            let selected=Set(zip(fields,checks).filter{$0.1.state == .on}.map{$0.0.0})
            let selectedMode:SharingMode = mode.indexOfSelectedItem == 0 ? .localOnly : mode.indexOfSelectedItem == 1 ? .askAfterExit : .automatic
            do {
                if let configure=self.configureSharing { try configure(selectedMode,selected) }
                else { try self.store.transaction { $0.policy.configure(mode:selectedMode,fields:selected) } }
                try self.store.transaction {
                    $0.policy.setExitPrompt(prompt.state == .on)
                    $0.policy.setExitNotifications(notify.state == .on)
                }
                self.refresh()
            } catch { self.failure(error) }
        }
    }
}
