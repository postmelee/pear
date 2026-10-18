// SPDX-FileCopyrightText: 2026 Pear contributors
// SPDX-License-Identifier: GPL-3.0-or-later
import AppKit

// Native adaptation of tools/catalog/tokens.css at efd9ed7. Keep semantic colors
// dynamic so appearance and accessibility remain native; no forced light theme.
@MainActor enum PearStyle {
    static func color(_ light: UInt32, _ dark: UInt32) -> NSColor {
        NSColor(name: nil) { appearance in
            let hex = appearance.bestMatch(from: [.aqua, .darkAqua]) == .darkAqua ? dark : light
            return NSColor(srgbRed: CGFloat((hex >> 16) & 255) / 255,
                           green: CGFloat((hex >> 8) & 255) / 255,
                           blue: CGFloat(hex & 255) / 255, alpha: 1)
        }
    }
    static let background = color(0xfffcf0, 0x100f0f)
    static let surface = color(0xf2f0e5, 0x1c1b1a)
    static let foreground = color(0x100f0f, 0xcecdc3)
    static let muted = color(0x6f6e69, 0xa5a39b)
    static let accent = color(0x536907, 0xa0af54)
    static let buttonFill = color(0x536907, 0x536907)
    static let negative = color(0xaf3029, 0xe8705f)
    static let selection = color(0xe0e7c5, 0x303526)
    static func label(_ title: String, size: CGFloat = 13, weight: NSFont.Weight = .regular, muted: Bool = false) -> NSTextField {
        let label = NSTextField(wrappingLabelWithString: title)
        label.font = .systemFont(ofSize: size, weight: weight)
        label.textColor = muted ? self.muted : foreground
        return label
    }
    static func button(_ title: String, target: AnyObject?, action: Selector?, primary: Bool = false) -> NSButton {
        let button = NSButton(title: title, target: target, action: action)
        button.bezelStyle = .rounded; button.controlSize = .large
        button.font = .systemFont(ofSize: 13, weight: primary ? .semibold : .regular)
        if primary { button.bezelColor = buttonFill }
        return button
    }
    static func stack(_ views: [NSView], horizontal: Bool = false, spacing: CGFloat = 12) -> NSStackView {
        let stack = NSStackView(views: views)
        stack.orientation = horizontal ? .horizontal : .vertical
        stack.alignment = horizontal ? .centerY : .leading
        stack.spacing = spacing
        return stack
    }
    static func pin(_ view: NSView, in parent: NSView, inset: CGFloat = 28) {
        view.translatesAutoresizingMaskIntoConstraints = false; parent.addSubview(view)
        NSLayoutConstraint.activate([
            view.leadingAnchor.constraint(equalTo: parent.leadingAnchor, constant: inset),
            view.trailingAnchor.constraint(equalTo: parent.trailingAnchor, constant: -inset),
            view.topAnchor.constraint(equalTo: parent.topAnchor, constant: inset),
            view.bottomAnchor.constraint(equalTo: parent.bottomAnchor, constant: -inset)])
    }
    static func window(_ window: NSWindow) { window.backgroundColor = background }
    static func editor(_ text: NSTextView, height: CGFloat = 100) -> NSScrollView {
        text.isRichText = false; text.font = .systemFont(ofSize: 14)
        text.textColor = .textColor; text.backgroundColor = .textBackgroundColor
        text.insertionPointColor = .textColor; text.textContainerInset = NSSize(width: 10, height: 10)
        text.isVerticallyResizable = true; text.isHorizontallyResizable = false
        text.autoresizingMask = [.width]; text.textContainer?.widthTracksTextView = true
        let scroll = NSScrollView(); scroll.documentView = text; scroll.hasVerticalScroller = true
        scroll.drawsBackground = true; scroll.backgroundColor = .textBackgroundColor
        scroll.borderType = .bezelBorder
        scroll.wantsLayer = true; scroll.layer?.cornerRadius = 6; scroll.layer?.masksToBounds = true
        scroll.heightAnchor.constraint(equalToConstant: height).isActive = true
        return scroll
    }
}

@MainActor final class PearHistoryRow: NSTableRowView {
    override var interiorBackgroundStyle: NSView.BackgroundStyle { .normal }
    override func drawSelection(in dirtyRect: NSRect) {
        PearStyle.selection.setFill()
        NSBezierPath(roundedRect: bounds.insetBy(dx: 0, dy: 2), xRadius: 6, yRadius: 6).fill()
    }
}

// Flipped document coordinates keep short settings forms aligned to the top.
@MainActor final class PearFormStack: NSStackView {
    override var isFlipped: Bool { true }
}
