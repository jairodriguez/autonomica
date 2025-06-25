#!/usr/bin/env python3
import json
import sys

def expand_task_13():
    tasks_file = '.taskmaster/tasks/tasks.json'
    
    # Subtasks for the ChatGPT-like interface
    subtasks = [
        {
            "id": 1,
            "title": "Create Projects Page Route",
            "description": "Set up the /projects route and page structure in Next.js",
            "dependencies": [],
            "details": "Create a new page at /app/projects/page.tsx with the basic layout structure for the project management interface",
            "status": "pending"
        },
        {
            "id": 2,
            "title": "Build Project Sidebar Component",
            "description": "Create the left sidebar component with expandable project folders",
            "dependencies": [1],
            "details": "Build ProjectSidebar component with project folders, expandable/collapsible functionality, and proper state management",
            "status": "pending"
        },
        {
            "id": 3,
            "title": "Implement Agent Hierarchies",
            "description": "Add agent lists under each project with status indicators",
            "dependencies": [2],
            "details": "Display agent hierarchies under project folders with visual status indicators (busy/spinning, idle/green, error/red, offline/gray)",
            "status": "pending"
        },
        {
            "id": 4,
            "title": "Create Main Panel Component",
            "description": "Build the main content panel that changes based on selection",
            "dependencies": [1],
            "details": "Create ProjectMainPanel component that displays different content based on what's selected in the sidebar",
            "status": "pending"
        },
        {
            "id": 5,
            "title": "Add Real-time Status Updates",
            "description": "Implement real-time agent status updates and animations",
            "dependencies": [3],
            "details": "Add real-time simulation of agent status changes with smooth transitions and spinning animations",
            "status": "pending"
        },
        {
            "id": 6,
            "title": "Build Individual Agent Chat Interfaces",
            "description": "Create chat interfaces for individual agents",
            "dependencies": [4],
            "details": "Implement individual chat interfaces for each agent, integrating with existing ChatContainerAI component",
            "status": "pending"
        },
        {
            "id": 7,
            "title": "Apply ChatGPT-style Styling",
            "description": "Style the interface to match ChatGPT design patterns",
            "dependencies": [2, 4],
            "details": "Apply professional styling, smooth animations, hover effects, and responsive design matching ChatGPT's aesthetic",
            "status": "pending"
        },
        {
            "id": 8,
            "title": "Test and Refine Interface",
            "description": "Test all functionality and refine the user experience",
            "dependencies": [5, 6, 7],
            "details": "Comprehensive testing of all features, fix any bugs, and refine the user experience",
            "status": "pending"
        }
    ]
    
    try:
        # Read existing tasks
        with open(tasks_file, 'r') as f:
            data = json.load(f)
        
        # Find task 13 and add subtasks
        for task in data['master']['tasks']:
            if task['id'] == 13:
                task['subtasks'] = subtasks
                break
        
        # Write back to file
        with open(tasks_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"Successfully added {len(subtasks)} subtasks to task 13")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    expand_task_13() 