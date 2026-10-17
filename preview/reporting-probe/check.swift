// SPDX-FileCopyrightText: 2026 Pear contributors
// SPDX-License-Identifier: GPL-3.0-or-later
import Foundation
import Security
final class NoRedirect: NSObject, URLSessionTaskDelegate, @unchecked Sendable {
    func urlSession(_ session: URLSession, task: URLSessionTask,
                    willPerformHTTPRedirection response: HTTPURLResponse,
                    newRequest request: URLRequest) async -> URLRequest? { nil }
}
@main struct CapabilityProbe {
    static func main() async throws {
        let session = URLSession(configuration: .ephemeral, delegate: NoRedirect(), delegateQueue: nil)
        defer { session.invalidateAndCancel() }
        var random = [UInt8](repeating: 0, count: 32)
        guard SecRandomCopyBytes(kSecRandomDefault, random.count, &random) == errSecSuccess else { fatalError("random source failed") }
        let token = random.map { String(format: "%02x", $0) }.joined()
        let id = UUID().uuidString
        let url = URL(string: "https://pear-reporting-validation.meleeisdeveloping.chatgpt.site/api/probe?id=\(id)")!
        if CommandLine.arguments.contains("--rate-limit") {
            var counts: [Int:Int] = [:]
            for _ in 0..<13 {
                let statuses = try await withThrowingTaskGroup(of: Int.self) { group in
                    for _ in 0..<10 { group.addTask {
                        var request = URLRequest(url:url); request.timeoutInterval = 15
                        let (_, response) = try await session.data(for:request)
                        return (response as? HTTPURLResponse)?.statusCode ?? 0
                    } }
                    var results: [Int] = []; for try await value in group { results.append(value) }; return results
                }
                for status in statuses { counts[status,default:0] += 1 }
                if counts[429] != nil { break }
            }
            print("Rate check: \(counts)")
            guard counts[429] != nil else { throw NSError(domain:"Rate limit not observed",code:1) }
            return
        }
        func payload(_ revision: Int, _ value: Int) throws -> Data {
            try JSONSerialization.data(withJSONObject: ["fixture":"pear-synthetic", "requestID":UUID().uuidString, "revision":revision, "value":value],options:.sortedKeys)
        }
        func check(_ name: String, _ method: String, _ body: Data? = nil,
                   _ capability: String? = nil, _ expected: Int) async throws {
            var request = URLRequest(url: url)
            request.httpMethod = method; request.timeoutInterval = 15
            request.httpBody = body
            if body != nil { request.setValue("application/json", forHTTPHeaderField: "Content-Type") }
            if let capability { request.setValue("Bearer \(capability)", forHTTPHeaderField: "Authorization") }
            let (_, response) = try await session.data(for: request)
            let status = (response as? HTTPURLResponse)?.statusCode ?? 0
            print("\(name): HTTP \(status)")
            guard status == expected else { throw NSError(domain:"Unexpected response",code:status) }
        }
        let first = try payload(1,1), second = try payload(2,2)
        try await check("missing capability", "GET", nil, nil, 401)
        try await check("create without ChatGPT login", "PUT", first, token, 200)
        try await check("identical retry", "PUT", first, token, 200)
        try await check("wrong owner read", "GET", nil, String(repeating:"0",count:64), 404)
        try await check("wrong owner write", "PUT", second, String(repeating:"0",count:64), 404)
        try await check("wrong owner delete", "DELETE", nil, String(repeating:"0",count:64), 404)
        try await check("update same report", "PUT", second, token, 200)
        try await check("stale revision", "PUT", first, token, 409)
        try await check("unknown fields", "PUT", Data("{\"note\":\"not accepted\"}".utf8), token, 400)
        try await check("oversize body", "PUT", Data(repeating:120,count:513), token, 413)
        try await check("owner read", "GET", nil, token, 200)
        try await check("owner delete", "DELETE", nil, token, 200)
        try await check("idempotent delete", "DELETE", nil, token, 200)
        try await check("read deleted", "GET", nil, token, 404)
        try await check("no resurrection on retry", "PUT", second, token, 410)
        print("PASS: public native transport with independent per-report capability; no Site service token")
    }
}
