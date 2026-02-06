# Google ADK Agents Repository

This repository contains reference implementations of intelligent agents built using the **Google Agent Development Kit (ADK)**. These agents demonstrate how to leverage Google Cloud Vertex AI, Gemini models, and the ADK framework to build scalable, production-ready AI applications.

## Goals

1.  **Reference Implementation**: Provide clear, copy-pasteable examples of how to structure ADK agents.
2.  **Showcase Capabilities**: Demonstrate various agent capabilities such as multi-modal generation (Image, Video), grounding, and tool use.
3.  **Best Practices**: Follow recommended patterns for agent architecture, testing, and deployment on Google Cloud.

## Architecture

This repository adopts a **mono-repo** structure where each agent resides in its own self-contained directory.

### Repository Structure

```
agents/
├── README.md           # This file
├── image-agent/        # Image Generation & Upscaling Agent
│   ├── app/            # Source code for the agent application
│   │   ├── agent.py    # Main agent definition
│   │   └── tools/      # Agent tools (skills)
│   ├── deployment/     # Deployment configuration and scripts
│   ├── tests/          # Unit and integration tests
│   └── pyproject.toml  # Project configuration and dependencies
└── ...
```

### Common Components

Most agents in this repository follow a similar internal architecture:
-   **Agent Definition**: Defined using the ADK `Agent` class (`agent.py`).
-   **Tools**: Python functions wrapped as tools that give the agent capabilities (e.g., calling Vertex AI APIs).
-   **Deployment**: Deployment configurations and scripts located in the `deployment/` directory, managed via `pyproject.toml`.

## Available Agents

| Agent Name | Description | Key Models |
| :--- | :--- | :--- |
| **[Image Agent](./image-agent/README.md)** | Generates and upscales images using natural language prompts. | `gemini-3-pro-image`, `imagen-4.0` |

## Getting Started

To get started with a specific agent, navigate to its directory and follow the `README.md` instructions there.

```bash
cd image-agent
# Follow instructions in image-agent/README.md
```
