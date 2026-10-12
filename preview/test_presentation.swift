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
        print("Presentation fixtures passed: fragmented UTF-8, multiple updates, retry reset, malformed event, metadata, bounded buffering.")
    }
}
