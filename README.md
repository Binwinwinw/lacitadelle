# La Citadelle

**English** | [Français](./README.fr.md)

La Citadelle is a local AI chat application. Your conversations are processed on your device by a local model and are not sent to a cloud service. On first setup, the application downloads the runtime and model from their official sources.

## Installation

### Prerequisites

- Windows 10 or later.
- Python 3.10 or later.
- About 3 GB of free disk space.
- An internet connection for the first launch.
- Git is not required.

### Steps

1. Download the latest archive from [GitHub Releases](https://github.com/Binwinwinw/lacitadelle/releases/latest) — the file is `lacitadelle-distribution.zip`.
2. Unzip it into a folder where you have write access.
3. Double-click `install.bat`. It checks that Python is available, downloads the llamafile runtime (about 42 MB) and Qwen3 model (about 1.28 GB), verifies their checksums, and starts `lancer.bat`.
4. Your browser opens at `http://localhost:8081`. Select **Sign up** (**Créer un compte**) to create an account, then log in.
5. Start chatting.

The first launch can take several minutes while the runtime and model download and the model loads. Later launches are much faster.

## Usage

Create an account, log in, and select **+ New session** (**+ Nouvelle session**) to start a conversation. Your conversations are saved locally and are available again when you log in later.

### Accounts and model management

- The initial account is named `superadmin`, but its application role is
  `admin`; there is no separate superadmin role.
- Admins can manage the allowed GGUF model paths and select the active model
  from **Settings** (**Paramètres**). A selected model is loaded the next time
  `lancer.bat` starts.
- Regular users can chat and access only their own conversations.

## Known limitations

- The Python server is single-threaded: a slow request blocks subsequent
  requests.
- The number of simultaneous users has not been tested. Concurrent load
  testing and a move to `ThreadingHTTPServer` require a dedicated concurrency
  GO.
- The automated load check covers 100 sequential logins (6.9 seconds on the
  tested machine; 10-second limit). It does not measure concurrent chats or
  model requests; timings vary by machine.

## Security

The web proxy listens on `127.0.0.1:8081` and the model server on
`127.0.0.1:8080`. The model server accepts browser CORS requests only from
`http://localhost:8081`; the web interface sends requests through the Python
proxy. CORS is not a firewall, so local programs can still access loopback.
Do not expose La Citadelle to a network or the public internet. The local
version uses HTTP; production network access requires HTTPS and the additional
protections described in the project security plan.

## Stopping La Citadelle

Close both command windows:

- **Lacitadelle Server** — model server on port 8080.
- **Lacitadelle Proxy** — web interface and authentication on port 8081.

## Troubleshooting

- **Antivirus blocks `dist\llamafile.exe`:** check your antivirus quarantine and allow the file if you trust this installation.
- **Python is not found:** install Python 3.10 or later and make sure `python` is available on your PATH.
- **A download fails:** check your internet connection and run `install.bat` again.
- **The browser does not open:** open `http://localhost:8081` manually after installation.
- **A port is already in use:** close any earlier La Citadelle windows and
  retry. Do not expose the services on another network interface.
- **The model is missing:** run `install.bat` again to verify or download the
  default runtime and model. An admin can select only an existing model in
  the allowed-model list.
- **The admin account is inaccessible:** stop the application and follow the
  isolated reset procedure in [`dev/docs/RUNBOOK.md`](./dev/docs/RUNBOOK.md).

## Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md) for developer setup and contribution guidance.

## License

La Citadelle is licensed under Apache 2.0. See [LICENSE](./LICENSE).
