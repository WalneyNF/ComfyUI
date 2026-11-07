# WMK Agent Studio — Manual do usuário (v1.0)

**Créditos:** Walney Moreira Klein — walneyk@hotmail.com

## O que é
Central de conversas com múltiplos provedores de modelos de linguagem. Interface hacker em português, agentes com prompts de sistema, gerenciamento de modelos, histórico local e exportação JSON.

## Como iniciar
1. Inicie o Ollama: `D:\Ollama\ollama.exe serve` (caso não esteja ativo).
2. Execute `INICIAR-WMK.bat` na pasta do projeto ou `python server.py`.
3. Abra `http://127.0.0.1:8765`.
4. Clique em **Nova conversa**, selecione **Ollama Local**, clique no botão ↻ e escolha `qwen2.5-coder:3b`.
5. Digite uma pergunta e pressione Enter; Shift+Enter quebra a linha.

## Provedores
- **Ollama**: endereço `http://127.0.0.1:11434`, sem chave, modelos locais. Pode consumir bastante RAM e CPU.
- **Groq**: URL `https://api.groq.com/openai/v1`, requer chave pessoal. Modelos variam conforme conta e disponibilidade. Não coloque a chave no prompt.
- **OpenAI / APIs compatíveis**: escolha o tipo OpenAI compatível, informe URL base, modelo e chave quando necessária. Nem toda API implementa exatamente o mesmo contrato.
- A lista de modelos é obtida da API do provedor ao clicar ↻.

## Agentes
Na aba **Agentes**, clique em **Novo agente** ou **Editar**. Defina nome, especialidade e prompt de sistema. Escolha o agente no topo da conversa. O histórico permanece na conversa ao trocar de agente.

## Parâmetros
A temperatura controla a variabilidade das respostas; valores menores tendem a ser mais consistentes. Os valores disponíveis são de 0 a 2, mas alguns provedores aceitam intervalos menores.

## Histórico e privacidade
O arquivo `data/studio.json` guarda agentes, conversas, prompts e **chaves em texto simples**. Não publique nem envie esse arquivo a terceiros. Faça backup com segurança. O servidor escuta apenas em `127.0.0.1` e não tem autenticação de usuário; não exponha na rede pública. Provedores remotos recebem as mensagens enviadas a eles.

## Limitações desta versão
- Respostas são exibidas após conclusão da requisição, sem streaming de tokens.
- Não há execução de ferramentas MCP nesta versão; a conexão Ollama/Groq é de chat de texto.
- Não há anexos, geração de imagens ou orquestração de agentes nesta versão.
- A chave de API é armazenada no servidor local, mas não está criptografada em disco.
- Não há atualização automática nem controle de permissões por usuário.

## Arquitetura
`web/index.html` — interface; `web/style.css` — tema; `web/app.js` — aplicação; `server.py` — API HTTP e comunicação com provedores; `data/studio.json` — persistência. Sem dependências Python externas.

## Próximas versões
Integração MCP real com ComfyUI, streaming, agentes com ferramentas e permissões, armazenamento seguro de credenciais, SQLite, gestão de tarefas e logs.

## Nova função: geração de imagem (v1.1)
No chat clique em Gerar imagem, descreva a cena, selecione 256x256 e 8 steps, confirme e aguarde. O backend envia um workflow SD 1.5 à API do ComfyUI, consulta o histórico e mostra a imagem quando concluída. O modelo de linguagem não invoca MCP automaticamente nesta versão. Teste de envio de workflow confirmado; geração final em CPU ainda em validação.


## Habilidade dos agentes (v1.2)
O chat agora oferece a ferramenta gerar_imagem via tool calling para Ollama e Groq. O modelo pode propor prompt, tamanho e steps; a proposta aparece no histórico. Clique Autorizar geração ou Rejeitar. Somente depois da autorização o backend envia o workflow pela API direta do ComfyUI. Não há execução MCP nesta função. Alguns modelos locais podem não chamar ferramentas corretamente. O teste completo de tool calling está em andamento.


## Visualização de grafo antes de gerar
No cartão de ferramenta do agente, clique em Ver grafo / plano. A janela mostra os nós e conexões do pipeline SD 1.5, além de permitir exportar workflow no formato API JSON. O grafo é uma prévia simplificada, não o editor nativo do ComfyUI. O JSON exportado utiliza seed fixa 42; a geração real utiliza seed aleatória.

