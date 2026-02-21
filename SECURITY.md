# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| main    | Yes       |

## Reporting a Vulnerability

If you discover a security vulnerability in this project, please report it
responsibly. **Do not open a public GitHub issue.**

Instead, please email **[opencode@microsoft.com](mailto:opencode@microsoft.com)**
with the following information:

- Description of the vulnerability.
- Steps to reproduce (or a proof-of-concept).
- Impact assessment.
- Any suggested remediation.

We will acknowledge receipt within **3 business days** and provide a detailed
response within **10 business days**, including an expected timeline for a fix.

## Security Considerations

This demo pack is designed for **local development and demo purposes**. Review
the following before deploying in any shared or production-like environment:

### Network Exposure

- The FastAPI UI server binds to `127.0.0.1` by default. To expose on a
  shared network, set `HOST=0.0.0.0` — but only do this in trusted
  environments.
- WebSocket connections are unauthenticated. Do not expose the UI port to
  untrusted networks.

### Foundry Local

- Foundry Local runs entirely on-device — no data leaves your machine.
- The API key (`FOUNDRY_API_KEY`) in `.env.example` is a placeholder for local
  use only. Never commit real API keys.

### Input Handling

- The demo accepts predefined task inputs only. If you extend the UI to accept
  user-provided prompts, ensure you sanitize and validate all inputs.
- The `/api/replay` endpoint reads files from local disk. It validates that the
  path resolves within the `demos/` directory and requires a `.jsonl` extension.

### Dependencies

- Pin critical dependency versions in production deployments.
- Regularly audit dependencies with `pip audit` or equivalent tools.
- The `--pre` flag for `agent-framework` packages installs pre-release versions;
  monitor for stable releases.

### Environment Files

- `.env` files are excluded from version control via `.gitignore`.
- Never commit secrets, tokens, or API keys.

## Microsoft Security Response Center

For security issues in Microsoft products (Agent Framework, Foundry Local),
please use the [Microsoft Security Response Center (MSRC)](https://msrc.microsoft.com/)
reporting process.
