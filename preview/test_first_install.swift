// SPDX-FileCopyrightText: 2026 Pear contributors
// SPDX-License-Identifier: GPL-3.0-or-later
import Foundation

// Cross-language regression: the real CLI owns the root before real Swift
// reporting writes. No runtime, network, keychain or user's state is used.
@main struct FirstInstallTests {
    @MainActor static func main() throws {
        func require(_ value: @autoclosure () throws -> Bool) throws {
            let result = try value(); precondition(result)
        }
        let cli = CommandLine.arguments[1]
        let fm = FileManager.default
        let scratch = fm.temporaryDirectory.appendingPathComponent(UUID().uuidString).resolvingSymlinksInPath()
        try fm.createDirectory(at: scratch, withIntermediateDirectories: true)
        defer { try? fm.removeItem(at: scratch) }
        func invoke(_ command: String, _ root: URL, executable: String = "") throws -> (Int32, Data) {
            let process = Process(), pipe = Pipe()
            process.executableURL = URL(fileURLWithPath: executable.isEmpty ? cli : executable)
            process.arguments = [command, "--root", root.path]
            process.standardOutput = pipe; process.standardError = pipe
            try process.run()
            let bytes = pipe.fileHandleForReading.readDataToEndOfFile()
            process.waitUntilExit()
            return (process.terminationStatus, bytes)
        }
        let clean = scratch.appendingPathComponent("clean")
        try require(try invoke("setup-info", clean).0 == 0)
        precondition(!fm.fileExists(atPath: clean.path))
        let first = try invoke("initialize", clean)
        precondition(first.0 == 0)
        try require(try JSONDecoder().decode(SetupInfo.self, from: first.1).ready == false)
        precondition(fm.fileExists(atPath: clean.appendingPathComponent(".owner").path))
        let cleanOwner = try ReportingSessionOwner(directory: clean.appendingPathComponent("history"))
        let cleanStore = try ReportingStore(directory: clean.appendingPathComponent("history"))
        try cleanStore.transaction { $0.policy.configure(mode: .localOnly, fields: []) }
        try require(try invoke("initialize", clean).0 == 0)
        withExtendedLifetime(cleanOwner) {}

        let failed = scratch.appendingPathComponent("failed")
        var legacyOwner: ReportingSessionOwner? = try ReportingSessionOwner(directory: failed.appendingPathComponent("history"))
        let legacy = try ReportingStore(directory: failed.appendingPathComponent("history"))
        let run = RunObservation(id: UUID(), startedAt: Date(timeIntervalSinceReferenceDate: 123.5),
            pear: "0.1.0", wine: "11.0", dxmt: "0.80", note: "Preserve the local note.")
        try legacy.transaction {
            $0.policy.configure(mode: .automatic, fields: [.game, .execution])
            $0.runs = [run]
        }
        let file = failed.appendingPathComponent("history/history.json")
        let before = try Data(contentsOf: file)
        if CommandLine.arguments.count > 2 {
            let original = try invoke("setup", failed, executable: CommandLine.arguments[2])
            precondition(original.0 != 0)
            precondition(String(decoding: original.1, as: UTF8.self).contains("contains unrelated files"))
        }
        try require(try invoke("initialize", failed).0 != 0)
        precondition(!fm.fileExists(atPath: failed.appendingPathComponent(".owner").path))
        withExtendedLifetime(legacyOwner) {}
        legacyOwner = nil
        let recovered = try invoke("initialize", failed)
        precondition(recovered.0 == 0, String(decoding: recovered.1, as: UTF8.self))
        try require(try Data(contentsOf: file) == before)
        let reopened = try ReportingStore(directory: failed.appendingPathComponent("history"))
        precondition(reopened.snapshot.policy.consent.mode == .automatic)
        precondition(reopened.snapshot.runs.first?.note == run.note)
        precondition(reopened.snapshot.runs.first?.startedAt == run.startedAt)
        print("PASS: clean initialization, actual Swift legacy snapshot, active-owner refusal and byte-preserving recovery")
    }
}
