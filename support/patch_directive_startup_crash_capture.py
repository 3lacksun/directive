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
method=s[start:end]
if 'directive_crash_try_start' in method: raise SystemExit('crash instrumentation already present')
needle='.method public onCreate()V\n    .locals 3\n'
if method.count(needle)!=1: raise SystemExit('unexpected onCreate locals contract')
method=method.replace(needle, needle+'\n    :directive_crash_try_start\n',1)
# The inherited onCreate has more than one legitimate return path. Do not rewrite control flow.
# Close one protected range after all original instructions and append an exception handler.
if method.count('    return-void') < 1:
    raise SystemExit('onCreate contains no return-void')
handler='''\n    :directive_crash_try_end\n    .catch Ljava/lang/Throwable; {:directive_crash_try_start .. :directive_crash_try_end} :directive_crash_catch\n\n    :directive_crash_catch\n    move-exception v0\n\n    invoke-static {p0, v0}, Lcom/directive/diagnostics/CrashRecorder;->record(Landroid/content/Context;Ljava/lang/Throwable;)V\n\n    throw v0\n'''
method=method.rstrip()+handler
s=s[:start]+method+s[end:]
app.write_text(s,encoding='utf-8')

out=root/'smali_classes4/com/directive/diagnostics/CrashRecorder.smali'
out.parent.mkdir(parents=True,exist_ok=True)
smali=f'''.class public final Lcom/directive/diagnostics/CrashRecorder;\n.super Ljava/lang/Object;\n.source "CrashRecorder.java"\n\n.method private constructor <init>()V\n    .locals 0\n    invoke-direct {{p0}}, Ljava/lang/Object;-><init>()V\n    return-void\n.end method\n\n.method public static record(Landroid/content/Context;Ljava/lang/Throwable;)V\n    .locals 11\n\n    :try_start_0\n    new-instance v0, Ljava/io/StringWriter;\n    invoke-direct {{v0}}, Ljava/io/StringWriter;-><init>()V\n\n    new-instance v1, Ljava/io/PrintWriter;\n    invoke-direct {{v1, v0}}, Ljava/io/PrintWriter;-><init>(Ljava/io/Writer;)V\n    invoke-virtual {{p1, v1}}, Ljava/lang/Throwable;->printStackTrace(Ljava/io/PrintWriter;)V\n    invoke-virtual {{v1}}, Ljava/io/PrintWriter;->flush()V\n\n    new-instance v2, Ljava/lang/StringBuilder;\n    invoke-direct {{v2}}, Ljava/lang/StringBuilder;-><init>()V\n    const-string v3, "DIRECTIVE {num} startup crash\\npackage="\n    invoke-virtual {{v2, v3}}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;\n    invoke-virtual {{p0}}, Landroid/content/Context;->getPackageName()Ljava/lang/String;\n    move-result-object v3\n    invoke-virtual {{v2, v3}}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;\n    const-string v3, "\\nsdk="\n    invoke-virtual {{v2, v3}}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;\n    sget v3, Landroid/os/Build$VERSION;->SDK_INT:I\n    invoke-virtual {{v2, v3}}, Ljava/lang/StringBuilder;->append(I)Ljava/lang/StringBuilder;\n    const-string v3, "\\ntime="\n    invoke-virtual {{v2, v3}}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;\n    invoke-static {{}}, Ljava/lang/System;->currentTimeMillis()J\n    move-result-wide v3\n    invoke-virtual {{v2, v3, v4}}, Ljava/lang/StringBuilder;->append(J)Ljava/lang/StringBuilder;\n    const-string v3, "\\n\\n"\n    invoke-virtual {{v2, v3}}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;\n    invoke-virtual {{v0}}, Ljava/io/StringWriter;->toString()Ljava/lang/String;\n    move-result-object v0\n    invoke-virtual {{v2, v0}}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;\n    invoke-virtual {{v2}}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;\n    move-result-object v0\n\n    const-string v2, "DIRECTIVE_STARTUP_CRASH"\n    invoke-static {{v2, v0, p1}}, Landroid/util/Log;->e(Ljava/lang/String;Ljava/lang/String;Ljava/lang/Throwable;)I\n\n    sget v2, Landroid/os/Build$VERSION;->SDK_INT:I\n    const/16 v3, 0x1d\n    if-lt v2, v3, :try_end_0\n\n    new-instance v2, Landroid/content/ContentValues;\n    invoke-direct {{v2}}, Landroid/content/ContentValues;-><init>()V\n\n    new-instance v3, Ljava/lang/StringBuilder;\n    const-string v4, "DIRECTIVE_{num}_CRASH_"\n    invoke-direct {{v3, v4}}, Ljava/lang/StringBuilder;-><init>(Ljava/lang/String;)V\n    invoke-static {{}}, Ljava/lang/System;->currentTimeMillis()J\n    move-result-wide v4\n    invoke-virtual {{v3, v4, v5}}, Ljava/lang/StringBuilder;->append(J)Ljava/lang/StringBuilder;\n    const-string v4, ".txt"\n    invoke-virtual {{v3, v4}}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;\n    invoke-virtual {{v3}}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;\n    move-result-object v3\n\n    const-string v4, "_display_name"\n    invoke-virtual {{v2, v4, v3}}, Landroid/content/ContentValues;->put(Ljava/lang/String;Ljava/lang/String;)V\n    const-string v3, "mime_type"\n    const-string v4, "text/plain"\n    invoke-virtual {{v2, v3, v4}}, Landroid/content/ContentValues;->put(Ljava/lang/String;Ljava/lang/String;)V\n    const-string v3, "relative_path"\n    const-string v4, "Download"\n    invoke-virtual {{v2, v3, v4}}, Landroid/content/ContentValues;->put(Ljava/lang/String;Ljava/lang/String;)V\n\n    invoke-virtual {{p0}}, Landroid/content/Context;->getContentResolver()Landroid/content/ContentResolver;\n    move-result-object v3\n    sget-object v4, Landroid/provider/MediaStore$Downloads;->EXTERNAL_CONTENT_URI:Landroid/net/Uri;\n    invoke-virtual {{v3, v4, v2}}, Landroid/content/ContentResolver;->insert(Landroid/net/Uri;Landroid/content/ContentValues;)Landroid/net/Uri;\n    move-result-object v2\n    if-eqz v2, :try_end_0\n\n    invoke-virtual {{v3, v2}}, Landroid/content/ContentResolver;->openOutputStream(Landroid/net/Uri;)Ljava/io/OutputStream;\n    move-result-object v2\n    if-eqz v2, :try_end_0\n\n    const-string v3, "UTF-8"\n    invoke-virtual {{v0, v3}}, Ljava/lang/String;->getBytes(Ljava/lang/String;)[B\n    move-result-object v0\n    invoke-virtual {{v2, v0}}, Ljava/io/OutputStream;->write([B)V\n    invoke-virtual {{v2}}, Ljava/io/OutputStream;->flush()V\n    invoke-virtual {{v2}}, Ljava/io/OutputStream;->close()V\n    :try_end_0\n    .catch Ljava/lang/Throwable; {{:try_start_0 .. :try_end_0}} :catch_0\n\n    return-void\n\n    :catch_0\n    move-exception v0\n    const-string v1, "DIRECTIVE_STARTUP_CRASH"\n    const-string v2, "Crash recorder failed"\n    invoke-static {{v1, v2, v0}}, Landroid/util/Log;->e(Ljava/lang/String;Ljava/lang/String;Ljava/lang/Throwable;)I\n    return-void\n.end method\n'''
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
