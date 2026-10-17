// SPDX-FileCopyrightText: 2026 Pear contributors
// SPDX-License-Identifier: GPL-3.0-or-later
import Foundation
@main struct ReportingPolicyTests {
 static func main() throws {
  var policy = ReportingPolicy()
  let start = Date(timeIntervalSince1970: 1_700_000_000)
  let run = RunObservation(id: UUID(), startedAt: start, endedAt: start.addingTimeInterval(125),
      macOS: "26.5.2", chip: "Apple M4 Pro", memoryGiB: 24, pear: "0.1.0", wine: "11.0",
      dxmt: "0.80", appID: 3405340, gameBuild: nil, note: "private note")
  precondition(policy.enqueue(run, origin: .automatic) == nil)
  precondition(!policy.shouldShowExitPrompt && !policy.shouldNotifyExit)
  policy.configure(mode: .askAfterExit, fields: Set(ReportField.allCases))
  precondition(policy.shouldShowExitPrompt)
  policy.suppressExitPrompt()
  precondition(!policy.shouldShowExitPrompt && policy.consent.mode == .askAfterExit)
  precondition(policy.enqueue(run, origin: .automatic) == nil)
  policy.configure(mode: .automatic, fields: [.game, .execution])
  let auto = policy.enqueue(run, origin: .automatic, explicitlyShareNote: true)!
  let payload = policy.authorizedRequest(auto)!.payload
  precondition(payload.note == nil && payload.macOS == nil && payload.pear == nil)
  precondition(payload.processMinutes == 2 && payload.userResult == .unknown && payload.observedExit == .unknown)
  let json = String(data: try JSONEncoder().encode(payload), encoding: .utf8)!
  precondition(!json.contains("startedAt") && !json.contains("endedAt") && !json.contains("private note"))
  let retry = policy.authorizedRequest(auto)!
  precondition(policy.authorizedRequest(auto) == retry)
  let manual = policy.enqueue(run, origin: .manual, explicitlyShareNote: true)!
  precondition(policy.authorizedRequest(manual)!.payload.note == "private note")
  precondition(policy.authorizedRequest(manual)!.payload.reportID == payload.reportID)
  precondition(policy.authorizedRequest(manual)!.revision > retry.revision)
  policy.disableAutomaticSharing()
  precondition(policy.authorizedRequest(auto) == nil && policy.authorizedRequest(manual) != nil)
  let restored = try JSONDecoder().decode(ReportingPolicy.self, from: JSONEncoder().encode(policy))
  precondition(restored.consent.mode == .localOnly && restored.authorizedRequest(auto) == nil)
  precondition(restored.authorizedRequest(manual) == policy.authorizedRequest(manual))
  policy.configure(mode: .automatic, fields: [.environment])
  let oldScope = policy.enqueue(run, origin: .automatic)!
  policy.configure(mode: .automatic, fields: [.game])
  precondition(policy.authorizedRequest(oldScope) == nil)
  print("PASS: default silence, prompt suppression, field projection, note privacy, retries, stable report identity, withdrawal and Codable restart")
 }
}
