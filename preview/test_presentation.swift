// SPDX-FileCopyrightText: 2026 Pear contributors
// SPDX-License-Identifier: GPL-3.0-or-later
import Foundation

@main
struct PresentationTests {
    static func main() throws {
        var stream = OutputLines()
        let message = Data("Checking…\n@download\t3\t10\tfixture\nDone".utf8)
        var received: [String] = []
        for byte in message { received += stream.append(Data([byte])) }
        received += stream.finish()
        precondition(received == ["Checking…", "@download\t3\t10\tfixture", "Done"])
        precondition(stream.finish().isEmpty)
        for bytes in [8, 2, 10] { // A curl retry may reset the byte count.
            guard case let .download(got, total, _) = SetupUpdate("@download\t\(bytes)\t10\tfixture") else { fatalError() }
            precondition(got == bytes && total == 10)
        }
        guard case .status = SetupUpdate("@download\t1\t0\tfixture") else { fatalError() }
        precondition(downloadSize(534424618) == "534.4 MB")
        let fresh = Data(#"{"version":"fixture","runtime_id":"fixture","runtime_bytes":10,"steam_bytes":3,"runtime_present":false,"steam_present":false,"ready":false}"#.utf8)
        let info = try JSONDecoder().decode(SetupInfo.self, from: fresh)
        precondition(!info.ready && info.runtime_bytes == 10)
        precondition((try? JSONDecoder().decode(SetupInfo.self, from: Data("{}".utf8))) == nil)
        var bounded = OutputLines()
        precondition(!bounded.append(Data(repeating: 120, count: 70_000)).isEmpty)
        precondition(bounded.finish().isEmpty)
        // Launch handoff alone never establishes a visible window.
        precondition(SteamOpening.state(elapsed: 0, visible: false) == .waiting)
        precondition(!SteamOpening.waiting.retryEnabled)
        precondition(SteamOpening.state(elapsed: 29.9, visible: false) == .waiting)
        precondition(SteamOpening.state(elapsed: 30, visible: false) == .delayed)
        precondition(SteamOpening.delayed.retryEnabled && SteamOpening.delayed.observing)
        precondition(SteamOpening.state(elapsed: 120, visible: false) == .unconfirmed)
        precondition(!SteamOpening.unconfirmed.observing)
        precondition(SteamOpening.state(elapsed: 120, visible: true) == .visible)
        precondition(!SteamOpening.visible.observing)
        let executable = "/fixture/runtime/wine"
        let prefix = "/fixture/with spaces/private/prefix"
        let steam = #"C:\Program Files (x86)\Steam\steam.exe"#
        let helper = #"C:\Program Files (x86)\Steam\bin\cef\cef.win64\steamwebhelper.exe"#
        func arguments(_ argv: [String], _ env: [String], exe: String = "/fixture/runtime/wine") -> Data {
            var count = Int32(argv.count)
            var bytes = withUnsafeBytes(of: &count) { Data($0) }
            bytes.append(Data((exe + "\0\0\0" + argv.joined(separator: "\0") + "\0" + env.joined(separator: "\0") + "\0\0").utf8))
            return bytes
        }
        for name in [steam, helper] {
            let data = arguments(["wine", name], ["UNRELATED=value", "WINEPREFIX=" + prefix])
            precondition(steamProcessMatches(data, executable: executable, prefix: prefix))
            precondition(!steamProcessMatches(data, executable: executable, prefix: prefix + "-other"))
            precondition(!steamProcessMatches(data, executable: "/other/wine", prefix: prefix))
        }
        precondition(steamProcessMatches(arguments([steam, "steam://open/games", ""], ["", "", "WINEPREFIX=" + prefix]), executable: executable, prefix: prefix))
        for bad in [
            arguments(["wine", "game.exe"], ["WINEPREFIX=" + prefix]),
            arguments(["wine", steam], []),
            arguments(["wine", steam], ["WINEPREFIX=" + prefix, "WINEPREFIX=/other"]),
            arguments(["wine", "game.exe"], [steam, "WINEPREFIX=" + prefix]),
            Data([1, 0, 0, 0]), Data([255, 255, 255, 255]), Data()
        ] {
            precondition(!steamProcessMatches(bad, executable: executable, prefix: prefix))
        }
        let valid = arguments(["wine", steam], ["WINEPREFIX=" + prefix])
        // Truncation before the prefix field terminator must not yield a match.
        for size in 0..<(valid.count - 2) {
            precondition(!steamProcessMatches(Data(valid.prefix(size)), executable: executable, prefix: prefix))
        }
        print("Presentation fixtures passed: fragmented UTF-8, multiple updates, retry reset, malformed event, metadata, bounded buffering.")
    }
}
