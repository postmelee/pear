// SPDX-FileCopyrightText: 2026 Pear contributors
// SPDX-License-Identifier: GPL-3.0-or-later
import AppKit
import WebKit

struct UpdateReleaseNotes {
    static let releases = URL(string:"https://github.com/postmelee/pear/releases")!
    static let maximumBytes = 256 * 1024
    let body: String
    let isHTML: Bool
    let source: URL
    init(body:String, isHTML:Bool, source:URL? = nil) {
        self.body=body;self.isHTML=isHTML
        self.source=Self.isReleaseLink(source) ? source! : Self.releases
    }
    static func isReleaseLink(_ url:URL?) -> Bool {
        guard let url,url.scheme == "https",url.host == "github.com",url.user == nil,url.password == nil,
              url.port == nil else { return false }
        return url.path == "/postmelee/pear/releases" || url.path.hasPrefix("/postmelee/pear/releases/tag/")
    }
    static func isNotesLink(_ url:URL?) -> Bool {
        guard let url,url.scheme == "https",url.host == "postmelee.github.io",url.user == nil,
              url.password == nil,url.port == nil,url.query == nil,url.fragment == nil else { return false }
        return url.path.hasPrefix("/pear/updates/") && !url.path.contains("..")
    }
    static func escape(_ text:String) -> String {
        text.replacingOccurrences(of:"&",with:"&amp;").replacingOccurrences(of:"<",with:"&lt;").replacingOccurrences(of:">",with:"&gt;").replacingOccurrences(of:"\"",with:"&quot;")
    }
    var document:String? {
        guard body.utf8.count <= Self.maximumBytes else { return nil }
        let content=isHTML ? body : "<pre>\(Self.escape(body))</pre>"
        // Render only release text. Scripts, frames, forms and remote resources
        // cannot run; the WebKit rule list separately blocks all resource loads.
        return """
        <!doctype html><html><head><meta charset="utf-8">
        <meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; img-src 'none'; font-src 'none'; media-src 'none'; frame-src 'none'; connect-src 'none'; form-action 'none'; base-uri 'none'">
        <meta name="color-scheme" content="light dark">
        <style>:root{color-scheme:light dark}body{font:14px -apple-system,sans-serif;line-height:1.55;margin:20px;overflow-wrap:anywhere}h1,h2,h3{font-size:17px;line-height:1.3;margin:18px 0 8px}h1:first-child,h2:first-child{margin-top:0}p,ul,ol{margin:8px 0}pre{white-space:pre-wrap;font:inherit}a{color:LinkText}img,iframe,form,video,audio{display:none!important}</style>
        </head><body>\(content)</body></html>
        """
    }
}

@MainActor final class UpdateNotesView: NSView, WKNavigationDelegate {
    private var web:WKWebView?
    private let status=NSTextField(wrappingLabelWithString:"Loading release notes…")
    private let sourceButton=NSButton(title:"View on GitHub ↗",target:nil,action:nil)
    private var source=UpdateReleaseNotes.releases
    private var pending:UpdateReleaseNotes?
    private var deadline:DispatchWorkItem?
    private var generation=0
    override init(frame:NSRect) {
        super.init(frame:frame)
        translatesAutoresizingMaskIntoConstraints=false
        status.font = .systemFont(ofSize:13);status.textColor = .secondaryLabelColor
        sourceButton.bezelStyle = .inline;sourceButton.target=self;sourceButton.action=#selector(openSource)
        let heading=NSTextField(labelWithString:"What’s new")
        heading.font = .systemFont(ofSize:14,weight:.semibold)
        for view in [heading,sourceButton,status] { view.translatesAutoresizingMaskIntoConstraints=false;addSubview(view) }
        NSLayoutConstraint.activate([
            heading.leadingAnchor.constraint(equalTo:leadingAnchor),heading.topAnchor.constraint(equalTo:topAnchor),
            sourceButton.trailingAnchor.constraint(equalTo:trailingAnchor),sourceButton.centerYAnchor.constraint(equalTo:heading.centerYAnchor),
            status.leadingAnchor.constraint(equalTo:leadingAnchor,constant:16),status.trailingAnchor.constraint(equalTo:trailingAnchor,constant:-16),
            status.topAnchor.constraint(equalTo:heading.bottomAnchor,constant:28),heightAnchor.constraint(equalToConstant:270)])
        let config=WKWebViewConfiguration()
        config.websiteDataStore = .nonPersistent()
        config.defaultWebpagePreferences.allowsContentJavaScript=false
        // Install network blocking before the first HTML document is loaded.
        WKContentRuleListStore.default().compileContentRuleList(forIdentifier:"PearReleaseNotesNoResources",encodedContentRuleList:"""
        [{"trigger":{"url-filter":".*"},"action":{"type":"block"}}]
        """) { [weak self] rules,_ in
            guard let self else { return }
            guard let rules else { self.unavailable();return }
            config.userContentController.add(rules)
            let web=WKWebView(frame:.zero,configuration:config);self.web=web
            web.navigationDelegate=self;web.translatesAutoresizingMaskIntoConstraints=false
            web.setAccessibilityLabel("Release notes")
            web.wantsLayer=true;web.layer?.cornerRadius=8;web.layer?.borderWidth=1
            web.layer?.borderColor=NSColor.separatorColor.cgColor
            self.addSubview(web,positioned:.below,relativeTo:self.status)
            NSLayoutConstraint.activate([web.leadingAnchor.constraint(equalTo:self.leadingAnchor),web.trailingAnchor.constraint(equalTo:self.trailingAnchor),web.topAnchor.constraint(equalTo:heading.bottomAnchor,constant:12),web.bottomAnchor.constraint(equalTo:self.bottomAnchor)])
            web.isHidden=true
            if let notes=self.pending { self.show(notes) }
        }
    }
    required init?(coder:NSCoder) { fatalError("init(coder:) has not been implemented") }
    func loading() {
        generation += 1;pending=nil;deadline?.cancel();web?.stopLoading();web?.isHidden=true
        source=UpdateReleaseNotes.releases
        status.stringValue="Loading release notes…";status.isHidden=false
        let token=generation
        let item=DispatchWorkItem { [weak self] in guard let self,self.generation==token else{return};self.unavailable() }
        deadline=item;DispatchQueue.main.asyncAfter(deadline:.now()+8,execute:item)
    }
    func show(_ notes:UpdateReleaseNotes) {
        pending=notes;source=notes.source
        guard let html=notes.document else { unavailable();return }
        guard let web else { return }
        web.loadHTMLString(html,baseURL:nil)
    }
    func unavailable() {
        deadline?.cancel();pending=nil;web?.stopLoading();web?.isHidden=true
        status.stringValue="Release notes couldn’t be loaded. You can still update, or read them on GitHub."
        status.isHidden=false
    }
    @objc private func openSource() { NSWorkspace.shared.open(source) }
    func webView(_ webView:WKWebView,didFinish navigation:WKNavigation!) {
        guard pending != nil else { return }
        deadline?.cancel();status.isHidden=true;webView.isHidden=false
    }
    func webView(_ webView:WKWebView,didFail navigation:WKNavigation!,withError error:Error) { unavailable() }
    func webView(_ webView:WKWebView,didFailProvisionalNavigation navigation:WKNavigation!,withError error:Error) { unavailable() }
    func webView(_ webView:WKWebView,decidePolicyFor action:WKNavigationAction,decisionHandler:@escaping (WKNavigationActionPolicy)->Void) {
        if action.navigationType == .linkActivated {
            if UpdateReleaseNotes.isReleaseLink(action.request.url),let url=action.request.url { NSWorkspace.shared.open(url) }
            decisionHandler(.cancel);return
        }
        decisionHandler(action.request.url?.absoluteString == "about:blank" && action.targetFrame?.isMainFrame == true ? .allow : .cancel)
    }
}
