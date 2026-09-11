#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

if len(sys.argv) != 2:
    raise SystemExit("usage: patch_directive_activitythread_abort.py PROJECT_ROOT")

root = Path(sys.argv[1]).resolve()
path = root / "smali_classes4/com/ticktick/task/utils/ActivityThreadCallback.smali"
if not path.is_file():
    raise SystemExit(f"required ActivityThreadCallback missing: {path}")

src = path.read_text(encoding="utf-8")
method_rx = re.compile(
    r"(?P<head>\.method private static abort\(Ljava/lang/Throwable;\)Z\n)(?P<body>.*?)(?P<tail>^\.end method)",
    re.M | re.S,
)
m = method_rx.search(src)
if not m:
    raise SystemExit("ActivityThreadCallback.abort(Throwable) not found")

body = m.group("body")
kill = "invoke-static {v0}, Landroid/os/Process;->killProcess(I)V"
exit_call = "invoke-static {p0}, Ljava/lang/System;->exit(I)V"
if body.count(kill) != 1 or body.count(exit_call) != 1:
    raise SystemExit(
        f"unexpected abort contract: killProcess={body.count(kill)} System.exit={body.count(exit_call)}"
    )

# This callback is installed during Application startup to absorb a small set of framework-side
# ActivityThread/Handler exceptions after rethrowIfCausedByUser() has already protected genuine
# app/user-code failures. The inherited abort() implementation logs the framework exception and
# then deliberately kills the process twice (killProcess + System.exit). On newer Android this
# converts a compatibility exception that the callback chose to consume into an immediate app
# closure. Preserve the logging and boolean 'handled' result, but remove only those deliberate
# process-termination calls. Do not alter the user-code rethrow checks at the call sites.
block_rx = re.compile(
    r"\n\s*:goto_0\n"
    r"\s*invoke-static \{v0\}, Landroid/os/Process;->killProcess\(I\)V\n"
    r"(?:\s*\.line[^\n]*\n|\s*)*"
    r"\s*const/16 p0, 0xa\n"
    r"(?:\s*\.line[^\n]*\n|\s*)*"
    r"\s*invoke-static \{p0\}, Ljava/lang/System;->exit\(I\)V\n"
    r"(?:\s*\.line[^\n]*\n|\s*)*"
    r"\s*const/4 p0, 0x1\n"
    r"(?:\s*\.line[^\n]*\n|\s*)*"
    r"\s*return p0\n",
    re.M,
)
replacement = "\n    :goto_0\n    # DIRECTIVE Android compatibility: framework exception was selected for suppression.\n    # Keep the process alive instead of deliberately terminating it.\n    const/4 p0, 0x1\n    return p0\n"
patched_body, count = block_rx.subn(replacement, body, count=1)
if count != 1:
    raise SystemExit("could not match exact ActivityThreadCallback abort termination block")
if "Landroid/os/Process;->killProcess(I)V" in patched_body:
    raise SystemExit("killProcess remains in ActivityThreadCallback.abort after remediation")
if "Ljava/lang/System;->exit(I)V" in patched_body:
    raise SystemExit("System.exit remains in ActivityThreadCallback.abort after remediation")

patched = src[: m.start("body")] + patched_body + src[m.end("body") :]
path.write_text(patched, encoding="utf-8")

# Verify the caller-side truth boundary is unchanged: app/user-caused exceptions are still
# explicitly passed through rethrowIfCausedByUser before framework-only abort/suppression paths.
caller_guard_count = patched.count("Lcom/ticktick/task/utils/ActivityThreadCallback;->rethrowIfCausedByUser")
abort_call_count = patched.count("Lcom/ticktick/task/utils/ActivityThreadCallback;->abort(Ljava/lang/Throwable;)Z")
if caller_guard_count < 1 or abort_call_count < 1:
    raise SystemExit(
        f"caller guard contract missing: rethrowIfCausedByUser={caller_guard_count} abortCalls={abort_call_count}"
    )

report = {
    "status": "PASS",
    "file": str(path.relative_to(root)),
    "method": "ActivityThreadCallback.abort(Throwable)",
    "framework_exception_process_kill_removed": True,
    "framework_exception_system_exit_removed": True,
    "framework_exception_logging_preserved": True,
    "framework_exception_handled_result_preserved": True,
    "user_code_rethrow_checks_preserved": True,
    "caller_rethrow_guard_count": caller_guard_count,
    "caller_abort_call_count": abort_call_count,
    "authentication_licensing_premium_entitlement_logic_changed": False,
    "offline_network_permission_boundary_changed": False,
    "inherited_ticktick_class_namespace_preserved": True,
    "purpose": "prevent deliberate process termination after framework-only ActivityThread compatibility exceptions"
}
out = root / "DIRECTIVE_ACTIVITYTHREAD_ABORT_REMEDIATION_REPORT.json"
out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print(json.dumps(report, sort_keys=True))
