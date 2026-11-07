# WMK Agent Studio — versão 1.1: estabilização e diagnóstico

**Autor:** Walney Moreira Klein — walneyk@hotmail.com

## Escopo implementado e verificado
- `GET /api/health`: verifica Ollama em `/api/tags` e ComfyUI em `/system_stats`, com timeout de 2 segundos por serviço. `ok: true` significa que **o servidor WMK está ativo**, não que todos os serviços externos estão disponíveis.
- Logs estruturados em JSON para requisições HTTP, falhas tratadas, submissão e enfileiramento de imagens. O sistema não registra prompts nem chaves nesses eventos.
- Erros internos HTTP 500 retornam mensagem genérica ao navegador, sem vazar detalhes de exceções.
- Testes automatizados com biblioteca padrão `unittest` para LoRA, ausência de LoRA, validação de parâmetros, seed, submissão simulada, indisponibilidade parcial e timeout.

## Executar os testes
Abra PowerShell na pasta `examples/wmk-agent-studio`:

```powershell
python -m unittest discover -s tests -v
python -m py_compile server.py
node --check web/app.js
```

## Diagnóstico da API
Com o servidor ligado:

```powershell
Invoke-RestMethod http://127.0.0.1:8765/api/health | ConvertTo-Json -Depth 5
```

O objeto `services` informa `online` ou `offline`, latência em milissegundos ou tipo de erro. O endpoint não deve ser exposto à internet sem autenticação.

## Evidências de validação — 07/11/2026
- 7 testes unitários e de integração simulada: **OK**.
- Sintaxe Python e JavaScript: **OK**.
- API ComfyUI `/system_stats`: **online**.
- API Ollama `/api/tags`: **online**.
- ComfyUI `/object_info/LoraLoader`: reconheceu `pytorch_lora_weights.safetensors`.
- **Não verificado:** renderização final de PNG com LoRA, fila persistente, cancelamento de job, desempenho e compatibilidade visual do modelo.

## Pendências da versão 1.1
1. Executar geração completa com LoRA, salvar PNG e verificar histórico.
2. Implementar fila WMK com limites de concorrência e cancelamento seguro.
3. Testes de integração HTTP com processo WMK isolado e fixtures.
4. Testes de falhas no meio de uma geração e recuperação de jobs.
5. Revisar dependências, caminhos absolutos e política de atualização do fork.

**Status:** implementação parcial validada. A v1.1 não deve ser marcada como concluída.
