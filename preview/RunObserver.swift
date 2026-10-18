// SPDX-FileCopyrightText: 2026 Pear contributors
// SPDX-License-Identifier: GPL-3.0-or-later
import Foundation
import Darwin

struct OwnedProcess: Hashable {
    let pid: Int32
    let startSeconds: UInt64
    let startMicroseconds: UInt64
    let appID: UInt32?
}
struct OwnedProcessSnapshot { var processes: Set<OwnedProcess>; var complete: Bool }

// Kernel paths may use /private/var while launch arguments use /var.
// Resolve both sides identically without relaxing runtime or prefix ownership.
func processIdentityPath(_ path: String) -> String? {
    guard path.hasPrefix("/") else { return nil }
    if let resolved = realpath(path, nil) {
        defer { free(resolved) }
        return String(cString: resolved)
    }
    return URL(fileURLWithPath: path).standardizedFileURL.path
}

// Decode only allowlisted identity fields; never persist argv or environment.
func ownedGameID(_ data: Data, executable: String, prefix: String) -> (owned: Bool, appID: UInt32?) {
    let bytes=[UInt8](data); guard bytes.count >= 4 else { return (false,nil) }
    let argc=bytes.withUnsafeBytes { $0.loadUnaligned(as:Int32.self) }
    guard argc > 0 && argc <= 4096 else { return (false,nil) }
    var at=4
    func take() -> String? {
        guard at < bytes.count,let end=bytes[at...].firstIndex(of:0) else { return nil }
        defer { at=end+1 }; return String(bytes:bytes[at..<end],encoding:.utf8)
    }
    guard let argumentPath = take(), processIdentityPath(argumentPath)==processIdentityPath(executable) else { return (false,nil) }
    while at < bytes.count && bytes[at]==0 { at+=1 }
    var steam=false
    for _ in 0..<argc {
        guard let arg=take() else { return (false,nil) }
        let base=arg.replacingOccurrences(of:"\\",with:"/").split(separator:"/").last?.lowercased()
        if ["steam.exe","steamwebhelper.exe","steamservice.exe"].contains(base) { steam=true }
    }
    while at < bytes.count && bytes[at]==0 { at+=1 }
    var prefixes:[String]=[], ids:[String]=[]
    while at < bytes.count {
        guard let entry=take() else { return (false,nil) }
        if entry.isEmpty { break }
        if entry.hasPrefix("WINEPREFIX=") { prefixes.append(String(entry.dropFirst(11))) }
        if entry.hasPrefix("SteamAppId=") { ids.append(String(entry.dropFirst(11))) }
    }
    guard prefixes.count == 1, let actualPrefix = processIdentityPath(prefixes[0]), actualPrefix == processIdentityPath(prefix) else { return (false,nil) }
    let id = ids.count == 1 ? UInt32(ids[0]) : nil
    return (true, !steam && id != 0 ? id : nil)
}

struct OwnedProcessProbe {
    let root: URL
    let runtime: String
    func snapshot(previous: Set<OwnedProcess>) -> OwnedProcessSnapshot {
        let base=root.appendingPathComponent("runtimes/\(runtime)/Libraries/Wine/lib/wine/x86_64-unix")
        let executables=Set([base.appendingPathComponent("wine").path,base.appendingPathComponent("wine64").path].compactMap(processIdentityPath))
        let prefix=root.appendingPathComponent("private/prefix").path
        let count=proc_listallpids(nil,0)
        guard count > 0 else { return .init(processes:[],complete:false) }
        var pids=[pid_t](repeating:0,count:Int(count)+128)
        let actual=proc_listallpids(&pids,Int32(pids.count*MemoryLayout<pid_t>.size))
        guard actual > 0 && actual < pids.count else { return .init(processes:[],complete:false) }
        var found=Set<OwnedProcess>(),complete=true
        for pid in pids.prefix(Int(actual)) where pid > 0 {
            var path=[CChar](repeating:0,count:4*Int(MAXPATHLEN))
            guard proc_pidpath(pid,&path,UInt32(path.count)) > 0 else {
                if previous.contains(where:{$0.pid==pid}) { complete=false };continue
            }
            let executable=String(cString:path)
            guard let canonicalExecutable = processIdentityPath(executable), executables.contains(canonicalExecutable) else { continue }
            var before=proc_bsdinfo(),after=proc_bsdinfo()
            let size=Int32(MemoryLayout<proc_bsdinfo>.size)
            guard proc_pidinfo(pid,PROC_PIDTBSDINFO,0,&before,size)==size else { complete=false;continue }
            var query:[Int32]=[CTL_KERN,KERN_PROCARGS2,pid],bytes=[UInt8](repeating:0,count:262_144)
            var length=bytes.count
            let status=bytes.withUnsafeMutableBytes { sysctl(&query,u_int(query.count),$0.baseAddress,&length,nil,0) }
            guard status==0,length<=bytes.count else { complete=false;continue }
            let identity=ownedGameID(Data(bytes.prefix(length)),executable:executable,prefix:prefix)
            guard identity.owned else { continue }
            guard proc_pidinfo(pid,PROC_PIDTBSDINFO,0,&after,size)==size,
                  before.pbi_start_tvsec==after.pbi_start_tvsec,before.pbi_start_tvusec==after.pbi_start_tvusec,
                  proc_pidpath(pid,&path,UInt32(path.count)) > 0,String(cString:path)==executable else { complete=false;continue }
            found.insert(.init(pid:pid,startSeconds:before.pbi_start_tvsec,startMicroseconds:before.pbi_start_tvusec,appID:identity.appID))
        }
        return .init(processes:found,complete:complete)
    }
}

struct ObservedSession {
    var id: UUID
    var appID: UInt32
    var began: Date
    var identities: Set<OwnedProcess>
    var continuous: Bool
}
struct FinishedSession { var session: ObservedSession; var observedEnd: Date?; var exit: ObservedExit }
struct RunObserverState {
    private(set) var sessions: [UInt32:ObservedSession] = [:]
    private(set) var previous=Set<OwnedProcess>()
    private var lastMonotonic: TimeInterval?
    private var lastWall: Date?
    mutating func consume(_ snapshot: OwnedProcessSnapshot, now: Date, monotonic: TimeInterval) -> ([ObservedSession],[FinishedSession]) {
        let gap=(lastMonotonic.map { monotonic-$0 > 10 || monotonic < $0 } ?? false) ||
            (lastWall.map { now.timeIntervalSince($0) > 10 || now < $0 } ?? false)
        lastWall=now
        lastMonotonic=monotonic
        if !snapshot.complete || gap {
            for id in sessions.keys { sessions[id]?.continuous=false }
        }
        guard snapshot.complete else { return ([],[]) }
        let groups=Dictionary(grouping:snapshot.processes.filter{$0.appID != nil},by:{$0.appID!})
        var started:[ObservedSession]=[],finished:[FinishedSession]=[]
        for (id,session) in sessions {
            let current=Set(groups[id] ?? [])
            if current.isEmpty || current.isDisjoint(with:session.identities) {
                finished.append(.init(session:session,observedEnd:session.continuous ? now : nil,
                                      exit:session.continuous ? .exited : .unknown))
                sessions.removeValue(forKey:id)
            }
        }
        for (id,processes) in groups {
            if sessions[id] == nil {
                // Observation begins here; kernel timestamps identify processes,
                // but do not establish continuous observation before this sample.
                let session=ObservedSession(id:UUID(),appID:id,began:now,identities:Set(processes),continuous:true)
                sessions[id]=session;started.append(session)
            } else { sessions[id]?.identities=Set(processes) }
        }
        previous=snapshot.processes
        return (started,finished)
    }
}

// Lock lifetime belongs to the observer, not the visible window. No PID killing.
final class ReportingSessionOwner {
    private let descriptor: Int32
    init(directory: URL) throws {
        descriptor=open(directory.appendingPathComponent("observer.lock").path,O_CREAT|O_RDWR|O_NOFOLLOW,0o600)
        guard descriptor >= 0 else { throw CocoaError(.fileWriteUnknown) }
        guard flock(descriptor,LOCK_EX|LOCK_NB)==0 else { close(descriptor);throw CocoaError(.fileLocking) }
    }
    deinit { flock(descriptor,LOCK_UN);close(descriptor) }
}

// Read only the three public identity fields from an app's installation manifest.
// Never parse Steam account/configuration files or persist the manifest path.
func installedGameIdentity(root: URL, appID: UInt32) -> (name: String?, build: String?) {
    let canonical = root.standardizedFileURL.resolvingSymlinksInPath()
    let file = canonical.appendingPathComponent("private/prefix/drive_c/Program Files (x86)/Steam/steamapps/appmanifest_\(appID).acf").resolvingSymlinksInPath()
    guard file.path.hasPrefix(canonical.path + "/"),
          let size = try? file.resourceValues(forKeys: [.fileSizeKey]).fileSize, size <= 262144,
          let text = try? String(contentsOf: file, encoding: .utf8) else { return (nil,nil) }
    func value(_ key: String) -> String? {
        let pattern = "(?m)^\\s*\"" + key + "\"\\s+\"([^\"\\r\\n]{1,300})\"\\s*$"
        guard let regex = try? NSRegularExpression(pattern: pattern) else { return nil }
        let matches = regex.matches(in: text, range: NSRange(text.startIndex..., in: text))
        guard matches.count == 1, let range = Range(matches[0].range(at: 1), in: text) else { return nil }
        return String(text[range])
    }
    guard value("appid") == String(appID) else { return (nil,nil) }
    let build = value("buildid")
    return (value("name"), build.flatMap { UInt64($0) == nil ? nil : $0 })
}

func reportingChipName() -> String? {
    var size = 0
    guard sysctlbyname("machdep.cpu.brand_string",nil,&size,nil,0) == 0, size > 0, size <= 256 else { return nil }
    var bytes = [CChar](repeating:0,count:size)
    guard sysctlbyname("machdep.cpu.brand_string",&bytes,&size,nil,0) == 0 else { return nil }
    return String(cString:bytes)
}
