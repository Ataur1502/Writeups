# RustyFrame --- Alternative Solve (Environment Variable Abuse Path)

## 1. Binary Characteristics

    file rusty_frame
    checksec rusty_frame

-   ELF 64-bit LSB PIE executable
-   NX enabled
-   No stack canary
-   Partial RELRO
-   Stripped

PIE implies runtime base randomization. NX eliminates shellcode
injection. Absence of canary suggests potential stack exploitation, but
this solve path uses a logic-level bypass.

------------------------------------------------------------------------

## 2. Initial Static Recon

    strings rusty_frame
    nm -C rusty_frame
    objdump -d rusty_frame

`nm` reveals no symbols (stripped). `strings` does not reveal obvious
flag or success strings.

Binary size is small → suggests minimal logic, likely branch-gated.

------------------------------------------------------------------------

## 3. Disassembly & Control Flow Mapping

Loaded into Ghidra.

High-level flow:

    main()
     └── initialize()
     └── read_input()
     └── process()
     └── conditional_gate()
     └── win()  (only if condition satisfied)

Primary logic resides inside a function that checks runtime state before
invoking `win()`.

------------------------------------------------------------------------

## 4. Identifying External State Dependency

Search for libc calls:

-   `read`
-   `strcmp`
-   `getenv`

Cross-reference `getenv`.

Disassembly reveals:

``` asm
call getenv
test rax, rax
je  <fail_path>

mov rdi, rax
lea rsi, [rip + offset_to_string]
call strcmp
test eax, eax
jne <fail_path>

call win
```

This sequence implies:

1.  Retrieve environment variable.
2.  If NULL → fail path.
3.  Compare with constant string.
4.  If match → call `win()`.

------------------------------------------------------------------------

## 5. Recovering the Environment Variable Name

Inspect argument passed to `getenv`.

Example snippet:

``` asm
lea rdi, [rip + 0x200a]   ; pointer to "RUSTY_WIN"
call getenv
```

Examining `.rodata` confirms:

    52 55 53 54 59 5f 57 49 4e 00
    "RUSTY_WIN"

------------------------------------------------------------------------

## 6. Recovering the Expected Value

Immediately after `getenv`:

``` asm
mov rdi, rax
lea rsi, [rip + 0x2015]   ; pointer to "1"
call strcmp
```

`.rodata` shows:

    31 00
    "1"

So the branch condition is:

    if getenv("RUSTY_WIN") != NULL &&
       strcmp(value, "1") == 0:
           win();

------------------------------------------------------------------------

## 7. Verifying Runtime Behavior

Without environment variable:

    ./rusty_frame

Program exits silently or follows normal failure path.

With environment variable:

    RUSTY_WIN=1 ./rusty_frame

Execution immediately enters success branch.

------------------------------------------------------------------------

## 8. win() Function Analysis

Disassembly of `win()`:

``` asm
lea rsi, [rip + encoded_flag]
mov ecx, length
mov al, xor_key
loop:
    xor byte ptr [rsi], al
    inc rsi
    loop
call puts
```

Observations:

-   Flag stored encoded in `.rodata`
-   XOR-based decode at runtime
-   No further validation checks
-   No stack-dependent gating

Once branch condition satisfied, flag always printed.

------------------------------------------------------------------------

## 9. Why This Path Exists

Likely causes:

1.  Debug/developer backdoor.
2.  Alternate intended solve path.
3.  Testing hook left in release build.
4.  Intentional misdirection against overflow solvers.

Because the binary is stripped and small, the presence of `getenv` is a
critical anomaly.

------------------------------------------------------------------------

## 10. Exploit Summary

Technique:

    Static analysis → Locate getenv check → Identify required key/value → Set environment variable → Direct win() execution

Final exploit command:

    RUSTY_WIN=1 ./rusty_frame

------------------------------------------------------------------------

## 11. Security Implications

This demonstrates:

-   Environment variables are trusted implicitly.
-   Hidden debug paths can invalidate intended exploitation routes.
-   Static reversing often reveals logic bypasses superior to memory
    corruption.

------------------------------------------------------------------------

## 12. Final Result

Execution enters `win()` without:

-   Stack overflow
-   Partial RIP overwrite
-   ROP
-   Shellcode

Pure logic-level exploitation.

------------------------------------------------------------------------

## Exploit Class

Environment Variable Abuse → Logic Gate Bypass → Direct Code Execution
Path
