# schemadrift

Detects and reports schema changes across versioned data sources over time.

---

## Installation

```bash
pip install schemadrift
```

---

## Usage

Compare schemas across versions of your data sources and get a clear report of what changed.

```python
from schemadrift import SchemaDrift

drift = SchemaDrift()

# Register two versions of a schema
drift.register("users_v1", "path/to/users_v1.json")
drift.register("users_v2", "path/to/users_v2.json")

# Detect and report changes
report = drift.compare("users_v1", "users_v2")
print(report.summary())
# Output:
# [+] Added columns: email_verified (bool)
# [-] Removed columns: legacy_id (int)
# [~] Modified columns: created_at (str -> datetime)
```

You can also run it from the command line:

```bash
schemadrift compare users_v1.json users_v2.json
```

---

## Features

- Detects added, removed, and modified fields
- Supports JSON, CSV, Parquet, and SQL schemas
- Version history tracking over time
- Human-readable and machine-readable reports

---

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

---

## License

This project is licensed under the [MIT License](LICENSE).