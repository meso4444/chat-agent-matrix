# Schedule Task Management Feature Detailed Guide

**Target Audience**: Agent (in knowledge base)
**Purpose**: Help Agents understand how to manage schedule tasks for users

---

## 🎯 Feature Overview

The scheduler system allows users to set up timed tasks without restarting the service. Agents can help users:
- Query existing schedule tasks
- Register new schedule tasks
- Delete unwanted tasks

---

## 📋 User-Delegable Tasks

### 1. Query Existing Schedules

**User Expression**:
- "I want to know what schedule tasks are currently set up"
- "List all schedules"
- "Check the system's automated tasks"

**Agent Operation**:
```bash
curl -X GET http://127.0.0.1:5002/scheduler/jobs
```

**Expected Response**:
```json
{
  "status": "ok",
  "total": 3,
  "jobs": [
    {
      "id": "Daily System Cleanup",
      "trigger": "<CronTrigger (hour=2, minute=0, second=0)>",
      "next_run_time": "2026-02-20 02:00:00"
    }
  ]
}
```

**Agent Response Example**:
```
✅ Currently there are 3 active schedule tasks:
1. Daily System Cleanup - Runs at 2 AM daily
2. Morning News - Runs at 8 AM daily
3. Friday Report - Runs at 5 PM every Friday
```

---

### 2. Register New Schedule

**User Expression**:
- "Set up a morning meeting reminder for me at 8 AM every day"
- "I want to automatically run a task every Monday at 9 AM"
- "Set a check task for the 1st of every month"

**Agent Process**:

#### Step 1: Understand Requirements
Extract from user description:
- ⏰ **Frequency**: Daily / Weekly / Monthly / Custom
- 🕐 **Time**: Specific time (e.g., 8:00)
- 📝 **Content**: What task to execute

#### Step 2: Confirm Parameters
Confirm with user once to avoid misunderstanding:
```
Let me confirm: your schedule is:
- Frequency: Daily
- Time: 8 AM
- Task: Send morning meeting reminder
- Active: Yes

Is that correct?
```

#### Step 3: Construct API Request

Choose the corresponding trigger type based on frequency:

**daily (Every day)**:
```bash
curl -X POST http://127.0.0.1:5002/scheduler/jobs/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Morning Meeting Reminder",
    "type": "agent_command",
    "agent": "Güpa",
    "command": "Remind user of morning meeting",
    "trigger": "daily",
    "hour": 8,
    "minute": 0,
    "second": 0,
    "active": true
  }'
```

**weekly (Every week)**:
```bash
curl -X POST http://127.0.0.1:5002/scheduler/jobs/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Monday Report",
    "type": "agent_command",
    "agent": "Güpa",
    "command": "Generate this week's report",
    "trigger": "weekly",
    "day_of_week": 0,
    "hour": 9,
    "minute": 0,
    "active": true
  }'
```

**monthly (Every month)**:
```bash
curl -X POST http://127.0.0.1:5002/scheduler/jobs/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Monthly Review",
    "type": "agent_command",
    "agent": "Güpa",
    "command": "Conduct monthly review",
    "trigger": "monthly",
    "day": 1,
    "hour": 9,
    "minute": 0,
    "active": true
  }'
```

#### Step 4: Handle Response

**Success (HTTP 200)**:
```json
{
  "status": "ok",
  "job_id": "Morning Meeting Reminder",
  "message": "Schedule task 'Morning Meeting Reminder' registered"
}
```

Respond to user:
```
✅ Schedule successfully set!
Task name: Morning Meeting Reminder
Execution time: Every day at 8:00 AM
Next execution: Tomorrow at 8 AM
```

**Failure (HTTP 400)**:
```json
{
  "status": "error",
  "message": "Missing required fields: hour, minute"
}
```

Respond to user:
```
❌ Failed to set schedule: Missing time parameters
Please tell me the specific time you want (e.g., 8 AM, 3 PM)
```

---

### 3. Delete Schedule

**User Expression**:
- "Cancel the morning meeting reminder I set earlier"
- "Delete the Friday report task"
- "Stop the daily cleanup task"

**Agent Process**:

#### Step 1: Confirm Task Name
```
I found the following related tasks:
1. Morning Meeting Reminder - 8:00 AM daily
2. Morning News - 8:00 AM daily

Which one do you want to delete?
```

#### Step 2: Call API
```bash
curl -X DELETE http://127.0.0.1:5002/scheduler/jobs/Morning\ Meeting\ Reminder
```

#### Step 3: Confirm Result
Success:
```
✅ Schedule task 'Morning Meeting Reminder' deleted
It will stop executing on next update
```

Failure:
```
❌ Deletion failed: No task named 'Morning Meeting Reminder' found
Please check if the task name is correct
```

---

## 🔧 Complete API Endpoint Reference

### Query All Tasks
```
GET http://127.0.0.1:5002/scheduler/jobs
```

### Register New Schedule
```
POST http://127.0.0.1:5002/scheduler/jobs/register
Content-Type: application/json
```

### Delete Schedule
```
DELETE http://127.0.0.1:5002/scheduler/jobs/{job_id}
```

### Refresh Configuration
```
POST http://127.0.0.1:5002/scheduler/refresh
```

---

## ⏰ Trigger Type Details

### daily (Every day)
**When to use**: Need to execute at a fixed time every day

```json
{
  "trigger": "daily",
  "hour": 8,        // 0-23
  "minute": 0,      // 0-59
  "second": 0       // 0-59 (optional, default 0)
}
```

**Example**: Every day at 8:30 AM
```json
{
  "hour": 8,
  "minute": 30,
  "second": 0
}
```

---

### weekly (Every week)
**When to use**: Need to execute on a specific day of the week at a specific time

```json
{
  "trigger": "weekly",
  "day_of_week": 0,  // 0=Monday, 1=Tuesday, ..., 6=Sunday
  "hour": 9,
  "minute": 0
}
```

**Example**: Every Friday at 5 PM
```json
{
  "day_of_week": 4,
  "hour": 17,
  "minute": 0
}
```

---

### monthly (Every month)
**When to use**: Need to execute on a specific day of the month

```json
{
  "trigger": "monthly",
  "day": 1,         // 1-31 (1 = 1st of every month)
  "hour": 9,
  "minute": 0
}
```

**Example**: 15th of every month at noon
```json
{
  "day": 15,
  "hour": 12,
  "minute": 0
}
```

---

### interval (Fixed interval)
**When to use**: Need to execute every N hours/minutes/seconds

```json
{
  "trigger": "interval",
  "hours": 6,       // Hours (optional)
  "minutes": 0,     // Minutes (optional)
  "seconds": 0      // Seconds (optional)
}
```

**Example**: Check every 6 hours
```json
{
  "hours": 6,
  "minutes": 0,
  "seconds": 0
}
```

---

### cron (Complex expression)
**When to use**: Need complex time logic

```json
{
  "trigger": "cron",
  "day_of_week": "0-4",  // Monday to Friday
  "hour": 9,
  "minute": 0
}
```

**Common usage**:
- `"0-4"` = Monday to Friday
- `"5,6"` = Saturday, Sunday
- `"1,15"` = 1st and 15th of each month
- `"L"` = Last day of month

---

## 🎬 Task Types

### agent_command (Agent instruction)
**Purpose**: Periodically send instructions to an Agent

```json
{
  "type": "agent_command",
  "agent": "Güpa",
  "command": "Generate today's report"
}
```

At the specified time, the system automatically sends the command to that Agent's tmux window.

### system (System action)
**Purpose**: Execute system-level operations

```json
{
  "type": "system",
  "action": "cleanup_images"
}
```

**Currently supported actions**:
- `cleanup_images` - Clean up expired images

---

## 📝 Complete Workflow Example

**User requirement**: "I want to automatically generate a weekly report every Monday at 9 AM"

### Step 1: Agent Confirms Requirements
```
Let me confirm:
- Frequency: Every Monday
- Time: 9 AM
- Task: Automatically generate weekly report

Is that correct?
```

### Step 2: Construct Request
```bash
curl -X POST http://127.0.0.1:5002/scheduler/jobs/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Monday Weekly Report Generation",
    "type": "agent_command",
    "agent": "Güpa",
    "command": "Generate weekly report based on this week's data",
    "trigger": "weekly",
    "day_of_week": 0,
    "hour": 9,
    "minute": 0,
    "active": true
  }'
```

### Step 3: Confirm Success
```
✅ Schedule successfully set!
Task: Monday Weekly Report Generation
Frequency: Every Monday
Time: 9:00 AM
Next execution: This Monday at 9 AM
```

---

## 🛡️ Error Handling

### Common Errors

| Error Message | Reason | Solution |
|---------|------|--------|
| Missing required fields | Missing name/type/trigger/active | Check all required fields are filled |
| Invalid trigger type | trigger is not one of the 5 supported types | Confirm using daily/weekly/monthly/cron/interval |
| agent_command requires agent | type is agent_command but missing agent | Add agent field |
| Schedule task 'X' not found | Task doesn't exist when deleting | Query first to confirm task name |

---

## 💡 Best Practices

### ✅ Do (Should do)
1. Communicate with users in natural language, hide technical details
2. Confirm user requirements before executing
3. Provide clear feedback on execution results
4. Remind users to check if schedule is activated
5. Explain errors and provide solutions

### ❌ Don't (Should not do)
1. Expose JSON format or API details to users
2. Assume users know trigger types
3. Create schedules without confirmation
4. Ignore API error messages
5. Use unclear task names (like "task1", "test")

---

**Last updated**: 2026-02-19
