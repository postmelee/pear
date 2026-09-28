// Stage 4 incremental marker: baseline
import Foundation
import Darwin

var result = Result()
var exitStatus: Int32 = 1
do {
    let raw = Array(CommandLine.arguments.dropFirst())
    guard raw.count == 14 else { throw Failure.usage }
    var flags: [String: String] = [:]
    let names = Set(["--bundle-root", "--entry", "--fixture-sha256", "--timeout-ms", "--output-limit", "--observer-ready", "--observer-gap"])
    for index in stride(from: 0, to: raw.count, by: 2) {
        guard names.contains(raw[index]), flags[raw[index]] == nil else { throw Failure.usage }
        flags[raw[index]] = raw[index + 1]
    }
    guard Set(flags.keys) == names,
          let timeout = Int(flags["--timeout-ms"]!), (100...5000).contains(timeout),
          let limit = Int(flags["--output-limit"]!), (256...65536).contains(limit),
          ["yes", "no"].contains(flags["--observer-ready"]!), ["yes", "no"].contains(flags["--observer-gap"]!),
          isHash(flags["--fixture-sha256"]!) else { throw Failure.usage }
    let native = nativeHost()
    result.translated = native.1
    if !native.0 { result.classification = "host_not_native"; exitStatus = 3 }
    else {
        let contract = try Contracts(flags["--bundle-root"]!)
        let input = try contract.validate(flags["--entry"]!, trustedHash: flags["--fixture-sha256"]!)
        try checkStateDirectories(input.files)
        if flags["--observer-ready"] == "no" {
            result.classification = "observer_not_ready"; exitStatus = 3
        } else {
            result = supervise(input, timeoutMS: timeout, outputLimit: limit, gap: flags["--observer-gap"] == "yes")
            exitStatus = result.classification == "success" ? 0 : (result.classification == "invalid_contract" ? 1 : 4)
        }
    }
} catch Failure.ineligible { result.classification = "ineligible"; exitStatus = 3 }
catch Failure.usage { result.classification = "invalid_contract"; exitStatus = 2 }
catch Failure.invalid { result.classification = "invalid_contract"; exitStatus = 1 }
catch { result.classification = "internal_error"; exitStatus = 4 }
let encoder = JSONEncoder()
encoder.outputFormatting = [.sortedKeys]
if let data = try? encoder.encode(result) {
    FileHandle.standardOutput.write(data)
    FileHandle.standardOutput.write(Data([10]))
} else {
    // Fixed diagnostic only; never interpolate input bytes or native errors.
    FileHandle.standardOutput.write(Data("{\"classification\":\"internal_error\"}\n".utf8))
    exitStatus = 4
}
exit(exitStatus)
