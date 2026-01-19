#!/usr/bin/env python3
# scheduler_manager.py
# 負責處理定時任務

import os
import sys
import subprocess
import time
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

# 導入配置
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import TMUX_SESSION_NAME

class SchedulerManager:
    def __init__(self, flask_app=None, image_manager=None):
        self.scheduler = BackgroundScheduler()
        self.app = flask_app
        self.image_manager = image_manager
        self.jobs = []

    def send_command_to_agent(self, agent_name, command):
        """定時任務的回調函數：發送指令到 tmux"""
        system_prompt = f"\n\n【系統提示】此指令來自系統排程任務，任務完成後請務必執行 python3 telegram_notifier.py '任務報告...' 來回報結果。"
        final_message = command + system_prompt
        
        print(f"⏰ [Scheduler] 正在執行定時任務 -> [{agent_name}]: {command}", flush=True)
        
        try:
            subprocess.run([
                'tmux', 'send-keys', '-t', f'{TMUX_SESSION_NAME}:{agent_name}',
                final_message
            ], check=True)
            
            # 增加延遲，確保指令輸入完成後才發送 Enter
            time.sleep(1)
            
            # 發送 Enter
            subprocess.run([
                'tmux', 'send-keys', '-t', f'{TMUX_SESSION_NAME}:{agent_name}',
                'Enter'
            ], check=True)
            
        except Exception as e:
            print(f"❌ [Scheduler] 定時任務執行失敗: {e}", flush=True)

    def load_jobs(self, job_list):
        """從配置載入任務"""
        print(f"🔧 [Scheduler] 開始載入 {len(job_list)} 個任務...", flush=True)
        for job_cfg in job_list:
            if not job_cfg or not job_cfg.get('active', True):
                continue
                
            name = job_cfg['name']
            trigger_type = job_cfg['trigger']
            
            func = None
            args = []
            
            # A. Agent 指令任務
            if job_cfg['type'] == 'agent_command':
                target_agent = job_cfg['agent']
                command = job_cfg['command']
                func = self.send_command_to_agent
                args = [target_agent, command]
                
            # B. 系統級任務
            elif job_cfg['type'] == 'system':
                action = job_cfg.get('action', '')
                if action == 'cleanup_images' and self.image_manager:
                    func = self.image_manager.cleanup_old_files
                    args = []
                else:
                    print(f"⚠️ [Scheduler] 未知或未實作的系統動作: {action}", flush=True)
                    continue
            else:
                continue

            # 設定觸發器
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
                    print(f"⚠️ [Scheduler] 未知的觸發類型: {trigger_type}", flush=True)
                    continue

                self.scheduler.add_job(
                    func, 
                    trigger, 
                    args=args, 
                    id=name, 
                    replace_existing=True
                )
                print(f"📅 [Scheduler] 已註冊任務: {name} ({trigger_type})", flush=True)
                
            except Exception as e:
                print(f"❌ [Scheduler] 註冊任務 {name} 失敗: {e}", flush=True)

    def start(self):
        if not self.scheduler.running:
            self.scheduler.start()
            print("🚀 [Scheduler] 背景排程器已啟動", flush=True)

    def stop(self):
        self.scheduler.shutdown()