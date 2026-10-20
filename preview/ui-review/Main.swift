// SPDX-FileCopyrightText: 2026 Pear contributors
// SPDX-License-Identifier: GPL-3.0-or-later
// UI-only executable. No transport, Steam launch, production state or Keychain.
import AppKit

@MainActor final class UIReview: NSObject, NSApplicationDelegate {
    let launcher = PreviewApp()
    var history: HistoryWindow!
    var store: ReportingStore!
    var introHistory: HistoryWindow?
    func applicationDidFinishLaunching(_ notification: Notification) {
        do {
            let directory=Bundle.main.bundleURL.deletingLastPathComponent().appendingPathComponent("ui-fixtures")
            store=try ReportingStore(directory:directory)
            if store.snapshot.runs.isEmpty {
                for (index,result) in [UserRunResult.unknown,.normal,.problems].enumerated() {
                    let start=Date().addingTimeInterval(Double(-86400 * index - 1200))
                    try store.record(RunObservation(id:UUID(),startedAt:start,endedAt:start.addingTimeInterval(1200),
                        macOS:"15.7.9",chip:"Apple M4 Pro",memoryGiB:24,pear:"UI review",wine:"11.0",dxmt:"0.80",appID:3405340,
                        gameBuild:"21750826",gameName:"Megabonk",observedExit:.exited,result:result,note:"UI sample only. No game was run."))
                }
                try store.transaction { $0.policy.configure(mode:.askAfterExit,fields:Set(ReportField.allCases)) }
            }
            history=HistoryWindow(store:store)
            launcher.buildMainWindow();launcher.history=history
            // Never wire launcher.start in this harness: its visible action only
            // demonstrates the next presentation state, without creating a process.
            launcher.button.target=self;launcher.button.action=#selector(ready)
            launcher.cancelButton.target=self;launcher.cancelButton.action=#selector(setup)
            let menu=NSMenu();let app=NSMenuItem();let appMenu=NSMenu()
            let about=NSMenuItem(title:"About Pear",action:#selector(PreviewApp.showAbout),keyEquivalent:"");about.target=launcher;appMenu.addItem(about)
            let runsEntry=NSMenuItem(title:"Run history",action:#selector(PreviewApp.showHistory),keyEquivalent:"h");runsEntry.target=launcher;runsEntry.keyEquivalentModifierMask=[.command,.shift]
            let settings=NSMenuItem(title:"Settings…",action:#selector(PreviewApp.showSharingSettings),keyEquivalent:",");settings.target=launcher;appMenu.addItem(settings)
            appMenu.addItem(.separator())
            appMenu.addItem(withTitle:"Quit UI review",action:#selector(NSApplication.terminate(_:)),keyEquivalent:"q")
            app.submenu=appMenu;menu.addItem(app)
            let windowItem=NSMenuItem(title:"Window",action:nil,keyEquivalent:"")
            let windowMenu=NSMenu(title:"Window");windowMenu.addItem(runsEntry);windowItem.submenu=windowMenu;menu.addItem(windowItem)
            let item=NSMenuItem(title:"Preview screens",action:nil,keyEquivalent:"");let screens=NSMenu()
            for (title,action,key) in [("Run history",#selector(runs),"1"),("First installation",#selector(setup),"2"),
                                       ("Downloading · with Cancel",#selector(downloading),"3"),("Opening Steam",#selector(opening),"4"),
                                       ("Steam window open",#selector(ready),"5"),("After a game",#selector(prompt),"6"),
                                       ("Light appearance",#selector(light),"7"),("Dark appearance",#selector(dark),"8"),("First-run sharing",#selector(introduction),"9"),
                                       ("App update available (fixture)",#selector(updateAvailable),"0")] {
                let entry=NSMenuItem(title:title,action:action,keyEquivalent:key);entry.target=self;screens.addItem(entry)
            }
            item.submenu=screens;menu.addItem(item);NSApp.mainMenu=menu
            launcher.window.center();ready();runs()
            print("UI review ready; synthetic records only; no transport or Steam execution.")
        } catch { fputs("UI review failed: \(error)\n",stderr);NSApp.terminate(nil) }
    }
    @objc func updateAvailable() {
        resetMain()
        launcher.presentUpdateOffer(current:"0.1.0",new:"0.1.1")
        launcher.updateNotes.show(UpdateReleaseNotes(body:"""
        <h2>Release notes preview</h2><p>This is sample content for UI review, not a published release.</p>
        <h3>Improvements</h3><ul><li>See the current and new Pear versions before updating.</li><li>Read what changed without leaving Pear.</li></ul>
        <h3>Your games and settings</h3><p>App updates keep your installed games, saved progress and sharing settings.</p>
        <h3>Updating</h3><p>Choose Update and launch to install the new app, or Later to keep using this version.</p>
        <p>Wine and DXMT use Pear’s existing installation and verification process.</p>
        """,isHTML:true))
        launcher.button.target=self;launcher.button.action=#selector(updateDownloading)
        launcher.cancelButton.title="Later";launcher.cancelButton.target=self;launcher.cancelButton.action=#selector(ready)
    }
    @objc func updateDownloading() {
        launcher.presentUpdate("Downloading Pear update","Your games and saved progress will be kept.",0.35)
        launcher.cancelButton.target=self;launcher.cancelButton.action=#selector(ready)
    }
    @objc func introduction() {
        let directory=Bundle.main.bundleURL.deletingLastPathComponent().appendingPathComponent("ui-fixtures/onboarding-" + UUID().uuidString)
        if let sample=try? ReportingStore(directory:directory) {
            introHistory=HistoryWindow(store:sample);introHistory?.showSharingIntroductionIfNeeded()
        }
    }
    @objc func runs() { history.show() }
    func resetMain() {
        launcher.hideUpdateOffer()
        launcher.button.target=self;launcher.button.action=#selector(ready)
        launcher.cancelButton.target=self;launcher.cancelButton.action=#selector(setup);launcher.cancelButton.title="Cancel"
        launcher.downloads?.isHidden=true;launcher.busy.stopAnimation(nil);launcher.busy.isHidden=true
        launcher.progress.isHidden=true;launcher.cancelButton.isHidden=true;launcher.button.isEnabled=true
        launcher.window.makeKeyAndOrderFront(nil)
    }
    @objc func ready() { resetMain();launcher.showOpening(.visible) }
    @objc func opening() { resetMain();launcher.showOpening(.waiting) }
    @objc func downloading() {
        resetMain();launcher.titleLabel.stringValue="Getting Pear ready"
        launcher.display("@download\t150000000\t534424618\truntime")
        launcher.cancelButton.isHidden=false;launcher.cancelButton.isEnabled=true
        launcher.button.title="Installing…";launcher.button.isEnabled=false
    }
    @objc func setup() {
        resetMain();launcher.titleLabel.stringValue="Set up Pear"
        // Assign a fixture history store so showSetup never constructs production services.
        launcher.historyStore=store
        let fixture=Data(#"{"version":"UI review","runtime_id":"fixture","runtime_bytes":534424618,"steam_bytes":2360000,"runtime_present":false,"steam_present":false,"ready":false}"#.utf8)
        launcher.showSetup(try! JSONDecoder().decode(SetupInfo.self,from:fixture))
    }
    @objc func prompt() {
        try? store.transaction { $0.policy.configure(mode:.askAfterExit,fields:Set(ReportField.allCases));$0.policy.setExitPrompt(true) }
        if let run=store.snapshot.runs.first { history.confirmFinished(run.id) }
    }
    @objc func light() { NSApp.appearance=NSAppearance(named:.aqua) }
    @objc func dark() { NSApp.appearance=NSAppearance(named:.darkAqua) }
    func applicationShouldTerminateAfterLastWindowClosed(_ sender:NSApplication)->Bool { true }
}
@main struct UIReviewMain {
    static func main() {
        let app=NSApplication.shared;let delegate=UIReview();app.delegate=delegate
        app.setActivationPolicy(.regular);app.run()
    }
}
