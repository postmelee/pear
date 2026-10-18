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
        let manifests = root.appendingPathComponent("private/prefix/drive_c/Program Files (x86)/Steam/steamapps")
        try FileManager.default.createDirectory(at: manifests, withIntermediateDirectories: true)
        let manifest = manifests.appendingPathComponent("appmanifest_3405340.acf")
        try "\"appid\" \"3405340\"\n\"name\" \"Fixture Game\"\n\"buildid\" \"12345\"\n".write(to:manifest,atomically:true,encoding:.utf8)
        let identity = installedGameIdentity(root:root,appID:3405340)
        precondition(identity.name == "Fixture Game" && identity.build == "12345")
        try "\"appid\" \"1\"\n".write(to:manifest,atomically:true,encoding:.utf8)
        precondition(installedGameIdentity(root:root,appID:3405340).name == nil)
        let folder = manifests.appendingPathComponent("common/Fixture Game")
        try FileManager.default.createDirectory(at:folder,withIntermediateDirectories:true)
        for name in ["Game.exe", "UnityCrashHandler64.exe"] { try Data().write(to:folder.appendingPathComponent(name)) }
        try "\"appid\" \"3405340\"\n\"installdir\" \"Fixture Game\"\n".write(to:manifest,atomically:true,encoding:.utf8)
        let installations = installedGames(root:root)
        precondition(installations.count == 1)
        let gamePrefix = root.appendingPathComponent("private/prefix").path
        let image = "C:\\Program Files (x86)\\Steam\\steamapps\\common\\Fixture Game\\Game.exe"
        let environment = ["WINEPREFIX=" + gamePrefix]
        func identify(_ argv: [String], _ env: [String]) -> UInt32? {
            ownedGameID(args(argv,env),executable:executable,prefix:gamePrefix,installations:installations).appID
        }
        precondition(identify([image],environment) == 3405340)
        precondition(identify(["helper.exe",image],environment) == nil)
        precondition(identify([image.replacingOccurrences(of:"Game.exe",with:"UnityCrashHandler64.exe")],environment) == nil)
        precondition(identify([image],environment+["SteamAppId=2"]) == nil)
        precondition(identify([image],["WINEPREFIX=/other"]) == nil)
        precondition(installedAppID(image:"Game.exe",prefix:gamePrefix,installations:installations) == nil)
        precondition(installedAppID(image:image,prefix:gamePrefix,installations:installations + [.init(appID:2,directory:installations[0].directory)]) == nil)
        let outside = root.appendingPathComponent("outside.exe");try Data().write(to:outside)
        try FileManager.default.createSymbolicLink(at:folder.appendingPathComponent("Escape.exe"),withDestinationURL:outside)
        precondition(identify([image.replacingOccurrences(of:"Game.exe",with:"Escape.exe")],environment) == nil)
        let owner=try ReportingSessionOwner(directory:root)
        withExtendedLifetime(owner) {
            do { _=try ReportingSessionOwner(directory:root);preconditionFailure("second owner") } catch {}
        }
        let fresh = root.appendingPathComponent("fresh/history")
        var freshOwner:ReportingSessionOwner? = try ReportingSessionOwner(directory:fresh)
        withExtendedLifetime(freshOwner) {
            do { _=try ReportingSessionOwner(directory:fresh);preconditionFailure("fresh second owner") } catch {}
        }
        freshOwner=nil
        let reopened=try ReportingSessionOwner(directory:fresh)
        withExtendedLifetime(reopened) {}
        let alias=root.appendingPathComponent("history-alias")
        try FileManager.default.createSymbolicLink(at:alias,withDestinationURL:fresh)
        do { _=try ReportingSessionOwner(directory:alias);preconditionFailure("symlink owner") } catch {}
        print("PASS: exact runtime/prefix, allowlisted game identity, helper exclusion, PID reuse, missed samples, sleep gap, single observer ownership")
    }
}
