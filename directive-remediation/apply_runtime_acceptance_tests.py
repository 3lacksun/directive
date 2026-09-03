#!/usr/bin/env python3
from pathlib import Path
import sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else "build-src")
test_dir = root / "app/src/androidTest/kotlin/com/example/directive"
test_dir.mkdir(parents=True, exist_ok=True)

accessibility = r'''package com.example.directive

import androidx.compose.ui.test.assertIsDisplayed
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.compose.ui.test.onNodeWithContentDescription
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performClick
import androidx.compose.ui.test.performScrollTo
import androidx.test.ext.junit.runners.AndroidJUnit4
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
class DirectiveLaunchAccessibilityInstrumentedTest {
    @get:Rule val compose = createAndroidComposeRule<MainActivity>()

    @Test fun launchExposesNamedQuickAddAction() {
        compose.onNodeWithContentDescription("Quick Add").assertIsDisplayed()
    }

    @Test fun primaryNavigationDestinationsRender() {
        compose.onNodeWithText("Calendar").performClick()
        compose.waitForIdle()
        compose.onNodeWithText("Previous").assertIsDisplayed()

        compose.onNodeWithText("Tasks").performClick()
        compose.waitForIdle()
        compose.onNodeWithText("Filters").performScrollTo().assertIsDisplayed()

        compose.onNodeWithText("Plan").performClick()
        compose.waitForIdle()
        compose.onNodeWithText("Master Plan").assertIsDisplayed()

        compose.onNodeWithText("More").performClick()
        compose.waitForIdle()
        compose.onNodeWithText("Dr Christopher Stone").assertIsDisplayed()

        compose.onNodeWithText("Today").performClick()
        compose.waitForIdle()
        compose.onNodeWithText("D I R E C T I V E").assertIsDisplayed()
    }
}
'''

behaviour = r'''package com.example.directive

import android.content.Intent
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import com.example.directive.data.database.DirectiveDatabaseFactory
import com.example.directive.data.database.entity.AttachmentEntity
import com.example.directive.data.database.entity.TaskEntity
import com.example.directive.data.portability.BackupAttachmentPayload
import com.example.directive.data.portability.BackupCodec
import com.example.directive.data.portability.DirectiveBackup
import com.example.directive.domain.model.AttachmentStorageMode
import com.example.directive.domain.model.RecurrenceEndMode
import com.example.directive.domain.model.RecurrenceFrequency
import com.example.directive.domain.model.ReminderState
import com.example.directive.domain.model.ReminderType
import com.example.directive.domain.model.RepeatMode
import com.example.directive.domain.recurrence.RecurrenceEngine
import com.example.directive.domain.recurrence.RecurrenceRule
import com.example.directive.notifications.ReminderReceiver
import java.time.ZoneId
import java.time.ZonedDateTime
import kotlinx.coroutines.delay
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.withTimeout
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertTrue
import org.junit.Test
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
class DirectiveRuntimeBehaviourInstrumentedTest {
    private val context get() = InstrumentationRegistry.getInstrumentation().targetContext

    @Test fun afterCompletionRecurrenceIsSingleCompletionRelativeAndBudgetBounded() {
        val zone = ZoneId.of("Europe/London")
        val anchor = ZonedDateTime.of(2026, 9, 1, 9, 0, 0, 0, zone)
        val completion = ZonedDateTime.of(2026, 9, 3, 10, 30, 0, 0, zone)
        val rule = RecurrenceRule(
            frequency = RecurrenceFrequency.DAILY,
            interval = 2,
            repeatMode = RepeatMode.AFTER_COMPLETION,
            zoneId = zone,
            endMode = RecurrenceEndMode.AFTER_OCCURRENCES,
            maxOccurrences = 3,
        )
        val generated = RecurrenceEngine.generate(
            anchor = anchor,
            rule = rule,
            windowStart = completion.toInstant(),
            windowEndExclusive = completion.plusDays(10).toInstant(),
            completionAnchor = completion,
            completedOccurrences = 1,
        )
        assertEquals(1, generated.size)
        assertEquals(completion.plusDays(2).toInstant(), generated.single().dateTime.toInstant())
        val exhausted = RecurrenceEngine.generate(
            anchor = anchor,
            rule = rule,
            windowStart = completion.toInstant(),
            windowEndExclusive = completion.plusDays(10).toInstant(),
            completionAnchor = completion,
            completedOccurrences = 3,
        )
        assertTrue(exhausted.isEmpty())
    }

    @Test fun backupV2RoundTripsPortableAttachmentPayload() {
        val task = TaskEntity(id = "runtime-backup-task", title = "Runtime backup", createdAt = 1L, updatedAt = 1L)
        val attachment = AttachmentEntity(
            id = "runtime-attachment",
            taskId = task.id,
            displayName = "runtime.txt",
            mimeType = "text/plain",
            storageMode = AttachmentStorageMode.SAF_URI,
            uriOrRelativePath = "content://directive.runtime/runtime.txt",
            sizeBytes = 1,
            createdAt = 1L,
        )
        val backup = DirectiveBackup(
            exportedAt = 1L,
            categories = emptyList(),
            tasks = listOf(task),
            checklistItems = emptyList(),
            recurrenceSeries = emptyList(),
            recurrenceStates = emptyList(),
            reminders = emptyList(),
            planEntries = emptyList(),
            attachments = listOf(attachment),
            attachmentPayloads = listOf(BackupAttachmentPayload(attachment.id, "eA==")),
            templates = emptyList(),
            taskActivity = emptyList(),
        )
        val encoded = BackupCodec.encode(backup)
        val (decoded, validation) = BackupCodec.decodeAndValidate(encoded)
        assertTrue(validation.errors.joinToString(), validation.valid)
        assertNotNull(decoded)
        assertEquals(2, decoded!!.schemaVersion)
        assertEquals("eA==", decoded.attachmentPayloads.single().dataBase64)
    }

    @Test fun explicitReminderDeliveryPersistsFiredState() = runBlocking {
        val now = System.currentTimeMillis()
        val suffix = now.toString()
        val taskId = "runtime-reminder-task-$suffix"
        val reminderId = "runtime-reminder-$suffix"
        val requestCode = (now % 1_000_000L).toInt() + 1_000_000
        val db = DirectiveDatabaseFactory.build(context)
        try {
            db.openHelper.writableDatabase
            db.taskDao().insert(TaskEntity(id = taskId, title = "Runtime reminder", createdAt = now, updatedAt = now))
            db.reminderDao().insert(
                com.example.directive.data.database.entity.ReminderEntity(
                    id = reminderId,
                    taskId = taskId,
                    type = ReminderType.ABSOLUTE,
                    absoluteAt = now,
                    scheduledAt = now,
                    systemRequestCode = requestCode,
                    state = ReminderState.SCHEDULED,
                    createdAt = now,
                    updatedAt = now,
                )
            )
            context.sendBroadcast(
                Intent(context, ReminderReceiver::class.java)
                    .putExtra("reminderId", reminderId)
                    .putExtra("taskId", taskId)
                    .putExtra("title", "Runtime reminder")
                    .putExtra("requestCode", requestCode)
            )
            val fired = withTimeout(10_000) {
                var value = db.reminderDao().getById(reminderId)
                while (value?.state != ReminderState.FIRED) {
                    delay(100)
                    value = db.reminderDao().getById(reminderId)
                }
                value
            }
            assertEquals(ReminderState.FIRED, fired.state)
            assertEquals(null, fired.scheduledAt)
        } finally {
            runCatching { runBlocking { db.reminderDao().delete(reminderId) } }
            runCatching { runBlocking { db.taskDao().softDelete(taskId, System.currentTimeMillis()) } }
            db.close()
        }
    }
}
'''

reboot = r'''package com.example.directive

import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import com.example.directive.data.database.DirectiveDatabaseFactory
import com.example.directive.data.database.entity.ReminderEntity
import com.example.directive.data.database.entity.TaskEntity
import com.example.directive.domain.model.ReminderState
import com.example.directive.domain.model.ReminderType
import kotlinx.coroutines.delay
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.withTimeout
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertTrue
import org.junit.Test
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
class DirectiveRebootReminderInstrumentedTest {
    private val context get() = InstrumentationRegistry.getInstrumentation().targetContext
    private val taskId = "runtime-reboot-task"
    private val reminderId = "runtime-reboot-reminder"
    private val requestCode = 1903701

    @Test fun seedFutureReminderForReboot() = runBlocking {
        val now = System.currentTimeMillis()
        val target = now + 15 * 60_000L
        val db = DirectiveDatabaseFactory.build(context)
        try {
            db.openHelper.writableDatabase
            runCatching { db.reminderDao().delete(reminderId) }
            db.taskDao().upsertAll(listOf(TaskEntity(id = taskId, title = "Reboot reminder", createdAt = now, updatedAt = now)))
            db.reminderDao().insert(
                ReminderEntity(
                    id = reminderId,
                    taskId = taskId,
                    type = ReminderType.ABSOLUTE,
                    absoluteAt = target,
                    exactTimingRequested = false,
                    scheduledAt = null,
                    systemRequestCode = requestCode,
                    state = ReminderState.PENDING,
                    createdAt = now,
                    updatedAt = now,
                )
            )
            val seeded = db.reminderDao().getById(reminderId)
            assertNotNull(seeded)
            assertEquals(ReminderState.PENDING, seeded!!.state)
            assertEquals(null, seeded.scheduledAt)
        } finally {
            db.close()
        }
    }

    @Test fun verifyReminderRestoredAfterActualBoot() = runBlocking {
        val db = DirectiveDatabaseFactory.build(context)
        try {
            db.openHelper.writableDatabase
            val restored = withTimeout(20_000) {
                var value = db.reminderDao().getById(reminderId)
                while (value == null || value.state != ReminderState.SCHEDULED || value.scheduledAt == null) {
                    delay(250)
                    value = db.reminderDao().getById(reminderId)
                }
                value
            }
            assertEquals(ReminderState.SCHEDULED, restored.state)
            assertNotNull(restored.scheduledAt)
            assertTrue(restored.scheduledAt!! > System.currentTimeMillis())
        } finally {
            runCatching { db.reminderDao().delete(reminderId) }
            runCatching { db.taskDao().softDelete(taskId, System.currentTimeMillis()) }
            db.close()
        }
    }
}
'''

(test_dir / "DirectiveLaunchAccessibilityInstrumentedTest.kt").write_text(accessibility, encoding="utf-8")
(test_dir / "DirectiveRuntimeBehaviourInstrumentedTest.kt").write_text(behaviour, encoding="utf-8")
(test_dir / "DirectiveRebootReminderInstrumentedTest.kt").write_text(reboot, encoding="utf-8")
print("RUNTIME_ACCEPTANCE_TEST_OVERLAY=PASS files=3")
