// SPDX-FileCopyrightText: 2026 Pear contributors
// SPDX-License-Identifier: GPL-3.0-or-later
import Foundation

struct DeliveryAttempt: Codable {
    var failures: Int = 0
    var nextAttempt: Date?
}

struct ReportingSnapshot: Codable {
    var schemaVersion = 1
    var policy = ReportingPolicy()
    var runs: [RunObservation] = []
    var shared: [UUID: SharedRun] = [:]
    var delivery: [UUID: DeliveryAttempt]? = nil
    // false = deletion requested/retry needed; true = server confirmed.
    var serverDeletions: [UUID: Bool]? = nil
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
        // Preserve a legacy request for no questions without enabling any sharing.
        if snapshot.policy.consent.mode == .askAfterExit && !snapshot.policy.consent.showExitPrompt {
            try transaction { $0.policy.disableAutomaticSharing() }
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
    private let now: () -> Date
    var changed: (() -> Void)?
    private var active: (id: UUID, origin: SendOrigin, transfer: ReportTransfer)?
    init(store: ReportingStore, transport: ReportTransport, now: @escaping () -> Date = Date.init) {
        self.store = store; self.transport = transport; self.now = now
    }

    func configure(mode: SharingMode, fields: Set<ReportField>) throws {
        // Cancellation is immediate even if persistence subsequently fails.
        if active?.origin == .automatic { active?.transfer.cancel(); active = nil }
        do { try store.transaction {
            $0.policy.configure(mode: mode, fields: fields)
            let remaining = Set($0.policy.pending.map(\.requestID))
            $0.delivery = $0.delivery?.filter { remaining.contains($0.key) }
        }; changed?() }
        catch { active?.transfer.cancel(); active = nil; throw error }
    }

    func disableAutomaticSharing() throws {
        try configure(mode: .localOnly, fields: store.snapshot.policy.consent.fields)
    }

    func enqueue(_ run: RunObservation, origin: SendOrigin, shareNote: Bool = false) throws {
        guard store.snapshot.serverDeletions?[run.id] == nil,
              !shareNote || run.note.count <= 4000 else { throw ReportingStoreError.unavailable }
        try store.transaction { $0.policy.enqueue(run, origin: origin, explicitlyShareNote: shareNote, now: now()) }
        changed?(); sendNext()
    }

    // Retry the already approved immutable payload, not a newly edited note.
    func retry(reportID: UUID) throws {
        guard let request = store.snapshot.policy.pending.first(where: { $0.payload.reportID == reportID }) else { return }
        try store.transaction {
            var delivery = $0.delivery ?? [:]
            delivery[request.requestID] = DeliveryAttempt(nextAttempt: now())
            $0.delivery = delivery
        }
        changed?(); sendNext(explicitRequest: request.requestID)
    }

    func stop() { active?.transfer.cancel(); active = nil }

    func prepareServerDeletion(reportID: UUID) throws {
        if let active, store.snapshot.policy.pending.contains(where: {
            $0.requestID == active.id && $0.payload.reportID == reportID
        }) { active.transfer.cancel(); self.active = nil }
        try store.transaction {
            $0.policy.removePending(reportID: reportID)
            var deleted = $0.serverDeletions ?? [:]; deleted[reportID] = false
            $0.serverDeletions = deleted
        }
        changed?()
    }

    func confirmServerDeletion(reportID: UUID) throws {
        try store.transaction { $0.serverDeletions?[reportID] = true; $0.shared.removeValue(forKey: reportID) }
        changed?()
    }

    func pruneLocalHistory() throws {
        let cutoff = now().addingTimeInterval(-90 * 86400)
        try store.transaction { state in
            let queued = Set(state.policy.pending.map { $0.payload.reportID })
            state.runs.removeAll { $0.startedAt < cutoff && !queued.contains($0.id) }
        }
    }

    func deleteLocal(reportID: UUID) throws {
        if let active, store.snapshot.policy.pending.contains(where: {
            $0.requestID == active.id && $0.payload.reportID == reportID
        }) { active.transfer.cancel(); self.active = nil }
        try store.transaction {
            let ids = Set($0.policy.pending.filter { $0.payload.reportID == reportID }.map(\.requestID))
            $0.policy.removePending(reportID: reportID)
            $0.delivery = $0.delivery?.filter { !ids.contains($0.key) }
            $0.runs.removeAll { $0.id == reportID }
            // Keep the shared receipt and ownership separately for server deletion.
        }
        changed?()
    }

    // A host timer may call this; no recursive retry. Requests older than 14 days
    // require explicit retry. A failed report does not block unrelated reports;
    // revisions for the same report remain ordered.
    func sendNext(explicitRequest: UUID? = nil) {
        guard store.available, active == nil else { return }
        var seen = Set<UUID>()
        let time = now()
        let request = store.snapshot.policy.pending.first { item in
            guard store.snapshot.serverDeletions?[item.payload.reportID] == nil,
                  seen.insert(item.payload.reportID).inserted,
                  store.snapshot.policy.authorizedRequest(item.requestID) != nil else { return false }
            if explicitRequest == item.requestID { return true }
            guard let created = item.createdAt, time >= created,
                  time.timeIntervalSince(created) < 14 * 86400 else { return false }
            return (store.snapshot.delivery?[item.requestID]?.nextAttempt ?? .distantPast) <= time
        }
        guard let request else { return }
        let id = request.requestID
        let transfer = transport.start(request) { [weak self] success in
            guard let self, self.active?.id == id else { return }
            self.active = nil
            do {
                try self.store.transaction { state in
                    var delivery = state.delivery ?? [:]
                    if success {
                        state.shared[request.payload.reportID] = request.payload
                        state.policy.acknowledge(id)
                        delivery.removeValue(forKey: id)
                    } else {
                        let failures = min(20, (delivery[id]?.failures ?? 0) + 1)
                        let delay = min(3600.0, 5 * pow(2, Double(failures - 1)))
                        delivery[id] = DeliveryAttempt(failures: failures, nextAttempt: self.now().addingTimeInterval(delay))
                    }
                    state.delivery = delivery
                }
            } catch { /* An unavailable store blocks all subsequent sends. */ }
            self.changed?()
        }
        active = (id, request.origin, transfer)
    }
}
