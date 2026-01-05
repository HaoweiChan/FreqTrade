# FreqTrade on GKE - Deployment Guide

This directory contains Kubernetes manifests to deploy 5 FreqTrade bots and the UI to Google Kubernetes Engine (GKE).

## Prerequisites

1.  **GKE Cluster**: Ensure you have a Standard or Autopilot cluster running.
    ```bash
    gcloud container clusters create-auto freqtrade-cluster --region asia-east1
    ```
2.  **kubectl**: Configured to connect to your cluster.
    ```bash
    gcloud container clusters get-credentials freqtrade-cluster --region asia-east1
    ```

## 1. Setup Secrets & Config

**Edit `k8s/00-secrets-config.yaml`** before applying!

1.  **Secrets**: Replace `REPLACE_WITH_...` with your actual API keys and passwords.
2.  **Config**: Paste your content of `user_data/config.json` into the `data.config.json` section.

```bash
kubectl apply -f k8s/00-secrets-config.yaml
```

## 2. Deploy Bots

Apply the manifests for all 5 bots. Each bot gets:
- A Deployment (1 replica)
- A PersistentVolumeClaim (5GB standard disk) for `user_data` (Trade history DB)
- A Service (ClusterIP)

```bash
kubectl apply -f k8s/ichi.yaml
kubectl apply -f k8s/lookahead.yaml
kubectl apply -f k8s/macd.yaml
kubectl apply -f k8s/psar.yaml
kubectl apply -f k8s/macdcci.yaml
```

## 3. Deploy UI

Deploy the FreqUI web interface. It uses Type `LoadBalancer` to expose an external IP.

```bash
kubectl apply -f k8s/ui.yaml
```

Run `kubectl get svc freqtrade-ui` to get the External IP.

## 4. Maintenance

### Logs
GKE automatically collects logs. View them in **Cloud Logging** or via kubectl:
```bash
kubectl logs -l app=freqtrade --tail=50
```

*Note: Logs are rotated automatically by GKE node agent, so disk space exhaustion on the node is handled by GCP.*

### Updates
To update bots to the latest image:
```bash
kubectl rollout restart deployment/freqtrade-ichi
# Repeat for others
```
