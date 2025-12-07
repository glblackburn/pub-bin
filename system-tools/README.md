# System Tools

System-level monitoring and event logging tools.

## Scripts

- `record-uptime.sh` - System uptime and load average
  - Records system uptime information using `uptime`
  - Output: `record-uptime_YYYY-MM-DD_HHMMSS.txt`
  - Options: `-h` for help
- `record-log-show.sh` - macOS login/logout events
  - Records macOS login/logout events from system logs using `log show`
  - Output: `~/log/log-show_YYYY-MM-DD_HHMMSS.log`
  - Options: `-h` for help
  - Note: macOS-specific (requires `log` command)

## Usage

### record-uptime.sh
Records system uptime information:
```bash
./system-tools/record-uptime.sh
```
Output: `record-uptime_YYYY-MM-DD_HHMMSS.txt`

### record-log-show.sh
Records macOS login/logout events from system logs:
```bash
./system-tools/record-log-show.sh
```
Output: `~/log/log-show_YYYY-MM-DD_HHMMSS.log`

Filters for screen unlock events: "LWScreenLock startUnlock" and "inform UA unlocked"
