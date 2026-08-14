# v4 Data

Place downloaded datasets under `data/raw/<dataset>` and run the v4 converter
scripts from the project root. Generated unified tables are written to
`data/unified/` and are ignored by Git.

Raw datasets remain local and are intentionally not stored in the normal Git
repository. Keep their provenance/validation documentation and manifests in
Git, but do not commit raw UCI, UMAFall, or other research data.
