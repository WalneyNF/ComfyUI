# WMK Agent Studio — Chat com IA e geração de imagens (PT-BR)

**Autor:** Walney Moreira Klein — walneyk@hotmail.com

Projeto local em Python + HTML/CSS/JavaScript para conversar com agentes de IA e gerar imagens usando **ComfyUI**. Integra **Ollama** (modelos locais de texto), provedores de API compatíveis com OpenAI (como Groq) e um gerador de imagens baseado em workflows.

> **Situação:** interface e integração API implementadas. O desempenho de geração depende do hardware; a integração do LoRA Pixel Art foi adicionada ao código, mas **a geração final com esse LoRA ainda não foi validada**. Não confunda integração de código com qualidade visual comprovada.

## 1. Recursos e ferramentas

| Ferramenta | Função | Acesso |
|---|---|---|
| WMK Agent Studio | Conversas, agentes, configuração de provedores, aprovação de geração | [Abrir localmente](http://127.0.0.1:8765) |
| Gerador de imagens | Prompts positivo/negativo, resolução, steps, CFG, sampler, scheduler, seed e LoRA | Botão **Gerar imagem** no Studio |
| Grafo de workflow | Inspeção e exportação do JSON de API enviado ao ComfyUI | Botão **Ver grafo** |
| ComfyUI | Motor de geração de imagens por nós | [Abrir localmente](http://127.0.0.1:8188) |
| Ollama | IA local de texto, interpretação do pedido e propostas de imagem | [API local](http://127.0.0.1:11434/api/tags) |
| Histórico de imagens | Exibição de imagens e download PNG no chat | Conversa no Studio |

Os links `127.0.0.1` só funcionam **no computador onde os serviços estão rodando**.

## 2. Documentação completa

- **[Central de manuais — instalação, chat, agentes, ComfyUI, MCP, CPU e diagnóstico](manuais/index.html)**
- **[Academia WMK — curso do básico ao desenvolvimento](manuais/ACADEMIA-WMK.html)**
- **[Modelos, Checkpoints, LoRA e parâmetros de geração — guia detalhado](manuais/GUIA-MODELOS-LORA-COMFYUI.html)**
- **[Manual resumido do usuário](manuais/MANUAL-PTBR.md)**

Para acessar os manuais pelo navegador com o servidor ligado:

- [Central de manuais](http://127.0.0.1:8765/manuais/)
- [Academia WMK](http://127.0.0.1:8765/manuais/ACADEMIA-WMK.html)
- [Guia de modelos e LoRA](http://127.0.0.1:8765/manuais/GUIA-MODELOS-LORA-COMFYUI.html)

## 3. Requisitos e limitações

- Windows, Python 3.13 usado no ambiente de desenvolvimento; o backend utiliza principalmente a biblioteca padrão.
- Ollama instalado e iniciado para conversas com modelos locais, **ou** uma API externa compatível devidamente configurada.
- ComfyUI instalado com ambiente Python e dependências próprias, para geração de imagens.
- Checkpoint SD 1.5 em `ComfyUI/models/checkpoints/`. O modelo usado no desenvolvimento foi `v1-5-pruned-emaonly.safetensors`.
- LoRA opcional em `ComfyUI/models/loras/`. O arquivo usado no desenvolvimento foi `pytorch_lora_weights.safetensors`.
- Na máquina de desenvolvimento, ComfyUI usa **CPU**, com aproximadamente 16 GB de RAM. Resoluções maiores e mais steps podem demorar muito. Sem GPU adequada, não espere geração rápida.

**Atenção à portabilidade:** esta versão contém caminhos absolutos específicos do Windows, especialmente `D:\IA-Local\ComfyUI\output` no servidor. Em outro computador, ajuste esses caminhos e o arquivo `INICIAR-WMK.bat`. O projeto não possui instalador automático.

## 4. Instalação e inicialização no Windows

1. Baixe ou clone o código do repositório para uma pasta de sua escolha.
2. Instale Python e verifique com `python --version`.
3. Instale o [Ollama](https://ollama.com/) e obtenha um modelo de texto, por exemplo `ollama pull qwen2.5-coder:3b`.
4. Instale o [ComfyUI](https://github.com/Comfy-Org/ComfyUI), configure suas dependências conforme o hardware e instale um checkpoint compatível.
5. No ComfyUI, coloque checkpoints em `models/checkpoints/` e LoRAs em `models/loras/`.
6. Inicie cada serviço em um terminal diferente. Os exemplos abaixo correspondem à máquina de desenvolvimento; **ajuste os caminhos no seu computador**.

### Terminal A — Ollama

```powershell
ollama serve
```

Se já estiver ativo, não abra uma segunda instância. Teste em `http://127.0.0.1:11434/api/tags`.

### Terminal B — ComfyUI (CPU, exemplo local)

```powershell
& 'D:\IA-Local\ComfyUI\venv\Scripts\python.exe' 'D:\IA-Local\ComfyUI\main.py' --cpu --listen 127.0.0.1 --port 8188
```

Aguarde a inicialização e acesse `http://127.0.0.1:8188`. Em uma máquina com GPU compatível, use os parâmetros recomendados pela documentação oficial do ComfyUI.

### Terminal C — WMK Agent Studio

```powershell
cd 'D:\Ferramentas\WMK-Agent-Studio'
python server.py
```

Abra `http://127.0.0.1:8765`. No ambiente original, também é possível usar `INICIAR-WMK.bat`.

## 5. Primeira conversa e provedores

Abra o Studio, crie uma conversa, selecione **Ollama Local**, consulte os modelos e escolha um modelo instalado. Em **Agentes**, escolha o agente ou crie um com um prompt de sistema próprio.

Para Groq ou outra API compatível, cadastre o endereço da API, modelo e chave na interface. **Nunca publique chaves, arquivos locais de configuração ou históricos pessoais no GitHub.** A compatibilidade de ferramentas varia entre provedores e modelos.

## 6. Como funciona a geração de imagem

```text
Pedido no chat
  → IA de texto propõe a ferramenta gerar_imagem
  → usuário revisa prompt e parâmetros
  → usuário autoriza
  → servidor monta JSON de API
  → ComfyUI executa nós e salva PNG
  → Studio consulta status e exibe imagem
```

A geração também pode ser iniciada pelo botão **Gerar imagem**. A ponte com ComfyUI usa **API HTTP direta**; não depende de executar um servidor MCP.

**Prompt positivo** descreve o que incluir. **Prompt negativo** descreve o que desencorajar. **Steps** controla iterações; **CFG** influencia aderência ao texto; **sampler/scheduler** definem a estratégia de amostragem; **seed** permite comparar resultados; **LoRA** aplica uma especialização de estilo ao checkpoint.

Configuração inicial para comparar personagens 2D: 384×384, 20–24 steps, CFG 7, DPM++ 2M, Karras, seed fixa e LoRA Pixel Art com força 0,7. **Não é garantia de qualidade.** Confira o guia detalhado para entender cada parâmetro.

### LoRA Pixel Art

O arquivo `pytorch_lora_weights.safetensors` deve estar em `ComfyUI/models/loras/`. O workflow do Studio contém integração com `LoraLoader` e opção para desativá-lo ou ajustar a força. LoRA **não** substitui checkpoint e não produz automaticamente spritesheets animados consistentes. Confira licença e compatibilidade do modelo na página do autor antes de usar comercialmente.

### Onde ficam as imagens?

O ComfyUI salva arquivos PNG em sua pasta `output/`; no ambiente de desenvolvimento: `D:\IA-Local\ComfyUI\output`. O Studio também oferece link de download quando a geração termina.

## 7. Diagnóstico

| Problema | O que verificar |
|---|---|
| Studio não abre | Python, porta 8765, terminal com erro, firewall local |
| Ollama não responde | `ollama serve`, porta 11434, modelo instalado, RAM |
| ComfyUI não responde | Processo em execução, porta 8188, logs, inicialização demorada |
| LoRA não aparece | Pasta `models/loras`, reinício, nome do arquivo, compatibilidade |
| Imagem ruim | Checkpoint, LoRA, prompt, seed, resolução, sampler, parâmetros e expectativas de sprites |
| Erro ao salvar | Permissões da pasta `output`, espaço em disco, status do workflow |
| CPU muito lenta | Reduza resolução, steps e batch; avalie GPU compatível |

Para reproduzir uma imagem, registre modelo, LoRA, força, prompts, resolução, seed, steps, CFG, sampler e scheduler.

## 8. Estrutura do projeto

```text
WMK-Agent-Studio/
├── server.py               # API HTTP, agentes, ComfyUI
├── web/                    # interface HTML, CSS e JavaScript
├── manuais/                # documentação em português
├── data/                   # estado local (não publicar)
└── INICIAR-WMK.bat         # inicializador com caminhos locais
```

## 9. Referências

- [ComfyUI — código e documentação](https://github.com/Comfy-Org/ComfyUI)
- [Ollama](https://ollama.com/)
- [Hugging Face — modelos](https://huggingface.co/models)
- [Civitai — modelos](https://civitai.com/models)

**Créditos:** Walney Moreira Klein — walneyk@hotmail.com

> Documentação destinada a estudo e colaboração. Não publique arquivos de pesos de terceiros sem verificar suas licenças, nem dados pessoais, chaves de API ou arquivos de estado local.
