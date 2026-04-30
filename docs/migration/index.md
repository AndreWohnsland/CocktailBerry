# Migration Guides

When a major version of CocktailBerry is released (e.g. `v2.9.0` → `v3.0.0`), it usually contains breaking changes that cannot all be migrated automatically. This page explains the general approach; per-version steps live in the subpages.

## Recommended path: backup + fresh install

The safest and lowest-effort upgrade path:

1. **Back up your data** — at minimum, the cocktail database and your `custom_config.yaml`.
2. **Reinstall the latest Raspberry Pi OS from scratch** (not an in-place upgrade).
3. **Install the latest CocktailBerry** using the standard installer.
4. **Restore your backup** through the in-app restore flow.

In-place OS upgrades work for some users but tend to produce hard-to-debug edge cases. If you don't already know how to fix a broken in-place upgrade, do the fresh install.

## Auto-migration of `custom_config.yaml`

Most config-shape changes between major versions are handled by the migrator on the first start of the new version. Before any change is applied, the migrator writes a snapshot of your config to:

```bash
~/cb_backup/custom_config_pre_<version>.yaml
```

If the migration goes wrong, restore that file:

```bash
cp ~/cb_backup/custom_config_pre_<version>.yaml ~/CocktailBerry/custom_config.yaml
```

Then pin your install to the previous tag (`git checkout <previous-version>`) and open an issue with the contents of the backup.

## Database backups

Database migrations also create a dated backup before any modifying step. To restore:

```bash
cp Cocktail_database_backup-{date}.db Cocktail_database.db
```

Check the production log to confirm a backup was created for the migration step you want to undo, otherwise you may roll back further than expected.

## Per-version migration notes

- [v3 update](v3.md) — NFC payment integration, PyQt5 → PyQt6.
- [v4 update](v4.md) — Hardware extension system, scale support, new dependency installer step.
