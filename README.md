# 🔥 Escape the Fire

**Escape the Fire** is a Python game built with **Pygame** that combines maze generation, AI pathfinding, and real-time fire simulation.

Your goal? Escape a burning maze before the fire reaches you — or let one of the search algorithms find a path for you.

---

## 🎮 Features

- 🧭 **Three Search Algorithms**
  - **A\*** (Adaptive): Recalculates its path dynamically as fire spreads.
  - **BFS** (Breadth-First Search): Explores all possible paths equally.
  - **Greedy Best-First Search**: Follows the most promising heuristic.
  
- 🔥 **Dynamic Fire Spread**
  - The fire expands gradually across the maze as you move.
  - The player (manual or AI-controlled) must avoid getting trapped.

- 🧱 **Random Maze Generation**
  - Each new game generates a unique maze with a **guaranteed path** from start to goal.
  - Walls appear in a red-orange brick pattern.

- ⏱️ **Animated Movement**
  - Algorithms move step-by-step (0.20s delay per step), letting you visually follow their decisions.

- 🧮 **Stat Comparison**
  - After each round, view side-by-side performance data for A*, BFS, Greedy, and manual play:
    - Total time
    - Path length
    - Nodes expanded
    - Success/failure state

- 🎛️ **Polished Interface**
  - Main menu with Start and Instructions
  - Restart or return to menu after each game
  - Highlighted buttons and clean design
  - Player sprite and fire visuals included (`Player.png`, `fire.png`, `BackButton.jpeg`)

---

## 🧩 Technologies Used

- **Python 3.10+**
- **Pygame**

---

## ⚙️ Installation & Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/<your-username>/escape-the-fire.git
   cd escape-the-fire
