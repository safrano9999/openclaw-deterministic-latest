# OpenClaw Deterministic Latest

[![Pinned version](https://img.shields.io/badge/OpenClaw-2026.9.6-111827)](#version-pin)
[![Patch](https://img.shields.io/badge/patch-dummy%2Fdummy%20%7C%20dummy%2Fnote-2563eb)](patches/openclaw-2026.9.6-deterministic-main.patch)
[![Image chain](https://img.shields.io/badge/images-Fedora%2045%20latest-0ea5e9)](https://github.com/safrano9999/fedora45-ai-safrano9999/blob/main/README.md)

The independently maintained, exact deterministic gateway patch used by the
Safrano OpenClaw latest image line. This repository is separate from the original
version-pinned distribution.

This is a standalone public repository owned by `safrano9999`. It is not a
GitHub fork and has no pull-request relationship to another repository.

## Patch

The canonical patch is:

```text
patches/openclaw-2026.9.6-deterministic-main.patch
```

SHA-256:

```text
373e7ef2e0f3b4f9668e03d3524c66f88bbea506964e81dcd7e8d83437fdb29a
```

It contains the deterministic, per-server MCP private-network and provider
activation performance change set without unrelated repository history or automation.

## Migration evidence

The [previous 2026.7.1 patch](patches/openclaw-2026.7.1-deterministic.patch),
[2026.9.2 patch](patches/openclaw-2026.9.2-deterministic.patch),
[2026.9.3 patch](patches/openclaw-2026.9.3-deterministic.patch), and
[2026.9.4 patch](patches/openclaw-2026.9.4-deterministic.patch) are retained for comparison. The current port follows upstream's new owners:

| Contract | 2026.7.1 patch | 2026.9.6 port / upstream equivalent |
|---|---|---|
| Fixed reply and NOTE precedence | Early fallback in `get-reply.ts` | Admitted-run `before-agent-reply.ts` owner; handled replies retain durable recovery bookkeeping. Deterministic turns skip model-backed maintenance. |
| Hook model identity | Added provider/model context fields | Upstream already supplies `modelProviderId` and `modelId`; no duplicate patch. |
| Hook user/media context | Legacy `MediaPaths` and related fields | Canonical `media[]`, location, and structured context project into the existing hook payload fields. |
| Catalog, picker, and auth | Added both dummy models and bypassed model auth | Both models remain available through manifest/prepared catalogs and picker paths, without changing native route variants or account-entitlement filtering. |
| Editable reply asset | `runtime-postbuild.mjs` copied the text file | The `.mts` postbuild owner and compiled test workers copy the same text asset. |
| Model-list activation cost | Per-row plugin activation | Reuse the existing operation-owned activation and same-turn auto-enable cache, including persisted manifest metadata; preserve aliases, provider normalization, freshness and lifecycle invalidation. |
| MCP private networking | Per-server explicit opt-in | Current transport and the shared `zod-schema.mcp-server.ts` retain the opt-in; default SSRF protection and upstream OAuth/timeout handling remain intact. |

The 2026.9.6 port follows upstream's shared MCP schema and inferred config types,
its prepared manifest-row planner, and its provider-policy artifact cache. The
previous outer provider cache is removed because upstream now owns the same
prepared facts with registry-version and bundled-root invalidation. Operation-scoped
activation projections retain separate setup/runtime eligibility, source-config
validation, and retained registry checks; lifecycle clear callbacks explicitly
belong to operations even while a Gateway is active. Compiled test workers retain
both upstream build identity and the editable deterministic reply asset.
Catalog tests preserve replacement-mode provider isolation and account entitlement
alongside both deterministic models; no account-restricted provider rows are added.
The model-list regression follows the published catalog through `models.list`
and the CLI, checking preserved rows and bounded policy scans without runtime
provider activation during a read. Published rows normalize configured provider
aliases before model IDs so default/fallback tags and display aliases keep the
same canonical identity as the catalog.
Deterministic turns continue to skip model-backed compaction and memory flush.
The read-only model-auth owner recognizes the two local deterministic routes
without credentials, so `/models` does not request sign-in for them. Provider-only
queries, external transport/runtime overrides, and ordinary provider authentication
retain their existing checks. Regression coverage exercises the catalog decisions
and command output with an empty credential snapshot.
The release workflow verifies the exact upstream base, runs the existing focused
contract tests, builds the runtime, and checks packaged imports before publishing.
These checks do not substitute for deployment and live service verification.

## Deterministic routes

| Model | Behavior |
|---|---|
| `dummy/dummy` | Commands and plugins run first. An unclaimed message receives a fixed reply without a normal model turn. |
| `dummy/note` | Commands and plugins run first. NOTE can claim and persist the message without an LLM call. |

Normal providers, tools, plugins, and LLM-backed models remain available when
another model is selected.

## Historical visible proof

The preserved native Telegram Desktop recording shows the route concept before
and after enabling `dummy/dummy`: an unavailable normal model produces a
provider error, while the deterministic route handles the ordinary message
immediately. Commands and plugin hooks remain ahead of the fallback.

<table>
  <thead>
    <tr>
      <th width="50%">Before</th>
      <th width="50%">Deterministic route</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>
        <a href="docs/demo/deterministic-before.mp4">
          <img src="docs/demo/deterministic-before.png" alt="Telegram before the deterministic patch">
        </a>
      </td>
      <td>
        <a href="docs/demo/deterministic-after.mp4">
          <img src="docs/demo/deterministic-after.png" alt="Telegram using the deterministic route">
        </a>
      </td>
    </tr>
  </tbody>
</table>

Click either screenshot to open its MP4 recording.

These recordings predate the `2026.7.1` port. They demonstrate routing behavior,
not byte-exact release wording or `2026.9.6` build/runtime verification; the
canonical behavior is the version-pinned patch in this repository.

### NOTE full mode

`dummy/note` lets the separate NOTE plugin claim ordinary non-command messages,
store them without a model request, acknowledge the save, and return them
through `/note show`.

![NOTE full mode in Telegram](https://raw.githubusercontent.com/safrano9999/NOTE/2026.7.36/docs/full-mode.jpg)

The NOTE screenshot is a workflow illustration captured on OpenClaw `2026.6.11`,
not a `2026.9.6` build-verification artifact.

## Version pin

The current patch is ported to OpenClaw `2026.9.6` at main commit
`eb377ac59e6c9fd6c7705028034812becf00271b`.
The released `.5` patch is retained as
`patches/openclaw-2026.9.5-deterministic-main.patch` for comparison.

The source of truth for builds and compatibility tests is the consuming repository's
`fedora45-ai-core-pre/Containerfile`:

```dockerfile
ARG OPENCLAW_VERSION=2026.9.6
ARG OPENCLAW_UPSTREAM_SHA=eb377ac59e6c9fd6c7705028034812becf00271b
```

An empty SHA selects the official release tag for that version. An unchanged stable
version preserves a manually selected SHA; a newer stable release updates the version
and clears the override. The reusable build workflow is called automatically by Core's
`openclaw-components.yml` workflow with its immutable source commit. It reads these
arguments before checking out upstream and running tests. `build.conf` records the
reviewed patch and toolchain; its effective upstream pin is derived from Core-pre.
A newer Core-pre version reuses the patch only if it applies and passes all tests;
failures publish nothing. Version selection never follows upstream main or latest.
The automatic check skips unchanged successful inputs and records each new verified
release and checksum in Core without starting an image build.

The build uses upstream's own complete npm packer and its separate Codex plugin
packer. This preserves the selected source's file rules, workspace packaging,
dependency versions and exports. The runtime bundle contains `openclaw.tgz`,
`codex.tgz`, and a manifest with source identity and checksums. It is not a raw
source-build `dist` overlay. Ephemeral's unit tests and Core's runtime compatibility
probe run against this same built selection before publication.

Machine version is `2026.9.6`; the separate display label is
`2026.9.6-patched`. The updater therefore waits for the next stable version.
Release revisions are unique and versioned assets are not overwritten.

The `.1` release series is prepared in source only. No runtime or image build has
been started for this change; no `.6` artifact exists until GitHub Actions publishes it.

## Public package

The distribution is intentionally split into three public repositories:

| Repository | Responsibility |
|---|---|
| [openclaw-deterministic-latest](https://github.com/safrano9999/openclaw-deterministic-latest) | This exact version-pinned patch |
| [NOTE](https://github.com/safrano9999/NOTE) | Independent storage plugin for `dummy/note` |
| [openclaw-ephemeral](https://github.com/safrano9999/openclaw-ephemeral) | Python startup configuration |

The current image integration starts at
[fedora45-ai-safrano9999](https://github.com/safrano9999/fedora45-ai-safrano9999)'s Core layer:

Core installs the verified Deterministic archive directly, then adds Ephemeral
in a separate step. Ephemeral does not embed or rebuild this package. The Core
installer validates provenance and archive contents, then installs the complete
matching npm runtime and Codex plugin. This also updates dependencies and exports.

```text
ghcr.io/safrano9999/fedora45-ai-core:latest
```

A standalone latest ephemeral image has not been published.

## License

See [LICENSE](LICENSE).
