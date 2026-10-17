// SPDX-FileCopyrightText: 2026 Pear contributors
// SPDX-License-Identifier: GPL-3.0-or-later
import Foundation
@main struct ObserverTests {
    static func main() throws {
        let executable="/fixture/wine",prefix="/fixture/private/prefix"
        func args(_ argv:[String],_ env:[String]) -> Data {
            var count=Int32(argv.count);var data=withUnsafeBytes(of:&count) { Data($0) }
            data.append(Data((executable+"\0\0"+argv.joined(separator:"\0")+"\0"+env.joined(separator:"\0")+"\0\0").utf8));return data
        }
        let valid=args(["wine","game.exe"],["WINEPREFIX="+prefix,"SteamAppId=3405340","SECRET=must not escape"])
        precondition(ownedGameID(valid,executable:executable,prefix:prefix).appID==3405340)
        precondition(!ownedGameID(valid,executable:executable,prefix:prefix+"other").owned)
        precondition(!ownedGameID(valid,executable:"/other/wine",prefix:prefix).owned)
        precondition(ownedGameID(args(["steamwebhelper.exe"],["WINEPREFIX="+prefix,"SteamAppId=3405340"]),executable:executable,prefix:prefix).appID==nil)
        precondition(!ownedGameID(args(["game.exe"],["WINEPREFIX="+prefix,"WINEPREFIX=/other"]),executable:executable,prefix:prefix).owned)
        precondition(ownedGameID(args(["game.exe"],["WINEPREFIX="+prefix,"SteamAppId=1","SteamAppId=2"]),executable:executable,prefix:prefix).appID==nil)
        var state=RunObserverState();let now=Date()
        let game=OwnedProcess(pid:100,startSeconds:10,startMicroseconds:0,appID:3405340)
        let steam=OwnedProcess(pid:101,startSeconds:9,startMicroseconds:0,appID:nil)
        let initial=state.consume(.init(processes:[game,steam],complete:true),now:now,monotonic:0)
        precondition(initial.0.count==1 && initial.1.isEmpty)
        precondition(state.consume(.init(processes:[game,steam],complete:true),now:now,monotonic:2).0.isEmpty)
        let end=state.consume(.init(processes:[steam],complete:true),now:now.addingTimeInterval(4),monotonic:4)
        precondition(end.1.count==1 && end.1[0].exit == .exited)
        _=state.consume(.init(processes:[game],complete:true),now:now,monotonic:6)
        let reused=OwnedProcess(pid:100,startSeconds:20,startMicroseconds:0,appID:3405340)
        let reuse=state.consume(.init(processes:[reused],complete:true),now:now,monotonic:8)
        precondition(reuse.0.count==1 && reuse.1.count==1 && reuse.0[0].id != reuse.1[0].session.id)
        _=state.consume(.init(processes:[],complete:false),now:now,monotonic:10)
        let uncertain=state.consume(.init(processes:[],complete:true),now:now,monotonic:12)
        precondition(uncertain.1[0].exit == .unknown && uncertain.1[0].observedEnd==nil)
        _=state.consume(.init(processes:[game],complete:true),now:now,monotonic:14)
        let sleep=state.consume(.init(processes:[],complete:true),now:now,monotonic:100)
        precondition(sleep.1[0].observedEnd==nil)
        let root=FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
        try FileManager.default.createDirectory(at:root,withIntermediateDirectories:true)
        defer { try? FileManager.default.removeItem(at:root) }
        let owner=try ReportingSessionOwner(directory:root)
        withExtendedLifetime(owner) {
            do { _=try ReportingSessionOwner(directory:root);preconditionFailure("second owner") } catch {}
        }
        print("PASS: exact runtime/prefix, allowlisted game identity, helper exclusion, PID reuse, missed samples, sleep gap, single observer ownership")
    }
}
