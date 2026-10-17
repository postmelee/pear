// SPDX-FileCopyrightText: 2026 Pear contributors
// SPDX-License-Identifier: GPL-3.0-or-later
// Separate local-only rehearsal executable; never included in the shipped launcher.
import AppKit

@MainActor final class LocalTransfer: ReportTransfer {
    var task: URLSessionDataTask?
    func cancel() { task?.cancel() }
}
final class NoRedirect: NSObject, URLSessionTaskDelegate, @unchecked Sendable {
    func urlSession(_ session: URLSession, task: URLSessionTask, willPerformHTTPRedirection response: HTTPURLResponse, newRequest request: URLRequest, completionHandler: @escaping (URLRequest?) -> Void) { completionHandler(nil) }
}
@MainActor final class LocalTransport: ReportTransport {
    let keys: any ReportCapabilityStore
    init(keys: (any ReportCapabilityStore)? = nil) { self.keys = keys ?? KeychainReportCapabilities() }
    let session: URLSession = {
        let c=URLSessionConfiguration.ephemeral;c.timeoutIntervalForRequest=10;c.timeoutIntervalForResource=15
        c.httpCookieStorage=nil;c.urlCache=nil;c.urlCredentialStorage=nil
        return URLSession(configuration:c,delegate:NoRedirect(),delegateQueue:nil)
    }()
    func start(_ request: PendingReport, completion: @escaping @MainActor (Bool)->Void) -> ReportTransfer {
        let transfer=LocalTransfer()
        do {
            let endpoint="http://127.0.0.1:8964/reports"
            let key=try keys.capability(reportID:request.payload.reportID,service:"local-rehearsal-8964")
            var req=URLRequest(url:URL(string:endpoint+"/"+request.payload.reportID.uuidString.lowercased())!)
            req.httpMethod="PUT";req.setValue("Bearer "+key,forHTTPHeaderField:"Authorization");req.setValue("application/json",forHTTPHeaderField:"Content-Type")
            req.httpBody=try JSONEncoder().encode(ReportEnvelope(schemaVersion:1,requestID:request.requestID,revision:request.revision,report:request.payload))
            transfer.task=session.dataTask(with:req) { data,response,error in
                let receipt=data.flatMap { try? JSONDecoder().decode(ReportReceipt.self,from:$0) }
                let ok=error == nil && (response as? HTTPURLResponse)?.statusCode == 200 && receipt?.reportID == request.payload.reportID && receipt?.requestID == request.requestID && receipt?.revision == request.revision
                Task { @MainActor in completion(ok) }
            };transfer.task?.resume()
        } catch { Task { @MainActor in completion(false) } }
        return transfer
    }
}
@MainActor final class SmokeCapability: ReportCapabilityStore {
    let value=UUID().uuidString.replacingOccurrences(of:"-",with:"").lowercased()+UUID().uuidString.replacingOccurrences(of:"-",with:"").lowercased()
    func capability(reportID:UUID,service:String)throws->String { value }
}
@MainActor final class Review: NSObject, NSApplicationDelegate {
    var history: HistoryWindow?
    var coordinator: ReportingCoordinator?
    var timer: Timer?
    func applicationDidFinishLaunching(_ notification: Notification) {
        do {
            let root=URL(fileURLWithPath:CommandLine.arguments[1]).resolvingSymlinksInPath()
            let store=try ReportingStore(directory:root)
            if CommandLine.arguments.contains("--smoke") {
                let c=ReportingCoordinator(store:store,transport:LocalTransport(keys:SmokeCapability()));coordinator=c
                let run=RunObservation(id:UUID(),startedAt:Date(),pear:"Local native transport test",wine:"11.0",dxmt:"0.80",appID:3405340,note:"PRIVATE NATIVE TEST")
                try c.configure(mode:.localOnly,fields:[.game,.components])
                c.changed={
                    if store.snapshot.shared[run.id] != nil { print("PASS: native URLSession local receiver, exact receipt, durable shared state");NSApp.terminate(nil) }
                }
                try c.enqueue(run,origin:.manual,shareNote:true)
                DispatchQueue.main.asyncAfter(deadline:.now()+20) { print("FAIL: native local transport timeout");exit(1) }
                return
            }
            if store.snapshot.runs.isEmpty {
                let now=Date();let os=ProcessInfo.processInfo.operatingSystemVersion
                try store.record(RunObservation(id:UUID(),startedAt:now.addingTimeInterval(-120),endedAt:now,
                    macOS:"\(os.majorVersion).\(os.minorVersion).\(os.patchVersion)",chip:"Apple Silicon",memoryGiB:Int(ProcessInfo.processInfo.physicalMemory/(1024*1024*1024)),pear:"Reporting review (local only)",wine:"11.0",dxmt:"0.80",appID:3405340,gameName:"Megabonk · rehearsal",observedExit:.unknown,note:"Local rehearsal record. No game was run for this record."))
            }
            let c=ReportingCoordinator(store:store,transport:LocalTransport());coordinator=c
            let h=HistoryWindow(store:store);history=h
            h.submit={ run,note in try c.enqueue(run,origin:.manual,shareNote:note) }
            h.configureSharing={ mode,fields in try c.configure(mode:mode,fields:fields) }
            h.retryReport={ id in try c.retry(reportID:id) }
            h.deleteLocalRecord={ id in try c.deleteLocal(reportID:id) }
            c.changed={ [weak h] in h?.refresh() }
            h.show();h.showSharingIntroductionIfNeeded()
            timer=Timer.scheduledTimer(withTimeInterval:2,repeats:true) { _ in Task { @MainActor in c.sendNext() } }
        } catch {
            let alert=NSAlert();alert.messageText="Local review could not start";alert.informativeText=error.localizedDescription;alert.runModal();NSApp.terminate(nil)
        }
    }
    func applicationShouldTerminateAfterLastWindowClosed(_ sender:NSApplication)->Bool { true }
}
@main struct Main {
    static func main() { let app=NSApplication.shared;let delegate=Review();app.delegate=delegate;app.setActivationPolicy(.regular);app.run() }
}
