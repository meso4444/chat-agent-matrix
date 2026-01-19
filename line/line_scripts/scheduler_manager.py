#!/usr/bin/env python3
# scheduler_manager.py
# Responsible for handling scheduled tasks

import os
import sys
import subprocess
import time
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

# Import configuration
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import TMUX_SESSION_NAME

class SchedulerManager:
    def __init__(self, flask_app=None, image_manager=None):
        self.scheduler = BackgroundScheduler()
        self.app = flask_app
        self.image_manager = image_manager
        self.jobs = []

    def send_command_to_agent(self, agent_name, command):
        """Scheduled task callback function: send command to tmux"""
        system_prompt = f"\n\n【System Prompt】This command is from system scheduled task, please be sure to execute python3 line_notifier.py 'task report...' to report the result after task completion."
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
        """Load tasks from configuration"""
        print(f"🔧 [Scheduler] Starting to load {len(job_list)} tasks...", flush=True)
        for job_cfg in job_list:
            if not job_cfg or not job_cfg.get('active', True):
                continue

            name = job_cfg['name']
            trigger_type = job_cfg['trigger']

            func = None
            args = []

            # A. Agent command tasks
            if job_cfg['type'] == 'agent_command':
                target_agent = job_cfg['agent']
                command = job_cfg['command']
                func = self.send_command_to_agent
                args = [target_agent, command]

            # B. System-level tasks
            elif job_cfg['type'] == 'system':
                action = job_cfg.get('action', '')
                if action == 'cleanup_images' and self.image_manager:
                    func = self.image_manager.cleanup_old_files
                    args = []
                else:
                    print(f"⚠️ [Scheduler] Unknown or unimplemented system action: {action}", flush=True)
                    continue
            else:
                continue

            # Configure trigger
            try:
                if trigger_type == 'cron':
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