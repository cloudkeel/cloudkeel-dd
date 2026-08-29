---
title: "Connecting integrations"
description: "The two-part desired-versus-actual model, which integration types are scan targets, and which are cross-check credentials."
---

> Mirrored for search visibility. Canonical, always-current version: **[https://cloudkeel.io/docs/integrations/overview/](https://cloudkeel.io/docs/integrations/overview/)**

Cloudkeel-DD compares **desired** state against **actual** state, so most clouds
need **two** integrations working together.

## The two-part model

1. A **state source** (Terraform Cloud, or raw `.tfstate` in S3/GCS/Azure Blob)
   — the *desired* state.
2. A **cross-check credential** (Azure / AWS / GCP, read-only) — the *actual*
   live state.

With only the state source, resources are discovered but tagged *"no live
comparison available"*: inventory, not drift. With only the cross-check
credential, there's nothing to compare against. **Connect both**, per cloud.

Kubernetes is the exception — one kubeconfig integration is self-contained
(desired = Helm release record, actual = live API).

## The recommended path

**Terraform (or raw state) + Azure cross-check.** Azure has the deepest
field-level verification. Start there, then add more sources.

## What to connect

| Guide | What it connects |
|---|---|
| [Terraform Cloud](https://cloudkeel.io/docs/integrations/terraform-cloud/) | The recommended first desired-state source |
| [Azure cross-check](https://cloudkeel.io/docs/integrations/azure-cross-check/) | Live Azure verification + unmanaged detection |
| [AWS cross-check](https://cloudkeel.io/docs/integrations/aws-cross-check/) | Live AWS security-group drift + unmanaged detection |
| [GCP cross-check](https://cloudkeel.io/docs/integrations/gcp-cross-check/) | Live GCP firewall-rule drift + unmanaged detection |
| [Azure Blob state](https://cloudkeel.io/docs/integrations/azure-state/) | Raw `.tfstate` in Azure Storage, via a narrow SAS |
| [AWS S3 state](https://cloudkeel.io/docs/integrations/aws-state/) | Raw `.tfstate` in S3, via a bucket-scoped IAM user |
| [GCP GCS state](https://cloudkeel.io/docs/integrations/gcp-state/) | Raw `.tfstate` in GCS, via a bucket-scoped service account |
| [Kubernetes / Helm](https://cloudkeel.io/docs/integrations/kubernetes/) | Drift on Helm releases — AKS, EKS, GKE, or any cluster |

## Which credential goes where

The most common setup mistake is putting a working credential in the wrong slot.
They are not interchangeable, and a state reader pasted into a cross-check
integration fails with a raw cloud error that does not say so. One row per
credential you will create:

| Integration | Credential to create | Scope it needs | The secret you paste |
|---|---|---|---|
| Azure cross-check | AAD app registration (service principal) | **Reader** on each subscription to verify | Client secret, shown once at creation |
| AWS cross-check | IAM user or role | Read-only on the described services | Access key ID + secret access key |
| GCP cross-check | Service account | Viewer / Cloud Asset Inventory read on the project | JSON key file |
| Azure Blob state | **SAS token** — no app registration, no RBAC | Read + List on **one container** | Query string from `generate-sas` |
| AWS S3 state | IAM user, separate from the cross-check one | `s3:ListBucket` + `s3:GetObject` on **one bucket** | Access key ID + secret access key |
| GCP GCS state | Service account, separate from the cross-check one | `storage.objectViewer` on **one bucket** | JSON key file |
| Terraform Cloud / Enterprise | User or team API token | Read on the workspaces | Token from the TFC/TFE UI |
| Kubernetes / Helm | ServiceAccount **token** kubeconfig | Read on the namespaces you care about | The kubeconfig you assemble |

Three things that trip people up:

- **The state credential and the cross-check credential for the same cloud are
  deliberately different identities.** The state one reads one bucket or
  container; the cross-check one reads live resources across a whole
  subscription, account, or project. Reusing one for both grants it more than it
  needs.
- **Azure state needs no app registration at all** — it is a plain SAS. If you are
  creating a service principal for it, you are on the wrong guide.
- **One credential per cloud, for now.** A second Azure tenant or AWS account
  cannot be connected alongside the first; the API rejects it.

## Don't-skip checklist

- [ ] **State source connected**, and each discovered `.tfstate` **Enabled**.
- [ ] **Cross-check credential connected** for the same cloud.
- [ ] **Cross-check scope enabled** — AWS/GCP auto-enable; **Azure** leaves
      discovered subscriptions disabled until you opt in.
- [ ] **Kubernetes:** a static **token** kubeconfig, not an exec-plugin one.
- [ ] **EKS:** cluster API access enabled first (access entry).

Hitting a **Test connection** error? See **[Troubleshooting](https://cloudkeel.io/docs/integrations/troubleshooting/)**
— every failure mode mapped to its fix.

## Credentials are always read-only

Cloudkeel-DD never writes to your cloud. Every guide uses a narrow, read-only
credential; the [security model](https://cloudkeel.io/docs/claims/security-model/) and
[least-privilege reference](https://cloudkeel.io/docs/claims/least-privilege/) spell out exactly
what each one can and cannot do.
