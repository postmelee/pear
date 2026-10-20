// SPDX-FileCopyrightText: 2026 Pear contributors
// SPDX-License-Identifier: GPL-3.0-or-later
import Foundation

@MainActor final class TestCapabilities: ReportCapabilityStore {
    var services: [String] = []
    func capability(reportID: UUID, service: String) throws -> String {
        services.append(service); return String(repeating: "a", count: 64)
    }
}
final class ReportProtocol: URLProtocol, @unchecked Sendable {
    static let lock = NSLock()
    nonisolated(unsafe) static var status = 200
    nonisolated(unsafe) static var responseBody = Data()
    nonisolated(unsafe) static var captured: URLRequest?
    nonisolated(unsafe) static var hold = false
    nonisolated(unsafe) static var stopped = false
    static func prepare(status: Int = 200, body: Data, hold: Bool = false) {
        lock.lock(); defer { lock.unlock() }
        self.status = status; responseBody = body; captured = nil; self.hold = hold; stopped = false
    }
    override class func canInit(with request: URLRequest) -> Bool { true }
    override class func canonicalRequest(for request: URLRequest) -> URLRequest { request }
    override func startLoading() {
        Self.lock.lock()
        Self.captured = request
        let status = Self.status, body = Self.responseBody, hold = Self.hold
        Self.lock.unlock()
        if hold { return }
        let response = HTTPURLResponse(url: request.url!, statusCode: status, httpVersion: "HTTP/1.1", headerFields: ["Content-Type": "application/json"])!
        client?.urlProtocol(self, didReceive: response, cacheStoragePolicy: .notAllowed)
        client?.urlProtocol(self, didLoad: body)
        client?.urlProtocolDidFinishLoading(self)
    }
    override func stopLoading() { Self.lock.lock(); Self.stopped = true; Self.lock.unlock() }
    static func hasStopped() -> Bool { lock.lock(); defer { lock.unlock() }; return stopped }
}
@main struct TransportTests {
    @MainActor static func main() async throws {
        let capabilities = TestCapabilities()
        do {
            _ = try URLSessionReportTransport(endpoint: URL(string:"http://example.invalid/reports")!, capabilities: capabilities)
            preconditionFailure("HTTP must be rejected")
        } catch {}
        let transport = try URLSessionReportTransport(endpoint: URL(string:"https://example.invalid/reports")!, capabilities: capabilities) {
            let config = URLSessionConfiguration.ephemeral; config.protocolClasses = [ReportProtocol.self]; return config
        }
        let run = RunObservation(id: UUID(), startedAt: Date(), pear:"test",wine:"11",dxmt:"0.80",note:"must stay local")
        var policy = ReportingPolicy(); policy.configure(mode: .automatic, fields: [.game])
        policy.enqueue(run, origin: .automatic)
        let request = policy.pending[0]
        let valid = try JSONEncoder().encode(ReportReceipt(reportID: run.id, requestID: request.requestID, revision: request.revision))
        func send(_ body: Data, status: Int = 200) async -> Bool {
            ReportProtocol.prepare(status: status, body: body)
            return await withCheckedContinuation { continuation in
                _ = transport.start(request) { continuation.resume(returning: $0) }
            }
        }
        let success = await send(valid); precondition(success)
        precondition(capabilities.services == ["https://example.invalid/reports"])
        precondition(ReportProtocol.captured?.httpMethod == "PUT")
        precondition(ReportProtocol.captured?.value(forHTTPHeaderField:"Authorization") == "Bearer " + String(repeating:"a",count:64))
        ReportProtocol.prepare(body: Data("{\"deleted\":true}".utf8))
        let deleted: Bool = await withCheckedContinuation { continuation in
            _ = transport.delete(reportID: run.id) { continuation.resume(returning: $0) }
        }
        precondition(deleted && ReportProtocol.captured?.httpMethod == "DELETE")
        ReportProtocol.prepare(body: Data("{\"deleted\":false}".utf8))
        let deniedDelete: Bool = await withCheckedContinuation { continuation in
            _ = transport.delete(reportID: run.id) { continuation.resume(returning: $0) }
        }
        precondition(!deniedDelete)
        let wrong = try JSONEncoder().encode(ReportReceipt(reportID: UUID(), requestID: request.requestID, revision: request.revision))
        let wrongSuccess = await send(wrong); precondition(!wrongSuccess)
        let emptySuccess = await send(Data("{}".utf8)); precondition(!emptySuccess)
        let rateSuccess = await send(valid, status:429); precondition(!rateSuccess)
        let redirectSuccess = await send(valid, status:302); precondition(!redirectSuccess)
        let largeSuccess = await send(Data(repeating:65,count:16385)); precondition(!largeSuccess)
        ReportProtocol.prepare(body: valid, hold: true)
        var completed: Bool?
        let transfer = transport.start(request) { completed = $0 }
        try await Task.sleep(for: .milliseconds(100))
        transfer.cancel()
        for _ in 0..<50 where completed == nil { try await Task.sleep(for: .milliseconds(20)) }
        precondition(completed == false && ReportProtocol.hasStopped())
        print("PASS: native URLSession request, HTTPS-only admission, exact receipt identity, invalid/oversize/rate/redirect rejection, actual task cancellation; synthetic URLProtocol, no external request")
    }
}
