# Change Log
All notable changes to this project will be documented in this file.

## [2.0.3] - 2026-02-04

### Added

- Patched the automatic authentication url retrieval process to only support federated tenants.
    - See the latest [DeviceCodePhishing commit](https://github.com/denniskniep/DeviceCodePhishing/commit/aa9a34061cab4b148f6d4991eb38ad8ffce7025b)


## [2.0.2] - 2025-04-23

### Added

- Suppot for automatic authentication URL retrieval via [@denniskniep](https://github.com/denniskniep) [DeviceCodePhishing](https://github.com/denniskniep/DeviceCodePhishing)

### Fixed

- Several minor bug fixes in the phishing server that prevented proper error handling


## [2.0.1] - 2025-04-23

### Added

- Support for URLs in emails in addition to QR codes
- Support for custom Entra configuration (client id, scope, tenant)
- Support for a custom User Agent on backend requests to Microsoft

### Fixed

- Bug in the send email loop that, instead of sending each email to one recipient at a time, would send each email to *all* recipients


## [2.0.0] - 2025-04-22

### Added

- Web front end to interact with SquarePhish
- Database to store configuration, credentials, and metrics

### Changed

- Full codebase rewrite to Golang