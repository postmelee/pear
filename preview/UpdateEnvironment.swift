// SPDX-FileCopyrightText: 2026 Pear contributors
// SPDX-License-Identifier: GPL-3.0-or-later
import Foundation
import Darwin
import Security
import LocalAuthentication
import CryptoKit

// No brew subprocess, shell evaluation or mutable marker inside the signed app.
enum UpdateOwnership {
    case direct, homebrew, uncertain
    static func inspect(app: URL, prefixes: [URL] = [URL(fileURLWithPath:"/opt/homebrew"), URL(fileURLWithPath:"/usr/local")]) -> UpdateOwnership {
        let original = app.standardizedFileURL
        let resolved = original.resolvingSymlinksInPath()
        for prefix in prefixes {
            let cask = prefix.appendingPathComponent("Caskroom/pear")
            if resolved.path.hasPrefix(cask.path + "/") { return .homebrew }
            // Cask apps can be moved into /Applications rather than symlinked.
            if FileManager.default.fileExists(atPath:cask.path) { return .homebrew }
        }
        if original != resolved || original.path.contains("/AppTranslocation/") || original.path.hasPrefix("/Volumes/") { return .uncertain }
        return .direct
    }
}

struct UpdateRestartReceipt: Codable {
    let from: String
    let to: String
    let expires: Date
    func accepts(build: String, now: Date) -> Bool {
        build == to && from != to && expires > now && expires.timeIntervalSince(now) <= 600
    }
}

// A one-use Keychain item, never an unauthenticated launch flag on disk. Access
// follows the app's code-signing identity. Consume only while holding the root's
// observer lock, so two app processes cannot both use it. Failure skips the
// convenience receipt, not signature validation or the live-session check.
protocol UpdateRestartHandling {
    func write(_ receipt:UpdateRestartReceipt) throws
    func clear()
}
struct UpdateRestartStore: UpdateRestartHandling {
    let service = "org.pear.rosetta-preview.update-restart"
    let account: String
    init(app:URL = Bundle.main.bundleURL, root:URL? = nil) {
        let stateRoot = root ?? URL(fileURLWithPath:ProcessInfo.processInfo.environment["PEAR_PREVIEW_ROOT"] ?? NSHomeDirectory()+"/Library/Application Support/Pear Preview")
        let scope=app.standardizedFileURL.resolvingSymlinksInPath().path + "\n" + stateRoot.standardizedFileURL.resolvingSymlinksInPath().path
        account=SHA256.hash(data:Data(scope.utf8)).map { String(format:"%02x",$0) }.joined()
    }
    private var query: [String:Any] {
        let context = LAContext(); context.interactionNotAllowed = true
        return [kSecClass as String:kSecClassGenericPassword,
         kSecAttrService as String:service, kSecAttrAccount as String:account,
         kSecUseAuthenticationContext as String:context]
    }
    func write(_ receipt: UpdateRestartReceipt) throws {
        clear()
        var item = query
        item[kSecValueData as String] = try JSONEncoder().encode(receipt)
        item[kSecAttrAccessible as String] = kSecAttrAccessibleAfterFirstUnlockThisDeviceOnly
        let status = SecItemAdd(item as CFDictionary,nil)
        guard status == errSecSuccess else { throw NSError(domain:NSOSStatusErrorDomain,code:Int(status)) }
    }
    func consume(build: String, now: Date = Date()) -> Bool {
        var request = query
        request[kSecReturnData as String] = true
        request[kSecMatchLimit as String] = kSecMatchLimitOne
        var result:CFTypeRef?
        guard SecItemCopyMatching(request as CFDictionary,&result) == errSecSuccess,
              let data = result as? Data else { return false }
        guard SecItemDelete(query as CFDictionary) == errSecSuccess else { return false }
        return (try? JSONDecoder().decode(UpdateRestartReceipt.self,from:data))?.accepts(build:build,now:now) == true
    }
    func clear() { SecItemDelete(query as CFDictionary) }
}

// Shares the CLI's setup/launch lock. Hold through app replacement; release
// before continuing to Steam. CLOEXEC prevents installer/helper inheritance.
final class UpdateInstallLease {
    private let descriptor: Int32
    init(root:URL) throws {
        let path=root.appendingPathComponent(".lock").path
        descriptor=open(path,O_CREAT|O_RDWR|O_NOFOLLOW|O_CLOEXEC,0o600)
        guard descriptor >= 0 else { throw NSError(domain:NSPOSIXErrorDomain,code:Int(errno)) }
        var status=stat()
        guard fstat(descriptor,&status)==0, status.st_mode & S_IFMT == S_IFREG,
              flock(descriptor,LOCK_EX|LOCK_NB)==0 else {
            close(descriptor);throw NSError(domain:"Pear.Update",code:2)
        }
    }
    deinit { flock(descriptor,LOCK_UN);close(descriptor) }
}
