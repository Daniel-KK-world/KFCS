import matplotlib.pyplot as plt

# Set up figure
fig, ax = plt.subplots(figsize=(12, 3))
ax.axis('off')

# Define steps with SUBSTEPS for reduction details
steps = [
    {"name": "FaceNet\n128D", "desc": "Original\nEmbedding", "color": "#FFD700"},
    {"name": "Variance\nThreshold", "desc": "σ > 0.15\nKept 84D", "color": "#FFA07A"},
    {"name": "SVM-RFE", "desc": "Removed 20D\n(84D → 64D)", "color": "#98FB98"},
    {"name": "Quantization", "desc": "Float32 → 8-bit\n64B/face", "color": "#ADD8E6"},
    {"name": "Final\n64D Vector", "desc": "54 Geometric\n8 Photometric\n2 Temporal", "color": "#9370DB"}
]

# Draw boxes and annotations
for i, step in enumerate(steps):
    # Main box
    ax.text(i*2.5, 0.5, step["name"], ha='center', va='center', 
            bbox=dict(facecolor=step["color"], edgecolor='black', boxstyle='round,pad=0.5'),
            fontsize=10, weight='bold')
    
    # Description below
    ax.text(i*2.5, -0.3, step["desc"], ha='center', va='center', fontsize=8)
    
    # Arrow (proportional)
    if i < len(steps)-1:
        ax.arrow(i*2.5+0.5, 0.5, 1.3, 0, head_width=0.1, head_length=0.1, 
                 fc='black', ec='black', width=0.01, length_includes_head=True)

# Add reduction metrics
ax.text(1.25, 1.0, "Dropped 44D\n(low σ)", ha='center', fontsize=8, color='red')
ax.text(3.75, 1.0, "Dropped 20D\n(SVM weights)", ha='center', fontsize=8, color='red')

# Add performance summary
ax.text(6.0, 0.5, "→ 96.4% Accuracy\n→ 9ms Matching", ha='left', va='center', 
        bbox=dict(facecolor='white', edgecolor='blue', pad=5), fontsize=9)

plt.tight_layout()
plt.savefig('feature_selection.png', dpi=300, bbox_inches='tight')