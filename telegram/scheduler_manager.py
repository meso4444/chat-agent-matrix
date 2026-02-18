#!/usr/bin/env python3
# scheduler_manager.py
# Responsible for handling scheduled tasks

import os
import sys
import subprocess
import time
import yaml
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

# Import configuration
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import TMUX_SESSION_NAME, SCHEDULER_YAML_PATH

class SchedulerManager:
    def __init__(self, flask_app=None, image_manager=None):
        self.scheduler = BackgroundScheduler()
        self.app = flask_app
        self.image_manager = image_manager
        self.jobs = []

    def send_command_to_agent(self, agent_name, command):
        """Callback function for scheduled tasks: send command to tmux"""
        system_prompt = f"\n\n【System Prompt】This command is from system scheduled task. After task completion, you must execute python3 telegram_notifier.py 'Task report...' to report the result."
        final_message = command + system_prompt

        print(f"⏰ [Scheduler] Executing scheduled task -> [{agent_name}]: {command}", flush=True)

        try:
            subprocess.run([
                'tmux', 'send-keys', '-t', f'{TMUX_SESSION_NAME}:{agent_name}',
                final_message
            ], check=True)

            # Add delay to ensure command input is complete before sending Enter
            time.sleep(1)

            # Send Enter
            subprocess.run([
                'tmux', 'send-keys', '-t', f'{TMUX_SESSION_NAME}:{agent_name}',
                'Enter'
            ], check=True)

        except Exception as e:
            print(f"❌ [Scheduler] Scheduled task execution failed: {e}", flush=True)

    def load_jobs(self, job_list):
        """Load jobs from configuration"""
        print(f"🔧 [Scheduler] Starting to load {len(job_list)} tasks...", flush=True)
        for job_cfg in job_list:
            if not job_cfg or not job_cfg.get('active', True):
                continue

            name = job_cfg['name']
            trigger_type = job_cfg['trigger']

            func = None
            args = []

            # A. Agent command task
            if job_cfg['type'] == 'agent_command':
                target_agent = job_cfg['agent']
                command = job_cfg['command']
                func = self.send_command_to_agent
                args = [target_agent, command]

            # B. System-level task
            elif job_cfg['type'] == 'system':
                action = job_cfg.get('action', '')
                if action == 'cleanup_images' and self.image_manager:
                    func = self.image_manager.cleanup_old_files
                    args = []
                elif action == 'rotate_memory_files':
                    func = self._rotate_agent_memory_files
                    args = []
                elif action == 'update_agent_memories':
                    func = self._update_agent_memories
                    args = [job_cfg.get('prompt', '')]
                else:
                    print(f"⚠️ [Scheduler] Unknown or unimplemented system action: {action}", flush=True)
                    continue
            else:
                continue

            # Set up trigger
            try:
                if trigger_type == 'daily':
                    trigger = CronTrigger(
                        hour=job_cfg.get('hour', 0),
                        minute=job_cfg.get('minute', 0),
                        second=job_cfg.get('second', 0)
                    )
                elif trigger_type == 'weekly':
                    trigger = CronTrigger(
                        day_of_week=job_cfg.get('day_of_week', 0),
                        hour=job_cfg.get('hour', 0),
                        minute=job_cfg.get('minute', 0),
                        second=job_cfg.get('second', 0)
                    )
                elif trigger_type == 'monthly':
                    trigger = CronTrigger(
                        day=job_cfg.get('day', 1),
                        hour=job_cfg.get('hour', 0),
                        minute=job_cfg.get('minute', 0),
                        second=job_cfg.get('second', 0)
                    )
                elif trigger_type == 'cron':
                    trigger = CronTrigger(
                        hour=job_cfg.get('hour', '*'),
                        minute=job_cfg.get('minute', '0'),
                        second=job_cfg.get('second', '0')
                    )
                elif trigger_type == 'interval':
                    trigger = IntervalTrigger(
                        hours=job_cfg.get('hours', job_cfg.get('hour', 0)),
                        minutes=job_cfg.get('minutes', job_cfg.get('minute', 0)),
                        seconds=job_cfg.get('seconds', job_cfg.get('second', 0))
                    )
                else:
                    print(f"⚠️ [Scheduler] Unknown trigger type: {trigger_type}", flush=True)
                    continue

                self.scheduler.add_job(
                    func,
                    trigger,
                    args=args,
                    id=name,
                    replace_existing=True
                )
                print(f"📅 [Scheduler] Task registered: {name} ({trigger_type})", flush=True)

            except Exception as e:
                print(f"❌ [Scheduler] Failed to register task {name}: {e}", flush=True)

    def start(self):
        if not self.scheduler.running:
            self.scheduler.start()
            print("🚀 [Scheduler] Background scheduler started", flush=True)

    def stop(self):
        self.scheduler.shutdown()

    def register_job(self, job_config):
        """Dynamically register new scheduled task"""
        # Validate required fields
        required_fields = ['name', 'type', 'trigger', 'active']
        missing_fields = [f for f in required_fields if f not in job_config]
        if missing_fields:
            return {
                'status': 'error',
                'message': f"Missing required fields: {', '.join(missing_fields)}"
            }

        name = job_config['name']
        trigger_type = job_config['trigger']

        # Validate trigger type
        valid_triggers = ['daily', 'weekly', 'monthly', 'interval', 'cron']
        if trigger_type not in valid_triggers:
            return {
                'status': 'error',
                'message': f"Invalid trigger type: {trigger_type}. Allowed: {', '.join(valid_triggers)}"
            }

        # Validate type field
        if job_config['type'] == 'agent_command':
            if 'agent' not in job_config or 'command' not in job_config:
                return {
                    'status': 'error',
                    'message': "agent_command type requires 'agent' and 'command' fields"
                }
        elif job_config['type'] == 'system':
            if 'action' not in job_config:
                return {
                    'status': 'error',
                    'message': "system type requires 'action' field"
                }
        else:
            return {
                'status': 'error',
                'message': f"Invalid type: {job_config['type']}. Allowed: agent_command, system"
            }

        # Add to scheduler
        try:
            self.load_jobs([job_config])

            # Persist to YAML
            self._save_job_to_yaml(job_config)

            return {
                'status': 'ok',
                'job_id': name,
                'message': f"Schedule task '{name}' registered"
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': f"Registration failed: {str(e)}"
            }

    def delete_job(self, job_id):
        """Delete scheduled task"""
        try:
            # Remove from APScheduler
            self.scheduler.remove_job(job_id)

            # Remove from YAML
            self._remove_job_from_yaml(job_id)

            return {
                'status': 'ok',
                'job_id': job_id,
                'message': f"Schedule task '{job_id}' deleted"
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': f"Deletion failed: {str(e)}"
            }

    def refresh_jobs(self):
        """Re-read scheduler.yaml and refresh schedules"""
        try:
            # Stop all existing schedules
            existing_jobs = len(self.scheduler.get_jobs())
            for job in self.scheduler.get_jobs():
                self.scheduler.remove_job(job.id)

            # Re-read YAML
            if os.path.exists(SCHEDULER_YAML_PATH):
                with open(SCHEDULER_YAML_PATH, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
                    job_list = config.get('scheduler', [])
            else:
                return {
                    'status': 'error',
                    'message': f"Schedule config file not found: {SCHEDULER_YAML_PATH}"
                }

            # Reload new schedules
            self.load_jobs(job_list)

            new_jobs = len(self.scheduler.get_jobs())

            return {
                'status': 'ok',
                'message': f"Schedule refreshed",
                'removed_jobs': existing_jobs,
                'loaded_jobs': new_jobs
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': f"Refresh failed: {str(e)}"
            }

    def list_jobs(self):
        """List all scheduled tasks"""
        jobs = []
        for job in self.scheduler.get_jobs():
            job_info = {
                'id': job.id,
                'trigger': str(job.trigger),
                'next_run_time': str(job.next_run_time) if job.next_run_time else None
            }
            jobs.append(job_info)
        return {
            'status': 'ok',
            'total': len(jobs),
            'jobs': jobs
        }

    def _save_job_to_yaml(self, job_config):
        """Save new task to scheduler.yaml"""
        if not os.path.exists(SCHEDULER_YAML_PATH):
            # Create new file if it doesn't exist
            config = {'scheduler': [job_config]}
        else:
            with open(SCHEDULER_YAML_PATH, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f) or {}
                if 'scheduler' not in config:
                    config['scheduler'] = []

                # Check if task with same name already exists
                for i, job in enumerate(config['scheduler']):
                    if job.get('name') == job_config['name']:
                        config['scheduler'][i] = job_config  # Override
                        break
                else:
                    config['scheduler'].append(job_config)  # Add

        # Write back to YAML
        with open(SCHEDULER_YAML_PATH, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

        print(f"✅ [Scheduler] Task '{job_config['name']}' saved to scheduler.yaml", flush=True)

    def _remove_job_from_yaml(self, job_id):
        """Remove task from scheduler.yaml"""
        if not os.path.exists(SCHEDULER_YAML_PATH):
            raise Exception(f"Schedule config file not found: {SCHEDULER_YAML_PATH}")

        with open(SCHEDULER_YAML_PATH, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f) or {}

        if 'scheduler' not in config:
            raise Exception("Cannot find 'scheduler' field in scheduler.yaml")

        # Remove matching task
        original_count = len(config['scheduler'])
        config['scheduler'] = [job for job in config['scheduler'] if job.get('name') != job_id]

        if len(config['scheduler']) == original_count:
            raise Exception(f"Schedule task '{job_id}' not found")

        # Write back to YAML
        with open(SCHEDULER_YAML_PATH, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

        print(f"✅ [Scheduler] Task '{job_id}' removed from scheduler.yaml", flush=True)

    def _rotate_agent_memory_files(self):
        """Rotate memory files for Agents in config list (execute at 00:00 daily)"""
        print("🔄 [Scheduler] Starting Agent memory file rotation…", flush=True)

        try:
            from config import AGENTS
        except ImportError:
            print(f"⚠️ [Scheduler] Unable to import AGENTS list", flush=True)
            return

        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        agent_home_path = os.path.join(base_dir, 'agent_home')

        if not os.path.exists(agent_home_path):
            print(f"⚠️ [Scheduler] Agent home directory not found: {agent_home_path}", flush=True)
            return

        # Get yesterday's date
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')

        # Only process Agents in config list
        try:
            for agent in AGENTS:
                agent_name = agent['name']
                agent_dir = os.path.join(agent_home_path, agent_name)

                if not os.path.isdir(agent_dir):
                    print(f"⚠️ [Scheduler] Agent directory not found: {agent_dir}", flush=True)
                    continue

                memory_dir = os.path.join(agent_dir, 'memory')
                if not os.path.exists(memory_dir):
                    os.makedirs(memory_dir, exist_ok=True)

                memory_file = os.path.join(memory_dir, 'memory.md')
                archived_file = os.path.join(memory_dir, f'memory_{yesterday}.md')

                # If current memory file exists, back it up to yesterday
                if os.path.exists(memory_file):
                    try:
                        with open(memory_file, 'r', encoding='utf-8') as f:
                            content = f.read()

                        # Write to history file
                        with open(archived_file, 'w', encoding='utf-8') as f:
                            f.write(content)

                        # Re-initialize current memory file
                        today = datetime.now().strftime('%Y-%m-%d')
                        with open(memory_file, 'w', encoding='utf-8') as f:
                            f.write(f"# {agent_name} Daily Memory\n\n")
                            f.write(f"**Date**: {today}\n\n")
                            f.write("## Today's Task Record\n\n")

                        print(f"✅ [Scheduler] {agent_name} memory file rotated → {archived_file}", flush=True)

                    except Exception as e:
                        print(f"❌ [Scheduler] {agent_name} memory file rotation failed: {e}", flush=True)

        except Exception as e:
            print(f"❌ [Scheduler] Error during memory file rotation: {e}", flush=True)

    def _update_agent_memories(self, prompt):
        """Inject memory update prompt to all Agents in config list"""
        if not prompt:
            print(f"⚠️ [Scheduler] Memory update prompt is empty", flush=True)
            return

        try:
            from config import AGENTS
        except ImportError:
            print(f"⚠️ [Scheduler] Unable to import AGENTS list", flush=True)
            return

        print(f"📝 [Scheduler] Starting to inject memory update prompt to all Agents…", flush=True)

        # Inject prompt to each Agent in config list
        try:
            for agent in AGENTS:
                agent_name = agent['name']
                try:
                    # Use tmux send-keys to inject prompt to Agent window
                    subprocess.run([
                        'tmux', 'send-keys', '-t', f'{TMUX_SESSION_NAME}:{agent_name}',
                        '-l', prompt
                    ], check=True)

                    time.sleep(0.3)

                    subprocess.run([
                        'tmux', 'send-keys', '-t', f'{TMUX_SESSION_NAME}:{agent_name}',
                        'Enter'
                    ], check=True)

                    # Double insurance
                    time.sleep(0.2)
                    subprocess.run([
                        'tmux', 'send-keys', '-t', f'{TMUX_SESSION_NAME}:{agent_name}',
                        'Enter'
                    ], check=True)

                    print(f"✅ [Scheduler] Memory update prompt injected to {agent_name}", flush=True)

                except Exception as e:
                    print(f"❌ [Scheduler] Failed to inject prompt to {agent_name}: {e}", flush=True)

        except Exception as e:
            print(f"❌ [Scheduler] Error during memory update: {e}", flush=True)
