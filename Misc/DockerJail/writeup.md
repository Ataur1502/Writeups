## Challenge: dockerjail -  Writeup

Category: Misc
Difficulty: Easy

---

## Overview

Players are presented with a minimal embedded firmware-style interface exposed over TCP.

The environment:

* Is containerized
* Runs a static Rust binary
* Provides only three commands:

  * `ls`
  * `read <file>`
  * `exitdoor`

There is no shell access.
The container root filesystem is intentionally hidden.
The firmware root is locked to `/srv`.

---

## Intended Solution Path

### 1. Initial Enumeration

Upon connecting:

```
=== Embedded Recovery Interface ===
System Boot: OK
>
```

The first logical step is:

```
ls
```

Output:

```
boot
flash
nvram
logs
backup
partitions
core
```

This suggests a firmware-like partition layout.

---

### 2. Identifying Interesting Partition

In embedded systems, `nvram` commonly stores:

* Boot mode
* Device state
* Recovery keys
* Flags

So:

```
read nvram/device_state.dat
```

Output:

```
boot_mode=normal
firmware_version=1.3.7
recovery_flag=bpctf{history-is-truth}
```

The recovery key is directly exposed.

---

### 3. Recovery Mechanism

The `exitdoor` command prompts:

```
Enter recovery key:
```

Entering:

```
bpctf{history-is-truth}
```

Triggers SHA256 validation in the binary.

If hash matches:

```
Recovery Successful.
bpctf{history-is-truth}
```

The process exits.

---

## Why This Works

The Rust binary:

* Locks file access to `/srv`
* Prevents traversal outside firmware root
* Uses SHA256 to validate recovery key
* Provides no system shell
* Ignores unsupported commands

The flag is intentionally stored in:

```
/srv/nvram/device_state.dat
```

---

## Design Philosophy

This challenge tests:

* Calm enumeration
* Understanding firmware partition layouts
* Recognizing embedded storage conventions
* Not overthinking exploitation

It is deliberately:

* Brutal-looking
* Minimalist
* Non-exploitative
* Enumeration-focused

---

## Common Mistakes by Players

* Attempting path traversal (`../../`)
* Trying to spawn shell
* Attempting command injection
* Searching for container escape
* Overcomplicating the solution

The solution requires no exploitation.

---

## Final Flag

```
bpctf{history-is-truth}
```
