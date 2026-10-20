// SPDX-FileCopyrightText: 2026 Pear contributors
// SPDX-License-Identifier: GPL-3.0-or-later
import AppKit
import Sparkle

@MainActor private final class FixtureEngine: AppUpdateChecking {
    var checks=0
    var fail=false
    func start() throws { if fail { throw NSError(domain:"fixture",code:1) } }
    func checkForUpdates() { checks += 1 }
}
private final class FixtureRestart: UpdateRestartHandling {
    var receipts:[UpdateRestartReceipt]=[]
    var failWrite=false
    func write(_ receipt:UpdateRestartReceipt) throws {
        if failWrite { throw NSError(domain:NSOSStatusErrorDomain,code:-25293) }
        receipts.append(receipt)
    }
    func clear() { receipts=[] }
}
@main struct SparkleAdapterTests {
    @MainActor static func main() throws {
        let root=FileManager.default.temporaryDirectory.appendingPathComponent("pear-sparkle-adapter-"+UUID().uuidString)
        let info=root.appendingPathComponent("Fixture.bundle/Contents/Info.plist")
        try FileManager.default.createDirectory(at:info.deletingLastPathComponent(),withIntermediateDirectories:true)
        defer { try? FileManager.default.removeItem(at:root) }
        try PropertyListSerialization.data(fromPropertyList:["CFBundleIdentifier":"org.pear.adapter-fixture","CFBundleVersion":"6",
            "SUFeedURL":"https://example.invalid/appcast.xml","SUPublicEDKey":Data(repeating:1,count:32).base64EncodedString()],format:.xml,options:0).write(to:info)
        let bundle=Bundle(url:info.deletingLastPathComponent().deletingLastPathComponent())!
        var count=0,offers=0,cancels=0,notes=0
        var state=UpdateLaunchPolicy.Session.idle
        var ownership=UpdateOwnership.direct
        var engine=FixtureEngine()
        var restart=FixtureRestart()
        var accept:((Bool)->Void)?
        func make()->PearUpdater {
            count=0;offers=0;cancels=0;notes=0;accept=nil;engine=FixtureEngine();restart=FixtureRestart()
            return PearUpdater(bundle:bundle,restart:restart,makeEngine:{ _,_,_ in engine },session:{ state },ownership:{ ownership },
                present:{ _,_,_ in },offer:{ _,reply in offers += 1;accept=reply },releaseNotes:{ _ in notes += 1 },proceed:{ count += 1 })
        }
        var driver=make();driver.begin();driver.begin();precondition(engine.checks==1)
        driver.showUpdateNotFoundWithError(NSError(domain:"fixture",code:0),acknowledgement:{})
        driver.cancel();precondition(count==1)
        var choices:[SPUUserUpdateChoice]=[]
        driver.receiveOffer(version:"test",build:"7",informationOnly:false,stage:.notDownloaded,reply:{choices.append($0)})
        precondition(offers==0 && choices == [.dismiss])
        driver=make();driver.begin()
        driver.receiveOffer(version:"test",build:"7",informationOnly:false,stage:.notDownloaded,reply:{choices.append($0)})
        precondition(offers==1)
        driver.showUpdateReleaseNotesFailedToDownloadWithError(NSError(domain:"fixture",code:1))
        precondition(notes==1 && count==0 && accept != nil)
        accept?(false);precondition(count==1)
        driver.showUpdateReleaseNotesFailedToDownloadWithError(NSError(domain:"late",code:1))
        precondition(notes==1 && count==1)
        driver=make();driver.begin();choices=[]
        driver.receiveOffer(version:"test",build:"7",informationOnly:false,stage:.notDownloaded,reply:{choices.append($0)})
        accept?(true);precondition(choices == [.install])
        driver.showDownloadInitiated { cancels += 1 }
        driver.cancel();precondition(count==1 && cancels==1)
        driver.showReady(toInstallAndRelaunch:{ choices.append($0) })
        precondition(choices == [.install,.skip] && count==1)
        driver=make();driver.begin();choices=[]
        driver.receiveOffer(version:"test",build:"7",informationOnly:false,stage:.notDownloaded,reply:{choices.append($0)})
        accept?(true);state = .active
        driver.showReady(toInstallAndRelaunch:{ choices.append($0) })
        precondition(choices == [.install,.skip] && count==1)
        for s in [UpdateLaunchPolicy.Session.active,.unknown] {
            state=s;driver=make();driver.begin();precondition(engine.checks==0 && count==1)
        }
        state = .idle;driver=make();driver.begin();choices=[]
        driver.receiveOffer(version:"cached",build:"7",informationOnly:false,stage:.installing,reply:{choices.append($0)})
        precondition(offers==0 && count==1 && choices == [.skip])
        state = .idle;ownership = .homebrew
        driver=make();driver.begin();precondition(engine.checks==0 && count==1)
        ownership = .direct;driver=make();engine.fail=true;driver.begin();precondition(count==1)
        driver=make();driver.begin()
        driver.showUpdaterError(NSError(domain:NSURLErrorDomain,code:NSURLErrorNotConnectedToInternet),acknowledgement:{})
        precondition(count==1)
        // An installer/authorization failure must clear the one-use relaunch
        // intent and release Steam once, even if Sparkle repeats its error.
        for code in [4001,4004,4005] {
            driver=make();driver.begin();choices=[]
            driver.receiveOffer(version:"test",build:"7",informationOnly:false,stage:.notDownloaded,reply:{choices.append($0)})
            accept?(true)
            driver.showReady(toInstallAndRelaunch:{choices.append($0)})
            precondition(driver.isInstalling && restart.receipts.count==1 && count==0)
            var acknowledgements=0
            let error=NSError(domain:"SUSparkleErrorDomain",code:code)
            driver.showUpdaterError(error,acknowledgement:{acknowledgements += 1})
            driver.showUpdaterError(error,acknowledgement:{acknowledgements += 1})
            precondition(!driver.isInstalling && restart.receipts.isEmpty)
            precondition(count==1 && acknowledgements==2 && choices == [.install,.install])
        }
        // If Keychain cannot retain the restart intent, never start installation.
        driver=make();restart.failWrite=true;driver.begin();choices=[]
        driver.receiveOffer(version:"test",build:"7",informationOnly:false,stage:.notDownloaded,reply:{choices.append($0)})
        accept?(true)
        driver.showReady(toInstallAndRelaunch:{choices.append($0)})
        precondition(count==1 && !driver.isInstalling && restart.receipts.isEmpty)
        precondition(choices == [.install,.skip])
        driver=make();driver.begin();driver.showUserInitiatedUpdateCheck { cancels += 1 }
        let start=ProcessInfo.processInfo.systemUptime
        while count==0 && ProcessInfo.processInfo.systemUptime-start < 9 {
            RunLoop.current.run(until:Date().addingTimeInterval(0.02))
        }
        precondition(count==1 && cancels==1 && ProcessInfo.processInfo.systemUptime-start < 8.5)
        driver.receiveOffer(version:"late",build:"7",informationOnly:false,stage:.notDownloaded,reply:{ _ in })
        precondition(offers==0 && count==1)
        print("PASS: adapter engine/callback integration; real 8-second watchdog, exactly-once release, Later, offline/start failure, download cancel, late ready-to-install rejection, live-session and Homebrew deferral, installer/authentication/relaunch error callbacks and restart-store denial. Synthetic engine; no installer/Keychain/report/Steam execution.")
    }
}
