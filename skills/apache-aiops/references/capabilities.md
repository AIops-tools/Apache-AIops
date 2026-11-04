# Capabilities

Six Apache read tools: `apache_version`, `apache_config_check`, `apache_vhosts`, `apache_modules`, `apache_probe`, `apache_diagnose`. Two common governance tools: `undo_list`, `undo_apply`.

Unsupported in this slice: vhost editing, reload/restart, TLS certificate management, mod_status setup, log inspection and module changes. Request missing capabilities with an Apache version and real command output in an issue or PR.
