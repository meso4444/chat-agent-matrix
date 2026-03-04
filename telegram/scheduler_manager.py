#!/usr/bin/env python3
# scheduler_manager.py
# 負責處理定時任務

import os
import sys
import subprocess
import time
import yaml
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

# 導入配置
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import TMUX_SESSION_NAME, SCHEDULER_YAML_PATH

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
                elif action == 'rotate_memory_files':
                    func = self._rotate_agent_memory_files
                    args = []
                elif action == 'update_agent_memories':
                    func = self._update_agent_memories
                    args = [job_cfg.get('prompt', '')]
                else:
                    print(f"⚠️ [Scheduler] 未知或未實作的系統動作: {action}", flush=True)
                    continue
            else:
                continue

            # 設定觸發器
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

    def register_job(self, job_config):
        """動態註冊新排程任務"""
        # 驗證必需欄位
        required_fields = ['name', 'type', 'trigger', 'active']
        missing_fields = [f for f in required_fields if f not in job_config]
        if missing_fields:
            return {
                'status': 'error',
                'message': f"缺少必需欄位: {', '.join(missing_fields)}"
            }

        name = job_config['name']
        trigger_type = job_config['trigger']

        # 驗證 trigger 類型
        valid_triggers = ['daily', 'weekly', 'monthly', 'interval', 'cron']
        if trigger_type not in valid_triggers:
            return {
                'status': 'error',
                'message': f"無效的 trigger 類型: {trigger_type}。允許: {', '.join(valid_triggers)}"
            }

        # 驗證 type 欄位
        if job_config['type'] == 'agent_command':
            if 'agent' not in job_config or 'command' not in job_config:
                return {
                    'status': 'error',
                    'message': "agent_command 類型需要 'agent' 和 'command' 欄位"
                }
        elif job_config['type'] == 'system':
            if 'action' not in job_config:
                return {
                    'status': 'error',
                    'message': "system 類型需要 'action' 欄位"
                }
        else:
            return {
                'status': 'error',
                'message': f"無效的 type: {job_config['type']}。允許: agent_command, system"
            }

        # 添加到 scheduler
        try:
            self.load_jobs([job_config])

            # 持久化到 YAML
            self._save_job_to_yaml(job_config)

            return {
                'status': 'ok',
                'job_id': name,
                'message': f"排程任務 '{name}' 已註冊"
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': f"註冊失敗: {str(e)}"
            }

    def delete_job(self, job_id):
        """刪除排程任務"""
        try:
            # 從 APScheduler 移除
            self.scheduler.remove_job(job_id)

            # 從 YAML 移除
            self._remove_job_from_yaml(job_id)

            return {
                'status': 'ok',
                'job_id': job_id,
                'message': f"排程任務 '{job_id}' 已刪除"
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': f"刪除失敗: {str(e)}"
            }

    def refresh_jobs(self):
        """重新讀取 scheduler.yaml 並刷新排程"""
        try:
            # 停止所有現有排程
            existing_jobs = len(self.scheduler.get_jobs())
            for job in self.scheduler.get_jobs():
                self.scheduler.remove_job(job.id)

            # 重新讀取 YAML
            if os.path.exists(SCHEDULER_YAML_PATH):
                with open(SCHEDULER_YAML_PATH, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
                    job_list = config.get('scheduler', [])
            else:
                return {
                    'status': 'error',
                    'message': f"排程配置檔案不存在: {SCHEDULER_YAML_PATH}"
                }

            # 重新載入新排程
            self.load_jobs(job_list)

            new_jobs = len(self.scheduler.get_jobs())

            return {
                'status': 'ok',
                'message': f"排程已刷新",
                'removed_jobs': existing_jobs,
                'loaded_jobs': new_jobs
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': f"刷新失敗: {str(e)}"
            }

    def list_jobs(self):
        """列出所有排程任務"""
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
        """將新任務保存到 scheduler.yaml"""
        if not os.path.exists(SCHEDULER_YAML_PATH):
            # 如果檔案不存在，創建新的
            config = {'scheduler': [job_config]}
        else:
            with open(SCHEDULER_YAML_PATH, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f) or {}
                if 'scheduler' not in config:
                    config['scheduler'] = []

                # 檢查是否已存在同名任務
                for i, job in enumerate(config['scheduler']):
                    if job.get('name') == job_config['name']:
                        config['scheduler'][i] = job_config  # 覆蓋
                        break
                else:
                    config['scheduler'].append(job_config)  # 新增

        # 寫回 YAML
        with open(SCHEDULER_YAML_PATH, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

        print(f"✅ [Scheduler] 任務 '{job_config['name']}' 已保存到 scheduler.yaml", flush=True)

    def _remove_job_from_yaml(self, job_id):
        """從 scheduler.yaml 移除任務"""
        if not os.path.exists(SCHEDULER_YAML_PATH):
            raise Exception(f"排程配置檔案不存在: {SCHEDULER_YAML_PATH}")

        with open(SCHEDULER_YAML_PATH, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f) or {}

        if 'scheduler' not in config:
            raise Exception("scheduler.yaml 中找不到 'scheduler' 欄位")

        # 移除匹配的任務
        original_count = len(config['scheduler'])
        config['scheduler'] = [job for job in config['scheduler'] if job.get('name') != job_id]

        if len(config['scheduler']) == original_count:
            raise Exception(f"找不到名為 '{job_id}' 的排程任務")

        # 寫回 YAML
        with open(SCHEDULER_YAML_PATH, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

        print(f"✅ [Scheduler] 任務 '{job_id}' 已從 scheduler.yaml 移除", flush=True)

    def _rotate_agent_memory_files(self):
        """輪轉配置清單中 Agent 的記憶檔（每天 00:00 執行）"""
        print("🔄 [Scheduler] 開始輪轉 Agent 記憶檔…", flush=True)

        try:
            from config import AGENTS
        except ImportError:
            print(f"⚠️ [Scheduler] 無法導入 AGENTS 清單", flush=True)
            return

        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        agent_home_path = os.path.join(base_dir, 'agent_home')

        if not os.path.exists(agent_home_path):
            print(f"⚠️ [Scheduler] Agent home 目錄不存在: {agent_home_path}", flush=True)
            return

        # 獲取前一天的日期
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')

        # 只處理配置清單中的 Agent
        try:
            for agent in AGENTS:
                agent_name = agent['name']
                agent_dir = os.path.join(agent_home_path, agent_name)

                if not os.path.isdir(agent_dir):
                    print(f"⚠️ [Scheduler] Agent 目錄不存在: {agent_dir}", flush=True)
                    continue

                memory_dir = os.path.join(agent_dir, 'memory')
                if not os.path.exists(memory_dir):
                    os.makedirs(memory_dir, exist_ok=True)

                memory_file = os.path.join(memory_dir, 'memory.md')
                archived_file = os.path.join(memory_dir, f'memory_{yesterday}.md')

                # 如果當日記憶檔存在，備份到前一天
                if os.path.exists(memory_file):
                    try:
                        with open(memory_file, 'r', encoding='utf-8') as f:
                            content = f.read()

                        # 寫入歷史檔
                        with open(archived_file, 'w', encoding='utf-8') as f:
                            f.write(content)

                        # 重新初始化當日檔
                        today = datetime.now().strftime('%Y-%m-%d')
                        with open(memory_file, 'w', encoding='utf-8') as f:
                            f.write(f"# {agent_name} 的每日記憶\n\n")
                            f.write(f"**日期**: {today}\n\n")
                            f.write("## 今日任務記錄\n\n")

                        print(f"✅ [Scheduler] {agent_name} 記憶檔已輪轉 → {archived_file}", flush=True)

                    except Exception as e:
                        print(f"❌ [Scheduler] {agent_name} 記憶檔輪轉失敗: {e}", flush=True)

        except Exception as e:
            print(f"❌ [Scheduler] 記憶檔輪轉過程出錯: {e}", flush=True)

    def _update_agent_memories(self, prompt):
        """向配置清單中的所有 Agent 注入記憶更新 prompt"""
        if not prompt:
            print(f"⚠️ [Scheduler] 記憶更新 prompt 為空", flush=True)
            return

        try:
            from config import AGENTS
        except ImportError:
            print(f"⚠️ [Scheduler] 無法導入 AGENTS 清單", flush=True)
            return

        print(f"📝 [Scheduler] 開始向所有 Agent 注入記憶更新 prompt…", flush=True)

        # 向配置清單中的每個 Agent 注入 prompt
        try:
            for agent in AGENTS:
                agent_name = agent['name']
                try:
                    # 使用 tmux send-keys 向 Agent 窗口注入 prompt
                    subprocess.run([
                        'tmux', 'send-keys', '-t', f'{TMUX_SESSION_NAME}:{agent_name}',
                        '-l', prompt
                    ], check=True)

                    time.sleep(0.3)

                    subprocess.run([
                        'tmux', 'send-keys', '-t', f'{TMUX_SESSION_NAME}:{agent_name}',
                        'Enter'
                    ], check=True)

                    # 雙重保險
                    time.sleep(0.2)
                    subprocess.run([
                        'tmux', 'send-keys', '-t', f'{TMUX_SESSION_NAME}:{agent_name}',
                        'Enter'
                    ], check=True)

                    print(f"✅ [Scheduler] 已向 {agent_name} 注入記憶更新 prompt", flush=True)

                except Exception as e:
                    print(f"❌ [Scheduler] 向 {agent_name} 注入 prompt 失敗: {e}", flush=True)

        except Exception as e:
            print(f"❌ [Scheduler] 記憶更新過程出錯: {e}", flush=True)