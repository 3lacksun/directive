#!/usr/bin/env python3
from pathlib import Path
import sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else "build-src")
path = root / "app/src/main/kotlin/com/example/directive/feature/tasks/TasksScreen.kt"
text = path.read_text(encoding="utf-8")
target = r'''package com.example.directive.feature.tasks

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.lifecycle.viewmodel.compose.viewModel
import com.example.directive.domain.model.TaskPriority
import com.example.directive.domain.model.TaskStatus
import java.time.LocalDate

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun TasksScreen(modifier:Modifier=Modifier,onEditTask:(String)->Unit={},vm:TasksViewModel=viewModel()){
    val state by vm.state.collectAsStateWithLifecycle()
    LazyColumn(
        modifier=modifier.fillMaxSize(),
        contentPadding=PaddingValues(16.dp),
        verticalArrangement=Arrangement.spacedBy(10.dp),
    ){
        item { Text("Tasks",style=MaterialTheme.typography.headlineMedium) }
        item { OutlinedTextField(state.query,vm::search,label={Text("Search title, notes, Category or checklist")},modifier=Modifier.fillMaxWidth(),singleLine=true) }
        item {
            LazyRow(horizontalArrangement=Arrangement.spacedBy(6.dp)) {
                items(TaskSmartList.entries,key={it.name}) { list ->
                    FilterChip(selected=state.categoryFilter==null && state.list==list,onClick={vm.select(list)},label={Text(list.label)})
                }
            }
        }
        item { Text("Categories",style=MaterialTheme.typography.labelLarge) }
        item {
            LazyRow(horizontalArrangement=Arrangement.spacedBy(6.dp)){
                item { FilterChip(selected=state.categoryFilter==TasksViewModel.UNCATEGORISED,onClick={vm.selectCategory(TasksViewModel.UNCATEGORISED)},label={Text("Uncategorised (${state.counts[null]?:0})")}) }
                items(state.categories,key={it.id}) { c ->
                    FilterChip(selected=state.categoryFilter==c.id,onClick={vm.selectCategory(c.id)},label={Text("${c.name} (${state.counts[c.id]?:0})")})
                }
            }
        }
        item { Text("Filters",style=MaterialTheme.typography.labelLarge) }
        item {
            LazyRow(horizontalArrangement=Arrangement.spacedBy(6.dp)){
                item { FilterChip(selected=state.filters.priority==TaskPriority.HIGH,onClick={vm.setPriority(if(state.filters.priority==TaskPriority.HIGH)null else TaskPriority.HIGH)},label={Text("High priority")}) }
                item { FilterChip(selected=state.filters.status==TaskStatus.ACTIVE,onClick={vm.setStatus(if(state.filters.status==TaskStatus.ACTIVE)null else TaskStatus.ACTIVE)},label={Text("Incomplete")}) }
                item { FilterChip(selected=state.filters.status==TaskStatus.COMPLETED,onClick={vm.setStatus(if(state.filters.status==TaskStatus.COMPLETED)null else TaskStatus.COMPLETED)},label={Text("Completed")}) }
                item { FilterChip(selected=state.filters.scheduled==true,onClick={vm.setScheduled(if(state.filters.scheduled==true)null else true)},label={Text("Scheduled")}) }
                item { FilterChip(selected=state.filters.scheduled==false,onClick={vm.setScheduled(if(state.filters.scheduled==false)null else false)},label={Text("Unscheduled")}) }
                item { FilterChip(selected=state.filters.recurring==true,onClick={vm.setRecurring(if(state.filters.recurring==true)null else true)},label={Text("Recurring")}) }
                item { FilterChip(selected=state.filters.recurring==false,onClick={vm.setRecurring(if(state.filters.recurring==false)null else false)},label={Text("Non-recurring")}) }
                item { FilterChip(selected=state.filters.startDate==LocalDate.now(),onClick={vm.setStartDate(if(state.filters.startDate==LocalDate.now())null else LocalDate.now())},label={Text("Starts today")}) }
                item { FilterChip(selected=state.filters.dueDate==LocalDate.now(),onClick={vm.setDueDate(if(state.filters.dueDate==LocalDate.now())null else LocalDate.now())},label={Text("Due today")}) }
            }
        }
        item { Text("Sort",style=MaterialTheme.typography.labelLarge) }
        item {
            LazyRow(horizontalArrangement=Arrangement.spacedBy(6.dp)){
                items(TaskSort.entries,key={it.name}) { sort -> FilterChip(selected=state.filters.sort==sort,onClick={vm.setSort(sort)},label={Text(sort.label)}) }
                if(state.filters.active) item { AssistChip(onClick=vm::clearFilters,label={Text("Clear filters")}) }
            }
        }
        items(state.tasks,key={"${it.task.id}-${it.occurrenceKey.orEmpty()}-${it.occurrenceCompleted}"}){item->
            val task=item.task
            ElevatedCard(Modifier.fillMaxWidth()){
                Row(Modifier.fillMaxWidth().padding(12.dp)){
                    Column(Modifier.weight(1f)){
                        Text(task.title)
                        Text(listOfNotNull(task.durationMinutes?.let{"${it}m"},task.dueAt?.let{"Deadline"},(item.seriesId ?: task.seriesId)?.let{if(item.occurrenceKey!=null)"Recurring occurrence" else "Recurring series"}).joinToString(" • "),style=MaterialTheme.typography.bodySmall)
                    }
                    Column {
                        val archivedOrDeleted = task.archivedAt != null || task.deletedAt != null
                        if(archivedOrDeleted) {
                            TextButton(onClick={vm.restore(item)}){Text("Restore")}
                        } else if(item.seriesId!=null && item.occurrenceKey!=null) {
                            TextButton(onClick={vm.toggleComplete(item)}){Text(if(item.occurrenceCompleted)"Reopen" else "Complete")}
                            if(!item.occurrenceCompleted) TextButton(onClick={vm.skipOccurrence(item)}){Text("Skip")}
                            TextButton(onClick={vm.editThisOccurrence(item,onEditTask)}){Text("This occurrence")}
                            TextButton(onClick={vm.editThisAndFuture(item,onEditTask)}){Text("This + future")}
                            TextButton(onClick={onEditTask(item.rootTaskId ?: task.id)}){Text("Entire series")}
                        } else {
                            TextButton(onClick={onEditTask(task.id)}){Text("Edit")}
                            if(!item.isSeriesDefinition) TextButton(onClick={vm.toggleComplete(item)}){Text(if(task.completedAt!=null)"Reopen" else "Complete")}
                        }
                    }
                }
            }
        }
        if(state.tasks.isEmpty()) item { Text("Nothing here.",style=MaterialTheme.typography.bodyMedium) }
    }
}
'''

if text == target:
    print("TASKS_LANDSCAPE_FIX=PASS changed=0")
elif "Column(modifier.fillMaxSize().padding(16.dp)" in text and "LazyColumn(verticalArrangement=Arrangement.spacedBy(8.dp))" in text:
    path.write_text(target, encoding="utf-8")
    print("TASKS_LANDSCAPE_FIX=PASS changed=1")
else:
    raise SystemExit("Expected pre-remediation TasksScreen structure not found")
