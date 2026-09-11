#!/usr/bin/env python3
from pathlib import Path
import json, sys

if len(sys.argv) != 3:
    raise SystemExit('usage: patch_directive_startup_crash_capture.py <project_root> <directive_number>')
root=Path(sys.argv[1])
num=str(sys.argv[2])
app=root/'smali_classes2/com/ticktick/task/TickTickApplication.smali'
if not app.is_file(): raise SystemExit(f'missing {app}')
s=app.read_text(encoding='utf-8')
start=s.find('.method public onCreate()V')
if start<0: raise SystemExit('TickTickApplication.onCreate not found')
end=s.find('.end method',start)
if end<0: raise SystemExit('TickTickApplication.onCreate end not found')
end += len('.end method')
method=s[start:end]
if 'directive_crash_try_start' in method: raise SystemExit('crash instrumentation already present')
needle='.method public onCreate()V\n    .locals 3\n'
if method.count(needle)!=1: raise SystemExit('unexpected onCreate locals contract')
method=method.replace(needle, needle+'\n    :directive_crash_try_start\n',1)
# The executable method has a single return-void. Put the end of the protected range immediately before it.
if method.count('    return-void') != 1:
    raise SystemExit(f'unexpected return count {method.count("    return-void")}')
catch='''    :directive_crash_try_end
    .catch Ljava/lang/Throwable; {:directive_crash_try_start .. :directive_crash_try_end} :directive_crash_catch

    return-void

    :directive_crash_catch
    move-exception v0

    invoke-static {p0, v0}, Lcom/directive/diagnostics/CrashRecorder;->record(Landroid/content/Context;Ljava/lang/Throwable;)V

    throw v0'''
method=method.replace('    return-void',catch,1)
s=s[:start]+method+s[end:]
app.write_text(s,encoding='utf-8')

out=root/'smali_classes4/com/directive/diagnostics/CrashRecorder.smali'
out.parent.mkdir(parents=True,exist_ok=True)
smali=f'''.class public final Lcom/directive/diagnostics/CrashRecorder;
.super Ljava/lang/Object;
.source "CrashRecorder.java"

.method private constructor <init>()V
    .locals 0
    invoke-direct {{p0}}, Ljava/lang/Object;-><init>()V
    return-void
.end method

.method public static record(Landroid/content/Context;Ljava/lang/Throwable;)V
    .locals 11

    :try_start_0
    new-instance v0, Ljava/io/StringWriter;
    invoke-direct {{v0}}, Ljava/io/StringWriter;-><init>()V

    new-instance v1, Ljava/io/PrintWriter;
    invoke-direct {{v1, v0}}, Ljava/io/PrintWriter;-><init>(Ljava/io/Writer;)V
    invoke-virtual {{p1, v1}}, Ljava/lang/Throwable;->printStackTrace(Ljava/io/PrintWriter;)V
    invoke-virtual {{v1}}, Ljava/io/PrintWriter;->flush()V

    new-instance v2, Ljava/lang/StringBuilder;
    invoke-direct {{v2}}, Ljava/lang/StringBuilder;-><init>()V
    const-string v3, "DIRECTIVE {num} startup crash\\npackage="
    invoke-virtual {{v2, v3}}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    invoke-virtual {{p0}}, Landroid/content/Context;->getPackageName()Ljava/lang/String;
    move-result-object v3
    invoke-virtual {{v2, v3}}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    const-string v3, "\\nsdk="
    invoke-virtual {{v2, v3}}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    sget v3, Landroid/os/Build$VERSION;->SDK_INT:I
    invoke-virtual {{v2, v3}}, Ljava/lang/StringBuilder;->append(I)Ljava/lang/StringBuilder;
    const-string v3, "\\ntime="
    invoke-virtual {{v2, v3}}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    invoke-static {{}}, Ljava/lang/System;->currentTimeMillis()J
    move-result-wide v3
    invoke-virtual {{v2, v3, v4}}, Ljava/lang/StringBuilder;->append(J)Ljava/lang/StringBuilder;
    const-string v3, "\\n\\n"
    invoke-virtual {{v2, v3}}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    invoke-virtual {{v0}}, Ljava/io/StringWriter;->toString()Ljava/lang/String;
    move-result-object v0
    invoke-virtual {{v2, v0}}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    invoke-virtual {{v2}}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;
    move-result-object v0

    const-string v2, "DIRECTIVE_STARTUP_CRASH"
    invoke-static {{v2, v0, p1}}, Landroid/util/Log;->e(Ljava/lang/String;Ljava/lang/String;Ljava/lang/Throwable;)I

    sget v2, Landroid/os/Build$VERSION;->SDK_INT:I
    const/16 v3, 0x1d
    if-lt v2, v3, :try_end_0

    new-instance v2, Landroid/content/ContentValues;
    invoke-direct {{v2}}, Landroid/content/ContentValues;-><init>()V

    new-instance v3, Ljava/lang/StringBuilder;
    const-string v4, "DIRECTIVE_{num}_CRASH_"
    invoke-direct {{v3, v4}}, Ljava/lang/StringBuilder;-><init>(Ljava/lang/String;)V
    invoke-static {{}}, Ljava/lang/System;->currentTimeMillis()J
    move-result-wide v4
    invoke-virtual {{v3, v4, v5}}, Ljava/lang/StringBuilder;->append(J)Ljava/lang/StringBuilder;
    const-string v4, ".txt"
    invoke-virtual {{v3, v4}}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    invoke-virtual {{v3}}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;
    move-result-object v3

    const-string v4, "_display_name"
    invoke-virtual {{v2, v4, v3}}, Landroid/content/ContentValues;->put(Ljava/lang/String;Ljava/lang/String;)V
    const-string v3, "mime_type"
    const-string v4, "text/plain"
    invoke-virtual {{v2, v3, v4}}, Landroid/content/ContentValues;->put(Ljava/lang/String;Ljava/lang/String;)V
    const-string v3, "relative_path"
    const-string v4, "Download"
    invoke-virtual {{v2, v3, v4}}, Landroid/content/ContentValues;->put(Ljava/lang/String;Ljava/lang/String;)V

    invoke-virtual {{p0}}, Landroid/content/Context;->getContentResolver()Landroid/content/ContentResolver;
    move-result-object v3
    sget-object v4, Landroid/provider/MediaStore$Downloads;->EXTERNAL_CONTENT_URI:Landroid/net/Uri;
    invoke-virtual {{v3, v4, v2}}, Landroid/content/ContentResolver;->insert(Landroid/net/Uri;Landroid/content/ContentValues;)Landroid/net/Uri;
    move-result-object v2
    if-eqz v2, :try_end_0

    invoke-virtual {{v3, v2}}, Landroid/content/ContentResolver;->openOutputStream(Landroid/net/Uri;)Ljava/io/OutputStream;
    move-result-object v2
    if-eqz v2, :try_end_0

    const-string v3, "UTF-8"
    invoke-virtual {{v0, v3}}, Ljava/lang/String;->getBytes(Ljava/lang/String;)[B
    move-result-object v0
    invoke-virtual {{v2, v0}}, Ljava/io/OutputStream;->write([B)V
    invoke-virtual {{v2}}, Ljava/io/OutputStream;->flush()V
    invoke-virtual {{v2}}, Ljava/io/OutputStream;->close()V
    :try_end_0
    .catch Ljava/lang/Throwable; {{:try_start_0 .. :try_end_0}} :catch_0

    return-void

    :catch_0
    move-exception v0
    const-string v1, "DIRECTIVE_STARTUP_CRASH"
    const-string v2, "Crash recorder failed"
    invoke-static {{v1, v2, v0}}, Landroid/util/Log;->e(Ljava/lang/String;Ljava/lang/String;Ljava/lang/Throwable;)I
    return-void
.end method
'''
out.write_text(smali,encoding='utf-8')
report={
 'diagnostic_only': True,
 'startup_throwable_rethrown': True,
 'authentication_licensing_entitlement_logic_changed': False,
 'inherited_ticktick_namespace_changed': False,
 'network_permissions_added': False,
 'crash_output':'MediaStore Downloads/DIRECTIVE_'+num+'_CRASH_<timestamp>.txt on Android 10+',
 'instrumented_method':'com.ticktick.task.TickTickApplication.onCreate'
}
(root/'DIRECTIVE_STARTUP_CRASH_CAPTURE_REPORT.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
