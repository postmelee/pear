// SPDX-FileCopyrightText: 2026 Pear contributors
// SPDX-License-Identifier: GPL-3.0-or-later
import Foundation
@main struct UpdateEnvironmentTests {
    static func main() throws {
        let fm=FileManager.default
        let scratch=fm.temporaryDirectory.appendingPathComponent("pear-update-"+UUID().uuidString)
        try fm.createDirectory(at:scratch,withIntermediateDirectories:true)
        defer { try? fm.removeItem(at:scratch) }
        let prefix=scratch.appendingPathComponent("brew")
        let app=scratch.appendingPathComponent("Applications/Pear.app")
        try fm.createDirectory(at:app,withIntermediateDirectories:true)
        precondition(UpdateOwnership.inspect(app:app,prefixes:[prefix]) == .direct)
        let cask=prefix.appendingPathComponent("Caskroom/pear/0.1/Pear.app")
        try fm.createDirectory(at:cask,withIntermediateDirectories:true)
        precondition(UpdateOwnership.inspect(app:app,prefixes:[prefix]) == .homebrew)
        let linked=scratch.appendingPathComponent("Linked.app")
        try fm.createSymbolicLink(at:linked,withDestinationURL:cask)
        precondition(UpdateOwnership.inspect(app:linked,prefixes:[prefix]) == .homebrew)
        precondition(UpdateOwnership.inspect(app:linked,prefixes:[]) == .uncertain)
        let scope=UpdateRestartStore(app:app,root:scratch).account
        precondition(scope == UpdateRestartStore(app:app,root:scratch).account)
        precondition(scope != UpdateRestartStore(app:linked,root:scratch).account)
        precondition(scope != UpdateRestartStore(app:app,root:prefix).account)
        precondition(!scope.contains(scratch.path))
        let now=Date()
        let receipt=UpdateRestartReceipt(from:"6",to:"7",expires:now.addingTimeInterval(300))
        precondition(receipt.accepts(build:"7",now:now))
        precondition(!receipt.accepts(build:"6",now:now))
        precondition(!receipt.accepts(build:"8",now:now))
        precondition(!receipt.accepts(build:"7",now:now.addingTimeInterval(400)))
        precondition(!receipt.accepts(build:"7",now:now.addingTimeInterval(-601)))
        var lease:UpdateInstallLease? = try UpdateInstallLease(root:scratch)
        precondition(lease != nil)
        precondition((try? UpdateInstallLease(root:scratch)) == nil)
        // Exercise the same flock from another process, not just two Swift objects.
        let child=Process();child.executableURL=URL(fileURLWithPath:"/usr/bin/python3")
        child.arguments=["-c","import fcntl,sys; f=open(sys.argv[1],'r+'); fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)",scratch.appendingPathComponent(".lock").path]
        child.standardError=FileHandle.nullDevice
        try child.run();child.waitUntilExit();precondition(child.terminationStatus != 0)
        lease=nil
        let child2=Process();child2.executableURL=child.executableURL;child2.arguments=child.arguments
        try child2.run();child2.waitUntilExit();precondition(child2.terminationStatus == 0)
        try fm.removeItem(at:scratch.appendingPathComponent(".lock"))
        try fm.createSymbolicLink(at:scratch.appendingPathComponent(".lock"),withDestinationURL:app)
        precondition((try? UpdateInstallLease(root:scratch)) == nil)
        print("PASS: Homebrew ownership, symlink/unknown ownership, bounded target-specific restart receipt, cross-process launch/install lease")
    }
}
