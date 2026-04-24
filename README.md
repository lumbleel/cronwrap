# cronwrap

A lightweight wrapper for cron jobs that adds logging, alerting, and retry logic via a simple config file.

---

## Installation

```bash
pip install cronwrap
```

Or install from source:

```bash
git clone https://github.com/yourname/cronwrap.git && cd cronwrap && pip install .
```

---

## Usage

Define your jobs in a `cronwrap.yaml` config file:

```yaml
jobs:
  backup:
    command: "/usr/local/bin/backup.sh"
    retries: 3
    alert_on_failure: true
    log: "/var/log/cronwrap/backup.log"
```

Then invoke it from your crontab:

```
0 2 * * * cronwrap run backup
```

cronwrap will:
- **Log** stdout/stderr output to the specified log file
- **Retry** the command up to the configured number of times on failure
- **Alert** via email or webhook if the job ultimately fails

### CLI Reference

```bash
cronwrap run <job_name>          # Run a configured job
cronwrap list                    # List all configured jobs
cronwrap logs <job_name>         # Tail logs for a job
```

### Environment Variables

| Variable | Description |
|---|---|
| `CRONWRAP_CONFIG` | Path to config file (default: `./cronwrap.yaml`) |
| `CRONWRAP_ALERT_EMAIL` | Email address for failure alerts |
| `CRONWRAP_WEBHOOK_URL` | Webhook URL for failure notifications |

---

## License

This project is licensed under the [MIT License](LICENSE).