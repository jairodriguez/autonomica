#!/usr/bin/env python3
import json
import sys

def add_task_to_json():
    tasks_file = '.taskmaster/tasks/tasks.json'
    
    # New task to add
    new_task = {
        "id": 13,
        "title": "ChatGPT-like Project Management Interface",
        "description": "Create a ChatGPT-style project management interface with expandable project folders, agent hierarchies, and real-time status indicators",
        "details": "Build a modern project management interface that mimics ChatGPT's design patterns:\n- Left sidebar with expandable project folders\n- Agent hierarchies displayed under each project\n- Real-time status indicators (busy/spinning, idle/green, error/red, offline/gray)\n- Individual chat interfaces for each agent\n- Smooth animations and professional styling\n- Responsive design for desktop and mobile\n- Main panel that changes content based on selection",
        "testStrategy": "Test by running the frontend application and verifying:\n1. Project folders expand/collapse properly\n2. Agent status indicators update in real-time\n3. Individual agent chat interfaces function correctly\n4. UI matches ChatGPT design patterns\n5. Responsive design works on different screen sizes",
        "priority": "high",
        "dependencies": [1],
        "status": "pending",
        "subtasks": []
    }
    
    try:
        # Read existing tasks
        with open(tasks_file, 'r') as f:
            data = json.load(f)
        
        # Add new task to master tag
        data['master']['tasks'].append(new_task)
        
        # Write back to file
        with open(tasks_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"Successfully added task {new_task['id']}: {new_task['title']}")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    add_task_to_json() 