// swift-tools-version: 6.0
import PackageDescription

// The shared build.py compiles this dependency-free target with the owned C ABI
// object. SwiftPM users must supply that same native_bridge.o at link time.
let package = Package(
    name: "PearManagerExperiment",
    platforms: [.macOS("26.0")],
    products: [.executable(name: "pear-manager-swift", targets: ["PearManager"])],
    targets: [.executableTarget(name: "PearManager")]
)
