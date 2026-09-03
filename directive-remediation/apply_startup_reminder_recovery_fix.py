#!/usr/bin/env python3
from pathlib import Path
import sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
path = root / "app/src/main/kotlin/com/example/directive/DirectiveApplication.kt"
if not path.is_file():
    raise SystemExit(f"missing {path}")

replacement = '''package com.example.directive

import android.app.Application
import com.example.directive.data.repository.ReminderRepository
import com.example.directive.data.repository.TaskRepository
import com.example.directive.domain.model.ReminderState
import com.example.directive.domain.model.ReminderType
import com.example.directive.notifications.RecurringReminderCoordinator
import com.example.directive.notifications.ReminderCoordinator
import dagger.hilt.android.HiltAndroidApp
import javax.inject.Inject
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.launch

@HiltAndroidApp
class DirectiveApplication : Application() {
    @Inject lateinit var reminders: ReminderRepository
    @Inject lateinit var tasks: TaskRepository
    @Inject lateinit var reminderCoordinator: ReminderCoordinator
    @Inject lateinit var recurringReminderCoordinator: RecurringReminderCoordinator
    private val applicationScope = CoroutineScope(SupervisorJob() + Dispatchers.IO)

    override fun onCreate() {
        super.onCreate()
        // Recover persisted reminders whenever the real application process starts. This is a
        // fallback for Android states that can defer BOOT_COMPLETED delivery until app launch.
        applicationScope.launch {
            runCatching {
                val states = listOf(ReminderState.PENDING, ReminderState.SCHEDULED, ReminderState.SNOOZED)
                reminders.pending(states).forEach { reminder ->
                    val task = tasks.get(reminder.taskId) ?: return@forEach
                    if (task.seriesId != null && reminder.occurrenceKey == null && reminder.type != ReminderType.ABSOLUTE) {
                        return@forEach
                    }
                    reminderCoordinator.recoverPersisted(reminder, task)
                }
                recurringReminderCoordinator.refreshAll()
            }
        }
    }
}
'''

current = path.read_text()
if current == replacement:
    print("STARTUP_REMINDER_RECOVERY_FIX=PASS changed=0")
    raise SystemExit(0)

required = [
    "@HiltAndroidApp",
    "recurringReminderCoordinator: RecurringReminderCoordinator",
    "recurringReminderCoordinator.refreshAll()",
]
missing = [marker for marker in required if marker not in current]
if missing:
    raise SystemExit("unexpected DirectiveApplication baseline; missing: " + ", ".join(missing))

path.write_text(replacement)
print("STARTUP_REMINDER_RECOVERY_FIX=PASS changed=1")
