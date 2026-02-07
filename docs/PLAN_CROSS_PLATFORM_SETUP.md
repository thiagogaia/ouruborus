# Plano: Cross-platform setup.sh (#23)

## Contexto

O setup.sh funciona em macOS e Linux Debian/Ubuntu. Quebra em RHEL/Fedora/Alpine (apt-get hardcoded). Windows nativo não é suportado — **WSL é requisito documentado** (decisão do dev). Python scripts já são cross-platform (pathlib em tudo).

## Decisão

**Opção A: WSL obrigatório para Windows.** Foco em corrigir gaps reais do shell script para Linux não-Debian. Sem PowerShell, sem rewrite em Python.

## Complexidade: Média
## Impacta: setup.sh, batch-setup.sh, maintain.sh, README.md

## Steps

### 1. Fix detecção de OS no setup.sh

Substituir `is_debian_based()` por `detect_linux_distro()` que retorna a família:

```bash
detect_linux_distro() {
    if [[ -f /etc/debian_version ]] || grep -qi "ubuntu\|debian" /etc/os-release 2>/dev/null; then
        echo "debian"
    elif [[ -f /etc/redhat-release ]] || grep -qi "fedora\|rhel\|centos\|rocky\|alma" /etc/os-release 2>/dev/null; then
        echo "redhat"
    elif [[ -f /etc/alpine-release ]]; then
        echo "alpine"
    elif [[ -f /etc/arch-release ]]; then
        echo "arch"
    else
        echo "unknown"
    fi
}
```

**Arquivo**: `setup.sh:420-423`

### 2. Fix instalação de python3-venv por distro

Substituir o bloco apt-get hardcoded por switch na família:

```bash
case "$(detect_linux_distro)" in
    debian)  sudo apt-get install -y -qq "python${PYTHON_VERSION}-venv" ;;
    redhat)  sudo dnf install -y -q "python3-venv" 2>/dev/null || sudo yum install -y -q "python3-venv" ;;
    alpine)  sudo apk add --quiet python3 ;;
    arch)    sudo pacman -S --noconfirm python ;;
    *)       echo "Instale python3-venv manualmente para sua distribuição" ;;
esac
```

**Arquivo**: `setup.sh:427-451`

### 3. Fix shebang do maintain.sh

```bash
# De:
#!/bin/bash
# Para:
#!/usr/bin/env bash
```

**Arquivo**: `.claude/brain/maintain.sh:1`

### 4. Adicionar seção de requisitos no README.md

Adicionar no README uma seção "Requirements":

```markdown
## Requirements

- **macOS** or **Linux** (Debian, Ubuntu, Fedora, RHEL, Alpine, Arch)
- **Windows**: Requires [WSL2](https://learn.microsoft.com/en-us/windows/wsl/install) with Ubuntu
- **Python 3.8+**
- **Git**
- **Bash 4+**
```

**Arquivo**: `README.md` (seção nova)

### 5. Remover silent failures críticos no setup.sh

Substituir `2>/dev/null` em operações críticas por tratamento real:

- `cp -r ... 2>/dev/null` → verificar se origem existe antes de copiar
- Manter `2>/dev/null` apenas onde o silêncio é intencional (grep que pode não encontrar nada)

**Arquivo**: `setup.sh` (linhas 221, 226, 242, 248)

### 6. Validação

```bash
# Verificar que setup.sh roda sem erros de syntax
bash -n setup.sh

# Verificar que maintain.sh tem shebang correto
head -1 .claude/brain/maintain.sh

# Verificar que detect_linux_distro funciona
source setup.sh && detect_linux_distro
```

### 7. Commit

```
feat(setup): add multi-distro Linux support + document WSL requirement

- Replace is_debian_based() with detect_linux_distro() supporting
  Debian, RHEL/Fedora, Alpine, and Arch families
- Add dnf/yum/apk/pacman package installation paths
- Fix maintain.sh shebang to use /usr/bin/env bash
- Add platform requirements section to README.md
- Remove critical silent failures in setup.sh
```

## Riscos

- **Não tenho como testar RHEL/Alpine/Arch localmente** — mitigação: lógica simples, fallback para instruções manuais
- **Remover 2>/dev/null pode expor warnings cosméticos** — mitigação: substituir por verificação condicional, não por remoção cega

## Decisões já tomadas

- Windows nativo: **não suportado** — WSL2 é requisito documentado
- Não reescrever setup.sh em Python (seria Ouroboros-friendly mas esforço alto)
- `date -Iseconds`: funciona no macOS moderno (Darwin 24+), não precisa de fix
