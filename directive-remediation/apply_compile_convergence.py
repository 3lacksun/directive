#!/usr/bin/env python3
from pathlib import Path
import re, sys
root=Path(sys.argv[1] if len(sys.argv)>1 else 'build-src')
def one(path, old, new):
    p=root/path; t=p.read_text(); c=t.count(old)
    if c!=1: raise SystemExit(f'{path}: expected 1 match, found {c}: {old[:80]}')
    p.write_text(t.replace(old,new,1))
# REM-001/002
p=root/'app/build.gradle.kts'; t=p.read_text()
one('app/build.gradle.kts','    alias(libs.plugins.kotlin.android)\n','')
t=p.read_text()
m=re.search(r'(?ms)^[ \t]*kotlinOptions[ \t]*\{[ \t\r\n]*jvmTarget[ \t]*=[ \t]*["\']21["\'][ \t\r\n]*\}[ \t]*(?:\r?\n)?',t)
if not m: raise SystemExit('legacy kotlinOptions block not found')
t=t[:m.start()]+t[m.end():]
imp='import org.jetbrains.kotlin.gradle.dsl.JvmTarget\n'
if imp not in t: t=imp+t
marker='dependencies {'
if t.count(marker)!=1: raise SystemExit('dependencies marker mismatch')
t=t.replace(marker,'kotlin {\n    compilerOptions {\n        jvmTarget = JvmTarget.fromTarget("21")\n    }\n}\n\n'+marker,1)
p.write_text(t)
# REM-003
sp=root/'app/src/main/res/xml/shortcuts.xml'; st=root/'app/src/main/res/values/strings.xml'
s=sp.read_text(); x=st.read_text()
for a,b in [('android:shortcutShortLabel="Add task"','android:shortcutShortLabel="@string/shortcut_quick_add_short"'),('android:shortcutLongLabel="Quick Add to DIRECTIVE"','android:shortcutLongLabel="@string/shortcut_quick_add_long"'),('android:shortcutShortLabel="Today"','android:shortcutShortLabel="@string/shortcut_today_short"'),('android:shortcutLongLabel="Open DIRECTIVE Today"','android:shortcutLongLabel="@string/shortcut_today_long"')]:
    if s.count(a)!=1: raise SystemExit('shortcut label mismatch')
    s=s.replace(a,b,1)
block='    <string name="shortcut_quick_add_short">Add task</string>\n    <string name="shortcut_quick_add_long">Quick Add to DIRECTIVE</string>\n    <string name="shortcut_today_short">Today</string>\n    <string name="shortcut_today_long">Open DIRECTIVE Today</string>\n'
if x.count('</resources>')!=1: raise SystemExit('resources close mismatch')
x=x.replace('</resources>',block+'</resources>',1); sp.write_text(s); st.write_text(x)
# REM-004
one('app/src/main/kotlin/com/example/directive/data/database/DatabaseSeedCallback.kt','arrayOf(c.id, c.name, c.icon, c.colour, c.order, now, now)','arrayOf<Any?>(c.id, c.name, c.icon, c.colour, c.order, now, now)')
one('app/src/main/kotlin/com/example/directive/feature/calendar/CalendarScreen.kt','ElevatedCard(Modifier.fillMaxWidth(), onClick = { onEditTask(item.task.id) }) {','ElevatedCard(onClick = { onEditTask(item.task.id) }, modifier = Modifier.fillMaxWidth()) {')
one('app/src/main/kotlin/com/example/directive/feature/plan/PlanScreen.kt','ElevatedCard(Modifier.fillMaxWidth(), onClick = { onEditTask(p.taskId) }) {','ElevatedCard(onClick = { onEditTask(p.taskId) }, modifier = Modifier.fillMaxWidth()) {')
editor='app/src/main/kotlin/com/example/directive/feature/taskedit/TaskEditorViewModel.kt'
for a,b in [('}.onFailure { _state.update { it.copy(loading=false,error=it.message) } }','}.onFailure { failure -> _state.update { it.copy(loading=false,error=failure.message) } }'),('}.onFailure { _state.update { it.copy(saving=false,error=it.message ?: "Could not save task") } }','}.onFailure { failure -> _state.update { it.copy(saving=false,error=failure.message ?: "Could not save task") } }'),('.onFailure { _state.update { it.copy(error=it.message ?: "Could not archive task") } }','.onFailure { failure -> _state.update { it.copy(error=failure.message ?: "Could not archive task") } }'),('.onFailure { _state.update { it.copy(error=it.message ?: "Could not delete task") } }','.onFailure { failure -> _state.update { it.copy(error=failure.message ?: "Could not delete task") } }')]: one(editor,a,b)
old='''    val state=combine(list,query,category,filters,tasks,categories,counts){l,q,c,f,t,cats,ct->\n        TasksUiState(l,q,c,f,t,cats,ct)\n    }.stateIn(viewModelScope,SharingStarted.WhileSubscribed(5_000),TasksUiState())'''
new='''    val state=combine(\n        combine(list,query,category,filters){l,q,c,f->Request(l,q,c,f)},\n        combine(tasks,categories,counts){t,cats,ct->Triple(t,cats,ct)},\n    ){request,content->\n        TasksUiState(request.list,request.query,request.category,request.filters,content.first,content.second,content.third)\n    }.stateIn(viewModelScope,SharingStarted.WhileSubscribed(5_000),TasksUiState())'''
one('app/src/main/kotlin/com/example/directive/feature/tasks/TasksViewModel.kt',old,new)
print('REM-001..004 compile convergence applied')
