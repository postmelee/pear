// SPDX-FileCopyrightText: 2026 Pear contributors
// SPDX-License-Identifier: GPL-3.0-or-later
import Foundation
@main struct UpdateNotesTests {
    static func main() {
        precondition(UpdateReleaseNotes.isReleaseLink(URL(string:"https://github.com/postmelee/pear/releases/tag/v0.1.0")))
        for value in ["http://github.com/postmelee/pear/releases", "https://github.com.evil.invalid/postmelee/pear/releases", "https://user@github.com/postmelee/pear/releases", "https://github.com/postmelee/pear/releases-other", "file:///tmp/release.html"] {
            precondition(!UpdateReleaseNotes.isReleaseLink(URL(string:value)))
        }
        precondition(UpdateReleaseNotes.isNotesLink(URL(string:"https://postmelee.github.io/pear/updates/v0.1.0.html")))
        for value in ["https://postmelee.github.io/other/updates/a.html", "https://postmelee.github.io/pear/updates/../private", "https://postmelee.github.io/pear/updates/a.html?q=secret", "https://github.com/postmelee/pear/releases"] {
            precondition(!UpdateReleaseNotes.isNotesLink(URL(string:value)))
        }
        let raw="<script>bad()</script> & <img src='http://localhost/'>"
        let notes=UpdateReleaseNotes(body:raw,isHTML:false,source:URL(string:"https://evil.invalid"))
        precondition(notes.source == UpdateReleaseNotes.releases)
        precondition(notes.document!.contains("&lt;script&gt;bad()&lt;/script&gt;"))
        precondition(!notes.document!.contains(raw))
        precondition(UpdateReleaseNotes(body:String(repeating:"é",count:UpdateReleaseNotes.maximumBytes),isHTML:true).document == nil)
        print("PASS: release source allowlist, plain-text escaping, bounded UTF-8 payload and safe source fallback.")
    }
}
