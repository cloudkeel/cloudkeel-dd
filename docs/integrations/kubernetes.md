---
title: "Kubernetes / Helm setup"
description: "Create a read-only ServiceAccount and kubeconfig, then detect Helm release drift and unmanaged workloads with no GitOps tool required."
---

> Mirrored for search visibility. Canonical, always-current version: **[https://cloudkeel.io/docs/integrations/kubernetes/](https://cloudkeel.io/docs/integrations/kubernetes/)**

This connects Cloudkeel-DD directly to a Kubernetes cluster to detect drift on
**Helm releases** - for clusters with no GitOps tool at all (plain
`helm install`/`upgrade`, no Argo CD, no Flux).

Works with **AKS, EKS, GKE, on-prem, or any distribution** - Cloudkeel-DD talks to
the Kubernetes API, not to a cloud provider.

Running Argo CD or Flux? Use those integrations instead - they know what git
declared. This one is for when Helm's own release record is the source of truth.

## How it detects drift

- **Desired state** = Helm's own stored release manifest (what `helm install`
  actually rendered and applied)
- **Actual state** = a live read from the Kubernetes API

Anything changed out-of-band - a `kubectl edit`, a `kubectl scale`, a console
click - shows up as a field-level diff.

Supported kinds: `Deployment`, `StatefulSet`, `DaemonSet`, `Service`,
`ConfigMap`, `Ingress`. **`Secret` is deliberately excluded** so secret values
never land in a diff.

## Important: use a static kubeconfig, not an exec-plugin one

**This is the step people get wrong.** The kubeconfig you get from:

```bash
aws eks update-kubeconfig ...              # EKS
gcloud container clusters get-credentials  # GKE
az aks get-credentials ...                 # AKS (admin form works, but see below)
```

...is an **exec-plugin** kubeconfig. It doesn't contain a credential - it
contains an *instruction to run a CLI* (`aws`, `gcloud`, `kubelogin`) to fetch a
token. Those CLIs don't exist inside Cloudkeel-DD's container, so the connection
fails with a `401 Unauthorized` even though `kubectl` works fine on your laptop.

Create a **static, token-based kubeconfig** backed by a read-only ServiceAccount
instead. This is also better practice: a narrow, revocable, least-privilege
credential rather than your personal admin access.

## Prerequisite (EKS only): make sure you can reach the cluster

Steps 1-3 below run `kubectl` against the cluster - which only works if your
identity already has cluster access. On **EKS this is not a given**: a cluster
trusts **only its creator** by default, and if it was created in the legacy
`CONFIG_MAP` authentication mode, no IAM access entry can be added at all until
you switch it. Symptom: every `kubectl` call returns

```
error: You must be logged in to the server (the server has asked for the client to provide credentials)
```

Fix it once, from an IAM identity that can administer the cluster (needs
`eks:UpdateClusterConfig` + `eks:CreateAccessEntry` + `eks:AssociateAccessPolicy`):

```bash
# 1. Switch to API auth mode (additive - keeps any existing aws-auth configmap).
aws eks update-cluster-config --name <cluster> --region <region> \
  --access-config authenticationMode=API_AND_CONFIG_MAP
# wait until it finishes (~2-3 min):
aws eks describe-cluster --name <cluster> --region <region> --query cluster.status

# 2. Grant your IAM principal cluster access via an access entry.
aws eks create-access-entry --cluster-name <cluster> --region <region> \
  --principal-arn arn:aws:iam::<account-id>:user/<you>
aws eks associate-access-policy --cluster-name <cluster> --region <region> \
  --principal-arn arn:aws:iam::<account-id>:user/<you> \
  --access-scope type=cluster \
  --policy-arn arn:aws:eks::aws:cluster-access-policy/AmazonEKSClusterAdminPolicy
```

> **Watch the policy ARN form:** it is `arn:aws:eks::aws:cluster-access-policy/...`
> (empty region, partition `aws`) - **not** `arn:aws:eks:::...`. The triple-colon
> form fails with `ResourceNotFoundException: The specified policyArn could not be
> found`.

Then `aws eks update-kubeconfig --name <cluster> --region <region>` and confirm
`kubectl get nodes` works before continuing. (AKS and GKE don't need this - their
`get-credentials` grants access directly; you still build the static kubeconfig
below so the credential works from inside Cloudkeel-DD's container.)

### 1. Create a read-only ServiceAccount

```bash
kubectl create serviceaccount ddetective-reader -n default
```

### 2. Grant it read-only access to exactly what's needed

```bash
cat <<'EOF' | kubectl apply -f -
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: ddetective-reader
rules:
- apiGroups: [""]
  resources: ["services", "configmaps", "secrets"]
  verbs: ["get", "list", "watch"]
- apiGroups: ["apps"]
  resources: ["deployments", "statefulsets", "daemonsets"]
  verbs: ["get", "list", "watch"]
- apiGroups: ["networking.k8s.io"]
  resources: ["ingresses"]
  verbs: ["get", "list", "watch"]
# Reads the kube-system namespace UID, which is the permanent per-cluster
# fingerprint Cloudkeel-DD uses to keep two clusters' identically-named objects
# apart. Without it a second cluster's Deployment/apps/web collides with the
# first one's on a single row.
- apiGroups: [""]
  resources: ["namespaces"]
  verbs: ["get", "list"]
# Flux integrations only. Harmless to include when Flux is not installed - an
# RBAC rule for a resource type the cluster does not have grants nothing. Omit
# these two and a Flux integration cannot list anything and its scans FAIL.
- apiGroups: ["helm.toolkit.fluxcd.io"]
  resources: ["helmreleases"]
  verbs: ["get", "list", "watch"]
- apiGroups: ["kustomize.toolkit.fluxcd.io"]
  resources: ["kustomizations"]
  verbs: ["get", "list", "watch"]
EOF

kubectl create clusterrolebinding ddetective-reader-binding \
  --clusterrole=ddetective-reader \
  --serviceaccount=default:ddetective-reader
```

> **Why `secrets` read access?** Helm stores its release records as Secrets -
> that's how Cloudkeel-DD learns the desired state. It reads Helm's own release
> Secrets, and **never** puts `Secret` contents into a diff (that kind is
> excluded from comparison entirely).
>
> This is read-only: no `create`, `update`, `patch`, or `delete` anywhere.

### 3. Mint a token and build the kubeconfig

```bash
TOKEN=$(kubectl create token ddetective-reader --duration=8760h)
SERVER=$(kubectl config view --raw --minify -o jsonpath='{.clusters[0].cluster.server}')
CA=$(kubectl config view --raw --minify -o jsonpath='{.clusters[0].cluster.certificate-authority-data}')

cat > ddetective-kubeconfig.yaml <<EOF
apiVersion: v1
kind: Config
clusters:
- name: target
  cluster:
    server: ${SERVER}
    certificate-authority-data: ${CA}
contexts:
- name: target
  context:
    cluster: target
    user: ddetective-reader
current-context: target
users:
- name: ddetective-reader
  user:
    token: ${TOKEN}
EOF
```

Verify it works standalone - this is exactly what Cloudkeel-DD will do:

```bash
KUBECONFIG=./ddetective-kubeconfig.yaml kubectl get deployments -A
```

If that returns your deployments with no CLI plugin involved, you're good.

> **Token lifetime:** `--duration=8760h` is one year; your cluster may cap it
> lower (check `kubectl create token` output). When it expires, scans fail and
> the real error shows in Inventory's **Last error** - mint a new one and update
> the integration.

### 4. Connect it in Cloudkeel-DD

**Connect** -> **Kubernetes**:

| Field | Value |
|---|---|
| Integration name | Any label, e.g. `prod-aks` |
| Kubeconfig file | The `ddetective-kubeconfig.yaml` from step 3 |
| Sync schedule | Manual, or a cadence |

**Test connection** reports how many Helm releases it found, then **Save and
start scanning**.

## Connecting more than one cluster

Fully supported - connect one integration per cluster. Each is scanned
independently.

Each Kubernetes integration derives a **real per-cluster identity** (the
`kube-system` namespace UID, the standard cross-tool cluster fingerprint) and
gets its own scope automatically. So two clusters running the *same* chart in the
*same* namespace - e.g. `hello-api` in `default` on both staging and prod - stay
two separate resources with two independent drift histories, not one row
overwriting the other.

## What gets detected

| Change | Result |
|---|---|
| `kubectl scale deployment x --replicas=3` | Drift: `spec.replicas` changed |
| `kubectl set image ...` | Drift: container image changed |
| `kubectl patch svc` (existing field) | Drift: that field changed |
| `kubectl delete deployment x` | Drift: resource gone from live |
| `helm upgrade` | **Not drift** - Helm's own record moves too. That's a legitimate change |
| `kubectl create deployment rogue` | Unmanaged workload - nothing claims it |

**Policy checks that apply to Kubernetes:** containers must not run as root; no
public LoadBalancer exposure without an exception annotation.

## Unmanaged workload detection

Alongside comparing Helm-managed objects, Cloudkeel-DD lists every object of the
six supported kinds and flags the ones no tool claims. This needs no Terraform
state source — unlike the cloud connectors, where a state file is what defines
"managed".

Ownership is read from **each object's own metadata**, not by asking your
deployment tools:

| Tool | What Cloudkeel-DD reads |
|---|---|
| Helm | `app.kubernetes.io/managed-by: helm` label, or the `meta.helm.sh/release-name` annotation |
| ArgoCD | `argocd.argoproj.io/tracking-id` annotation, or the `app.kubernetes.io/instance` / `argocd.argoproj.io/instance` labels |

Reading ownership off the object rather than querying ArgoCD or Flux is
deliberate. It keeps detection per-cluster (an ArgoCD Application on one cluster
can't silence a rogue workload on another), it survives an unreachable GitOps
server, and it needs no access to `argoproj.io` or `*.toolkit.fluxcd.io` custom
resources — which the ServiceAccount above does not grant.

**The trade-off:** labels can be stripped. An object whose ownership metadata was
removed reads as unmanaged. Nothing on the object claims it, so that is arguably
the honest answer — but if your cluster rewrites labels, expect findings here.

To verify it works, create something nothing owns and re-scan:

```bash
kubectl create deployment rogue-nginx --image=nginx -n default
```

It appears as an unmanaged resource on the next scan. Remove it with
`kubectl delete deployment rogue-nginx -n default`; the finding auto-resolves
once a later scan no longer sees it.

**Known behaviour worth understanding:** the comparison ignores fields that exist
live but were never in the Helm manifest. The API server defaults dozens of
fields (`clusterIP`, `protocol: TCP`, ...) that no chart declares - without this,
every resource would "drift" the moment it was created. The practical
consequence: *adding* a brand-new field out-of-band isn't drift on its own;
*changing a field the chart declares* is.
