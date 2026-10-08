//! The approved v2 setting subset; paths and values never become shell commands.
use crate::{
    fs::{self, Error, Result, Root, require},
    json::J,
    state,
};
use std::collections::BTreeMap;

pub fn validate(profile: &J) -> Result<()> {
    let operations = profile.get("operations")?.a()?;
    require(
        operations.is_empty() || profile.get("schema_version")?.i()? == 2,
        "unsupported_operations",
    )?;
    require(operations.len() <= 1, "unsupported_operations")?;
    for operation in operations {
        require(
            operation.get("operation")?.s()? == "set_setting"
                && operation.get("root")?.s()? == "prefix"
                && operation.get("path")?.s()? == "config/options.json"
                && operation.get("key")?.s()? == "fixture_flag"
                && matches!(operation.get("value")?, J::Bool(_)),
            "unsupported_operations",
        )?;
    }
    if profile.get("schema_version")?.i()? == 2 {
        require(
            profile.get("save_inventory_status")?.get("status")?.s()? == "known",
            "save_mapping_incomplete",
        )?;
        for observation in profile.get("path_observations")?.a()? {
            require(
                observation.get("kind")?.s()? != "saves"
                    || observation.get("status")?.s()? == "observed",
                "save_mapping_incomplete",
            )?;
        }
    }
    require(
        !profile.get("save_paths")?.a()?.is_empty(),
        "save_mapping_incomplete",
    )?;
    for path in profile.get("save_paths")?.a()? {
        require(path.get("root")?.s()? == "saves", "save_mapping_incomplete")?;
        fs::relative(path.get("path")?.s()?)?;
    }
    Ok(())
}
pub fn apply(root: &Root, request: &J, profile: &J) -> Result<()> {
    validate(profile)?;
    let prefix = Root {
        file: root.directory(request.get("roots")?.get("prefix")?.s()?)?,
    };
    for operation in profile.get("operations")?.a()? {
        state::mkdirs(&prefix, "config")?;
        let mut settings = match prefix.json("config/options.json") {
            Ok(value) => value,
            Err(error) if error.errno == Some(libc::ENOENT) => J::Obj(BTreeMap::new()),
            Err(error) => return Err(error),
        };
        let J::Obj(fields) = &mut settings else {
            return Err(Error::code("invalid_settings"));
        };
        fields.insert("fixture_flag".into(), operation.get("value")?.clone());
        state::write_json(&prefix, "config/options.json", &settings)?;
    }
    Ok(())
}

pub(crate) fn check(root: &Root, request: &J, profile: &J) -> Result<()> {
    let prefix = Root {
        file: root.directory(request.get("roots")?.get("prefix")?.s()?)?,
    };
    for operation in profile.get("operations")?.a()? {
        require(
            prefix.json("config/options.json")?.get("fixture_flag")? == operation.get("value")?,
            "settings_changed",
        )?;
    }
    Ok(())
}
