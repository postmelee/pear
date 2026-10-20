// SPDX-FileCopyrightText: 2026 Pear contributors
// SPDX-License-Identifier: GPL-3.0-or-later
import Foundation

// A deterministic launch gate shared by updater callbacks and the watchdog.
// The adapter must execute returned actions on one serialized owner, rechecking
// session ownership immediately before starting Sparkle installation.
struct UpdateLaunchPolicy {
    enum Session { case idle, active, unknown }
    enum Phase { case initial, checking, offering, downloading, installing, released }
    enum Action: Equatable { case none, check, offer, download, install, continueSteam, deferUpdate }
    private(set) var phase: Phase = .initial
    private(set) var launchReleased = false
    private var deadline: TimeInterval = 0
    private var managedByHomebrew = false

    mutating func begin(now: TimeInterval, session: Session, homebrew: Bool) -> Action {
        guard phase == .initial else { return .none }
        managedByHomebrew = homebrew
        if homebrew || session != .idle { return release() }
        deadline = now + 8
        phase = .checking
        return .check
    }

    mutating func checked(updateAvailable: Bool, now: TimeInterval) -> Action {
        guard phase == .checking else { return .none }
        guard now < deadline, updateAvailable else { return release() }
        phase = .offering
        return .offer
    }

    mutating func tick(now: TimeInterval) -> Action {
        guard phase == .checking, now >= deadline else { return .none }
        return release()
    }

    mutating func chooseUpdate(_ accepted: Bool, session: Session) -> Action {
        guard phase == .offering else { return .none }
        guard accepted else { return release() }
        guard session == .idle, !managedByHomebrew else { return release(deferred: true) }
        phase = .downloading
        return .download
    }

    mutating func readyToInstall(session: Session) -> Action {
        guard phase == .downloading else { return .none }
        guard session == .idle, !managedByHomebrew else { return release(deferred: true) }
        phase = .installing
        return .install
    }

    mutating func failedOrCancelled() -> Action {
        guard phase != .initial && phase != .released else { return .none }
        return release()
    }

    private mutating func release(deferred: Bool = false) -> Action {
        guard !launchReleased else { return .none }
        phase = .released
        launchReleased = true
        return deferred ? .deferUpdate : .continueSteam
    }
}
