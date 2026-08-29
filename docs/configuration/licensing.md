---
title: "Licensing"
description: "How a Cloudkeel-DD licence key is applied - at install time as a Helm value, or later from Settings - what an install does without one, and why it all works with no internet access."
---

> Mirrored for search visibility. Canonical, always-current version: **[https://cloudkeel.io/docs/configuration/licensing/](https://cloudkeel.io/docs/configuration/licensing/)**

> [!NOTE]
> The licence key value and the Settings field described here need **chart 0.3.4
> or newer**. On earlier charts an install runs on its pilot window and needs no
> key at all.


A Cloudkeel-DD install does not need a licence key to work. Without one it runs
its pilot window and then continues within the Free allowance. A key raises the
limits; it does not switch the product on.

## What a key changes

A key names a tier, a scope limit, a user limit and an expiry date. Those become
the install's limits while the key is valid.

Nothing about the key is checked over the network. It is signed, and the
signature is verified against a public key compiled into the image, so
verification works exactly the same on a machine with no route to the internet.
**There is no licence server, no callout, and no Cloudkeel-DD-operated endpoint**
involved in reading a key.

## Applying a key at install time

Pass it as a secret value:

```bash
helm upgrade --install dd oci://registry-1.docker.io/driftdetective/d-detective \
  --version 0.3.6 \
  --namespace ddetective --create-namespace \
  --set secrets.licenseKey='CKDD1....'
```

It lands in the release's Kubernetes Secret alongside the other credentials, and
reaches the API, worker, beat and migration workloads.

A key is not a confidentiality secret - reading it tells you only what it already
says on its face. It is a **bearer** token: whoever holds it can apply it to an
install. Handle it the way you handle the rest of your Helm secret values.

## Applying a key later, from Settings

An owner can paste a key into **Settings → Licence**. It is checked when you save,
so a key that cannot be read is refused there and then rather than failing
quietly at the next scan. The page also shows the current tier, both meters and
which clouds your scopes are spread across.

Clearing the field returns the install to its unkeyed state.

### If both are set, the Helm value wins

A key in your Helm values takes precedence over one entered in Settings, so a
`helm upgrade` is always the authoritative answer and never loses silently to
something typed into a browser months earlier.

When a Helm value is present the Settings field is closed and says so, rather
than accepting a key that could not take effect.

## Without a key

Nothing stops. The install runs its pilot window, and after that stays within the
Free allowance: fewer scopes and fewer users than a paid tier, with every feature
still present.

Scopes beyond the allowance stop getting new scans and say so on their own row in
the UI. Findings, history, integrations and sign-in all keep working, and nothing
is deleted.

## Air-gapped installs

Nothing extra to do. Verification is offline by construction, so a key applies on
an air-gapped install exactly as it does anywhere else - see
[Air-gapped installation](https://cloudkeel.io/docs/operations/offline/) for mirroring the images and
the chart.

The one thing to watch is the same one air-gapped installs already watch: the
expiry date inside the key is compared against the install's own clock, so a
badly-wrong clock affects when a key reads as expired.

## Related

- [Helm values](https://cloudkeel.io/docs/configuration/helm-values/) - `secrets.licenseKey` and the
  pilot window settings
- [Secrets](https://cloudkeel.io/docs/configuration/secrets/) - how the release's Secret is built
