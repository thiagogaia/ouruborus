---
name: devops-patterns
description: Padroes de infraestrutura e DevOps para projetos em Kubernetes. Use quando
  precisar configurar ou debugar deploys (GitOps/ArgoCD), pipelines CI/CD,
  secrets management, auto-scaling (HPA/Karpenter), canary deployments,
  API gateways (Kong/Nginx), ou troubleshooting de pods, rollouts e pipelines.
---

# DevOps Patterns

## Proposito

Guia de padroes e troubleshooting para infraestrutura de microservicos em Kubernetes.
Cobre o ciclo completo: CI/CD pipeline, build, deploy, monitoramento e rollback.

## Kubernetes Patterns

### Manifests por Servico

Cada servico deve ter manifests separados por tipo:

```
overlays/{cluster}/{service}/
├── kustomization.yaml      # Orquestra todos os manifests
├── manifests/
│   ├── rollout.yaml        # Argo Rollout (substitui Deployment)
│   ├── services.yaml       # stable + preview services
│   ├── hpa.yaml            # Horizontal Pod Autoscaler
│   ├── pdb.yaml            # Pod Disruption Budget
│   ├── secretstore.yaml    # External Secrets
│   └── envs.yaml           # ConfigMap com env vars
```

### Rollout (Canary Deploy)

Usar Argo Rollouts em vez de Deployment padrao:

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Rollout
spec:
  strategy:
    canary:
      stableService: {app}-stable
      canaryService: {app}-preview
      maxUnavailable: 0
      steps:
      - setWeight: 20
      - pause: {duration: 5m}
      - setWeight: 50
      - pause: {duration: 5m}
      - setWeight: 100
```

Sem `steps`: deploy automatico (100% de uma vez, aguarda readiness).

**Dois services por app:**
- `{app}-stable` — trafego principal
- `{app}-preview` — canary (nova versao em teste)

### HPA (Auto-Scaling)

```yaml
minReplicas: 2
maxReplicas: 8
metrics:
- type: Resource
  resource:
    name: memory
    target:
      averageUtilization: 75
- type: Resource
  resource:
    name: cpu
    target:
      averageUtilization: 70
```

Servicos criticos: min 2+, max 8+.
Workers de fila: ajustar por throughput, nao CPU.

### PDB (Disruption Budget)

```yaml
minAvailable: 1    # Padrao
minAvailable: 10%  # Servicos criticos (alta disponibilidade)
```

### Resources

```yaml
resources:
  requests:
    memory: 450Mi
    cpu: 150m
  limits:
    memory: 600Mi
    cpu: 300m
```

Regra: limits = ~1.3x requests. Nunca omitir limits.

## GitOps com ArgoCD

### Fluxo Completo

```
Developer commit → CI Pipeline → Build Docker → Push ECR
    → Update image tag in GitOps repo → ArgoCD detects
    → ArgoCD syncs → Argo Rollouts executa canary → Done
```

### Repositorios GitOps

**gitops-apps**: manifests Kubernetes (kustomize overlays)
**argocd-apps**: configuracoes de Applications do ArgoCD

### Kustomize

Pipeline atualiza tag da imagem via:
```bash
kustomize edit set image {ecr-url}/{app}:{pipeline-id}-{commit-sha}
```

Tags geradas:
- `{pipeline-id}-{commit-sha}` — unica, imutavel
- `{branch}` — latest da branch

### Rollback

3 formas, em ordem de preferencia:
1. **Git revert** no gitops repo (ArgoCD sincroniza automaticamente)
2. **ArgoCD CLI**: `argocd app rollback {app} {revision}`
3. **Argo Rollouts**: `kubectl argo rollouts undo {app} -n {ns}`

## CI/CD Pipeline

### Stages

```
test → sonarqube-check → setup → build → deploy
```

1. **test**: roda testes unitarios, gera junit.xml + cobertura
2. **sonarqube**: analise de qualidade (bugs, smells, vulnerabilities)
3. **setup**: prepara ambiente (se necessario)
4. **build**: Kaniko build Docker → push ECR
5. **deploy**: atualiza tag no gitops repo → ArgoCD deploy

### Build com Kaniko

Kaniko constroi imagens Docker SEM Docker daemon:
```yaml
/kaniko/executor \
  --context $CI_PROJECT_DIR \
  --dockerfile $CI_PROJECT_DIR/Dockerfile \
  --destination $ECR_URL/$CI_PROJECT_PATH:$TAG
```

Dockerfile separado do codigo (repo dedicado de dockerfiles).

### Pipeline Templates

Reutilizar templates por stack:
```yaml
include:
- project: {org}/devops/pipeline
  file:
  - .gitlab/ci/{stack}/test/test.yml
  - .gitlab/ci/{stack}/build/build.yml
  - .gitlab/ci/{stack}/deploy/deploy.yml
```

## Secrets Management

### Stack

```
AWS Parameter Store → External Secrets Operator → Kubernetes Secrets
```

**Nunca** commitar secrets em Git. Usar:
1. AWS Parameter Store (ou Secrets Manager) como source of truth
2. External Secrets Operator sincroniza para K8s Secrets
3. Pods referenciam Secrets via `envFrom.secretRef`

### IRSA (IAM Roles for Service Accounts)

Cada servico tem ServiceAccount com IAM Role dedicada:
```yaml
serviceAccountName: {app}-secret
# Annotations apontam para IAM Role especifica
```

Pod so acessa os secrets que a role permite.

## API Gateway (Kong)

### Arquitetura

```
Internet → CDN (Akamai/CloudFront) → Kong (API Gateway) → K8s Services
```

Kong como ingress controller:
- **Control Plane**: configuracao de rotas e plugins
- **Data Plane**: proxy de trafego

### Plugins Essenciais

- **rate-limiting**: protecao contra abuse
- **key-auth / jwt**: autenticacao
- **cors**: cross-origin
- **request-transformer**: manipulacao de headers
- **prometheus**: metricas

## Troubleshooting

### Deploy travou (OutOfSync)

```bash
kubectl get app -n argocd {app} -o yaml  # Ver diff
argocd app sync {app}                     # Forcar sync
```

### Pods nao sobem

```bash
kubectl describe pod -n {ns} {pod}        # Ver eventos
kubectl logs -n {ns} {pod} -f             # Ver logs
kubectl get events -n {ns} --sort-by='.lastTimestamp'
```

### Rollout em loop

```bash
kubectl argo rollouts get rollout -n {ns} {app}    # Status
kubectl argo rollouts pause -n {ns} {app}          # Pausar
kubectl argo rollouts abort -n {ns} {app}          # Abortar
```

### Image pull failed

```bash
aws ecr describe-images --repository-name {repo}   # Verificar ECR
kubectl get secret -n {ns} | grep ecr              # Verificar pull secret
```

### Pipeline falha

- **test**: rodar `npm run test:ci` localmente
- **build**: verificar Dockerfile e permissoes SSH
- **deploy**: verificar se path existe no gitops repo

## Regras

- NUNCA aplicar manifests manualmente no cluster (sempre via Git)
- SEMPRE testar em dev/staging antes de producao
- SEMPRE configurar readiness/liveness probes
- SEMPRE ter PDB para servicos com 2+ replicas
- NUNCA commitar secrets em repositorios Git
- Rollback via git revert (mantendo auditoria)
- Monitorar metricas (Grafana/Prometheus) durante deploy

## Output Esperado

Ao resolver problemas de infra, reportar:
```
Diagnostico: [o que esta acontecendo]
Causa: [por que]
Solucao: [comandos/mudancas especificas]
Prevencao: [como evitar no futuro]
```
