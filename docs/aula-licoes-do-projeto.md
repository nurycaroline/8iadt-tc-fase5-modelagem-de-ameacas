# Aula completa — Tudo que este projeto ensina a um dev fullstack

> Um estudo guiado do **STRIDE Threat Modeling MVP**: como um sistema que "olha"
> para um diagrama de arquitetura e devolve um relatório de ameaças foi
> construído, por que cada decisão foi tomada, e quais lições você leva para
> qualquer projeto — de ML ou não.

Este documento assume que você é dev fullstack (web, APIs, bancos) e **não**
assume experiência prévia com machine learning ou visão computacional. Cada
conceito novo é explicado antes de ser usado.

---

## Índice

1. [O problema e o produto](#1-o-problema-e-o-produto)
2. [A arquitetura em uma frase (e em um diagrama)](#2-a-arquitetura-em-uma-frase-e-em-um-diagrama)
3. [Como o modelo funciona — visão computacional para dev fullstack](#3-como-o-modelo-funciona--visão-computacional-para-dev-fullstack)
4. [A base de treinamento](#4-a-base-de-treinamento)
5. [Por que essa stack foi escolhida](#5-por-que-essa-stack-foi-escolhida)
6. [A camada semântica: do pixel ao risco](#6-a-camada-semântica-do-pixel-ao-risco)
7. [STRIDE — o domínio de segurança](#7-stride--o-domínio-de-segurança)
8. [Os bugs que só aparecem em produção de ML (e como foram corrigidos)](#8-os-bugs-que-só-aparecem-em-produção-de-ml-e-como-foram-corrigidos)
9. [Engenharia de software aplicada (o que copiar para seus projetos)](#9-engenharia-de-software-aplicada-o-que-copiar-para-seus-projetos)
10. [Testes em um sistema com componente probabilístico](#10-testes-em-um-sistema-com-componente-probabilístico)
11. [Dependências, empacotamento e Docker — as batalhas reais](#11-dependências-empacotamento-e-docker--as-batalhas-reais)
12. [O processo: desenvolvimento guiado por especificação](#12-o-processo-desenvolvimento-guiado-por-especificação)
13. [Checklist de lições transferíveis](#13-checklist-de-lições-transferíveis)

---

## 1. O problema e o produto

**Problema**: modelagem de ameaças (threat modeling) é o exercício de olhar para
uma arquitetura e perguntar "o que pode dar errado aqui?". É manual, lento e
depende de especialistas de segurança. O enunciado do hackathon (FIAP, fase 5)
pedia: a partir de uma **imagem** de diagrama de arquitetura, identificar os
componentes com **IA treinada de forma supervisionada** e gerar automaticamente
um **Relatório de Modelagem de Ameaças STRIDE**, com vulnerabilidades e
contramedidas por componente.

**Produto entregue** (`stride-mvp`):

```bash
stride-mvp analyze data/eval/arch1/arch1.png --out reports
# → reports/arch1.md (relatório legível) + reports/arch1.json (estruturado)
```

Além do CLI, há uma UI Gradio (`stride-mvp ui`), empacotamento Docker e um
detector real treinado (mAP ≈ 0.83 no split de validação — ver
`models/weights/metrics.json`).

A primeira lição já está aqui: **o requisito molda a arquitetura**. O enunciado
exigia treino supervisionado com dataset anotado. Isso descartou a solução
"manda a imagem pra um LLM multimodal e pede o relatório" — que seria mais
rápida de construir, porém não atenderia o requisito e seria não-determinística.
A decisão está registrada em `.specs/STATE.md` como AD-001: *detecção
supervisionada + pipeline híbrido (regras + knowledge base), não LLM-only*.

## 2. A arquitetura em uma frase (e em um diagrama)

> Um detector de objetos **probabilístico** encontra componentes na imagem; todo
> o resto do sistema é **determinístico** e guiado por dados versionados em YAML.

```
imagem (PNG/JPG)
   │
   ▼
[validate]  ── formato, tamanho máximo, corrupção → erro claro, exit ≠ 0
   │
   ▼
[detect]    ── YOLO11n fine-tunado → [(classe, confiança, bounding box), ...]
   │
   ▼
[dedupe]    ── remove caixas sobrepostas da mesma classe (IoU/contenção/centros)
   │
   ▼
[map]       ── class_map.yaml: 87+ classes cloud → ~20 famílias (database, api…)
   │
   ▼
[engine]    ── KB threats.yaml: família × categoria STRIDE → ameaça +
   │            vulnerabilidade + contramedida; papéis (workload/control/zone…)
   ▼
[report]    ── Markdown pt-BR + JSON; sumário, cobertura, avisos de confiança
```

O código segue exatamente essa decomposição (`src/stride_mvp/`):

| Módulo | Responsabilidade |
| ------ | ---------------- |
| `pipeline/validate.py` | Validação de entrada (fronteira do sistema) |
| `detection/` | Treino (`train.py`), inferência (`detector.py`), dedupe espacial (`dedupe.py`), métricas (`eval_metrics.py`) |
| `data/` | Download Kaggle, conversão Pascal VOC→YOLO, split, mapa classe→família |
| `stride/` | KB (`kb.py`), motor de análise (`engine.py`), renderização (`report.py`) |
| `pipeline/run.py` | Orquestração: validate → detect → dedupe → map → engine → report |
| `cli.py` / `web/` | Interfaces (Typer CLI e Gradio UI) sobre o mesmo pipeline |

Note a fronteira mais importante do projeto: **só um estágio é ML**. Detecção é
onde vive a incerteza; da detecção para frente, o mesmo input produz sempre o
mesmo output. Isso torna o sistema auditável (a KB é um arquivo YAML revisável
em PR), testável (dá para testar 90% do sistema sem GPU nem modelo) e explicável
(cada finding aponta a entrada da KB que o gerou).

## 3. Como o modelo funciona — visão computacional para dev fullstack

### 3.1 Classificação vs. detecção de objetos

- **Classificação**: "esta imagem é um gato?" — um rótulo por imagem.
- **Detecção de objetos**: "onde estão e o que são as coisas nesta imagem?" —
  uma lista de `(classe, caixa delimitadora, confiança)` por imagem.

Um diagrama de arquitetura tem vários componentes em posições arbitrárias,
então o problema é de **detecção**. O output do modelo é literalmente o que o
`ComponentDetector.predict()` retorna:

```python
Detection(
    class_name="aws_rds",
    confidence=0.98,
    bbox_xyxy=(x1, y1, x2, y2),  # cantos da caixa em pixels
)
```

### 3.2 YOLO em 5 parágrafos

**YOLO** ("You Only Look Once") é uma família de arquiteturas de rede neural
convolucional para detecção em tempo real. A ideia central: em vez de propor
regiões candidatas e classificar cada uma em etapas separadas (como o R-CNN
clássico), a rede olha a imagem **uma vez** e prevê todas as caixas e classes
simultaneamente, numa única passada. Por isso é rápida o suficiente para rodar
em CPU nesse MVP.

A imagem entra redimensionada (aqui, 640×640 — o parâmetro `imgsz`). A rede
divide a imagem implicitamente em regiões e, para cada região, prevê: existe
objeto aqui? De qual classe? Com que caixa exata? Cada previsão sai com um
**score de confiança** entre 0 e 1 — que não é uma probabilidade calibrada, mas
serve de ranking de certeza.

Usamos o **YOLO11n** da Ultralytics, onde "n" = *nano*, a menor variante da
família (~2.6M parâmetros). Modelos maiores (s/m/l/x) seriam mais precisos e
mais lentos. Para ícones de serviços cloud — formas bem definidas, alto
contraste, pouca variação — o nano basta, e treina em minutos numa GPU ou até
num Mac (MPS).

**Transfer learning**: o treino não parte do zero. `train.py` carrega
`yolo11n.pt`, os pesos pré-treinados no dataset COCO (80 classes de objetos do
mundo real: pessoas, carros, cadeiras...). As camadas iniciais da rede já sabem
detectar bordas, cantos, texturas e formas — conhecimento reaproveitável. O
*fine-tuning* ajusta a rede para as ~87 classes de ícones cloud com bem menos
dados e tempo do que treinar do zero exigiria. Essa é provavelmente a técnica
de ML mais importante para você conhecer como fullstack: **quase nunca se
treina do zero; adapta-se um modelo pré-treinado**.

**NMS (Non-Maximum Suppression)**: a rede naturalmente produz várias caixas
quase idênticas para o mesmo objeto. O NMS é o pós-processamento padrão que
mantém a caixa de maior confiança e descarta as vizinhas com alta sobreposição.
Aqui, o NMS é delegado ao Ultralytics — decisão registrada explicitamente: o
MVP não reimplementa NMS (e a seção 8 mostra por que o NMS sozinho não bastou).

### 3.3 O vocabulário mínimo de métricas

- **IoU (Intersection over Union)**: área da interseção de duas caixas dividida
  pela área da união. 1.0 = caixas idênticas; 0 = sem sobreposição. É a régua
  para dizer "essa detecção acertou o objeto anotado?" e também a base do
  dedupe (`detection/dedupe.py` implementa `iou()` em ~15 linhas legíveis).
- **Precision**: das caixas que o modelo previu, quantas estavam certas?
- **Recall**: dos objetos que existiam, quantos o modelo encontrou?
- **mAP (mean Average Precision)**: métrica agregada padrão de detecção —
  resume precision/recall por classe em vários limiares de IoU e tira a média.
  O comando `stride-mvp eval` grava o mAP em `metrics.json`; o modelo deste
  repo atingiu **mAP ≈ 0.83**, alto para um MVP (explicável: ícones cloud são
  visualmente consistentes, e o dataset é aumentado a partir de uma base menor
  — ver seção 4).

### 3.4 Hiperparâmetros de treino que você vai reencontrar em qualquer projeto de ML

Da assinatura de `train()` em `detection/train.py`:

| Parâmetro | O que é | Lição prática |
| --------- | ------- | ------------- |
| `epochs=50` | Quantas vezes o dataset inteiro passa pela rede | Mais nem sempre é melhor (overfitting); 50 foi suficiente aqui |
| `imgsz=640` | Resolução de entrada | Maior = mais detalhe e mais custo; 640 é o padrão YOLO |
| `batch=16/32` | Imagens por passo de otimização | Limitado pela memória da GPU; **no Mac, batch fixo** — o AutoBatch (`batch=-1`) do Ultralytics é orientado a CUDA e falha no MPS |
| `device` | `cuda` → `mps` → `cpu` | O código auto-detecta (`resolve_train_device`); MPS = GPU da Apple via Metal |
| `amp=True` | Mixed precision (float16+float32) | Praticamente de graça: mais rápido, menos memória |
| `fraction=0.1` | Treinar com 10% do dataset | Ideal para *smoke test* do pipeline antes do treino longo |

Duas lições operacionais que o projeto codificou em contrato:

1. **Treino interrompido ≠ modelo pronto.** O `best.pt` de uma corrida parcial
   não é promovido. `train()` só copia `train/weights/best.pt` →
   `models/weights/best.pt` ao fim de uma corrida completa. Artefatos de ML
   precisam do mesmo rigor de promoção que um build de produção.
2. **Smoke test antes do treino caro.** Rodar 3 épocas com `fraction=0.1` valida
   dataset, labels e device em minutos, antes de queimar horas de GPU. É o
   equivalente ML do "sobe local antes de fazer deploy".

## 4. A base de treinamento

### 4.1 O dataset

**Software Architecture Dataset** (Kaggle, `carlosrian/software-architecture-dataset`):
~8 mil imagens (com data augmentation) de diagramas de arquitetura cloud,
anotadas com bounding boxes de **~87 classes** de serviços AWS/Azure/GCP
(`aws_rds`, `azure_sql`, `gcp_cloud_run`, `user`, `api`...), no formato
**Pascal VOC** (um XML por imagem). A escolha está registrada em AD-003: o
dataset já vinha anotado, alinhado ao domínio (diagramas cloud) e ao requisito
de treino supervisionado.

Conceitos que você aprende aqui:

- **Anotação supervisionada**: alguém marcou manualmente, em cada imagem, cada
  componente com uma caixa e uma classe. Sem isso não há treino supervisionado.
  Anotar é a parte cara de ML — encontrar um dataset já anotado muda a
  viabilidade do projeto.
- **Data augmentation**: as ~8k imagens vêm de uma base menor multiplicada por
  transformações (rotação, escala, ruído...). Aumenta a robustez, mas atenção:
  imagens aumentadas da mesma origem são **correlacionadas** — o mAP de
  validação fica otimista se o split separar variantes da mesma imagem base.
- **Formatos de anotação**: Pascal VOC usa XML com coordenadas absolutas
  (`xmin, ymin, xmax, ymax`); YOLO usa TXT com valores normalizados
  (`classe x_centro y_centro largura altura`, tudo em [0,1]). O script
  `scripts/prepare_yolo_dataset.py` faz a conversão + split treino/validação
  (80/20, `seed=42` para reprodutibilidade) e gera o `data.yaml` que o
  Ultralytics consome. Conversão de formatos de dados é trabalho clássico de
  fullstack — em ML não é diferente, só muda o schema.

### 4.2 Dados de avaliação separados dos de treino

`data/eval/arch1` e `arch2` são as arquiteturas de avaliação do hackathon,
anotadas no mesmo pipeline mas **fora do treino**. Isso importa por causa de
**domain shift**: o modelo aprende a distribuição do Kaggle (diagramas AWS com
ícones oficiais); diagramas de estilo diferente (Azure, desenhos à mão, outra
paleta) degradam a precisão. O projeto sentiu isso na prática: o dataset tem
poucos exemplos Azure, e o detector alucinava classes AWS em diagramas Azure —
ver seção 8.

### 4.3 Binários fora do git

Dataset (~8k imagens) e pesos não são commitados; o download é reprodutível por
script (`stride_mvp/data/download.py` via API do Kaggle, credenciais em
`~/.kaggle/kaggle.json`). O `.gitignore` cuida do resto. Regra geral: **git
versiona código e dados pequenos e revisáveis (YAMLs, labels de eval); artefatos
grandes têm download documentado e reprodutível**.

## 5. Por que essa stack foi escolhida

Cada escolha está registrada com razão e trade-off em `.specs/STATE.md`
(decisões AD-001 a AD-008). Resumo comentado:

| Escolha | Por quê | Trade-off aceito |
| ------- | ------- | ---------------- |
| **Python 3.11+** | Ecossistema de ML/CV é Python-first; greenfield sem legado | Sem stack JS no backend |
| **Ultralytics YOLO11n** | API de treino/inferência em ~5 linhas, NMS embutido, docs fortes, funciona com o dataset VOC convertido | Acoplamento ao ecossistema Ultralytics |
| **Regras + KB YAML** (não LLM) | Requisito de determinismo e auditabilidade; hackathon exigia ML supervisionado no *detector*, não texto gerado | Menos "mágica"; conteúdo da KB é curado à mão |
| **Typer (CLI)** | Interface P1 mínima para demo e automação; type hints viram argumentos | Sem API REST no MVP |
| **Gradio (UI)** | UI de upload em ~30 linhas, ideal para demo de ML; sem build frontend | Sem React/controle fino de UX |
| **pytest** | Padrão de facto; fixtures e parametrização | — |
| **uv + índice PyTorch CPU** | `pip install` padrão puxava wheels CUDA de vários GB; CPU basta para inferência de demo | GPU local exige `STRIDE_TORCH_INDEX` apontando para índice CUDA |
| **Docker (python:3.11-slim)** | Reprodução da demo em qualquer máquina | Pesos ficam **fora** da imagem, montados por volume |

A meta-lição: em MVP, o critério dominante é **menor distância até a demo que
prova a tese** — com portas abertas para evoluir. CLI antes de UI; Gradio antes
de React; YAML antes de banco; arquivo em `reports/` antes de persistência. Cada
"não" está documentado na seção *Out of Scope* da spec, o que protege o escopo
contra boas ideias na hora errada.

## 6. A camada semântica: do pixel ao risco

Aqui mora o design mais interessante do projeto para um fullstack — e ele não
tem nada de ML.

### 6.1 O problema da granularidade

O detector conhece ~87 classes (`aws_rds`, `azure_sql`, `gcp_cloud_sql`...). A
análise de segurança não deveria ter 87 conjuntos de ameaças: um RDS, um Azure
SQL e um Cloud SQL compartilham essencialmente os mesmos riscos de "banco de
dados gerenciado". A solução é uma **camada de indireção**:

```
classe do detector ──(class_map.yaml)──> família ──(threats.yaml)──> ameaças
   aws_rds                                database              6 entradas STRIDE
   azure_sql            ─┘                                      (spoofing, tampering…)
   gcp_cloud_sql        ─┘
```

- `data/class_map.yaml`: ~20 famílias (`database`, `compute`, `api`, `storage`,
  `zone`, `security`, `observability`, `edge`, `filesystem`, `backup`, `email`,
  `scaling`, `client`, `management`...), cada uma listando as classes que a
  compõem. A normalização remove prefixos de vendor (`aws-waf` e `waf` colapsam).
- `data/kb/threats.yaml`: a knowledge base — para cada `família × categoria
  STRIDE`, uma entrada com `threat` (ameaça), `vulnerability` (exemplo concreto)
  e `countermeasure` (mitigação acionável). Versão 2 da KB adiciona `roles`
  (papéis por família — ver 6.2) e um `fallback` explícito para o não mapeado.

Padrões clássicos reconhecíveis: **normalização de vocabulário** (como mapear
sinônimos de categorias num e-commerce) e **rules engine dirigida por dados**
(a lógica está nos dados versionados, não em `if/else` espalhado no código —
adicionar uma ameaça nova é um PR num YAML, revisável por um analista de
segurança que nunca leu Python).

### 6.2 Papéis: nem todo componente é uma superfície de ataque

Insight de domínio que virou modelo de dados. A primeira versão do relatório
tratava tudo igual — e um review externo apontou o absurdo: o WAF (um
*firewall*) aparecia listado como superfície vulnerável a ataques. A correção
(AD-007) introduziu **papéis por família** na KB:

| Papel | Exemplos | O relatório gera |
| ----- | -------- | ---------------- |
| `workload` | database, compute, api, storage | Ameaças STRIDE clássicas |
| `control` | security (KMS), observability (CloudWatch), edge (WAF, CloudFront), backup, scaling | **Verificações de eficácia/configuração** ("o WAF tem as regras certas?"), não ameaças de exposição |
| `zone` | subnets, VPC | Verificações estruturais de segmentação |
| `external` | client/usuário | Ameaças no contexto de entrada externa |
| `scope` | region, resource group, cloud | Só sumário — fronteira lógica não tem superfície própria |

E a regra de honestidade: componente sem mapeamento vai para **"Inventário não
classificado"** com categoria `Não classificado` — o sistema **nunca inventa**
uma ameaça genérica para parecer completo. Antes dessa regra, tudo que era
desconhecido virava um "Information Disclosure" fabricado, minando a
credibilidade do relatório inteiro.

### 6.3 Cobertura como métrica de qualidade em runtime

O relatório expõe `coverage` = detecções mapeadas / total. Abaixo de
`STRIDE_MIN_COVERAGE` (default 0.8), o CLI emite warning em stderr apontando o
remédio (`stride-mvp check-map`) — sem mudar o exit code, porque cobertura baixa
degrada mas não invalida o resultado. E o comando `stride-mvp check-map` audita
**antes do deploy** se toda classe do vocabulário do detector resolve para uma
família (exit ≠ 0 lista os gaps). É o mesmo raciocínio de um contract test entre
serviços: valida a integridade do contrato detector→class_map como um gate, não
como uma surpresa em produção.

## 7. STRIDE — o domínio de segurança

STRIDE é um framework da Microsoft para categorizar ameaças. As seis categorias,
com os exemplos reais da KB deste projeto (família `database`):

| Categoria | Pergunta | Exemplo da KB |
| --------- | -------- | ------------- |
| **S**poofing | Alguém pode fingir ser outra identidade? | Credenciais padrão/compartilhadas → IAM, rotação de segredos, MFA |
| **T**ampering | Dados/código podem ser alterados sem autorização? | Sem controles de integridade → checksums, audit logs imutáveis |
| **R**epudiation | Alguém pode negar uma ação por falta de rastro? | Logs de acesso ausentes → auditoria completa de queries |
| **I**nformation Disclosure | Dados podem vazar? | DB sem criptografia/exposto → at-rest encryption, private endpoints, least privilege |
| **D**enial of Service | O serviço pode ser derrubado? | Sem limites de conexão → rate limiting, réplicas, backups testados |
| **E**levation of Privilege | Alguém pode ganhar permissões indevidas? | Usuário da app com permissão demais → menor privilégio, roles separadas |

Para você como fullstack, o valor é duplo: (1) STRIDE é um checklist mental
excelente para revisar **qualquer** feature que você constrói — passe as seis
perguntas no seu próximo endpoint; (2) o projeto mostra que dá para codificar
conhecimento de segurança como **dados estruturados e versionados**, não como
conhecimento tribal na cabeça do especialista.

## 8. Os bugs que só aparecem em produção de ML (e como foram corrigidos)

Esta é talvez a parte mais valiosa do projeto como aula: o histórico de
correções depois que o modelo real rodou em diagramas reais. Duas rodadas de
review externo geraram duas features inteiras de correção (`stride-report-quality`
e `stride-report-fidelity`, com specs completas em `.specs/features/`).

### 8.1 Rodada 1 — o relatório mentia com confiança

Review do relatório de uma arquitetura AWS real: **30 de 34 findings** caíam no
fallback genérico, controles (WAF, KMS, CloudTrail) apareciam como superfícies
vulneráveis, e instâncias repetidas geravam blocos duplicados. Correções:

- Papéis por família (seção 6.2) — controle gera verificação, não ameaça.
- Fallback honesto — "Inventário não classificado", nunca ameaça inventada.
- Agrupamento por classe com `instance_count` — 4 subnets = 1 finding ×4, não
  4 blocos idênticos.
- Métrica `coverage` + warning + `check-map` como gate de vocabulário.

### 8.2 Rodada 2 — o detector alucina, o sistema precisa ser honesto sobre isso

Review (via Gemini) das análises de arch1/arch2 achou problemas mais sutis:

**Problema A — vizinho semântico errado.** O texto de ameaça de S3 (buckets
públicos, ACL) aparecia para EFS (filesystem NFS) e AWS Backup; texto de SQS
para SES (e-mail). A família era "próxima", mas a ameaça era **tecnicamente
errada** — pior que não dizer nada, porque parece certo. Correção: famílias
semânticas mais finas (`filesystem`, `backup`, `email`, `scaling`,
`integration`, `dependency`, `management`), cada uma com ameaças específicas
(ex.: EFS → "mount targets expostos a subnets/SGs indevidos", não "bucket
público"). Lição: **granularidade de taxonomia é uma decisão de produto** — de
tempos em tempos a realidade cobra uma categoria nova.

**Problema B — contagens infladas.** Em diagramas Azure (raros no treino), o
detector emitia caixas múltiplas e sobrepostas para o mesmo ícone — que o NMS
do YOLO **não** removia, porque eram sobreposições parciais abaixo do limiar
interno, ou double-reads com IoU baixo mas centros quase coincidentes. O
relatório dizia "6 bancos de dados" onde havia 2. Correção: dedupe espacial
próprio (`detection/dedupe.py`), rodando **depois** do NMS e **antes** da
análise, com três critérios (mesma classe normalizada): IoU ≥ 0.3, contenção ≥
0.8 (uma caixa 80% dentro da outra), ou centros mais próximos que 0.55× a
diagonal média. A sobreposição é transitiva (A~B e B~C ⇒ um cluster, via
union-find), e sobrevive a detecção de maior confiança. Configurável por
`STRIDE_DEDUPE_IOU`; `0` desliga.

**Problema C — incerteza invisível.** Detecções de confiança 0.3 e 0.99 eram
apresentadas com a mesma autoridade. Correção: coluna de confiança no sumário,
marcador ⚠ abaixo de `STRIDE_LOW_CONF` (default 0.5) e nota explicando que
podem ser falsos positivos "especialmente em diagramas fora da distribuição de
treino".

As três lições macro desta seção:

1. **Um pipeline com componente probabilístico precisa de camadas de defesa
   determinísticas** — dedupe, fallback honesto, cobertura, marcadores de
   confiança. Você não conserta o modelo em um dia; você torna o sistema
   honesto sobre as limitações dele hoje e agenda o retreino (aqui: feature
   futura `detector-azure-robustness`, explicitamente fora de escopo).
2. **Review externo do output real vale mais que qualquer métrica agregada.**
   O mAP era 0.83 e mesmo assim o relatório era ruim — porque os erros que
   importavam (semântica errada, contagem inflada) não são o que o mAP mede.
3. **UX de incerteza é feature.** Mostrar o quanto o sistema *não* sabe
   (coverage, ⚠, inventário) é o que torna o output confiável.

## 9. Engenharia de software aplicada (o que copiar para seus projetos)

Padrões concretos do código que valem em qualquer stack:

**Injeção de dependência estrutural, sem framework.** `pipeline/run.py` aceita
`detector`, `mapper`, `kb` e `renderer` opcionais; o contrato do detector é um
`typing.Protocol` (duck typing verificável — a versão Python de uma interface
TypeScript). Resultado: os testes de integração rodam o pipeline inteiro com um
detector fake, sem GPU, sem pesos, em milissegundos.

```python
class DetectorProtocol(Protocol):
    def predict(self, image_path: Path) -> list[Detection]: ...
```

**Configuração em camadas com validação na fronteira.** `config.py`: defaults →
YAML opcional → env vars (`STRIDE_CONF`, `STRIDE_MODEL_PATH`,
`STRIDE_DEDUPE_IOU`...), tudo num `AppConfig` **imutável** (`@dataclass(frozen=True)`).
Valores que devem estar em [0,1] são validados com mensagem acionável na carga
— não com um crash critico três estágios depois.

**Mensagens de erro que ensinam o remédio.** `MissingWeightsError` não diz
"file not found": diz que os pesos não existem, onde o treino os deixa, para
onde são promovidos e **todos os caminhos tentados**. O resolver de pesos
(`resolve_model_path`) tenta uma lista ordenada de candidatos (path configurado,
layout do Ultralytics `train/weights/best.pt`, mount Docker) — tolerância a
variação de layout sem magia.

**Não confiar cegamente na lib.** O `ComponentDetector` re-filtra por confiança
mesmo sabendo que o Ultralytics já filtra — o comentário no código explica: "re-
filters for a hard guarantee". A garantia do *seu* contrato é sua, não da
dependência.

**Fronteira dupla de interface, um core.** CLI e UI Gradio são cascas finas
sobre o mesmo `run_pipeline`. O CLI traduz exceções de domínio em exit codes e
mensagens coloridas em stderr; nenhuma lógica vive na interface.

**Warnings ≠ errors.** Cobertura baixa gera warning em stderr sem mudar o exit
code; imagem inválida gera erro com exit ≠ 0. Distinguir "degradado" de
"inválido" é design de operabilidade.

## 10. Testes em um sistema com componente probabilístico

O repositório tem **160 testes** (`pytest -q`), organizados como pirâmide:

- `tests/unit/` — um arquivo por módulo (engine, kb, class_map, dedupe, report,
  config, train, detector...). Rápidos, sem I/O pesado, sem modelo.
- `tests/integration/` — CLI de ponta a ponta e pipeline e2e, com detector fake
  injetado.

Como se testa o não-determinístico? **Separando-o.** O modelo em si é testado
por métrica (mAP no split de validação), não por assert unitário. Todo o resto —
que é a maioria do sistema — é determinístico e testado normalmente: o dedupe
tem testes geométricos puros; o engine tem testes de tabela (detecções de
entrada → findings esperados); a conversão VOC→YOLO tem fixtures de XML.

Três práticas menos comuns que valem a pena conhecer:

1. **Gates nomeados** (documentados no README): *Quick* (`pytest -q tests/unit`)
   a cada mudança, *Full* (`pytest -q`) antes de commit de feature, *Build*
   (`compileall + pytest`) no fim de fase. Custo de feedback proporcional ao
   risco da mudança.
2. **Mutation testing manual**: a validação da feature de fidelity registra
   "3/3 mutants killed" — mutações introduzidas de propósito no código (ex.:
   trocar `mapped_instances` por `total_instances`) para verificar se algum
   teste falha. Se nenhum falha, o teste é decorativo. Uma dessas mutações
   sobreviveu numa rodada anterior e virou a lição L-005 em `.specs/LESSONS.md`.
3. **Testes de regressão nascidos de reviews**: os problemas achados pelo review
   Gemini (seção 8.2) viraram cenários de teste com as detecções reais de
   arch1/arch2 — o bug de ontem é o teste de regressão de hoje.

## 11. Dependências, empacotamento e Docker — as batalhas reais

O `pyproject.toml` deste projeto é uma aula em si, porque os comentários
documentam **por que** cada pin existe:

- **Extras opcionais** (`[project.optional-dependencies]`): `dev` (pytest),
  `ml` (ultralytics, opencv), `ui` (gradio), `kaggle`. Quem só roda testes não
  baixa PyTorch. Instalação seletiva: `bash scripts/install_deps.sh dev`.
- **A guerra do numpy 2**: Gradio <4.44 pinava `numpy~=1.0`; OpenCV 4.12+ exige
  `numpy>=2`. Instalar `gradio` + `ultralytics` sem os pins certos fazia o
  resolver do pip *backtrackear* por minutos ou falhar. Solução: `gradio>=4.44`,
  `opencv <5`, `pytest <10` — cada um com comentário explicando o motivo. Lição:
  **pins sem comentário são bombas-relógio; pins com comentário são
  documentação**.
- **O problema das wheels CUDA**: `pip install torch` em Linux baixa por padrão
  builds com CUDA (2+ GB) — inútil para inferência CPU de demo. O
  `scripts/install_deps.sh` pré-instala torch do índice CPU
  (`download.pytorch.org/whl/cpu`) usando **uv** (resolver em Rust, ordens de
  magnitude mais rápido que pip), com opt-in para GPU via `STRIDE_TORCH_INDEX`.
  Setup caiu de "vários GB e muitos minutos" para segundos/minutos (AD-006).
- **Docker com cache de camadas consciente**: o `Dockerfile` copia só
  `pyproject.toml` + um stub de `src/`, instala dependências (camada cara,
  cacheada), e só então copia o código real (camada barata que muda sempre).
  Mudou código → rebuild em segundos.
- **Pesos fora da imagem**: `best.pt` é montado por volume
  (`STRIDE_MODEL_PATH=/weights/best.pt`), não embutido. Imagem leve, modelo
  atualizável sem rebuild — modelo é artefato de dado, não de código. E sem o
  peso, a UI mostra erro claro em vez de traceback.

## 12. O processo: desenvolvimento guiado por especificação

O diretório `.specs/` registra o processo que produziu o código — e é um modelo
replicável:

- **Uma pasta por feature** (`stride-threat-modeling-mvp`,
  `stride-report-quality`, `stride-report-fidelity`), cada uma com `spec.md`
  (requisitos com IDs rastreáveis — DATA-01, DET-02, KB-04... — e critérios de
  aceitação no formato WHEN/THEN), `design.md`, `tasks.md` (tarefas atômicas,
  um commit por tarefa) e `validation.md` (verificação independente com
  evidência: "18/18 ACs, 3/3 mutants killed").
- **`STATE.md`** — o registro de decisões (AD-001…AD-008), cada uma com
  *decisão, razão, trade-off, escopo, data, status*. É a resposta permanente ao
  "por que isso é assim?" seis meses depois. Se você adotar uma única prática
  deste projeto, adote esta: **ADRs leves, escritos no momento da decisão**.
- **`LESSONS.md`** — lições extraídas de falhas de verificação (mutante que
  sobreviveu, critério de aceitação frouxo), com regra de promoção: uma lição só
  vira "guidance" após se repetir em ≥2 features. Anti-overfitting aplicado ao
  próprio processo.
- **Spec também diz o que NÃO fazer**: a seção *Out of Scope* (sem detecção de
  fluxos/setas, sem auth, sem treinar LLM, sem app mobile) e o *sweep* de
  requisitos implícitos (validação de input, estados de falha, idempotência,
  observabilidade...) — a tabela que caça o requisito que ninguém escreveu mas
  todo mundo assume.

Repare como as seções 8 e 12 se conectam: os reviews externos viraram
**features especificadas** com requisitos rastreáveis e testes de regressão —
não uma sequência de hotfixes soltos.

## 13. Checklist de lições transferíveis

Para fechar, o resumo do que este projeto ensina, aplicável ao seu próximo
sistema (com ou sem ML):

**Sobre ML para produto:**

1. Isole o componente probabilístico atrás de uma interface; mantenha o resto
   determinístico, auditável e testável.
2. Use transfer learning — parta de pesos pré-treinados; treinar do zero quase
   nunca se justifica.
3. Métrica agregada boa (mAP 0.83) não significa output bom. Revise o resultado
   real, de preferência com olhos externos.
4. Seja honesto sobre incerteza: exponha confiança, cobertura e o que não foi
   classificado. Nunca invente conteúdo para parecer completo.
5. Espere domain shift: o modelo degrada fora da distribuição de treino; tenha
   defesas em runtime (dedupe, fallbacks) e um plano de retreino.
6. Trate pesos como artefato promovível: corrida parcial não vira release;
   smoke test barato antes do treino caro.

**Sobre arquitetura:**

7. Lógica de domínio como dados versionados (class_map, KB YAML) — revisável em
   PR por quem entende do domínio, sem tocar código.
8. Camadas de indireção com propósito: 87 classes → ~20 famílias → papéis.
9. Interfaces (CLI/UI) como cascas finas sobre um core único.
10. Configuração em camadas (default → arquivo → env), imutável, validada na
    fronteira com erro acionável.

**Sobre qualidade:**

11. Injeção de dependência via Protocol/interface torna o pipeline testável sem
    infraestrutura pesada.
12. Distinga warning (degradado) de error (inválido) — em exit codes e em UX.
13. Mensagens de erro devem ensinar o remédio, não só apontar a falha.
14. Verifique seus testes com mutantes: teste que não mata mutante é enfeite.
15. Bug encontrado em review vira teste de regressão com dados reais.

**Sobre processo e DevEx:**

16. Registre decisões com razão e trade-off no momento em que as toma (ADRs).
17. Escreva o Out of Scope — proteger escopo é decidir por escrito o que não
    entra.
18. Todo pin de dependência merece um comentário com o motivo.
19. Setup reprodutível e rápido é feature (uv, índice torch CPU, extras
    seletivos, Dockerfile com cache consciente).
20. Binários grandes fora do git; download reprodutível por script; modelo
    montado por volume, não embutido na imagem.

---

## Referências dentro do repositório

| Tema | Onde olhar |
| ---- | ---------- |
| Fluxo completo de desenvolvimento | `docs/fluxo-desenvolvimento.md` |
| Decisões de arquitetura (AD-001…AD-008) | `.specs/STATE.md` |
| Specs, designs, tasks e validações por feature | `.specs/features/*/` |
| Lições de verificação | `.specs/LESSONS.md` |
| Treino e promoção de pesos | `src/stride_mvp/detection/train.py` |
| Dedupe espacial (IoU, contenção, centros, union-find) | `src/stride_mvp/detection/dedupe.py` |
| Motor STRIDE (papéis, fallback, coverage) | `src/stride_mvp/stride/engine.py` |
| Knowledge base | `data/kb/threats.yaml` |
| Mapa classe→família | `data/class_map.yaml` |
| Config em camadas + resolver de pesos | `src/stride_mvp/config.py` |
| Batalhas de dependências (comentadas) | `pyproject.toml`, `scripts/install_deps.sh` |
| Relatórios reais gerados | `reports/arch1.md`, `reports/arch2.md` |
