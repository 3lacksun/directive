#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

if len(sys.argv) != 3:
    raise SystemExit('usage: patch_directive_startup_diagnostics.py PROJECT_ROOT TARGET_PACKAGE')

root = Path(sys.argv[1]).resolve()
target = sys.argv[2].strip()
if not root.is_dir():
    raise SystemExit(f'missing project root: {root}')
if not re.fullmatch(r'com\.directive\.v\d+', target):
    raise SystemExit(f'unexpected target package: {target}')

# A wrapper Application catches startup exceptions thrown by the inherited application
# before Android can terminate the process. It persists only the exception stack trace
# to app-private SharedPreferences. No user data, credentials or entitlement state is touched.
smali_dir = root / 'smali_classes5' / 'com' / 'directive' / 'diagnostic'
smali_dir.mkdir(parents=True, exist_ok=True)
wrapper = smali_dir / 'DirectiveDiagnosticApplication.smali'
wrapper.write_text(r'''.class public Lcom/directive/diagnostic/DirectiveDiagnosticApplication;
.super Lcom/ticktick/task/TickTickApplication;
.source "DirectiveDiagnosticApplication.java"

.method public constructor <init>()V
    .locals 0
    invoke-direct {p0}, Lcom/ticktick/task/TickTickApplication;-><init>()V
    return-void
.end method

.method public onCreate()V
    .locals 4
    :try_start_0
    invoke-super {p0}, Lcom/ticktick/task/TickTickApplication;->onCreate()V
    :try_end_0
    .catch Ljava/lang/Throwable; {:try_start_0 .. :try_end_0} :catch_0
    return-void

    :catch_0
    move-exception v0
    invoke-static {v0}, Landroid/util/Log;->getStackTraceString(Ljava/lang/Throwable;)Ljava/lang/String;
    move-result-object v1
    const-string v2, "directive_diagnostics"
    const/4 v3, 0x0
    invoke-virtual {p0, v2, v3}, Landroid/content/Context;->getSharedPreferences(Ljava/lang/String;I)Landroid/content/SharedPreferences;
    move-result-object v2
    invoke-interface {v2}, Landroid/content/SharedPreferences;->edit()Landroid/content/SharedPreferences$Editor;
    move-result-object v2
    const-string v3, "startup_error"
    invoke-interface {v2, v3, v1}, Landroid/content/SharedPreferences$Editor;->putString(Ljava/lang/String;Ljava/lang/String;)Landroid/content/SharedPreferences$Editor;
    move-result-object v2
    invoke-interface {v2}, Landroid/content/SharedPreferences$Editor;->commit()Z
    return-void
.end method
''', encoding='utf-8')

java_dir = root / 'src' / 'com' / 'directive' / 'diagnostic'
java_dir.mkdir(parents=True, exist_ok=True)
activity = java_dir / 'DirectiveDiagnosticActivity.java'
activity.write_text(r'''package com.directive.diagnostic;

import android.app.Activity;
import android.content.Intent;
import android.content.SharedPreferences;
import android.graphics.Typeface;
import android.os.Bundle;
import android.os.Process;
import android.text.method.ScrollingMovementMethod;
import android.util.Log;
import android.view.View;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.TextView;

public final class DirectiveDiagnosticActivity extends Activity {
    private SharedPreferences prefs;

    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        prefs = getSharedPreferences("directive_diagnostics", MODE_PRIVATE);
        String startup = prefs.getString("startup_error", null);
        String runtime = prefs.getString("runtime_error", null);
        if (startup != null && !startup.isEmpty()) {
            showReport("DIRECTIVE startup failure captured", startup);
            return;
        }
        if (runtime != null && !runtime.isEmpty()) {
            showReport("DIRECTIVE runtime failure captured", runtime);
            return;
        }
        launchOriginal();
    }

    private void launchOriginal() {
        final Thread.UncaughtExceptionHandler previous = Thread.getDefaultUncaughtExceptionHandler();
        Thread.setDefaultUncaughtExceptionHandler((thread, error) -> {
            try {
                prefs.edit().putString("runtime_error", Log.getStackTraceString(error)).commit();
            } catch (Throwable ignored) { }
            if (previous != null) previous.uncaughtException(thread, error);
            else Process.killProcess(Process.myPid());
        });
        try {
            Intent i = new Intent();
            i.setClassName(this, "com.ticktick.task.activity.MeTaskActivity");
            startActivity(i);
        } catch (Throwable error) {
            prefs.edit().putString("runtime_error", Log.getStackTraceString(error)).commit();
            showReport("DIRECTIVE launch failure captured", Log.getStackTraceString(error));
        }
    }

    private void showReport(String heading, String report) {
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        int pad = (int)(16 * getResources().getDisplayMetrics().density);
        root.setPadding(pad, pad, pad, pad);
        root.setBackgroundColor(0xfff4f6f9);

        TextView title = new TextView(this);
        title.setText(heading);
        title.setTextSize(20f);
        title.setTextColor(0xff161a1f);
        title.setTypeface(Typeface.DEFAULT_BOLD);
        root.addView(title, new LinearLayout.LayoutParams(-1, -2));

        TextView detail = new TextView(this);
        detail.setText("This report was captured inside DIRECTIVE. No Developer Options or ADB are required.\n\n" + report);
        detail.setTextIsSelectable(true);
        detail.setMovementMethod(new ScrollingMovementMethod());
        detail.setTextSize(12f);
        detail.setTextColor(0xff161a1f);
        LinearLayout.LayoutParams detailParams = new LinearLayout.LayoutParams(-1, 0, 1f);
        detailParams.topMargin = pad;
        root.addView(detail, detailParams);

        Button retry = new Button(this);
        retry.setText("Clear report and retry app");
        retry.setOnClickListener((View v) -> {
            prefs.edit().remove("startup_error").remove("runtime_error").commit();
            recreate();
        });
        root.addView(retry, new LinearLayout.LayoutParams(-1, -2));
        setContentView(root);
    }
}
''', encoding='utf-8')

manifest = root / 'AndroidManifest.xml'
m = manifest.read_text(encoding='utf-8')
old_app = 'android:name="com.ticktick.task.TickTickApplication"'
new_app = 'android:name="com.directive.diagnostic.DirectiveDiagnosticApplication"'
if m.count(old_app) != 1:
    raise SystemExit(f'expected one inherited Application declaration, found {m.count(old_app)}')
m = m.replace(old_app, new_app, 1)

activity_decl = '<activity android:name="com.directive.diagnostic.DirectiveDiagnosticActivity" android:exported="false" android:theme="@android:style/Theme.Material.Light.NoActionBar"/>'
anchor = '<activity android:theme="@style/AppTheme.Launcher" android:name="com.ticktick.task.activity.MeTaskActivity"'
idx = m.find(anchor)
if idx < 0:
    raise SystemExit('MeTaskActivity declaration anchor missing')
m = m[:idx] + activity_decl + '\n        ' + m[idx:]

# Retarget only the enabled default launcher alias. Disabled seasonal aliases are kept for
# compatibility with inherited icon-management code and are not made launchable.
alias_rx = re.compile(r'(<activity-alias\b[^>]*android:name="com\.ticktick\.task\.HomeAlia_default"[^>]*android:targetActivity=")com\.ticktick\.task\.activity\.MeTaskActivity("[^>]*>)')
m, count = alias_rx.subn(r'\1com.directive.diagnostic.DirectiveDiagnosticActivity\2', m, count=1)
if count != 1:
    raise SystemExit(f'expected one default launcher alias retarget, found {count}')
manifest.write_text(m, encoding='utf-8')

report = {
    'status': 'PASS',
    'target_package': target,
    'application_wrapper': 'com.directive.diagnostic.DirectiveDiagnosticApplication',
    'diagnostic_launcher': 'com.directive.diagnostic.DirectiveDiagnosticActivity',
    'startup_exception_capture': True,
    'runtime_exception_capture': True,
    'default_launcher_retargeted': True,
    'diagnostic_storage': 'app-private SharedPreferences only',
    'auth_billing_entitlement_modified': False,
}
(root / 'DIRECTIVE_STARTUP_DIAGNOSTICS_REPORT.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
print(json.dumps(report, indent=2))
