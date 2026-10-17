// SPDX-FileCopyrightText: 2026 Pear contributors
// SPDX-License-Identifier: GPL-3.0-or-later
import Foundation

struct ReportingSnapshot: Codable {
    var schemaVersion = 1
    var policy = ReportingPolicy()
    var runs: [RunObservation] = []
    var shared: [UUID: SharedRun] = [:]
}

enum ReportingStoreError: Error { case unsafePath, unknownSchema, unavailable }

// A single main-thread owner serializes consent, disk state and transport admission.
// A failed read never resets consent over an existing file or starts transport.
@MainActor final class ReportingStore {
    private(set) var snapshot: ReportingSnapshot
    private(set) var available = true
    private let file: URL
    private let saveBytes: (Data, URL) throws -> Void

    init(directory: URL, save: ((Data, URL) throws -> Void)? = nil) throws {
        let fm = FileManager.default
        let resolved = directory.standardizedFileURL.resolvingSymlinksInPath()
        guard resolved.path == directory.standardizedFileURL.path else { throw ReportingStoreError.unsafePath }
        try fm.createDirectory(at: directory, withIntermediateDirectories: true,
                               attributes: [.posixPermissions: 0o700])
        file = directory.appendingPathComponent("history.json")
        if fm.fileExists(atPath: file.path) {
            let attributes = try fm.attributesOfItem(atPath: file.path)
            guard attributes[.type] as? FileAttributeType == .typeRegular else { throw ReportingStoreError.unsafePath }
            snapshot = try JSONDecoder().decode(ReportingSnapshot.self, from: Data(contentsOf: file))
            guard snapshot.schemaVersion == 1 else { throw ReportingStoreError.unknownSchema }
        } else { snapshot = ReportingSnapshot() }
        saveBytes = save ?? { data, url in
            // Atomic replacement never leaves a partially encoded consent/queue.
            try data.write(to: url, options: [.atomic])
            try fm.setAttributes([.posixPermissions: 0o600], ofItemAtPath: url.path)
        }
    }

    func transaction(_ edit: (inout ReportingSnapshot) throws -> Void) throws {
        guard available else { throw ReportingStoreError.unavailable }
        var next = snapshot
        try edit(&next)
        do {
            try saveBytes(JSONEncoder().encode(next), file)
            snapshot = next
        } catch {
            // The caller must cancel all active transfers and display this error.
            // Do not claim durable withdrawal when the filesystem rejected it.
            available = false
            snapshot.policy.disableAutomaticSharing()
            throw error
        }
    }

    func record(_ run: RunObservation) throws {
        try transaction { state in
            if let i = state.runs.firstIndex(where: { $0.id == run.id }) { state.runs[i] = run }
            else { state.runs.append(run) }
            state.runs.sort { $0.startedAt > $1.startedAt }
        }
    }
}

// Tests inject transport; production URLSession must use its own non-redirecting
// ephemeral session and report-scoped Keychain capability. No networking here.
@MainActor protocol ReportTransfer: AnyObject { func cancel() }
@MainActor protocol ReportTransport: AnyObject {
    func start(_ request: PendingReport, completion: @escaping @MainActor (Bool) -> Void) -> ReportTransfer
}

@MainActor final class ReportingCoordinator {
    let store: ReportingStore
    private let transport: ReportTransport
    private var active: (id: UUID, origin: SendOrigin, transfer: ReportTransfer)?
    init(store: ReportingStore, transport: ReportTransport) { self.store = store; self.transport = transport }

    func configure(mode: SharingMode, fields: Set<ReportField>) throws {
        // Cancellation is immediate even if persistence subsequently fails.
        if active?.origin == .automatic { active?.transfer.cancel(); active = nil }
        do { try store.transaction { $0.policy.configure(mode: mode, fields: fields) } }
        catch { active?.transfer.cancel(); active = nil; throw error }
    }

    func disableAutomaticSharing() throws {
        try configure(mode: .localOnly, fields: store.snapshot.policy.consent.fields)
    }

    // Call after an explicit manual share or a permitted automatic enqueue, and
    // after bounded retry delay. No recursive retry loop and no timer on consent-off.
    func sendNext() {
        guard store.available, active == nil,
              let request = store.snapshot.policy.pending.first,
              store.snapshot.policy.authorizedRequest(request.requestID) != nil else { return }
        let id = request.requestID
        // Completion is dispatched to a later main-thread turn by the adapter.
        let transfer = transport.start(request) { [weak self] success in
            guard let self, self.active?.id == id else { return }
            self.active = nil
            guard success else { return } // Same immutable payload stays queued.
            do {
                try self.store.transaction { state in
                    state.shared[request.payload.reportID] = request.payload
                    state.policy.acknowledge(id)
                }
            } catch { /* Unavailable store blocks subsequent sends. UI surfaces status. */ }
        }
        active = (id, request.origin, transfer)
    }
}
