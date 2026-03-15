# Schedule Task Management Feature Detailed Guide

**Audience**: Agent (in knowledge base)
**Purpose**: Help Agent understand how to manage scheduled tasks for users

---

## 🎯 Feature Overview

The scheduling system allows users to set up timed tasks without restarting services. Agent can help users:
- Query existing scheduled tasks
- Register new scheduled tasks
- Delete unnecessary tasks

---

## 📋 Tasks Users Can Delegate

### 1. Query Existing Schedules

**User Expression**:
- "I want to know what scheduled tasks currently exist"
- "List all schedules"
- "Check what automatic tasks are set in the system"

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

**Sample Agent Response**:
```
✅ There are currently 3 active scheduled tasks:
1. Daily System Cleanup - runs at 2:00 AM every day
2. Morning News - runs at 8:00 AM every day
3. Friday Report - runs at 5:00 PM every Friday
```

---

### 2. Register New Schedule

**User Expression**:
- "Set up a morning meeting reminder for 8 AM every day"
- "I want to automatically execute a task every Monday at 9 AM"
- "Schedule a check task for the 1st of every month"

**Agent Workflow**:

#### Step 1: Understand Requirements
Extract from user description:
- ⏰ **Frequency**: Daily / Weekly / Monthly / Custom
- 🕐 **Time**: Specific time (e.g., 8:00 AM)
- 📝 **Content**: What task to execute

#### Step 2: Confirm Parameters
Confirm with user to avoid misunderstanding:
```
Let me confirm: The schedule you want to set is:
- Frequency: Daily
- Time: 8:00 AM
- Task: Send morning meeting reminder
- Active: Yes

Is this correct?
```

#### Step 3: Construct API Request

Select appropriate trigger type based on frequency:

**daily (Every Day)**:
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

**weekly (Every Week)**:
```bash
curl -X POST http://127.0.0.1:5002/scheduler/jobs/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Monday Report",
    "type": "agent_command",
    "agent": "Güpa",
    "command": "Generate weekly report",
    "trigger": "weekly",
    "day_of_week": 0,
    "hour": 9,
    "minute": 0,
    "active": true
  }'
```

**monthly (Every Month)**:
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

**Success** (HTTP 200):
```json
{
  "status": "ok",
  "job_id": "Morning Meeting Reminder",
  "message": "Schedule task 'Morning Meeting Reminder' has been registered"
}
```

Response to user:
```
✅ Schedule has been successfully set!
Task Name: Morning Meeting Reminder
Execution Time: 8:00 AM daily
Next Execution: Tomorrow at 8:00 AM
```

**Failure** (HTTP 400):
```json
{
  "status": "error",
  "message": "Missing required field: hour, minute"
}
```

Response to user:
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

**Agent Workflow**:

#### Step 1: Confirm Task Name
```
I found the following related tasks:
1. Morning Meeting Reminder - 8:00 AM daily
2. Morning News - 8:00 AM daily

Which one do you want to delete?
```

#### Step 2: Call API
```bash
curl -X DELETE http://127.0.0.1:5002/scheduler/jobs/Morning%20Meeting%20Reminder
```

#### Step 3: Confirm Result
Success:
```
✅ Schedule task 'Morning Meeting Reminder' has been deleted
It will stop executing on the next update
```

Failure:
```
❌ Deletion failed: Cannot find task named 'Morning Meeting Reminder'
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

## ⏰ Trigger Type Detailed Explanation

### daily (Every Day)
**When to Use**: Need to execute at a fixed time every day

```json
{
  "trigger": "daily",
  "hour": 8,        // 0-23
  "minute": 0,      // 0-59
  "second": 0       // 0-59 (optional, default 0)
}
```

**Example**: 8:30 AM every day
```json
{
  "hour": 8,
  "minute": 30,
  "second": 0
}
```

---

### weekly (Every Week)
**When to Use**: Need to execute at a specific time on a specific day of week

```json
{
  "trigger": "weekly",
  "day_of_week": 0,  // 0=Monday, 1=Tuesday, ..., 6=Sunday
  "hour": 9,
  "minute": 0
}
```

**Example**: 5:00 PM every Friday
```json
{
  "day_of_week": 4,
  "hour": 17,
  "minute": 0
}
```

---

### monthly (Every Month)
**When to Use**: Need to execute on a specific date every month

```json
{
  "trigger": "monthly",
  "day": 1,         // 1-31 (1 = 1st of every month)
  "hour": 9,
  "minute": 0
}
```

**Example**: Noon on the 15th of every month
```json
{
  "day": 15,
  "hour": 12,
  "minute": 0
}
```

---

### interval (Fixed Interval)
**When to Use**: Need to execute every N hours/minutes/seconds

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

### cron (Complex Expression)
**When to Use**: Need complex time logic

```json
{
  "trigger": "cron",
  "day_of_week": "0-4",  // Monday to Friday
  "hour": 9,
  "minute": 0
}
```

**Common Usage**:
- `"0-4"` = Monday to Friday
- `"5,6"` = Saturday, Sunday
- `"1,15"` = 1st and 15th of month
- `"L"` = Last day of month

---

## 🎬 Task Types

### agent_command (Agent Command)
**Purpose**: Send commands to Agent at scheduled time

```json
{
  "type": "agent_command",
  "agent": "Güpa",
  "command": "Generate today's report"
}
```

At the specified time, system automatically sends command to the Agent's tmux window.

### system (System Action)
**Purpose**: Execute system-level operations

```json
{
  "type": "system",
  "action": "cleanup_images"
}
```

**Currently Supported Actions**:
- `cleanup_images` - Clean up expired images

---

## 📝 Complete Workflow Example

**User Requirement**: "I want to automatically generate a weekly report every Monday at 9 AM"

### Step 1: Agent Confirms Requirement
```
Let me confirm:
- Frequency: Every Monday
- Time: 9:00 AM
- Content: Automatically generate weekly report

Is this correct?
```

### Step 2: Construct Request
```bash
curl -X POST http://127.0.0.1:5002/scheduler/jobs/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Monday Weekly Report Generation",
    "type": "agent_command",
    "agent": "Güpa",
    "command": "Generate weekly report based on this week'\''s data",
    "trigger": "weekly",
    "day_of_week": 0,
    "hour": 9,
    "minute": 0,
    "active": true
  }'
```

### Step 3: Confirm Success
```
✅ Schedule has been successfully set!
Task: Monday Weekly Report Generation
Frequency: Every Monday
Time: 9:00 AM
Next Execution: This Monday at 9:00 AM
```

---

## 🛡️ Error Handling

### Common Errors

| Error Message | Cause | Solution |
|---------|------|--------|
| Missing required field | Missing name/type/trigger/active | Check all required fields are filled |
| Invalid trigger type | trigger is not one of 5 supported types | Confirm using daily/weekly/monthly/cron/interval |
| agent_command requires agent | type is agent_command but missing agent field | Add agent field |
| Cannot find schedule named X | Task doesn't exist when deleting | Query first to confirm task name |

---

## 💡 Best Practices

### ✅ Do (Should Do)
1. Communicate with users in natural language, hide technical details
2. Confirm user requirements before executing
3. Provide clear feedback of execution results
4. Remind users to check if schedule is active
5. Explain errors and provide solutions when issues occur

### ❌ Don't (Should Not Do)
1. Expose JSON format or API details to users
2. Assume users know about trigger types
3. Create schedules without confirmation
4. Ignore error messages returned by API
5. Use unclear task names (like "task1", "test")

---

**Last Updated**: 2026-02-19
