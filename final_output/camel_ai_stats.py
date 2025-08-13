import matplotlib.pyplot as plt

# GitHub statistics for camel-ai framework
stats = {
    'Stars': 13200,
    'Forks': 1400,
    'Pull Requests': 164,
    'Issues': 355
}

# Create a bar chart
fig, ax = plt.subplots()
ax.bar(stats.keys(), stats.values(), color=['blue', 'green', 'orange', 'red'])

# Add title and labels
ax.set_title('GitHub Statistics for camel-ai Framework')
ax.set_ylabel('Count')

# Show the plot
plt.tight_layout()
plt.savefig('/Users/bernardojrodriguez/Documents/code/autonomica/final_output/camel_ai_stats.png')
plt.show()