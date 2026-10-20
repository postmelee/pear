// SPDX-FileCopyrightText: 2026 Pear contributors
// SPDX-License-Identifier: GPL-3.0-or-later
import Foundation
import Security

@MainActor protocol ReportCapabilityStore {
    func capability(reportID: UUID, service: String) throws -> String
}

enum ReportNetworkError: Error { case endpoint, keychain(OSStatus) }

// Each report owns an independent capability. No common secret ships in the app.
@MainActor final class KeychainReportCapabilities: ReportCapabilityStore {
    func capability(reportID: UUID, service: String) throws -> String {
        let query: [String: Any] = [kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: "org.pear.reports." + service,
            kSecAttrAccount as String: reportID.uuidString.lowercased(),
            kSecAttrSynchronizable as String: false]
        var lookup = query
        lookup[kSecReturnData as String] = true
        lookup[kSecMatchLimit as String] = kSecMatchLimitOne
        var result: CFTypeRef?
        let status = SecItemCopyMatching(lookup as CFDictionary, &result)
        if status == errSecSuccess, let bytes = result as? Data, bytes.count == 32 {
            return bytes.map { String(format: "%02x", $0) }.joined()
        }
        guard status == errSecItemNotFound else { throw ReportNetworkError.keychain(status) }
        var bytes = [UInt8](repeating: 0, count: 32)
        let randomStatus = SecRandomCopyBytes(kSecRandomDefault, bytes.count, &bytes)
        guard randomStatus == errSecSuccess else { throw ReportNetworkError.keychain(randomStatus) }
        var insert = query
        insert[kSecValueData as String] = Data(bytes)
        insert[kSecAttrAccessible as String] = kSecAttrAccessibleAfterFirstUnlockThisDeviceOnly
        let added = SecItemAdd(insert as CFDictionary, nil)
        guard added == errSecSuccess else { throw ReportNetworkError.keychain(added) }
        return bytes.map { String(format: "%02x", $0) }.joined()
    }
}

struct ReportEnvelope: Codable {
    let schemaVersion: Int
    let requestID: UUID
    let revision: UInt64
    let report: SharedRun
}
private struct DeleteReceipt: Decodable { let deleted: Bool }
struct ReportReceipt: Codable {
    let reportID: UUID
    let requestID: UUID
    let revision: UInt64
}

// URLSession owns this delegate until completion. All delegate state is confined
// to one serial operation queue; UI/store mutation is delivered on MainActor.
private final class ReportExchange: NSObject, URLSessionDataDelegate, @unchecked Sendable {
    private var bytes = Data()
    private var accepted = false
    private let expected: PendingReport?
    private let completion: @MainActor (Bool) -> Void
    init(expected: PendingReport?, completion: @escaping @MainActor (Bool) -> Void) {
        self.expected = expected; self.completion = completion
    }
    func urlSession(_ session: URLSession, task: URLSessionTask,
                    willPerformHTTPRedirection response: HTTPURLResponse, newRequest request: URLRequest,
                    completionHandler: @escaping (URLRequest?) -> Void) {
        // Capabilities must never follow redirects, including to another origin.
        completionHandler(nil)
    }
    func urlSession(_ session: URLSession, dataTask: URLSessionDataTask, didReceive response: URLResponse,
                    completionHandler: @escaping (URLSession.ResponseDisposition) -> Void) {
        guard let http = response as? HTTPURLResponse, http.statusCode == 200,
              http.mimeType == "application/json", response.expectedContentLength <= 16384 else {
            completionHandler(.cancel); return
        }
        accepted = true; completionHandler(.allow)
    }
    func urlSession(_ session: URLSession, dataTask: URLSessionDataTask, didReceive data: Data) {
        guard bytes.count + data.count <= 16384 else { accepted = false; dataTask.cancel(); return }
        bytes.append(data)
    }
    func urlSession(_ session: URLSession, task: URLSessionTask, didCompleteWithError error: Error?) {
        let receipt = try? JSONDecoder().decode(ReportReceipt.self, from: bytes)
        let matches: Bool
        if let expected {
            matches = receipt?.reportID == expected.payload.reportID && receipt?.requestID == expected.requestID && receipt?.revision == expected.revision
        } else {
            matches = (try? JSONDecoder().decode(DeleteReceipt.self, from: bytes).deleted) == true
        }
        let success = accepted && error == nil && matches
        session.finishTasksAndInvalidate()
        Task { @MainActor in completion(success) }
    }
}

@MainActor private final class NetworkReportTransfer: ReportTransfer {
    var session: URLSession?
    func cancel() { session?.invalidateAndCancel(); session = nil }
}

@MainActor final class URLSessionReportTransport: ReportTransport {
    private let endpoint: URL
    private let capabilities: ReportCapabilityStore
    private let configuration: () -> URLSessionConfiguration
    init(endpoint: URL, capabilities: ReportCapabilityStore,
         configuration: @escaping () -> URLSessionConfiguration = { .ephemeral }) throws {
        guard endpoint.scheme == "https", endpoint.host != nil,
              endpoint.user == nil, endpoint.password == nil,
              endpoint.query == nil, endpoint.fragment == nil else { throw ReportNetworkError.endpoint }
        self.endpoint = endpoint; self.capabilities = capabilities; self.configuration = configuration
    }
    func delete(reportID: UUID, completion: @escaping @MainActor (Bool) -> Void) -> ReportTransfer {
        let transfer = NetworkReportTransfer()
        do {
            let cap = try capabilities.capability(reportID: reportID, service: endpoint.absoluteString)
            var request = URLRequest(url: endpoint.appendingPathComponent(reportID.uuidString.lowercased()))
            request.httpMethod = "DELETE"
            request.setValue("Bearer " + cap, forHTTPHeaderField: "Authorization")
            let config = configuration()
            config.httpCookieStorage = nil; config.httpShouldSetCookies = false
            config.urlCredentialStorage = nil; config.urlCache = nil
            config.timeoutIntervalForRequest = 15; config.timeoutIntervalForResource = 20
            config.waitsForConnectivity = false
            let delegate = ReportExchange(expected: nil, completion: completion)
            let queue = OperationQueue(); queue.maxConcurrentOperationCount = 1
            let session = URLSession(configuration: config, delegate: delegate, delegateQueue: queue)
            transfer.session = session; session.dataTask(with: request).resume()
        } catch { Task { @MainActor in completion(false) } }
        return transfer
    }

    func start(_ request: PendingReport, completion: @escaping @MainActor (Bool) -> Void) -> ReportTransfer {
        let transfer = NetworkReportTransfer()
        do {
            let body = try JSONEncoder().encode(ReportEnvelope(schemaVersion: 1,
                requestID: request.requestID, revision: request.revision, report: request.payload))
            guard body.count <= 16384 else { throw ReportNetworkError.endpoint }
            // The complete endpoint scopes ownership; a different service cannot
            // receive capabilities generated for an earlier collection service.
            let capability = try capabilities.capability(reportID: request.payload.reportID, service: endpoint.absoluteString)
            var urlRequest = URLRequest(url: endpoint.appendingPathComponent(request.payload.reportID.uuidString.lowercased()))
            urlRequest.httpMethod = "PUT"; urlRequest.httpBody = body
            urlRequest.setValue("application/json", forHTTPHeaderField: "Content-Type")
            urlRequest.setValue("Bearer " + capability, forHTTPHeaderField: "Authorization")
            let config = configuration()
            config.httpCookieStorage = nil; config.httpShouldSetCookies = false
            config.urlCredentialStorage = nil; config.urlCache = nil
            config.requestCachePolicy = .reloadIgnoringLocalCacheData
            config.timeoutIntervalForRequest = 15; config.timeoutIntervalForResource = 20
            config.waitsForConnectivity = false
            let delegate = ReportExchange(expected: request, completion: completion)
            let queue = OperationQueue(); queue.maxConcurrentOperationCount = 1
            let session = URLSession(configuration: config, delegate: delegate, delegateQueue: queue)
            transfer.session = session
            session.dataTask(with: urlRequest).resume()
        } catch { Task { @MainActor in completion(false) } }
        return transfer
    }
}
