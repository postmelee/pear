import Foundation
import Darwin

struct LaunchInput {
    let files: BundleFiles
    let executable: OpenedFile
    let executablePath: String
    let arguments: [String]
    let environment: [String]
}

final class Contracts {
    let files: BundleFiles
    var records: [String: JSON] = [:]
    var hashes: [String: String] = [:]
    var visiting = Set<String>()
    var ids: [String: String] = [:]
    var recordBytes = 0
    var blobCache: [String: OpenedFile] = [:]
    var identities: [String: String] = [:]
    var ineligible = false

    init(_ root: String) throws { files = try BundleFiles(root) }
    func digest(_ node: JSON?, scope: String) throws -> String {
        let d = try object(node, "algorithm scope value")
        try equal(d["algorithm"], "sha256"); try equal(d["scope"], scope)
        let value = try string(d["value"])
        try require(isHash(value)); return value
    }
    func blob(_ node: JSON?, scope: String? = nil) throws -> OpenedFile {
        let reference = try object(node, "ref_type path digest")
        try equal(reference["ref_type"], "blob")
        let path = try string(reference["path"])
        let d = try object(reference["digest"], "algorithm scope value")
        let declaredScope = try string(d["scope"])
        try require(["file_bytes", "source_archive_bytes", "evidence_json_bytes", "build_configuration_bytes", "patch_bytes"].contains(declaredScope))
        if let scope { try require(scope == declaredScope) }
        let hash = try digest(reference["digest"], scope: declaredScope)
        let file: OpenedFile
        if let cached = blobCache[path] { file = cached }
        else {
            file = try files.read(path, max: 16 * 1024 * 1024)
            files.blobBytes += file.data.count
            try require(files.blobBytes <= 64 * 1024 * 1024)
            blobCache[path] = file
        }
        try require(sha256(file.data) == hash)
        return file
    }
    func reference(_ node: JSON?, kind: String) throws -> (String, JSON) {
        let r = try object(node, "ref_type path record_kind schema_version digest")
        try equal(r["ref_type"], "record"); try equal(r["record_kind"], kind)
        try require(r["schema_version"] == .integer(1))
        let path = try string(r["path"])
        let hash = try digest(r["digest"], scope: "exact_utf8_file_bytes")
        let result = try record(path, expectedKind: kind)
        try require(hashes[path] == hash)
        return (path, result)
    }
    func record(_ path: String, expectedKind: String) throws -> JSON {
        try require(!visiting.contains(path))
        if let cached = records[path] {
            try equal(cached.object?["record_kind"], expectedKind)
            return cached
        }
        try require(records.count + visiting.count < 128)
        visiting.insert(path)
        defer { visiting.remove(path) }
        let bytes = try files.read(path, max: 262_144).data
        recordBytes += bytes.count
        try require(recordBytes <= 4 * 1024 * 1024)
        var parser = try StrictJSON(bytes)
        let parsed = try parser.parse()
        guard let fields = parsed.object else { throw Failure.invalid }
        try equal(fields["record_kind"], expectedKind)
        try require(fields["schema_version"] == .integer(1))
        let context = try string(fields["record_context"])
        try require(["fixture", "runtime", "research"].contains(context))
        if context != "fixture" { ineligible = true }
        let identifier = try string(fields["record_id"])
        if let old = ids[identifier] { try require(old == path) }
        ids[identifier] = path
        let disclosure = try object(fields["disclosure"], "mode withheld origin_token")
        let mode = try string(disclosure["mode"])
        try require(["full", "public_partial"].contains(mode))
        if mode != "full" { ineligible = true }
        let withheld = try strings(disclosure["withheld"])
        try require(withheld.allSatisfy { ["private_launch", "private_evidence", "private_configuration"].contains($0) })
        if mode != "full" {
            let token = try string(disclosure["origin_token"], max: 96)
            try require(!withheld.isEmpty && token.utf8.first.map { (48...57).contains($0) || (65...90).contains($0) || (97...122).contains($0) } == true && token.utf8.allSatisfy { (48...57).contains($0) || (65...90).contains($0) || (97...122).contains($0) || [45, 46, 95].contains($0) })
        }
        if mode == "full" { try require(disclosure["withheld"] == .array([]) && disclosure["origin_token"] == .null) }
        var referenceCount = 0
        func walk(_ node: JSON, _ depth: Int) throws {
            try require(depth <= 32)
            if let object = node.object {
                if object["ref_type"] != nil {
                    referenceCount += 1
                    try require(referenceCount <= 64)
                    let type = try string(object["ref_type"])
                    if type == "blob" { _ = try blob(node) }
                    else if type == "record" {
                        let kind = try string(object["record_kind"])
                        try require(["runtime_lock", "runtime_artifact", "game_profile", "launch"].contains(kind))
                        _ = try reference(node, kind: kind)
                    } else { throw Failure.invalid }
                    return
                }
                for child in object.values { try walk(child, depth + 1) }
            } else if let array = node.array { for child in array { try walk(child, depth + 1) } }
        }
        try walk(parsed, 0)
        records[path] = parsed
        hashes[path] = sha256(bytes)
        return parsed
    }
    let base = "record_kind schema_version record_context record_id disclosure "
    func host(_ node: JSON?) throws {
        let h = try object(node, "os architecture version capabilities")
        try equal(h["os"], "macos"); try equal(h["architecture"], "arm64")
        try require(h["version"] == .array([.integer(26), .integer(0), .integer(0)]))
        try require(h["capabilities"] == .array([.string("fixture-capability")]))
    }
    func evidence(_ node: JSON?) throws {
        let refs = try array(node)
        try require(!refs.isEmpty)
        for ref in refs { _ = try blob(ref, scope: "evidence_json_bytes") }
    }
    func validateLock(_ node: JSON) throws {
        let lock = try object(node, base + "source_inventory_ref compatibility_family component_coverage components toolchains host_requirements signing_requirements evidence")
        try equal(lock["record_id"], "fixture.lock"); try require(lock["source_inventory_ref"] == .null)
        let family = try known(lock["compatibility_family"], "value")
        try equal(family["value"], "fixture-family")
        let coverage = try known(lock["component_coverage"], "complete")
        try require(coverage["complete"] == .bool(true))
        let components = try array(lock["components"])
        try require(components.count == 1)
        let c = try object(components[0], "component_id role source dependencies patches build_context terms evidence")
        try equal(c["component_id"], "fixture-translator"); try equal(c["role"], "fixture")
        let source = try known(c["source"], "url immutable_ref content")
        let url = try string(source["url"])
        try require(url == "https://pear.invalid/self-owned-fixture")
        let immutable = try object(source["immutable_ref"], "kind object_format value")
        try equal(immutable["kind"], "archive")
        try require(immutable["object_format"] == .null && immutable["value"] == .null)
        _ = try blob(source["content"], scope: "source_archive_bytes")
        let dependencies = try known(c["dependencies"], "component_ids")
        try require(dependencies["component_ids"] == .array([]))
        let patches = try known(c["patches"], "items")
        try require(patches["items"] == .array([]))
        let build = try known(c["build_context"], "toolchain_ids targets configuration")
        try require(build["toolchain_ids"] == .array([.string("fixture-toolchain")]))
        let targets = try array(build["targets"])
        try require(targets.count == 1)
        let target = try object(targets[0], "role format architecture triple")
        try equal(target["role"], "host"); try equal(target["format"], "mach_o")
        try equal(target["architecture"], "arm64"); try equal(target["triple"], "arm64-apple-macosx26.0")
        _ = try blob(build["configuration"], scope: "build_configuration_bytes")
        let terms = try known(c["terms"], "references")
        let refs = try array(terms["references"])
        try require(!refs.isEmpty)
        for ref in refs { _ = try blob(ref, scope: "file_bytes") }
        try evidence(c["evidence"])
        let tools = try array(lock["toolchains"])
        try require(tools.count == 1)
        let tool = try object(tools[0], "toolchain_id version sdk")
        try equal(tool["toolchain_id"], "fixture-toolchain")
        _ = try string(tool["version"]); _ = try string(tool["sdk"])
        try host(known(lock["host_requirements"], "value")["value"])
        try equal(known(lock["signing_requirements"], "value")["value"], "development")
        try evidence(lock["evidence"])
    }
    func validate(_ path: String, trustedHash: String) throws -> LaunchInput {
        let request = try record(path, expectedKind: "launch")
        let q = try object(request, base + "variant run_id purpose lock artifact profile qualification roots prefix_family cache_identity entry_file_id observer_required configuration signing_scope")
        try equal(q["record_id"], "fixture.request"); try equal(q["variant"], "request")
        try equal(q["run_id"], "fixture-run")
        let purpose = try string(q["purpose"])
        try require(["fixture_launch", "qualification_run", "supported_launch"].contains(purpose))
        if purpose != "fixture_launch" { ineligible = true }
        try require(q["qualification"] == .null)
        let (lockPath, lock) = try reference(q["lock"], kind: "runtime_lock")
        try validateLock(lock)
        let (artifactPath, artifact) = try reference(q["artifact"], kind: "runtime_artifact")
        let a = try object(artifact, base + "lock compatibility_family abi translator_component files signing build_evidence")
        try equal(a["record_id"], "fixture.artifact")
        let (artifactLock, _) = try reference(a["lock"], kind: "runtime_lock")
        try require(artifactLock == lockPath && a["lock"] == q["lock"])
        try equal(a["compatibility_family"], "fixture-family"); try equal(a["abi"], "fixture-abi")
        try equal(a["translator_component"], "fixture-translator")
        let artifactFiles = try array(a["files"])
        try require(artifactFiles.count == 1)
        let file = try object(artifactFiles[0], "file_id content role format architecture")
        try equal(file["file_id"], "fixture-main"); try equal(file["role"], "host")
        try equal(file["format"], "mach_o"); try equal(file["architecture"], "arm64")
        let content = try object(file["content"], "ref_type path digest")
        let executablePath = try string(content["path"])
        try require(executablePath == "blobs/fixture-child")
        let executable = try blob(file["content"], scope: "file_bytes")
        let fileHash = sha256(executable.data)
        try require(fileHash == trustedHash)
        let signing = try object(a["signing"], "status scope payload_digests evidence")
        try equal(signing["status"], "passed"); try equal(signing["scope"], "development")
        try require(signing["payload_digests"] == .array([.string(fileHash)]))
        _ = try blob(signing["evidence"], scope: "evidence_json_bytes")
        try evidence(a["build_evidence"])
        let (profilePath, profile) = try reference(q["profile"], kind: "game_profile")
        let p = try object(profile, base + "store app_id game_build executable compatibility_family renderer arguments environment operations required_checks required_processes save_paths")
        try equal(p["record_id"], "fixture.profile"); try equal(p["store"], "fixture")
        try require(p["app_id"] == .integer(1))
        try equal(p["game_build"], "fixture-game"); try equal(p["compatibility_family"], "fixture-family")
        try equal(p["renderer"], "fixture-renderer")
        let guest = try object(p["executable"], "path_type path")
        try equal(guest["path_type"], "guest_relative"); try equal(guest["path"], "fixture.exe")
        try require(p["operations"] == .array([]))
        try require(p["required_checks"] == .array([.string("fixture-check")]))
        try require(p["required_processes"] == .array([.string("game")]))
        let saves = try array(p["save_paths"])
        try require(saves.count == 1)
        let save = try object(saves[0], "root path")
        try equal(save["root"], "saves"); try equal(save["path"], "game/save.dat")
        let args = try array(p["arguments"], max: 3).map { try string($0) }
        let modes = ["success", "args", "environment", "stdin", "nonzero", "signal", "delay", "excess_stdout", "excess_stderr", "malformed", "secret", "descendant_pipe"]
        try require(!args.isEmpty && modes.contains(args[0]))
        try require(args == (args[0] == "args" ? ["args", "value with spaces", "Unicode-λ-🍐"] : [args[0]]))
        let env = try array(p["environment"])
        var environment: [String] = []
        if args[0] == "environment" {
            try require(env.count == 1)
            let e = try object(env[0], "key value")
            try equal(e["key"], "PEAR_FIXTURE_VALUE"); try equal(e["value"], "allowed")
            environment = ["PEAR_FIXTURE_VALUE=allowed"]
        } else { try require(env.isEmpty) }
        let roots = try object(q["roots"], "runtime prefix saves cache logs")
        for name in ["runtime", "prefix", "saves", "cache", "logs"] { try equal(roots[name], "state/" + name) }
        try equal(q["prefix_family"], "fixture-family")
        let cache = try object(q["cache_identity"], "lock_digest artifact_digest profile_digest cpu_features translator_component abi")
        try equal(cache["lock_digest"], hashes[lockPath]!); try equal(cache["artifact_digest"], hashes[artifactPath]!)
        try equal(cache["profile_digest"], hashes[profilePath]!)
        try require(cache["cpu_features"] == .array([.string("fixture-capability")]))
        try equal(cache["translator_component"], "fixture-translator"); try equal(cache["abi"], "fixture-abi")
        try equal(q["entry_file_id"], "fixture-main"); try require(q["observer_required"] == .bool(true))
        let configuration = try object(q["configuration"], "host chip game_build steam_build renderer translator")
        try host(configuration["host"])
        try equal(configuration["chip"], "synthetic-arm64"); try equal(configuration["game_build"], "fixture-game")
        try equal(configuration["steam_build"], "fixture-steam"); try equal(configuration["renderer"], "fixture-renderer")
        try equal(configuration["translator"], "fixture-translator"); try equal(q["signing_scope"], "development")
        try require(records.count == 4)
        if ineligible { throw Failure.ineligible }
        return LaunchInput(files: files, executable: executable, executablePath: executablePath, arguments: args, environment: environment)
    }
}
