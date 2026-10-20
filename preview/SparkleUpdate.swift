// SPDX-FileCopyrightText: 2026 Pear contributors
// SPDX-License-Identifier: GPL-3.0-or-later
import AppKit
import Sparkle

@MainActor protocol AppUpdateChecking: AnyObject {
    func start() throws
    func checkForUpdates()
}
@MainActor private final class SparkleCheckEngine: AppUpdateChecking {
    let updater: SPUUpdater
    init(bundle:Bundle, driver:SPUUserDriver, delegate:SPUUpdaterDelegate) {
        updater=SPUUpdater(hostBundle:bundle,applicationBundle:bundle,userDriver:driver,delegate:delegate)
    }
    func start() throws {
        updater.automaticallyChecksForUpdates=false
        updater.automaticallyDownloadsUpdates=false
        updater.sendsSystemProfile=false
        updater.userAgentString="Pear/" + (updater.hostBundle.object(forInfoDictionaryKey:"CFBundleShortVersionString") as? String ?? "unknown") + " Sparkle/2.10.0"
        _=updater.clearFeedURLFromUserDefaults()
        try updater.start()
    }
    func checkForUpdates() { updater.checkForUpdates() }
}

// Sparkle owns download verification, installation, authorization and relaunch.
// Pear owns only the launch gate and its presentation; all callbacks serialize
// on the main actor. Reporting consent and data are not provided to Sparkle.
@MainActor final class PearUpdater: NSObject, SPUUserDriver, SPUUpdaterDelegate {
    private var engine: AppUpdateChecking!
    private let bundle: Bundle
    private let makeEngine: (Bundle, SPUUserDriver, SPUUpdaterDelegate) -> AppUpdateChecking
    private var policy = UpdateLaunchPolicy()
    private var watchdog: DispatchWorkItem?
    private var cancelTransfer: (() -> Void)?
    private var choice: ((SPUUserUpdateChoice) -> Void)?
    private var choiceStage: SPUUserUpdateStage = .notDownloaded
    private var expectedBytes: UInt64 = 0
    private var receivedBytes: UInt64 = 0
    private var targetBuild: String?
    private var releaseSource: URL?
    private let restart: UpdateRestartHandling
    let session: () -> UpdateLaunchPolicy.Session
    let ownership: () -> UpdateOwnership
    let present: (String, String, Double?) -> Void
    let offer: (String, @escaping (Bool) -> Void) -> Void
    let releaseNotes: (UpdateReleaseNotes?) -> Void
    let proceed: () -> Void
    var isBusy: Bool { policy.phase != .initial && policy.phase != .released }
    var isInstalling: Bool { policy.phase == .installing }
    var installationDeferred = false
    private var deferredInstall: (() -> Void)?
    func resumeDeferredInstallation() {
        guard installationDeferred, let install=deferredInstall,
              ownership() == .direct,session() == .idle,let targetBuild else { return }
        do {
            try restart.write(UpdateRestartReceipt(from:bundle.object(forInfoDictionaryKey:"CFBundleVersion") as? String ?? "",to:targetBuild,expires:Date().addingTimeInterval(600)))
        } catch { return }
        installationDeferred=false;deferredInstall=nil
        present("Installing Pear update","Pear will reopen, then continue to Steam.",nil)
        install()
    }

    init(bundle:Bundle = .main,
         restart: UpdateRestartHandling = UpdateRestartStore(),
         makeEngine: ((Bundle,SPUUserDriver,SPUUpdaterDelegate)->AppUpdateChecking)? = nil,
         session: @escaping () -> UpdateLaunchPolicy.Session,
         ownership: @escaping () -> UpdateOwnership,
         present: @escaping (String,String,Double?) -> Void,
         offer: @escaping (String,@escaping (Bool)->Void) -> Void,
         releaseNotes: @escaping (UpdateReleaseNotes?) -> Void = { _ in },
         proceed: @escaping () -> Void) {
        self.restart=restart
        self.bundle=bundle
        self.makeEngine=makeEngine ?? { SparkleCheckEngine(bundle:$0,driver:$1,delegate:$2) }
        self.session=session; self.ownership=ownership; self.present=present
        self.offer=offer; self.releaseNotes=releaseNotes; self.proceed=proceed
        super.init()
    }
    func begin() {
        guard policy.phase == .initial else { return }
        let action = policy.begin(now:ProcessInfo.processInfo.systemUptime,session:session(),homebrew:ownership() != .direct)
        guard action == .check else { proceed(); return }
        // Development builds without an admitted feed and public key cannot update.
        guard let feed = bundle.object(forInfoDictionaryKey:"SUFeedURL") as? String,
              URL(string:feed)?.scheme == "https",
              let key = bundle.object(forInfoDictionaryKey:"SUPublicEDKey") as? String,
              Data(base64Encoded:key)?.count == 32 else { finish(policy.failedOrCancelled()); return }
        present("Checking for updates", "Steam will open shortly. You can continue with this version.", nil)
        engine=makeEngine(bundle,self,self)
        do {
            try engine.start()
            armDeadline(seconds:8) { [weak self] in
                guard let self else { return }
                self.finish(self.policy.tick(now:ProcessInfo.processInfo.systemUptime))
            }
            engine.checkForUpdates()
        } catch { finish(policy.failedOrCancelled()) }
    }
    private func armDeadline(seconds:Double, action:@escaping ()->Void) {
        watchdog?.cancel()
        let item=DispatchWorkItem(block:action);watchdog=item
        DispatchQueue.main.asyncAfter(deadline:.now()+seconds,execute:item)
    }
    private func finish(_ action: UpdateLaunchPolicy.Action) {
        guard action == .continueSteam || action == .deferUpdate else { return }
        watchdog?.cancel();watchdog=nil
        let cancel=cancelTransfer;cancelTransfer=nil
        let reply=choice;choice=nil
        // Skip at the installing stage cancels; dismiss would install on quit.
        reply?(choiceStage == .installing ? .skip : .dismiss)
        cancel?()
        proceed()
    }
    func cancel() { finish(policy.failedOrCancelled()) }
    func stopForQuit() {
        watchdog?.cancel()
        if !isInstalling { cancelTransfer?(); cancelTransfer=nil }
    }
    func choose(_ accepted:Bool) {
        let action=policy.chooseUpdate(accepted,session:ownership() == .direct ? session() : .unknown)
        if action == .download {
            let reply=choice;choice=nil;reply?(.install)
        } else { finish(action) }
    }
    func show(_ request:SPUUpdatePermissionRequest, reply:@escaping (SUUpdatePermissionResponse)->Void) {
        reply(SUUpdatePermissionResponse(automaticUpdateChecks:false,sendSystemProfile:false))
    }
    func showUserInitiatedUpdateCheck(cancellation:@escaping ()->Void) {
        guard policy.phase == .checking else { cancellation(); return }
        cancelTransfer=cancellation
    }
    func showUpdateFound(with appcastItem:SUAppcastItem, state:SPUUserUpdateState, reply:@escaping (SPUUserUpdateChoice)->Void) {
        releaseSource=appcastItem.infoURL
        receiveOffer(version:appcastItem.displayVersionString,build:appcastItem.versionString,
                     informationOnly:appcastItem.isInformationOnlyUpdate,stage:state.stage,reply:reply)
        guard policy.phase == .offering else { return }
        if let body=appcastItem.itemDescription, !body.isEmpty {
            releaseNotes(UpdateReleaseNotes(body:body,isHTML:appcastItem.itemDescriptionFormat != "plain-text",source:appcastItem.infoURL))
        } else if !UpdateReleaseNotes.isNotesLink(appcastItem.releaseNotesURL) { releaseNotes(nil) }
    }
    // Scalar boundary keeps callback ordering testable without creating private
    // Sparkle objects or executing its installer in a synthetic fixture.
    func receiveOffer(version:String, build:String, informationOnly:Bool,
                      stage:SPUUserUpdateStage, reply:@escaping (SPUUserUpdateChoice)->Void) {
        // Do not revive an installation left pending by an older session.
        guard stage == .notDownloaded else {
            reply(.skip);finish(policy.failedOrCancelled());return
        }
        let action=policy.checked(updateAvailable:!informationOnly,now:ProcessInfo.processInfo.systemUptime)
        guard action == .offer else {
            reply(stage == .installing ? .skip : .dismiss)
            finish(action);return
        }
        watchdog?.cancel();cancelTransfer=nil
        targetBuild=build
        choice=reply;choiceStage=stage
        let current=bundle.object(forInfoDictionaryKey:"CFBundleShortVersionString") as? String
        let display=current == version ? "\(version) (build \(build))" : version
        offer(display) { [weak self] accepted in self?.choose(accepted) }
    }
    func showUpdateReleaseNotes(with downloadData:SPUDownloadData) {
        guard policy.phase == .offering else { return }
        guard UpdateReleaseNotes.isNotesLink(downloadData.url),downloadData.data.count <= UpdateReleaseNotes.maximumBytes,
              let body=String(data:downloadData.data,encoding:.utf8) else { releaseNotes(nil);return }
        releaseNotes(UpdateReleaseNotes(body:body,isHTML:downloadData.mimeType == "text/html",source:releaseSource))
    }
    func showUpdateReleaseNotesFailedToDownloadWithError(_ error:Error) { if policy.phase == .offering { releaseNotes(nil) } }
    func showUpdateNotFoundWithError(_ error:Error, acknowledgement:@escaping ()->Void) {
        acknowledgement(); finish(policy.checked(updateAvailable:false,now:ProcessInfo.processInfo.systemUptime))
    }
    func showUpdaterError(_ error:Error, acknowledgement:@escaping ()->Void) {
        acknowledgement(); restart.clear(); finish(policy.failedOrCancelled())
    }
    func showDownloadInitiated(cancellation:@escaping ()->Void) {
        guard policy.phase == .downloading else { cancellation();return }
        cancelTransfer=cancellation
        present("Downloading Pear update", "Your games and saved progress will be kept.",nil)
        resetDownloadDeadline()
    }
    private func resetDownloadDeadline() {
        armDeadline(seconds:60) { [weak self] in self?.cancel() }
    }
    func showDownloadDidReceiveExpectedContentLength(_ expectedContentLength:UInt64) { expectedBytes=expectedContentLength }
    func showDownloadDidReceiveData(ofLength length:UInt64) {
        guard policy.phase == .downloading else { return }
        receivedBytes += length;resetDownloadDeadline()
        present("Downloading Pear update", "Your games and saved progress will be kept.",expectedBytes > 0 ? min(1,Double(receivedBytes)/Double(expectedBytes)) : nil)
    }
    func showDownloadDidStartExtractingUpdate() {
        guard policy.phase == .downloading else { return }
        cancelTransfer=nil
        present("Preparing Pear update", "Verifying and preparing the new app…",nil)
        armDeadline(seconds:120) { [weak self] in self?.cancel() }
    }
    func showExtractionReceivedProgress(_ progress:Double) {
        guard policy.phase == .downloading else { return }
        present("Preparing Pear update","Verifying and preparing the new app…",progress)
    }
    func showReady(toInstallAndRelaunch reply:@escaping (SPUUserUpdateChoice)->Void) {
        watchdog?.cancel();cancelTransfer=nil
        let action=policy.readyToInstall(session:ownership() == .direct ? session() : .unknown)
        guard action == .install else { reply(.skip);finish(action);return }
        guard let targetBuild else { reply(.skip);finish(policy.failedOrCancelled());return }
        do {
            try restart.write(UpdateRestartReceipt(from:bundle.object(forInfoDictionaryKey:"CFBundleVersion") as? String ?? "",to:targetBuild,expires:Date().addingTimeInterval(600)))
        } catch { reply(.skip);finish(policy.failedOrCancelled());return }
        present("Installing Pear update","Pear will reopen, then continue to Steam.",nil)
        reply(.install)
    }
    func showInstallingUpdate(withApplicationTerminated applicationTerminated:Bool, retryTerminatingApplication:@escaping ()->Void) {}
    func showUpdateInstalledAndRelaunched(_ relaunched:Bool, acknowledgement:@escaping ()->Void) { acknowledgement() }
    func dismissUpdateInstallation() {
        if !isInstalling { finish(policy.failedOrCancelled()) }
    }
    func updaterShouldPromptForPermissionToCheck(forUpdates updater:SPUUpdater)->Bool { false }
    func allowedSystemProfileKeys(for updater:SPUUpdater)->[String]? { [] }
    func feedParameters(for updater:SPUUpdater,sendingSystemProfile:Bool)->[[String:String]] { [] }
    func updater(_ updater:SPUUpdater,shouldDownloadReleaseNotesForUpdate item:SUAppcastItem)->Bool { UpdateReleaseNotes.isNotesLink(item.releaseNotesURL) }
    func updater(_ updater:SPUUpdater,mayPerform updateCheck:SPUUpdateCheck)throws {
        guard policy.phase == .checking,ownership() == .direct,session() == .idle else {
            throw NSError(domain:"Pear.Update",code:1,userInfo:[NSLocalizedDescriptionKey:"Update postponed while Steam is active."])
        }
    }
    func updater(_ updater:SPUUpdater,shouldPostponeRelaunchForUpdate item:SUAppcastItem,untilInvokingBlock installHandler:@escaping ()->Void)->Bool {
        guard ownership() == .direct,session() == .idle else {
            installationDeferred=true;deferredInstall=installHandler;restart.clear()
            present("Update postponed","Close Steam and your games, then choose Finish update.",nil)
            // Keep this installation stalled. Explicit quit also checks live activity.
            return true
        }
        return false
    }
    func updater(_ updater:SPUUpdater,didAbortWithError error:Error) { restart.clear();finish(policy.failedOrCancelled()) }
}
