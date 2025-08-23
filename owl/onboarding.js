// Onboarding System JavaScript
// This file contains the frontend JavaScript for the user onboarding system

// Onboarding wizard state management
let currentStepIndex = 0;
let wizardSteps = ['welcome', 'api_setup', 'first_task', 'feature_tour', 'help_resources'];
let onboardingState = {
    currentStep: 'welcome',
    completedSteps: [],
    skippedSteps: []
};

// Initialize onboarding when page loads
window.addEventListener('load', function() {
    initializeOnboarding();
});

function initializeOnboarding() {
    // Check if user has already completed onboarding
    if (localStorage.getItem('onboarding_completed') === 'true') {
        hideOnboarding();
        return;
    }
}

function startOnboarding() {
    // Transition to the first wizard step
    currentStepIndex = 1;
    showWizardStep('api_setup');
}

function skipOnboarding() {
    // Mark as completed in localStorage
    localStorage.setItem('onboarding_completed', 'true');
    hideOnboarding();
}

function hideOnboarding() {
    // Hide welcome screen and show main interface
    const welcomeScreen = document.querySelector('.onboarding-welcome');
    if (welcomeScreen) {
        welcomeScreen.style.display = 'none';
    }
}

function showWizardStep(stepId) {
    // This would be implemented to show the actual wizard steps
    console.log('Showing wizard step:', stepId);
}

function markStepComplete(stepId) {
    if (!onboardingState.completedSteps.includes(stepId)) {
        onboardingState.completedSteps.push(stepId);
    }
    console.log('Completed step:', stepId);
}

// Feature Tour Functions
let currentTour = null;
let currentTourStep = 0;
let tourSteps = [];

function startTour(tourType) {
    console.log('Starting tour:', tourType);

    // Define tour steps based on type
    switch(tourType) {
        case 'task_creation':
            tourSteps = [
                {
                    title: 'Task Description',
                    content: 'Enter a detailed description of what you want the AI system to accomplish. Be specific about your requirements and expected outcomes.',
                    target: '#question_input',
                    position: 'bottom'
                },
                {
                    title: 'AI Module Selection',
                    content: 'Choose the appropriate AI module for your task. Each module is optimized for different types of tasks and capabilities.',
                    target: '.module-dropdown',
                    position: 'right'
                },
                {
                    title: 'Advanced Options',
                    content: 'Fine-tune your task with advanced settings like timeout duration, iteration limits, and output format preferences.',
                    target: '.advanced-options-toggle',
                    position: 'top'
                }
            ];
            break;

        case 'results_history':
            tourSteps = [
                {
                    title: 'Task Results',
                    content: 'View the results of your completed tasks here. Each task shows its execution details, output, and any relevant information.',
                    target: '.log-display',
                    position: 'top'
                }
            ];
            break;

        case 'settings':
            tourSteps = [
                {
                    title: 'Environment Variables',
                    content: 'Securely manage your API keys and environment variables. Values are masked for security and can be temporarily revealed when needed.',
                    target: '.env-table',
                    position: 'bottom'
                }
            ];
            break;
    }

    currentTour = tourType;
    currentTourStep = 0;
    showTourStep();
}

function showTourStep() {
    if (currentTourStep >= tourSteps.length) {
        endTour();
        return;
    }

    const step = tourSteps[currentTourStep];

    // Create tooltip overlay
    let overlay = document.getElementById('tour-overlay');
    if (!overlay) {
        overlay = document.createElement('div');
        overlay.id = 'tour-overlay';
        overlay.className = 'feature-tour-overlay';
        overlay.innerHTML = `
            <div class="feature-tour-tooltip show" id="tour-tooltip">
                <div class="feature-tour-arrow ` + step.position + `"></div>
                <h3 class="feature-tour-title">` + step.title + `</h3>
                <div class="feature-tour-content">` + step.content + `</div>
                <div class="feature-tour-navigation">
                    <span class="tour-progress">` + (currentTourStep + 1) + ` of ` + tourSteps.length + `</span>
                    <div>
                        <button class="tour-button secondary" onclick="skipTour()">Skip Tour</button>
                        <button class="tour-button" onclick="nextTourStep()">Next</button>
                    </div>
                </div>
            </div>
        `;
        document.body.appendChild(overlay);
    }

    overlay.style.display = 'block';

    // Highlight target element
    highlightElement(step.target);
}

function highlightElement(selector) {
    const element = document.querySelector(selector);
    if (element) {
        element.classList.add('tour-highlight');
    }
}

function removeHighlight() {
    const highlighted = document.querySelector('.tour-highlight');
    if (highlighted) {
        highlighted.classList.remove('tour-highlight');
    }
}

function nextTourStep() {
    removeHighlight();
    currentTourStep++;
    showTourStep();
}

function skipTour() {
    endTour();
}

function endTour() {
    removeHighlight();

    const overlay = document.getElementById('tour-overlay');
    if (overlay) {
        overlay.style.display = 'none';
    }

    currentTour = null;
    currentTourStep = 0;
    tourSteps = [];
}

// Utility functions
function loadExample(taskId) {
    // Load example task into the task creation form
    const examples = {
        'example_1': 'Open Brave search, find information about AI assistants, and summarize the key features of modern AI chatbots.',
        'example_2': 'Browse Amazon and find a product that would be useful for programmers. Provide the product name, price, and key features.',
        'example_3': 'Write a simple Python script that generates a report about the current date and time, then save it locally.',
        'example_4': 'Research the latest developments in AI safety, create a summary report, and generate a simple visualization of the findings.'
    };

    const questionInput = document.getElementById('question_input');
    if (questionInput && examples[taskId]) {
        questionInput.value = examples[taskId];
    }
}

// Make functions globally available
window.startOnboarding = startOnboarding;
window.skipOnboarding = skipOnboarding;
window.markStepComplete = markStepComplete;
window.startTour = startTour;
window.nextTourStep = nextTourStep;
window.skipTour = skipTour;
window.loadExample = loadExample;
