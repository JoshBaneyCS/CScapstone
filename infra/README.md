# Infrastructure - Casino Capstone

This directory contains all infrastructure-as-code (IaC) for deploying the Casino Capstone application.

---

## Table of Contents

1. [Overview](#overview)
2. [Directory Structure](#directory-structure)
3. [Local Development](#local-development)
4. [Kubernetes Deployment](#kubernetes-deployment)
5. [ArgoCD GitOps](#argocd-gitops)
6. [GitHub Actions CI/CD](#github-actions-cicd)
7. [Domain Configuration](#domain-configuration)

---

## Overview

### Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        DEPLOYMENT ARCHITECTURE                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  GitHub Repository                                                           │
│       │                                                                      │
│       ├──▶ GitHub Actions (CI)                                              │
│       │         │                                                            │
│       │         ├──▶ Build Docker Images                                    │
│       │         ├──▶ Run Tests                                              │
│       │         └──▶ Push to Container Registry                             │
│       │                                                                      │
│       └──▶ ArgoCD (CD)                                                      │
│                 │                                                            │
│                 └──▶ Kubernetes Cluster                                     │
│                           │                                                  │
│                           ├──▶ PostgreSQL (StatefulSet + PVC 30GB)          │
│                           ├──▶ Backend API (Deployment)                     │
│                           ├──▶ Frontend (Deployment)                        │
│                           └──▶ Ingress (umgcgroupe.com)                     │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Technologies

| Tool | Purpose |
|------|---------|
| Docker | Container runtime |
| Kubernetes | Container orchestration |
| Kustomize | Kubernetes manifest management |
| ArgoCD | GitOps continuous delivery |
| GitHub Actions | CI/CD pipelines |
| Ingress-NGINX | Ingress controller |
| Cert-Manager | TLS certificate management |

---

## Directory Structure

```
infra/
├── README.md                 # This file
├── docker/
│   └── docker-compose.yml    # Local development (symlink to root)
├── k8s/
│   ├── base/                 # Base Kubernetes manifests
│   │   ├── kustomization.yaml
│   │   ├── namespace.yaml
│   │   ├── postgres/
│   │   │   ├── statefulset.yaml
│   │   │   ├── service.yaml
│   │   │   ├── pvc.yaml
│   │   │   └── secret.yaml
│   │   ├── backend/
│   │   │   ├── deployment.yaml
│   │   │   ├── service.yaml
│   │   │   └── configmap.yaml
│   │   ├── frontend/
│   │   │   ├── deployment.yaml
│   │   │   └── service.yaml
│   │   └── ingress/
│   │       └── ingress.yaml
│   └── overlays/
│       ├── dev/              # Development environment
│       │   ├── kustomization.yaml
│       │   └── patches/
│       └── prod/             # Production environment
│           ├── kustomization.yaml
│           └── patches/
├── argocd/
│   ├── application.yaml      # ArgoCD Application CRD
│   ├── project.yaml          # ArgoCD Project
│   └── README.md
└── scripts/
    ├── setup-cluster.sh      # Initial cluster setup
    └── deploy-argocd.sh      # ArgoCD installation
```

---

## Local Development

For local development, use Docker Compose from the repository root:

```bash
# From repository root
cp .env.example .env
docker compose up --build
```

Services:
- Frontend: http://localhost:5173
- Backend API: http://localhost:8080
- PostgreSQL: localhost:5432

---

## Kubernetes Deployment

### Prerequisites

- Kubernetes cluster (local: minikube, kind, k3s, or Docker Desktop)
- kubectl configured
- Kustomize (included in kubectl 1.14+)

### Quick Deploy

```bash
# Deploy to dev environment
kubectl apply -k infra/k8s/overlays/dev

# Deploy to prod environment
kubectl apply -k infra/k8s/overlays/prod
```

### Manual Step-by-Step

```bash
# 1. Create namespace
kubectl apply -f infra/k8s/base/namespace.yaml

# 2. Create secrets (edit first!)
kubectl apply -f infra/k8s/base/postgres/secret.yaml

# 3. Deploy PostgreSQL
kubectl apply -f infra/k8s/base/postgres/

# 4. Wait for PostgreSQL to be ready
kubectl wait --for=condition=ready pod -l app=postgres -n casino --timeout=120s

# 5. Deploy Backend
kubectl apply -f infra/k8s/base/backend/

# 6. Deploy Frontend
kubectl apply -f infra/k8s/base/frontend/

# 7. Create Ingress
kubectl apply -f infra/k8s/base/ingress/
```

### Verify Deployment

```bash
# Check all pods
kubectl get pods -n casino

# Check services
kubectl get svc -n casino

# Check ingress
kubectl get ingress -n casino

# View logs
kubectl logs -f deployment/backend -n casino
kubectl logs -f deployment/frontend -n casino
```

---

## ArgoCD GitOps

### Install ArgoCD

```bash
# Create namespace
kubectl create namespace argocd

# Install ArgoCD
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

# Wait for ArgoCD to be ready
kubectl wait --for=condition=available deployment/argocd-server -n argocd --timeout=300s

# Get initial admin password
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d
```

### Access ArgoCD UI

```bash
# Port forward to access UI
kubectl port-forward svc/argocd-server -n argocd 8080:443

# Open https://localhost:8080
# Username: admin
# Password: (from command above)
```

### Deploy Application via ArgoCD

```bash
# Apply the ArgoCD Application
kubectl apply -f infra/argocd/application.yaml
```

### ArgoCD Sync Policies

The application is configured with:
- **Auto-sync**: Automatically deploys when Git changes
- **Self-heal**: Reverts manual cluster changes
- **Prune**: Removes resources deleted from Git

---

## GitHub Actions CI/CD

### Workflows

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| `ci.yaml` | Push/PR to main | Build, test, lint |
| `docker-build.yaml` | Push to main | Build & push Docker images |
| `deploy.yaml` | Release tag | Deploy to production |

### Required Secrets

Add these secrets in GitHub repository settings:

| Secret | Description |
|--------|-------------|
| `DOCKERHUB_USERNAME` | Docker Hub username |
| `DOCKERHUB_TOKEN` | Docker Hub access token |
| `KUBE_CONFIG` | Base64-encoded kubeconfig (for direct deploy) |
| `ARGOCD_SERVER` | ArgoCD server URL |
| `ARGOCD_TOKEN` | ArgoCD API token |

### Setting Up Secrets

```bash
# Generate base64 kubeconfig
cat ~/.kube/config | base64 | tr -d '\n'

# Get ArgoCD token
argocd account generate-token --account admin
```

---

## Domain Configuration

### Domain: umgcgroupe.com

### DNS Setup

Add these DNS records:

| Type | Name | Value |
|------|------|-------|
| A | @ | `<cluster-external-ip>` |
| A | www | `<cluster-external-ip>` |
| CNAME | api | `umgcgroupe.com` |

### TLS Certificates (Cert-Manager)

```bash
# Install cert-manager
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml

# Create ClusterIssuer for Let's Encrypt
kubectl apply -f - <<EOF
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: admin@umgcgroupe.com
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - http01:
        ingress:
          class: nginx
EOF
```

### Local Development with Custom Domain

For local testing with the domain:

```bash
# Add to /etc/hosts (Linux/Mac) or C:\Windows\System32\drivers\etc\hosts (Windows)
127.0.0.1 umgcgroupe.com
127.0.0.1 api.umgcgroupe.com
```

---

## Storage

### Persistent Volume Claim (30GB)

PostgreSQL data is stored on a 30GB PVC:

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: postgres-pvc
  namespace: casino
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 30Gi
  storageClassName: standard  # Adjust for your cluster
```

### Backup Strategy

For production, consider:
- Velero for cluster-wide backups
- pg_dump CronJob for database backups
- Storing backups in S3/GCS

---

## Troubleshooting

### Common Issues

**Pods stuck in Pending:**
```bash
kubectl describe pod <pod-name> -n casino
# Check for resource constraints or PVC issues
```

**Database connection errors:**
```bash
# Check PostgreSQL logs
kubectl logs statefulset/postgres -n casino

# Verify secret is mounted
kubectl exec -it deployment/backend -n casino -- env | grep DATABASE
```

**Ingress not working:**
```bash
# Check ingress controller
kubectl get pods -n ingress-nginx

# Check ingress status
kubectl describe ingress casino-ingress -n casino
```

### Useful Commands

```bash
# Shell into a pod
kubectl exec -it deployment/backend -n casino -- /bin/sh

# Port forward to a service
kubectl port-forward svc/backend -n casino 8080:8080

# View all resources in namespace
kubectl get all -n casino

# Delete and recreate
kubectl delete -k infra/k8s/overlays/dev
kubectl apply -k infra/k8s/overlays/dev
```

---

## Next Steps

1. **Set up your Kubernetes cluster** (minikube, kind, or cloud)
2. **Install ArgoCD** using the commands above
3. **Configure DNS** for umgcgroupe.com
4. **Add GitHub secrets** for CI/CD
5. **Push to main branch** to trigger first deployment

Questions? Create an issue on GitHub!