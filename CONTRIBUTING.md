# Contributing to Agent Patterns Demo Pack

Thank you for your interest in contributing! This project showcases visual agent
orchestration patterns using Foundry Local and the Microsoft Agent Framework.

## Code of Conduct

This project has adopted the
[Microsoft Open Source Code of Conduct](https://opensource.microsoft.com/codeofconduct/).
For more information see the
[Code of Conduct FAQ](https://opensource.microsoft.com/codeofconduct/faq/) or
contact [opencode@microsoft.com](mailto:opencode@microsoft.com) with any
additional questions or comments.

## How to Contribute

### Reporting Issues

- Use GitHub Issues to report bugs or request features.
- Include steps to reproduce, expected vs. actual behaviour, and your environment
  (OS, Python version, Foundry Local version).

### Pull Requests

1. Fork the repository and create a feature branch from `main`.
2. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate   # Windows
   source .venv/bin/activate # macOS / Linux
   pip install -r requirements.txt
   ```
3. Make your changes, keeping commits focused and well-described.
4. Ensure the code runs without errors:
   ```bash
   python app.py
   ```
5. Open a pull request against `main` with a clear description of your changes.

### Adding a New Demo

1. Create a folder under `demos/<your_demo_name>/`.
2. Include these files:
   - `README.md`: description, pattern used, agent table, run instructions.
   - `topology.json`: nodes and edges for the D3 graph.
   - `__init__.py`: empty.
   - `agents.py`: agent definitions using `create_agent()`.
   - `run.py`: runner with `run_demo(event_bus)` and `main()`.
3. Register the demo in the `DEMO_REGISTRY` list in `app.py`.
4. Clearly state which Agent Framework orchestration pattern(s) the demo uses.

### Code Style

- Follow PEP 8 conventions.
- Use type hints where practical.
- Keep functions small and focused.
- Docstrings on modules and public functions should state the orchestration
  pattern(s) used.

## Security

Please see [SECURITY.md](SECURITY.md) for reporting security vulnerabilities.

## License

By contributing, you agree that your contributions will be licensed under the
[MIT License](LICENSE).
