# Deployment guide

`deepface-api` is a stateless HTTP service. The only persistent state is
the `output/` directory, which holds optional annotated renders — mount
it as a volume if you want them retained.

## Recommended baseline

- **Python**: 3.11 (3.10 and 3.12 are also supported).
- **CPU/RAM**: 2 vCPU + 2 GB RAM is enough for low QPS; expect ~1 GB
  RSS once TensorFlow has loaded the RetinaFace + DeepFace weights.
- **GPU**: optional. Use `Dockerfile.gpu` and an NVIDIA host with the
  Container Toolkit. The first analyze request will trigger weight
  downloads — pre-warm by issuing a request during boot.

## Docker (single host)

### docker compose

```bash
git clone https://github.com/foru17/deepface-api.git
cd deepface-api
cp .env.example .env
docker compose up -d --build
```

The compose file mounts `./output` to `/data/output` and reads env vars
from `.env`. To run the GPU profile instead:

```bash
docker compose --profile gpu up -d --build
```

### Raw `docker run`

```bash
docker run -d --name deepface-api \
  --restart unless-stopped \
  -p 8008:8008 \
  -v deepface-output:/data/output \
  -e DEEPFACE_MAX_UPLOAD_SIZE_MB=20 \
  -e DEEPFACE_LOG_JSON=true \
  ghcr.io/foru17/deepface-api:latest
```

## Kubernetes

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: deepface-api
spec:
  replicas: 2
  selector:
    matchLabels:
      app: deepface-api
  template:
    metadata:
      labels:
        app: deepface-api
    spec:
      containers:
        - name: app
          image: ghcr.io/foru17/deepface-api:latest
          ports:
            - containerPort: 8008
          env:
            - name: DEEPFACE_LOG_JSON
              value: "true"
            - name: DEEPFACE_CORS_ORIGINS
              value: "https://app.example.com"
          readinessProbe:
            httpGet:
              path: /api/v1/ready
              port: 8008
            initialDelaySeconds: 5
            periodSeconds: 10
          livenessProbe:
            httpGet:
              path: /health
              port: 8008
            initialDelaySeconds: 60
            periodSeconds: 30
          resources:
            requests:
              cpu: "500m"
              memory: "1Gi"
            limits:
              cpu: "2"
              memory: "3Gi"
          volumeMounts:
            - name: output
              mountPath: /data/output
      volumes:
        - name: output
          emptyDir: {}
---
apiVersion: v1
kind: Service
metadata:
  name: deepface-api
spec:
  selector:
    app: deepface-api
  ports:
    - port: 80
      targetPort: 8008
```

## Operational concerns

### Logs

Set `DEEPFACE_LOG_JSON=true` for structured JSON line logs that include
the request ID. Tail with `docker logs -f deepface-api` or your usual
aggregator (Datadog, Loki, Cloud Logging, …).

### Metrics

Not bundled. Add `prometheus-fastapi-instrumentator` and a single line
in `main.create_app()` if you want Prometheus exposition:

```python
from prometheus_fastapi_instrumentator import Instrumentator

Instrumentator().instrument(app).expose(app, endpoint="/metrics")
```

### Rate limiting / auth

Front the service with a reverse proxy (NGINX, Traefik, Envoy) or an
API gateway. For lightweight token auth, add a FastAPI dependency that
reads `Authorization: Bearer …` and reject unauthorized requests early.

### Scaling

The ML hot path runs on the threadpool, so a single process serves
roughly 1 inflight ML request at a time. For higher concurrency:

- Run multiple uvicorn workers (`UVICORN_WORKERS=4`).
- Or scale horizontally with N pods + a load balancer.

### Backups

Nothing to back up unless you depend on the annotated images in
`output/`.

### Upgrading

Images are tagged with semver (`v2.0.0`, `2.0`, `2`) plus `latest` on
the default branch. Pin to a specific tag in production and roll
forward intentionally.
