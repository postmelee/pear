import Foundation

enum Failure: Error { case invalid, ineligible, usage, internalError }

indirect enum JSON: Equatable {
    case object([String: JSON]), array([JSON]), string(String), integer(Int64), bool(Bool), null
    var object: [String: JSON]? { if case .object(let v) = self { return v }; return nil }
    var array: [JSON]? { if case .array(let v) = self { return v }; return nil }
    var string: String? { if case .string(let v) = self { return v }; return nil }
    var integer: Int64? { if case .integer(let v) = self { return v }; return nil }
}

// Parse raw UTF-8 before any Foundation object decoder can discard duplicate
// keys or conflate Boolean and numeric NSNumber values.
struct StrictJSON {
    let bytes: [UInt8]
    var index = 0
    var nodes = 0

    init(_ data: Data) throws {
        guard data.count <= 262_144, String(data: data, encoding: .utf8) != nil,
              !data.starts(with: [0xef, 0xbb, 0xbf]) else { throw Failure.invalid }
        bytes = Array(data)
    }
    mutating func parse() throws -> JSON {
        let value = try value(0)
        white()
        guard index == bytes.count else { throw Failure.invalid }
        return value
    }
    mutating func white() {
        while index < bytes.count && [UInt8(32), 9, 10, 13].contains(bytes[index]) { index += 1 }
    }
    mutating func take(_ byte: UInt8) -> Bool {
        white()
        if index < bytes.count && bytes[index] == byte { index += 1; return true }
        return false
    }
    mutating func value(_ depth: Int) throws -> JSON {
        nodes += 1
        guard depth <= 32, nodes <= 8192 else { throw Failure.invalid }
        white()
        guard index < bytes.count else { throw Failure.invalid }
        switch bytes[index] {
        case 123:
            guard depth < 32 else { throw Failure.invalid }
            index += 1
            var result: [String: JSON] = [:]
            if take(125) { return .object(result) }
            repeat {
                white()
                let key = try string()
                nodes += 1
                guard nodes <= 8192, key.unicodeScalars.count <= 96 else { throw Failure.invalid }
                guard result[key] == nil, take(58) else { throw Failure.invalid }
                result[key] = try value(depth + 1)
                if take(125) { return .object(result) }
                guard take(44) else { throw Failure.invalid }
            } while true
        case 91:
            guard depth < 32 else { throw Failure.invalid }
            index += 1
            var result: [JSON] = []
            if take(93) { return .array(result) }
            repeat {
                result.append(try value(depth + 1))
                if take(93) { return .array(result) }
                guard take(44) else { throw Failure.invalid }
            } while true
        case 34: return .string(try string())
        case 116: try literal("true"); return .bool(true)
        case 102: try literal("false"); return .bool(false)
        case 110: try literal("null"); return .null
        case 45, 48...57:
            let start = index
            if bytes[index] == 45 { index += 1 }
            guard index < bytes.count else { throw Failure.invalid }
            if bytes[index] == 48 { index += 1 }
            else {
                guard (49...57).contains(bytes[index]) else { throw Failure.invalid }
                while index < bytes.count && (48...57).contains(bytes[index]) { index += 1 }
            }
            guard index - start <= 17,
                  let number = Int64(String(decoding: bytes[start..<index], as: UTF8.self)),
                  number >= -9_007_199_254_740_991, number <= 9_007_199_254_740_991 else { throw Failure.invalid }
            return .integer(number)
        default: throw Failure.invalid
        }
    }
    mutating func literal(_ s: String) throws {
        let expected = Array(s.utf8)
        guard index + expected.count <= bytes.count,
              Array(bytes[index..<(index + expected.count)]) == expected else { throw Failure.invalid }
        index += expected.count
    }
    mutating func hex4() throws -> UInt32 {
        guard index + 4 <= bytes.count else { throw Failure.invalid }
        var value: UInt32 = 0
        for _ in 0..<4 {
            let b = bytes[index]; index += 1
            let n: UInt32
            switch b {
            case 48...57: n = UInt32(b - 48)
            case 65...70: n = UInt32(b - 55)
            case 97...102: n = UInt32(b - 87)
            default: throw Failure.invalid
            }
            value = value * 16 + n
        }
        return value
    }
    mutating func string() throws -> String {
        guard index < bytes.count, bytes[index] == 34 else { throw Failure.invalid }
        index += 1
        var output: [UInt8] = []
        while index < bytes.count {
            guard output.count <= 8192 else { throw Failure.invalid }
            let b = bytes[index]; index += 1
            if b == 34 {
                guard let result = String(bytes: output, encoding: .utf8),
                      result.unicodeScalars.count <= 2048,
                      !result.unicodeScalars.contains(where: { $0.value < 32 }) else { throw Failure.invalid }
                return result
            }
            guard b >= 32 else { throw Failure.invalid }
            if b != 92 { output.append(b); continue }
            guard index < bytes.count else { throw Failure.invalid }
            let escaped = bytes[index]; index += 1
            switch escaped {
            case 34, 92, 47: output.append(escaped)
            case 98: output.append(8)
            case 102: output.append(12)
            case 110: output.append(10)
            case 114: output.append(13)
            case 116: output.append(9)
            case 117:
                var scalar = try hex4()
                if (0xd800...0xdbff).contains(scalar) {
                    guard index + 2 <= bytes.count, bytes[index] == 92, bytes[index + 1] == 117 else { throw Failure.invalid }
                    index += 2
                    let low = try hex4()
                    guard (0xdc00...0xdfff).contains(low) else { throw Failure.invalid }
                    scalar = 0x10000 + (scalar - 0xd800) * 0x400 + low - 0xdc00
                }
                guard !(0xdc00...0xdfff).contains(scalar), let code = UnicodeScalar(scalar) else { throw Failure.invalid }
                output.append(contentsOf: String(code).utf8)
            default: throw Failure.invalid
            }
        }
        throw Failure.invalid
    }
}

func object(_ value: JSON?, _ keys: String) throws -> [String: JSON] {
    guard let result = value?.object, Set(result.keys) == Set(keys.split(separator: " ").map(String.init)) else { throw Failure.invalid }
    return result
}
func string(_ value: JSON?, max: Int = 4096) throws -> String {
    guard let result = value?.string, !result.isEmpty, result.utf8.count <= max,
          !result.unicodeScalars.contains(where: { $0.value < 32 || $0.value == 127 }) else { throw Failure.invalid }
    return result
}
func array(_ value: JSON?, max: Int = 64) throws -> [JSON] {
    guard let result = value?.array, result.count <= max else { throw Failure.invalid }; return result
}
func require(_ condition: Bool) throws { if !condition { throw Failure.invalid } }
func equal(_ value: JSON?, _ expected: String) throws { try require(value == .string(expected)) }
func strings(_ value: JSON?, max: Int = 64) throws -> [String] {
    let result = try array(value, max: max).map { try string($0) }
    try require(Set(result).count == result.count)
    return result
}
func known(_ value: JSON?, _ extra: String) throws -> [String: JSON] {
    let result = try object(value, "status reason " + extra)
    try equal(result["status"], "known")
    _ = try string(result["reason"])
    return result
}
