# Contributing to Job Scraper

First off, thank you for considering contributing to Job Scraper! It's people like you that make Job Scraper such a great tool.

We welcome all contributions, from reporting bugs to submitting pull requests for new features or fixes.

## Table of Contents

1. [Code of Conduct](#code-of-conduct)
2. [Getting Started](#getting-started)
   - [Prerequisites](#prerequisites)
   - [Installation](#installation)
3. [Development Workflow](#development-workflow)
   - [Running the Application](#running-the-application)
   - [Running Tests](#running-tests)
4. [How to Contribute](#how-to-contribute)
   - [Reporting Bugs](#reporting-bugs)
   - [Suggesting Enhancements](#suggesting-enhancements)
   - [Submitting Pull Requests](#submitting-pull-requests)
5. [Style Guide](#style-guide)

## Code of Conduct

This project and everyone participating in it is governed by the [Job Scraper Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code. Please report unacceptable behavior to **davioliveira353.do@gmail.com**.

## Getting Started

### Prerequisites

To contribute to this project, you will need:
* **Python 3.12** or higher
* **Poetry** for dependency management
* A **Serper API Key** (you can get a free one at [serper.dev](https://serper.dev))

### Installation

1.  **Fork the repository** on GitHub.
2.  **Clone your fork** locally:
    ```bash
    git clone https://github.com/oPaozinh0/job-scraper.git
    cd job-scraper
    ```
3.  **Install dependencies** using Poetry:
    ```bash
    poetry install
    ```
4.  **Set up environment variables**:
    ```bash
    cp .env.example .env
    ```
    Open `.env` and add your API key:
    ```env
    SERPAPI_API_KEY_1=your_serper_api_key_here
    ```

## Development Workflow

### Running the Application

You can run the application in two modes:

**1. CLI Mode (Command Line)**
To search for jobs directly via the terminal:
```bash
poetry run python main.py --technology python --level senior
```

**2. Web Server Mode (Dashboard)**
To start the Flask development server:
```bash
poetry run python server.py
```
Access the dashboard at `http://127.0.0.1:8000`.

### Running Tests

We use `pytest` for testing. Please ensure all tests pass before submitting a Pull Request.

Run the complete test suite:
```bash
poetry run pytest
```

To run tests with coverage report:
```bash
poetry run pytest --cov=. --cov-report=html
```

## How to Contribute

### Reporting Bugs

This section guides you through submitting a bug report.
* **Use the GitHub Issues search** — check if the issue has already been reported.
* **Open a new Issue** — provide a clear title and description. Include as much information as possible: steps to reproduce, expected behavior, and screenshots if applicable.

### Suggesting Enhancements

* **Open a new Issue** — describe the feature you would like to see, why you need it, and how it should work.

### Submitting Pull Requests

1.  **Create a new branch** for your feature or fix:
    ```bash
    git checkout -b feature/amazing-feature
    ```
2.  **Commit your changes** with clear, descriptive commit messages.
3.  **Push to your fork**:
    ```bash
    git push origin feature/amazing-feature
    ```
4.  **Open a Pull Request** against the `main` branch of the original repository.
5.  **Describe your changes** in the PR description and link to any relevant issues (e.g., "Fixes #123").

## Style Guide

* **Python Code**: Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) guidelines.
* **Type Hinting**: Use type hints where possible to improve code readability and maintainability.
* **Documentation**: Ensure new functions and classes have docstrings.
