// SPDX-FileCopyrightText: 2026 Pear contributors
// SPDX-License-Identifier: GPL-3.0-or-later
import Foundation

enum SharingMode: String, Codable { case localOnly, askAfterExit, automatic }
enum ReportField: String, Codable, CaseIterable, Hashable {
    case environment, components, game, execution
}
enum UserRunResult: String, Codable { case normal, problems, unknown }
enum ObservedExit: String, Codable { case exited, interrupted, unknown }
enum SendOrigin: String, Codable { case manual, automatic }

struct SharingConsent: Codable, Equatable {
    var mode: SharingMode = .localOnly
    var fields: Set<ReportField> = []
    var generation: UInt64 = 0
    var disclosureVersion: Int? = nil
    var showExitPrompt = true
    var notifyAutomaticCompletion = false
}

// Local timestamps and potentially identifying local metadata are never encoded
// into a shared payload. Missing observations stay nil/unknown.
struct RunObservation: Codable {
    var id: UUID
    var startedAt: Date
    var endedAt: Date?
    var macOS: String?
    var chip: String?
    var memoryGiB: Int?
    var pear: String
    var wine: String
    var dxmt: String
    var appID: UInt32?
    var gameBuild: String?
    var gameName: String? = nil
    var observedExit: ObservedExit = .unknown
    var result: UserRunResult = .unknown
    var note: String = ""
    var supplemental: SupplementalReport? = nil

    func payload(fields: Set<ReportField>, shareNote: Bool) -> SharedRun {
        var shared = SharedRun(reportID: id, userResult: result)
        if fields.contains(.environment) {
            shared.macOS = macOS; shared.chip = chip; shared.memoryGiB = memoryGiB
        }
        if fields.contains(.components) {
            shared.pear = pear; shared.wine = wine; shared.dxmt = dxmt
        }
        if fields.contains(.game) { shared.appID = appID; shared.gameBuild = gameBuild }
        if fields.contains(.execution) {
            let formatter = DateFormatter()
            formatter.locale = Locale(identifier: "en_US_POSIX")
            formatter.calendar = Calendar(identifier: .gregorian)
            formatter.timeZone = TimeZone(secondsFromGMT: 0)
            formatter.dateFormat = "yyyy-MM-dd"
            shared.dateUTC = formatter.string(from: startedAt)
            if let end = endedAt, end >= startedAt {
                shared.processMinutes = Int(end.timeIntervalSince(startedAt) / 60)
            }
            shared.observedExit = observedExit
        }
        // Deliberately no Pass, actual-play duration, account, path or raw log field.
        if shareNote, !note.isEmpty { shared.note = note }
        shared.supplemental = supplemental
        return shared
    }
}

struct SharedRun: Codable, Equatable {
    var reportID: UUID
    var userResult: UserRunResult
    var macOS: String?
    var chip: String?
    var memoryGiB: Int?
    var pear: String?
    var wine: String?
    var dxmt: String?
    var appID: UInt32?
    var gameBuild: String?
    var dateUTC: String?
    var processMinutes: Int?
    var observedExit: ObservedExit?
    var note: String?
    var supplemental: SupplementalReport? = nil
}

// Optional user observations are distinct from process observations.
struct SupplementalReport: Codable, Equatable {
    var furthestResult: String = "unknown"
    var activePlayMinutes: Int?
    var input: String = "unknown"
    var audio: String = "unknown"
    var saveReload: String = "unknown"
    var recovery: String = "unknown"
    var settings: String = ""
}

struct PendingReport: Codable, Equatable {
    // Stable across retries; changing result/note creates a new request revision
    // for the same reportID. Server still needs ownership and revision checks.
    var requestID: UUID
    var disclosureVersion: Int? = 2
    var createdAt: Date? = nil
    var revision: UInt64
    var origin: SendOrigin
    var consentGeneration: UInt64
    var payload: SharedRun
}

struct ReportingPolicy: Codable {
    private(set) var consent = SharingConsent()
    private(set) var pending: [PendingReport] = []
    private(set) var revisions: [UUID: UInt64] = [:]

    mutating func configure(mode: SharingMode, fields: Set<ReportField>) {
        consent.generation += 1
        consent.disclosureVersion = 2
        consent.mode = mode
        consent.fields = fields
        // Changing either scope or mode revokes previously queued auto payloads.
        pending.removeAll { $0.origin == .automatic }
    }

    mutating func disableAutomaticSharing() {
        configure(mode: .localOnly, fields: consent.fields)
    }

    mutating func setExitPrompt(_ enabled: Bool) { consent.showExitPrompt = enabled }
    mutating func suppressExitPrompt() { consent.showExitPrompt = false }
    mutating func setExitNotifications(_ enabled: Bool) { consent.notifyAutomaticCompletion = enabled }

    var shouldShowExitPrompt: Bool { consent.mode == .askAfterExit && consent.showExitPrompt }
    var shouldNotifyExit: Bool { consent.mode == .automatic && consent.notifyAutomaticCompletion }

    @discardableResult
    mutating func enqueue(_ run: RunObservation, origin: SendOrigin,
                          explicitlyShareNote: Bool = false, now: Date = Date()) -> UUID? {
        guard origin == .manual || (consent.mode == .automatic && consent.disclosureVersion == 2 && !consent.fields.isEmpty) else { return nil }
        let revision = (revisions[run.id] ?? 0) + 1
        revisions[run.id] = revision
        var payload = run.payload(fields: consent.fields, shareNote: origin == .manual && explicitlyShareNote)
        if origin == .automatic { payload.supplemental = nil }
        let request = PendingReport(requestID: UUID(), createdAt: now, revision: revision, origin: origin,
            consentGeneration: consent.generation,
            payload: payload)
        pending.append(request)
        return request.requestID
    }

    // Invoke under the same serialized owner as consent mutation, immediately
    // before starting transport. Transport must cancel active auto leases when
    // generation changes. This model alone makes no network cancellation claim.
    func authorizedRequest(_ id: UUID) -> PendingReport? {
        guard let request = pending.first(where: { $0.requestID == id }) else { return nil }
        guard request.disclosureVersion == 2 else { return nil }
        guard request.origin == .manual ||
            (consent.mode == .automatic && consent.disclosureVersion == 2 && consent.generation == request.consentGeneration) else { return nil }
        return request
    }

    mutating func removePending(reportID: UUID) {
        pending.removeAll { $0.payload.reportID == reportID }
    }

    mutating func acknowledge(_ id: UUID) { pending.removeAll { $0.requestID == id } }
}
