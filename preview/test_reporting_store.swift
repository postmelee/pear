// SPDX-FileCopyrightText: 2026 Pear contributors
// SPDX-License-Identifier: GPL-3.0-or-later
import Foundation
@MainActor final class FakeTransfer: ReportTransfer { var cancelled = false; func cancel() { cancelled = true } }
@MainActor final class FakeTransport: ReportTransport {
    var calls: [PendingReport] = []
    var transfers: [FakeTransfer] = []
    var completions: [@MainActor (Bool) -> Void] = []
    func start(_ request: PendingReport, completion: @escaping @MainActor (Bool) -> Void) -> ReportTransfer {
        calls.append(request); completions.append(completion)
        let transfer = FakeTransfer(); transfers.append(transfer); return transfer
    }
}
@main struct StoreTests {
    @MainActor static func main() throws {
        let root = FileManager.default.temporaryDirectory.resolvingSymlinksInPath().appendingPathComponent(UUID().uuidString)
        defer { try? FileManager.default.removeItem(at: root) }
        let store = try ReportingStore(directory: root)
        let transport = FakeTransport(), coordinator = ReportingCoordinator(store: store, transport: transport)
        coordinator.sendNext(); precondition(transport.calls.isEmpty)
        let run = RunObservation(id: UUID(), startedAt: Date(), endedAt: Date(), pear:"test",wine:"11.0",dxmt:"0.80",note:"private")
        try store.transaction { $0.policy.markSharingIntroductionSeen() }
        try store.record(run)
        try store.transaction { $0.policy.enqueue(run,origin:.automatic) }
        coordinator.sendNext();precondition(transport.calls.isEmpty)
        let seenRestart=try ReportingStore(directory:root)
        precondition(!seenRestart.snapshot.policy.needsSharingIntroduction)
        precondition(seenRestart.snapshot.policy.consent.mode == .localOnly)
        precondition(seenRestart.snapshot.policy.consent.fields.isEmpty)
        try coordinator.configure(mode: .automatic, fields: [.game])
        try store.transaction { $0.policy.enqueue(run, origin:.automatic) }
        coordinator.sendNext(); precondition(transport.calls.count == 1)
        try coordinator.disableAutomaticSharing()
        precondition(transport.transfers[0].cancelled)
        transport.completions[0](true) // Late callback cannot restore consent/queue.
        coordinator.sendNext(); precondition(transport.calls.count == 1)
        let restored = try ReportingStore(directory: root)
        precondition(restored.snapshot.policy.consent.mode == .localOnly)
        precondition(restored.snapshot.policy.pending.isEmpty && restored.snapshot.shared.isEmpty)
        precondition(restored.snapshot.runs.count == 1)
        try store.transaction { $0.policy.enqueue(run, origin:.manual, explicitlyShareNote:true) }
        coordinator.sendNext(); let request = transport.calls.last!
        transport.completions.last!(false)
        let callsBeforeRetry = transport.calls.count
        coordinator.sendNext(); precondition(transport.calls.count == callsBeforeRetry)
        try coordinator.retry(reportID: run.id); precondition(transport.calls.last == request)
        transport.completions.last!(true)
        precondition(store.snapshot.policy.pending.isEmpty && store.snapshot.shared[run.id]?.note == "private")
        let reread = try ReportingStore(directory: root)
        precondition(reread.snapshot.shared[run.id]?.note == "private")
        var clock = Date(timeIntervalSince1970: 1_800_000_000)
        let queued = try ReportingStore(directory: root.appendingPathComponent("queue"))
        let queuedTransport = FakeTransport()
        let queue = ReportingCoordinator(store: queued, transport: queuedTransport, now: { clock })
        try queue.enqueue(run, origin: .manual, shareNote: true)
        let first = queuedTransport.calls[0]
        queuedTransport.completions[0](false)
        queue.sendNext(); precondition(queuedTransport.calls.count == 1)
        let restart = try ReportingStore(directory: root.appendingPathComponent("queue"))
        precondition(restart.snapshot.delivery?[first.requestID]?.failures == 1)
        var other = run; other.id = UUID()
        try queue.enqueue(other, origin: .manual)
        precondition(queuedTransport.calls.count == 2 && queuedTransport.calls[1].payload.reportID == other.id)
        queuedTransport.completions[1](true)
        clock.addTimeInterval(5)
        queue.sendNext(); precondition(queuedTransport.calls.last == first)
        queuedTransport.completions.last!(false)
        clock.addTimeInterval(14 * 86400)
        queue.sendNext(); precondition(queuedTransport.calls.count == 3)
        try queue.retry(reportID: run.id)
        precondition(queuedTransport.calls.count == 4 && queuedTransport.calls.last == first)
        try queue.deleteLocal(reportID: run.id)
        precondition(queuedTransport.transfers.last!.cancelled)
        queuedTransport.completions.last!(true)
        precondition(queued.snapshot.policy.pending.isEmpty && queued.snapshot.shared[run.id] == nil)
        precondition(queued.snapshot.shared[other.id] != nil)
        try queue.deleteLocal(reportID: other.id)
        precondition(queued.snapshot.shared[other.id] != nil) // Receipt retained; no server delete implied.
        try coordinator.prepareServerDeletion(reportID: run.id)
        precondition(store.snapshot.serverDeletions?[run.id] == false)
        do { try coordinator.enqueue(run, origin: .manual); preconditionFailure("resending deleted report") } catch {}
        try coordinator.confirmServerDeletion(reportID: run.id)
        precondition(store.snapshot.shared[run.id] == nil && store.snapshot.serverDeletions?[run.id] == true)
        let deletedRestart = try ReportingStore(directory: root)
        precondition(deletedRestart.snapshot.serverDeletions?[run.id] == true)
        var ancient = run; ancient.id = UUID(); ancient.startedAt = clock.addingTimeInterval(-91 * 86400)
        try queued.record(ancient); try queue.pruneLocalHistory()
        precondition(!queued.snapshot.runs.contains { $0.id == ancient.id })
        let broken = try ReportingStore(directory:root,save:{_,_ in throw CocoaError(.fileWriteOutOfSpace)})
        let brokenTransport = FakeTransport(), brokenCoordinator = ReportingCoordinator(store:broken,transport:brokenTransport)
        do { try brokenCoordinator.configure(mode:.automatic,fields:[.game]); preconditionFailure("expected disk error") } catch {}
        brokenCoordinator.sendNext(); precondition(!broken.available && brokenTransport.calls.isEmpty)
        let legacyRoot=root.appendingPathComponent("legacy")
        let legacyStore=try ReportingStore(directory:legacyRoot)
        try legacyStore.transaction { $0.policy.configure(mode:.askAfterExit,fields:[.game]) }
        let legacyFile=legacyRoot.appendingPathComponent("history.json")
        var legacyJSON=try JSONSerialization.jsonObject(with:Data(contentsOf:legacyFile)) as! [String:Any]
        var legacyPolicy=legacyJSON["policy"] as! [String:Any]
        var legacyConsent=legacyPolicy["consent"] as! [String:Any]
        legacyConsent["showExitPrompt"]=false;legacyConsent.removeValue(forKey:"introductionSeen")
        legacyPolicy["consent"]=legacyConsent;legacyJSON["policy"]=legacyPolicy
        try JSONSerialization.data(withJSONObject:legacyJSON).write(to:legacyFile)
        let migrated=try ReportingStore(directory:legacyRoot)
        precondition(migrated.snapshot.policy.consent.mode == .localOnly)
        precondition(!migrated.snapshot.policy.shouldShowExitPrompt && !migrated.snapshot.policy.needsSharingIntroduction)
        let migratedRestart=try ReportingStore(directory:legacyRoot)
        precondition(migratedRestart.snapshot.policy.consent.mode == .localOnly)
        let file = root.appendingPathComponent("history.json")
        try Data("incomplete JSON".utf8).write(to:file)
        do { _ = try ReportingStore(directory:root); preconditionFailure("must preserve corrupt file") } catch {}
        let preserved = try Data(contentsOf:file)
        precondition(preserved == Data("incomplete JSON".utf8))
        print("PASS: durable consent, restart, default silence, cancellation, late callback, manual sharing, immutable retry, disk failure, corrupt-file preservation, bounded durable retry, expiry, unrelated-report progress, delete cancellation")
    }
}
