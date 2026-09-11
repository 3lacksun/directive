#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

if len(sys.argv) != 3:
    raise SystemExit("usage: patch_directive_d5_diagnostic_runtime.py PROJECT_ROOT TARGET_PACKAGE")

root = Path(sys.argv[1]).resolve()
target = sys.argv[2].strip()
if not root.is_dir():
    raise SystemExit(f"missing project root: {root}")
if not re.fullmatch(r"com\.directive\.v\d+", target):
    raise SystemExit(f"unexpected target package: {target}")

manifest = root / "AndroidManifest.xml"
if not manifest.is_file():
    raise SystemExit("AndroidManifest.xml missing")

text = manifest.read_text(encoding="utf-8", errors="strict")
old_app = 'android:name="com.ticktick.task.TickTickApplication"'
new_app = 'android:name="com.directive.runtime.DirectiveDiagnosticApplication"'
if text.count(old_app) != 1:
    raise SystemExit(f"expected exactly one inherited application class, found {text.count(old_app)}")
text = text.replace(old_app, new_app, 1)

# Disable every inherited launcher alias. The diagnostic launcher is direct, package-owned,
# and intentionally avoids any runtime alias enable/disable code path while we capture startup.
alias_rx = re.compile(
    r'(<activity-alias\b[^>]*\bandroid:name="com\.ticktick\.task\.HomeAlia_[^"]+"[^>]*)(/?>)',
    re.S,
)
disabled = 0

def disable_alias(m: re.Match[str]) -> str:
    global disabled
    head, tail = m.group(1), m.group(2)
    if 'android:enabled=' in head:
        head = re.sub(r'android:enabled="[^"]+"', 'android:enabled="false"', head, count=1)
    else:
        head += ' android:enabled="false"'
    disabled += 1
    return head + tail

text = alias_rx.sub(disable_alias, text)
if disabled < 1:
    raise SystemExit("no inherited HomeAlia_* launcher aliases found")

application_close = text.rfind("</application>")
if application_close < 0:
    raise SystemExit("</application> missing")

diag_activity = """
        <activity
            android:name="com.directive.runtime.DirectiveDiagnosticActivity"
            android:exported="true"
            android:label="DIRECTIVE 5"
            android:theme="@android:style/Theme.Material.Light.NoActionBar">
            <intent-filter>
                <action android:name="android.intent.action.MAIN"/>
                <category android:name="android.intent.category.LAUNCHER"/>
            </intent-filter>
        </activity>
"""
if "com.directive.runtime.DirectiveDiagnosticActivity" in text:
    raise SystemExit("diagnostic launcher already declared")
text = text[:application_close] + diag_activity + text[application_close:]
manifest.write_text(text, encoding="utf-8")

diag_dir = root / "smali/com/directive/runtime"
diag_dir.mkdir(parents=True, exist_ok=True)

app_smali = r'''.class public Lcom/directive/runtime/DirectiveDiagnosticApplication;
.super Lcom/ticktick/task/TickTickApplication;
.source "DirectiveDiagnosticApplication.java"

.field private static volatile startupError:Ljava/lang/String;

.field private static instance:Landroid/content/Context;


.method public constructor <init>()V
    .locals 0

    invoke-direct {p0}, Lcom/ticktick/task/TickTickApplication;-><init>()V

    return-void
.end method

.method public onCreate()V
    .locals 1

    sput-object p0, Lcom/directive/runtime/DirectiveDiagnosticApplication;->instance:Landroid/content/Context;

    :try_start
    invoke-super {p0}, Lcom/ticktick/task/TickTickApplication;->onCreate()V
    :try_end
    .catch Ljava/lang/Throwable; {:try_start .. :try_end} :catch_all

    return-void

    :catch_all
    move-exception v0

    invoke-static {v0}, Lcom/directive/runtime/DirectiveDiagnosticApplication;->recordThrowable(Ljava/lang/Throwable;)V

    return-void
.end method

.method public static recordThrowable(Ljava/lang/Throwable;)V
    .locals 7

    new-instance v0, Ljava/io/StringWriter;
    invoke-direct {v0}, Ljava/io/StringWriter;-><init>()V

    new-instance v1, Ljava/io/PrintWriter;
    invoke-direct {v1, v0}, Ljava/io/PrintWriter;-><init>(Ljava/io/Writer;)V

    if-eqz p0, :no_throwable
    invoke-virtual {p0, v1}, Ljava/lang/Throwable;->printStackTrace(Ljava/io/PrintWriter;)V
    goto :after_trace

    :no_throwable
    const-string v2, "DIRECTIVE diagnostic received null Throwable"
    invoke-virtual {v1, v2}, Ljava/io/PrintWriter;->println(Ljava/lang/String;)V

    :after_trace
    invoke-virtual {v1}, Ljava/io/PrintWriter;->flush()V
    invoke-virtual {v0}, Ljava/io/StringWriter;->toString()Ljava/lang/String;
    move-result-object v2

    sput-object v2, Lcom/directive/runtime/DirectiveDiagnosticApplication;->startupError:Ljava/lang/String;

    const-string v3, "DIRECTIVE_DIAG"
    invoke-static {v3, v2, p0}, Landroid/util/Log;->e(Ljava/lang/String;Ljava/lang/String;Ljava/lang/Throwable;)I

    sget-object v4, Lcom/directive/runtime/DirectiveDiagnosticApplication;->instance:Landroid/content/Context;
    if-eqz v4, :return_now

    :pref_try_start
    const-string v5, "directive_runtime_diag"
    const/4 v6, 0x0
    invoke-virtual {v4, v5, v6}, Landroid/content/Context;->getSharedPreferences(Ljava/lang/String;I)Landroid/content/SharedPreferences;
    move-result-object v4
    invoke-interface {v4}, Landroid/content/SharedPreferences;->edit()Landroid/content/SharedPreferences$Editor;
    move-result-object v4
    const-string v5, "startup_failure"
    invoke-interface {v4, v5, v2}, Landroid/content/SharedPreferences$Editor;->putString(Ljava/lang/String;Ljava/lang/String;)Landroid/content/SharedPreferences$Editor;
    move-result-object v4
    invoke-interface {v4}, Landroid/content/SharedPreferences$Editor;->apply()V
    :pref_try_end
    .catch Ljava/lang/Throwable; {:pref_try_start .. :pref_try_end} :pref_catch

    :return_now
    return-void

    :pref_catch
    move-exception v4
    goto :return_now
.end method

.method public static getStartupError(Landroid/content/Context;)Ljava/lang/String;
    .locals 3

    sget-object v0, Lcom/directive/runtime/DirectiveDiagnosticApplication;->startupError:Ljava/lang/String;
    if-eqz v0, :read_pref
    return-object v0

    :read_pref
    if-eqz p0, :none

    :try_start
    const-string v0, "directive_runtime_diag"
    const/4 v1, 0x0
    invoke-virtual {p0, v0, v1}, Landroid/content/Context;->getSharedPreferences(Ljava/lang/String;I)Landroid/content/SharedPreferences;
    move-result-object v0
    const-string v1, "startup_failure"
    const/4 v2, 0x0
    invoke-interface {v0, v1, v2}, Landroid/content/SharedPreferences;->getString(Ljava/lang/String;Ljava/lang/String;)Ljava/lang/String;
    move-result-object v0
    return-object v0
    :try_end
    .catch Ljava/lang/Throwable; {:try_start .. :try_end} :catch_all

    :catch_all
    move-exception v0

    :none
    const/4 v0, 0x0
    return-object v0
.end method
'''
(diag_dir / "DirectiveDiagnosticApplication.smali").write_text(app_smali, encoding="utf-8")

activity_smali = r'''.class public Lcom/directive/runtime/DirectiveDiagnosticActivity;
.super Landroid/app/Activity;
.source "DirectiveDiagnosticActivity.java"

.field private launched:Z

.field private text:Landroid/widget/TextView;


.method public constructor <init>()V
    .locals 0
    invoke-direct {p0}, Landroid/app/Activity;-><init>()V
    return-void
.end method

.method protected onCreate(Landroid/os/Bundle;)V
    .locals 4

    invoke-super {p0, p1}, Landroid/app/Activity;->onCreate(Landroid/os/Bundle;)V

    new-instance v0, Landroid/widget/ScrollView;
    invoke-direct {v0, p0}, Landroid/widget/ScrollView;-><init>(Landroid/content/Context;)V

    new-instance v1, Landroid/widget/TextView;
    invoke-direct {v1, p0}, Landroid/widget/TextView;-><init>(Landroid/content/Context;)V
    iput-object v1, p0, Lcom/directive/runtime/DirectiveDiagnosticActivity;->text:Landroid/widget/TextView;

    const/16 v2, 0x2c
    invoke-virtual {v1, v2, v2, v2, v2}, Landroid/widget/TextView;->setPadding(IIII)V

    const/high16 v2, 0x41800000    # 16.0f
    invoke-virtual {v1, v2}, Landroid/widget/TextView;->setTextSize(F)V

    const/4 v2, 0x1
    invoke-virtual {v1, v2}, Landroid/widget/TextView;->setTextIsSelectable(Z)V

    invoke-virtual {v0, v1}, Landroid/widget/ScrollView;->addView(Landroid/view/View;)V
    invoke-virtual {p0, v0}, Landroid/app/Activity;->setContentView(Landroid/view/View;)V

    invoke-direct {p0}, Lcom/directive/runtime/DirectiveDiagnosticActivity;->refresh()V
    return-void
.end method

.method protected onResume()V
    .locals 0
    invoke-super {p0}, Landroid/app/Activity;->onResume()V
    invoke-direct {p0}, Lcom/directive/runtime/DirectiveDiagnosticActivity;->refresh()V
    return-void
.end method

.method private refresh()V
    .locals 6

    invoke-static {p0}, Lcom/directive/runtime/DirectiveDiagnosticApplication;->getStartupError(Landroid/content/Context;)Ljava/lang/String;
    move-result-object v0

    iget-object v1, p0, Lcom/directive/runtime/DirectiveDiagnosticActivity;->text:Landroid/widget/TextView;
    if-nez v1, :have_view
    return-void

    :have_view
    if-eqz v0, :no_error

    new-instance v2, Ljava/lang/StringBuilder;
    invoke-direct {v2}, Ljava/lang/StringBuilder;-><init>()V
    const-string v3, "DIRECTIVE 5 startup failure captured\n\n"
    invoke-virtual {v2, v3}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    invoke-virtual {v2, v0}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    invoke-virtual {v2}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;
    move-result-object v2
    invoke-virtual {v1, v2}, Landroid/widget/TextView;->setText(Ljava/lang/CharSequence;)V
    return-void

    :no_error
    iget-boolean v2, p0, Lcom/directive/runtime/DirectiveDiagnosticActivity;->launched:Z
    if-nez v2, :waiting

    const/4 v2, 0x1
    iput-boolean v2, p0, Lcom/directive/runtime/DirectiveDiagnosticActivity;->launched:Z

    const-string v2, "DIRECTIVE 5 diagnostic startup\n\nNo Application exception has been captured yet.\nLaunching inherited task surface now.\n\nIf it returns here, this screen will display the captured failure."
    invoke-virtual {v1, v2}, Landroid/widget/TextView;->setText(Ljava/lang/CharSequence;)V

    :launch_try_start
    new-instance v2, Landroid/content/Intent;
    invoke-direct {v2}, Landroid/content/Intent;-><init>()V
    const-string v3, "com.directive.v5"
    const-string v4, "com.ticktick.task.activity.MeTaskActivity"
    invoke-virtual {v2, v3, v4}, Landroid/content/Intent;->setClassName(Ljava/lang/String;Ljava/lang/String;)Landroid/content/Intent;
    invoke-virtual {p0, v2}, Landroid/app/Activity;->startActivity(Landroid/content/Intent;)V
    :launch_try_end
    .catch Ljava/lang/Throwable; {:launch_try_start .. :launch_try_end} :launch_catch
    return-void

    :launch_catch
    move-exception v2
    invoke-static {v2}, Lcom/directive/runtime/DirectiveDiagnosticApplication;->recordThrowable(Ljava/lang/Throwable;)V
    const/4 v5, 0x0
    iput-boolean v5, p0, Lcom/directive/runtime/DirectiveDiagnosticActivity;->launched:Z
    invoke-direct {p0}, Lcom/directive/runtime/DirectiveDiagnosticActivity;->refresh()V
    return-void

    :waiting
    const-string v2, "DIRECTIVE 5 diagnostic startup\n\nInherited task surface was launched. If it closed, return to DIRECTIVE 5; any captured startup/lifecycle exception will appear here."
    invoke-virtual {v1, v2}, Landroid/widget/TextView;->setText(Ljava/lang/CharSequence;)V
    return-void
.end method
'''
(diag_dir / "DirectiveDiagnosticActivity.smali").write_text(activity_smali, encoding="utf-8")

# Patch the inherited main-thread recovery path only for this diagnostic build.
callback = root / "smali_classes4/com/ticktick/task/utils/ActivityThreadCallback.smali"
if not callback.is_file():
    raise SystemExit("ActivityThreadCallback.smali missing")
src = callback.read_text(encoding="utf-8")
method_rx = re.compile(r'\.method private abort\(Ljava/lang/Throwable;\)Z.*?\.end method', re.S)
m = method_rx.search(src)
if not m:
    raise SystemExit("ActivityThreadCallback.abort(Throwable) method missing")
replacement = r'''.method private abort(Ljava/lang/Throwable;)Z
    .locals 1

    invoke-static {p1}, Lcom/directive/runtime/DirectiveDiagnosticApplication;->recordThrowable(Ljava/lang/Throwable;)V

    const/4 v0, 0x1
    return v0
.end method'''
src = src[:m.start()] + replacement + src[m.end():]
callback.write_text(src, encoding="utf-8")

crash = root / "smali_classes4/com/ticktick/task/utils/CrashLogHandler.smali"
if not crash.is_file():
    raise SystemExit("CrashLogHandler.smali missing")
src = crash.read_text(encoding="utf-8")
method_rx = re.compile(r'\.method public uncaughtException\(Ljava/lang/Thread;Ljava/lang/Throwable;\)V.*?\.end method', re.S)
m = method_rx.search(src)
if not m:
    raise SystemExit("CrashLogHandler.uncaughtException method missing")
replacement = r'''.method public uncaughtException(Ljava/lang/Thread;Ljava/lang/Throwable;)V
    .locals 0

    invoke-static {p2}, Lcom/directive/runtime/DirectiveDiagnosticApplication;->recordThrowable(Ljava/lang/Throwable;)V

    return-void
.end method'''
src = src[:m.start()] + replacement + src[m.end():]
crash.write_text(src, encoding="utf-8")

# Static fail-closed assertions.
mtext = manifest.read_text(encoding="utf-8")
assert 'android:name="com.directive.runtime.DirectiveDiagnosticApplication"' in mtext
assert 'android:name="com.directive.runtime.DirectiveDiagnosticActivity"' in mtext
assert 'android:name="android.intent.action.MAIN"' in mtext
assert 'android:name="android.intent.category.LAUNCHER"' in mtext

# No inherited launcher alias is allowed to remain explicitly enabled for this diagnostic candidate.
for mm in re.finditer(r'<activity-alias\b[^>]*\bandroid:name="com\.ticktick\.task\.HomeAlia_[^"]+"[^>]*>', mtext, re.S):
    if 'android:enabled="true"' in mm.group(0):
        raise SystemExit("inherited HomeAlia launcher remains enabled")

callback_after = callback.read_text(encoding="utf-8")
abort_body = re.search(r'\.method private abort\(Ljava/lang/Throwable;\)Z(.*?)\.end method', callback_after, re.S)
if not abort_body:
    raise SystemExit("patched abort missing")
if "killProcess" in abort_body.group(1) or "System;->exit" in abort_body.group(1):
    raise SystemExit("diagnostic abort still kills process")

crash_after = crash.read_text(encoding="utf-8")
u = re.search(r'\.method public uncaughtException\(Ljava/lang/Thread;Ljava/lang/Throwable;\)V(.*?)\.end method', crash_after, re.S)
if not u:
    raise SystemExit("patched uncaughtException missing")
if "killProcess" in u.group(1) or "System;->exit" in u.group(1):
    raise SystemExit("diagnostic crash handler still kills process")

report = {
    "status": "PASS",
    "target_package": target,
    "application_wrapper": "com.directive.runtime.DirectiveDiagnosticApplication",
    "launcher": "com.directive.runtime.DirectiveDiagnosticActivity",
    "inherited_launcher_aliases_disabled": disabled,
    "activity_thread_abort_kill_suppressed_for_diagnostic_capture": True,
    "crash_log_handler_kill_suppressed_for_diagnostic_capture": True,
    "authentication_billing_entitlement_logic_changed": False,
    "purpose": "physical-device startup exception capture; not final release behavior",
}
out = root / "DIRECTIVE_D5_DIAGNOSTIC_INSTRUMENTATION_REPORT.json"
out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print(json.dumps(report, indent=2))
