# TODO - Fix Railway 502

- [x] Atualizar `WellReserve/settings.py` para usar `CompressedManifestStaticFilesStorage`.
- [x] Atualizar `app/views/api.py`:
  - [x] `health_check` com verificação de base de dados.
  - [x] resposta JSON com detalhes de estado.
- [x] Atualizar `app/views/dashboard.py`:
  - [x] proteger `home` com try/except.
  - [x] adicionar logging de exceções e fallback seguro.
- [ ] Rever alterações e validar consistência.
