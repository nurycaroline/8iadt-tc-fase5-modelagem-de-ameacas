# Arquiteturas de avaliação (DATA-03, DET-04, PIPE-04)

Imagens placeholder em `data/eval/` inspiradas nas Arquiteturas 1–2 do enunciado do hackathon. Substitua pelas figuras oficiais do PDF quando disponíveis e reanote no Label Studio / YOLO se necessário.

## Checklist de componentes esperados

### Arquitetura 1 — `data/eval/arch1/arch1.png`

| Componente esperado | Família STRIDE | Label YOLO (classes.txt) |
| ------------------- | -------------- | ------------------------ |
| Cliente / usuário   | client         | `client`                 |
| API / gateway       | api            | `api`                    |
| Banco de dados      | database       | `database`               |

Label: `data/eval/arch1/arch1.txt`

### Arquitetura 2 — `data/eval/arch2/arch2.png`

| Componente esperado | Família STRIDE | Label YOLO |
| ------------------- | -------------- | ---------- |
| Cliente             | client         | `client`   |
| Compute / app       | compute        | `compute`  |
| Storage             | storage        | `storage`  |
| Banco de dados      | database       | `database` |

Label: `data/eval/arch2/arch2.txt`

## Como anotar / atualizar

1. Abra a imagem no Label Studio (ou ferramenta YOLO) e marque bounding boxes.
2. Exporte labels no formato `class xc yc w h` normalizado.
3. Atualize `classes.txt` se novas classes forem necessárias e sincronize `data/class_map.yaml`.

## Demo rápida (detector fake / pesos reais)

```bash
stride-mvp analyze data/eval/arch1/arch1.png --out reports
stride-mvp analyze data/eval/arch2/arch2.png --out reports
```
