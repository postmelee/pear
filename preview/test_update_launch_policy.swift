// SPDX-FileCopyrightText: 2026 Pear contributors
// SPDX-License-Identifier: GPL-3.0-or-later
import Foundation
@main struct UpdateLaunchPolicyTests {
 static func main() {
  var timeout = UpdateLaunchPolicy()
  precondition(timeout.begin(now: 100, session: .idle, homebrew: false) == .check)
  precondition(timeout.tick(now: 107) == .none)
  precondition(timeout.tick(now: 108) == .continueSteam)
  precondition(timeout.checked(updateAvailable: true, now: 109) == .none)
  precondition(timeout.failedOrCancelled() == .none)
  var noUpdate = UpdateLaunchPolicy()
  _ = noUpdate.begin(now: 0, session: .idle, homebrew: false)
  precondition(noUpdate.checked(updateAvailable: false, now: 1) == .continueSteam)
  var later = UpdateLaunchPolicy()
  _ = later.begin(now: 0, session: .idle, homebrew: false)
  precondition(later.checked(updateAvailable: true, now: 1) == .offer)
  precondition(later.chooseUpdate(false, session: .idle) == .continueSteam)
  var race = UpdateLaunchPolicy()
  _ = race.begin(now: 0, session: .idle, homebrew: false)
  _ = race.checked(updateAvailable: true, now: 1)
  precondition(race.chooseUpdate(true, session: .idle) == .download)
  precondition(race.readyToInstall(session: .active) == .deferUpdate)
  precondition(race.readyToInstall(session: .idle) == .none)
  var install = UpdateLaunchPolicy()
  _ = install.begin(now: 0, session: .idle, homebrew: false)
  _ = install.checked(updateAvailable: true, now: 1)
  _ = install.chooseUpdate(true, session: .idle)
  precondition(install.readyToInstall(session: .idle) == .install)
  precondition(install.failedOrCancelled() == .continueSteam)
  for state in [UpdateLaunchPolicy.Session.active, .unknown] {
   var busy = UpdateLaunchPolicy()
   precondition(busy.begin(now: 0, session: state, homebrew: false) == .continueSteam)
  }
  var brew = UpdateLaunchPolicy()
  precondition(brew.begin(now: 0, session: .idle, homebrew: true) == .continueSteam)
  print("PASS: bounded checks, no update, later, late callbacks, active/unknown session, install race, failure and Homebrew gate")
 }
}
