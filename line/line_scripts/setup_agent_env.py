#!/usr/bin/env python3
# setup_agent_env.py
# Responsible for initializing Agent home directory structure and collaboration links

import os
import sys
import yaml
import shutil

# Define paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(BASE_DIR, 'config.yaml')
AGENT_HOME_BASE = os.path.join(BASE_DIR, 'agent_home')
TEMPLATES_DIR = os.path.join(BASE_DIR, 'agent_home_rules_templates')

def load_config():
    if not os.path.exists(CONFIG_PATH):
        print(f"❌ Error: Configuration file not found {CONFIG_PATH}")
        sys.exit(1)
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def setup_agent_dirs(agent_name):
    """Create directory structure for single Agent"""
    home = os.path.join(AGENT_HOME_BASE, agent_name)
    subdirs = ['toolbox', 'knowledge', 'my_shared_space', 'images_temp']

    for d in subdirs:
        path = os.path.join(home, d)
        if not os.path.exists(path):
            os.makedirs(path)
            # print(f"   + Created directory: {d}")

    return home

def setup_collaboration_links(agents, groups):
    """Create symlinks for collaboration groups and clean up stale old links"""
    agent_names = [a['name'] for a in agents]

    # 1. Calculate all "should exist" links (Expected Links)
    # Format: {agent_home: set([partner_link_name, ...])}
    expected_links = {name: set() for name in agent_names}

    if groups:
        for group in groups:
            members = group.get('members', [])
            valid_members = [m for m in members if m in agent_names]

            if len(valid_members) < 2:
                continue

            print(f"🔗 Processing collaboration group: {group.get('name', 'unnamed')} ({', '.join(valid_members)})")

            # Full mesh connectivity
            for me in valid_members:
                my_home = os.path.join(AGENT_HOME_BASE, me)
                for partner in valid_members:
                    if me == partner:
                        continue

                    # Link target and name
                    target_real_path = os.path.join(AGENT_HOME_BASE, partner, 'my_shared_space')
                    link_name = f"{partner}_shared_space" # Store filename only
                    full_link_path = os.path.join(my_home, link_name)

                    # Record in expected list
                    expected_links[me].add(link_name)

                    # Calculate relative path
                    rel_target = os.path.relpath(target_real_path, my_home)

                    if not os.path.exists(full_link_path):
                        try:
                            os.symlink(rel_target, full_link_path)
                            print(f"   + Created link: {me} -> {partner}")
                        except OSError as e:
                            print(f"   ⚠️ Failed to create link: {e}")

    # 2. Clean up stale old links (Cleanup Stale Links)
    print("🧹 Checking and cleaning up stale collaboration links...")
    for agent in agent_names:
        home = os.path.join(AGENT_HOME_BASE, agent)
        if not os.path.exists(home):
            continue

        # Scan all files in Agent home
        for item in os.listdir(home):
            # Only process symlinks ending with this suffix
            if item.endswith("_shared_space"):
                full_path = os.path.join(home, item)

                # Check if it is a symlink
                if os.path.islink(full_path):
                    # If this link is not in expected list, delete it
                    if item not in expected_links[agent]:
                        try:
                            os.unlink(full_path)
                            print(f"   - Removed stale link: {agent}/{item}")
                        except OSError as e:
                            print(f"   ⚠️ Failed to remove: {e}")

def apply_manual_templates(agent_name, home_path, engine):
    """Check if there are manually defined protocol templates, copy if exists"""
    template_file = os.path.join(TEMPLATES_DIR, f"{agent_name}.md")
    target_file = os.path.join(home_path, f"{engine.upper()}.md")

    if os.path.exists(template_file):
        print(f"   📄 Found custom protocol: {agent_name}.md -> copying")
        shutil.copy2(template_file, target_file)
        return True # Indicates manual protocol exists
    return False

def main():
    print("🧬  Initializing Agent ecosystem...")
    config = load_config()
    agents = config.get('agents', [])
    groups = config.get('collaboration_groups', [])

    # 1. Create directories
    for agent in agents:
        name = agent['name']
        engine = agent['engine']
        # print(f"   🏠 Agent: {name}")
        home = setup_agent_dirs(name)

        # 2. Check manual templates
        apply_manual_templates(name, home, engine)

    # 3. Create collaboration links
    setup_collaboration_links(agents, groups)

    print("✅ Environment initialization complete")

if __name__ == '__main__':
    main()
