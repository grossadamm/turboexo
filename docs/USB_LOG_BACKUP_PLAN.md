# USB datalog backup plan (Pi)

Status: **planned, not implemented**. The USB drive must be plugged into the Pi
before implementation so its filesystem, UUID, contents, and usable space can be
verified. Do not format or erase it without explicit approval.

## Objective

Automatically copy every completed TSDash `.mlg` from:

`/home/dietpi/TSDashProjects/TurboExo_2026-06-01_21.16.20/DataLogs/`

to a disposable USB drive. The Pi remains the primary log location; the USB holds
a second copy. A missing, failed, full, read-only, or incorrectly mounted USB drive
must never block TSDash, live logging, or boot.

## Architecture

Use a short, idempotent systemd **oneshot service** started by a timer every 30
seconds. Do not run a permanent polling shell process and do not depend on TSDash
actions or `inotify-tools`.

The USB drive has a fixed mount point:

`/mnt/turbologs`

Mount it by filesystem UUID using a systemd automount generated from `/etc/fstab`.
Use `nofail`, `x-systemd.automount`, and a short device timeout so:

- boot succeeds with no USB drive;
- accessing `/mnt/turbologs` mounts a drive inserted after boot;
- removal and reinsertion can recover without restarting TSDash;
- the copy service remains completely outside TSDash's boot dependency chain.

Before every write, the copy program must use `findmnt`/`blkid` to verify all of
the following:

1. `/mnt/turbologs` is a separate mounted filesystem, not an ordinary directory
   on the SD card;
2. the mounted block device has the configured filesystem UUID;
3. the destination directory is writable;
4. a small marker file on the drive contains the expected TurboExo backup ID.

If any check fails, exit successfully after one rate-limited state-change message.
Never fall through and write into the bare mount-point directory.

## Filesystem decision

Inspect the drive before choosing or changing its filesystem:

- **exFAT:** preferred if the drive must plug directly into the Mac. It is broadly
  readable but less resilient to abrupt power loss than ext4.
- **ext4:** preferred for resilience on the Pi, but macOS cannot read it natively.
- **FAT32:** Mac-readable but has a 4 GiB per-file limit. Current `.mlg` files are
  much smaller, but this remains a hard limit.

Do not promise crash-proof storage on any disposable USB stick. Atomic rename and
explicit sync reduce exposure but cannot protect against the stick's controller or
filesystem being corrupted by sudden automotive power loss.

For FAT32/exFAT, mount with explicit `uid=dietpi`, `gid=dietpi`, and conservative
`umask` options. Copy file contents and modification times only; do not attempt to
preserve Unix ownership, mode bits, ACLs, or extended attributes that those
filesystems do not support.

## Determining that a log is closed

File stability alone is insufficient: a live log can pause for 30 seconds and
resume. A source `.mlg` is eligible only when all of these are true:

1. It is a regular file, ends in `.mlg`, and is at least 1 byte.
2. Its inode, size, and nanosecond modification time are unchanged from the
   preceding timer pass (at least 30 seconds stable).
3. No live TSDash/Java process has the file open. Inspect `/proc/<pid>/fd/` for
   every process matching the actual TSDash command, resolving descriptor links
   to the same device and inode. Do not rely on filenames alone.

`lsof`/`fuser` may be used for diagnostics, but the implementation should use
`/proc` so no package installation is required. If process inspection is
inconclusive because of permissions or races, treat the file as open and retry on
the next pass.

A truncated file left behind by a TSDash crash or ECU disconnect becomes eligible
once it is stable and no process holds it open. Preserve that partial evidence.

## Race-safe copy and verification

For each eligible source:

1. Acquire a non-blocking `flock` so only one copy pass can operate.
2. Record source device, inode, size, and nanosecond mtime (`stat_before`).
3. Recheck that TSDash does not have that device/inode open.
4. Copy into a hidden temporary file on the USB filesystem, for example
   `.2026-08-18_12.34.56.mlg.partial`. Resume or replace a stale partial safely.
5. Record the source metadata again (`stat_after_copy`). If any field differs from
   `stat_before`, discard/restart the candidate later; do not finalize it.
6. Calculate SHA-256 for the source and temporary destination.
7. Record source metadata a third time (`stat_after_hash`). Finalize only if all
   three metadata snapshots match and both hashes match.
8. Select the final name. If that name exists, compare hashes—not just sizes. An
   identical file is already backed up; a different file receives a deterministic
   suffix such as `__dup-2.mlg` and emits a collision warning.
9. Rename the temporary file to the final `.mlg` name on the same USB filesystem.
   This rename is atomic from the filesystem's point of view.
10. Flush the destination file and containing filesystem with `sync -f` before
    reporting success.

Never delete, rename, truncate, or otherwise modify the source log.

An interrupted copy must remain under a `.partial` name and must never be mistaken
for a completed `.mlg`. On the next pass, reuse it only if doing so is safe;
otherwise replace it.

## Revalidation after reboot or unsafe removal

Atomic rename does not guarantee durable data through power loss, particularly on
FAT/exFAT and low-cost USB controllers. The runtime state directory disappears on
every boot, which deliberately triggers a full reconciliation:

- compare every source `.mlg` with the corresponding final USB file by hash;
- recopy missing or corrupt destinations;
- retain and report same-name/different-content collisions;
- clean or resume stale `.partial` files only after their source is identified.

The same full reconciliation must happen after the expected USB UUID disappears
and later returns. Thus a copy reported before an unsafe removal is not trusted
forever merely because its filename exists.

## Runtime state and write control

Keep observations, lock files, and rate-limit state only under:

`/run/turboexo-log-copy/`

`/run` is tmpfs, so polling does not add SD-card writes. Successful-copy state does
not need to persist: destination hashes are authoritative and reboot intentionally
causes reconciliation.

Log only state transitions and material events:

- USB became available/unavailable or failed validation;
- copy succeeded;
- verification failed and will retry;
- collision, full/read-only media, or corrupt prior copy;
- reconciliation started/completed.

Do not log every timer tick or repeated absence. Journald on this DietPi is already
RAM-backed, but bounded logs are still required.

## Files to add during implementation

Version-controlled in this repository:

- `scripts/pi/copy-closed-logs.sh` — one idempotent scan/copy/reconcile pass;
- `scripts/pi/turboexo-log-copy.service` — hardened oneshot unit;
- `scripts/pi/turboexo-log-copy.timer` — 30-second timer with randomized delay
  disabled so closure timing is predictable;
- optionally `scripts/pi/install-log-copy.sh` — validates and installs the selected
  UUID without formatting the drive.

Installed on the Pi:

- `/usr/local/libexec/turboexo-copy-closed-logs`;
- `/etc/systemd/system/turboexo-log-copy.service`;
- `/etc/systemd/system/turboexo-log-copy.timer`;
- one UUID-specific `/etc/fstab` automount entry for `/mnt/turbologs`;
- `/mnt/turbologs/.turboexo-log-backup-id` on the USB drive.

The service runs as `dietpi`, has no network access, uses low CPU/I/O priority, and
has narrowly scoped read/write paths. Its failure must not affect TSDash or the
graphical session.

## Implementation sequence

1. Plug in one disposable USB drive.
2. Record `lsblk -f`, `blkid`, filesystem UUID/type, capacity, existing contents,
   current mount state, and USB device identity. Do not modify it yet.
3. Choose exFAT, ext4, or FAT32 based on whether direct Mac readability is needed.
   Obtain explicit approval before any format/erase operation.
4. Mount it manually at `/mnt/turbologs` and test write, read, rename, SHA-256, sync,
   and clean unmount behavior.
5. Add the marker ID and UUID-specific `fstab` automount entry. Validate that the
   mounted UUID and marker are both rejected when wrong.
6. Verify access with the drive present, absent, inserted after boot, removed, and
   reinserted. Confirm no operation writes to the bare mount-point directory.
7. Implement the copy script, oneshot service, and timer. Run a shell syntax/static
   check and inspect the systemd units with `systemd-analyze verify`.
8. Run a dry scan and review exactly which existing logs would be backfilled.
9. Enable the timer and perform the initial reconciliation.
10. Test an actively growing file and an open-but-paused file. Neither may finalize
    while TSDash/Java holds the matching inode open.
11. Test source growth during copying; metadata/hash checks must prevent finalization.
12. Test stale partials, identical existing copies, same-size/different-content
    collisions, full/read-only media, wrong UUID/marker, and concurrent invocations.
13. Simulate interruption at copy, hash, rename, and sync stages, then restart the
    service and confirm safe recovery. Where practical, test unsafe USB removal;
    never intentionally cut Pi power while modifying the SD card.
14. Reboot once with the USB attached and once without it. Confirm TSDash starts,
    its project opens, logging arms, and the USB units cannot delay/fail dash boot.
15. With the ECU later connected, verify a real `.mlg` remains untouched while
    open and appears on USB within 60–90 seconds after TSDash closes it.

## Operational checks

```bash
systemctl status turboexo-log-copy.timer turboexo-log-copy.service
journalctl -u turboexo-log-copy.service -n 50 --no-pager
findmnt /mnt/turbologs
ls -lh /mnt/turbologs/TurboExo/DataLogs/
```

Before removing the USB drive, either power down the Pi or stop the timer and
unmount cleanly:

```bash
sudo systemctl stop turboexo-log-copy.timer
sudo umount /mnt/turbologs
```

Restart the timer after reinsertion if it was manually stopped. The explicit sync
reduces risk after a reported successful copy, but clean unmounting remains the
rule.

## Acceptance criteria

- TSDash boot and live logging work whether the USB is present or absent.
- The configured UUID and marker are required; wrong media is never written.
- An open `.mlg`, including an open-but-paused one, is never finalized on USB.
- A closed, stable, non-empty `.mlg` is copied within 60–90 seconds.
- Source metadata remains unchanged throughout copy/hash verification.
- Every finalized destination matches the source by SHA-256.
- Source logs are never deleted or altered.
- Missing/corrupt copies backfill after boot or USB reinsertion.
- Interrupted copies never appear under a final `.mlg` filename.
- USB absence and recurring errors produce bounded, state-change-only logs.
- Timer state and observation data remain in tmpfs and create no periodic SD writes.
