Lista de tarefas adicionadas, ideias e funcionalidades a serem adicionadas (Front e Back)

#### Tecnologia usada

**Frontend**

- React com Vite e Typescript
- Tanstack - https://tanstack.com/
- Zod Forms - https://zod.dev/
- Shadcn - https://ui.shadcn.com/
- React Hook Form - https://react-hook-form.com/

**Backend**

- Fastapi
- Pydantic v2
- Redis
- Postgresql

---

## Modulo Prestashop

Modulo prestashop para unificar e estender a comunicação entre o Gensys e o Prestashop - com modulo também facilita a
portablidade entre várias versões de prestashop.

## Prestashop

- [ ] Endpoint para login
- [ ] Endpoint para exportar categorias
- [ ] Endpoint para exportar produtos
- [ ] Endpoint para atualizar produtos (preço e quantidade)
- [ ] Endpoint/Cron para associar produtos com UPC = 0 para serem controlados com Genesys

## Infraestrutura

- [x] Logs por pedido
- [ ] JWT Auth (access/refresh, claims: sub, role, exp)
- [x] Health check `/health`
- [x] Configurado redis VPS contabo

## Autenticação

- [ ] Autenticação com credencias de Prestashop
- [ ] Autenticação OAuth já implementada por completo - https://oauth.net/2/

## Integrar fornecedor

- [ ] Meta básico (nome, imagem, contacto)
- [ ] Configurar ligação feed
  - [ ] Tipo de Feed
    - [ ] CSV
    - [ ] JSON
    - [ ] Limitador
  - [ ] Tipo de Ligação
    - [ ] FTP
    - [ ] SFTP
    - [ ] HTTP
  - [ ] Autenticação padrão
    - [ ] Sem autenticação
    - [ ] Basic
    - [ ] Bearer
    - [ ] Api Key
    - [ ] OAuth
  - [ ] Outras configurações
    - [ ] Params
    - [ ] Headers
    - [ ] Estado
    - [ ] Metodo
    - [ ] Payload
  - [ ] Realizar teste de ligação
- [ ] Mapeamento de campos
  - [ ] Campo de base de dados x Campo do feed do fornecedor
  - [ ] Regras por campo
    - [ ] Trim
    - [ ] Lowercase
    - [ ] Converter tipo
    - [ ] Mapeamento de campo
  - [ ] Campos obrigatórios - Levanta erro em caso algum campo obrigatório não seja definido/encontrado no feed do
        fornecedor
  - [ ] Regras condicionais (Condição) > Set
    - [ ] Condições suportadas (>, =, <, <=, >=, Regex, Contém, Começa por, Termina em, Em lista)
  - [ ] Filtrar linhas
    - [ ] Avança linha caso campo esteja em falta
  - [ ] Editor em Json

## Listagem de Produtos Fornecedor

- [ ] Listagem com paginação de todos os produtos por fornecedor
- [ ] Adicionar filtros
  - [ ] Marca
  - [ ] Categoria
  - [ ] Específicos (Atualização, última aparição, etc...)
  - [ ] Ordem Asc e Desc
  - [ ] Número de resultados por paginas
- [ ] Ver produtos já importados para o prestashop
- [ ] Filtrar por categorias de produtos
- [ ] Filtrar por marcas de produtos
- [ ] Comparar preços com KuantoKusta
- [ ] Ver fornecedores de cada produto
- [ ] Preço praticado de cada produto por fornecedor
- [ ] Stock de cada produto por fornecedor
- [ ] Marcar visualmente fornecedores com stock
- [ ] Marcar visualmente fornecedor com o preço mais baixo
- [ ] Conectar pesquisa de navbar com catalogo

## Lista de Categorias

- [ ] Categorias de Prestashop
- [ ] Categorias de Fornecedor

## Lista de Marcas

- [ ] Marcas de Prestashop
- [ ] Marcas de Fornecedor

## Página de Produto

- [ ] Ver dados de produto
- [ ] Métricas de produto
  - [ ] Movimentos de stock
  - [ ] Movimentos de preço
- [ ] Editar dados
  - [ ] Alterar imagem
- [ ] Importar artigo prestashop
  - [ ] Adicionar e editar dados
  - [ ] Fazer pedido ao n8n para completar a informação e etiquetas do artigo
  - [ ] Selecionar categorias de prestashop
  - [ ] Selecionar margem de produto (fallback para margem do fornecedor)

## Encomendas

- [ ] ...

## Sage

- [ ] Notas de encomenda

## Encomendas Prestashop

- [ ] ...

## Pagamentos

- [ ] ...

## Encomendas fornecedor

- [ ] ...

## Agendamentos

- [ ] Tarefa para sincronização com e sem jitter
- [ ] Push de atualização por redis-stream
- [ ] Tarefa para pesquisar produtos com UPC = 0 para serem controlados

## Bugs Encontrados

- [ ] Avançar na página devia dar scroll para cima
- [ ] Melhorar filtros de pesquisa

## Melhorias

- [ ] Design de pesquisa de produtos - filtros

## Ideias

#### Comparador de Preços

- Retornar também o gráfico de preços do kuantokusta - depende se conseguir encontrar
- Verificar valor de venda mínimo possível

### Notas

#### Updates de Produtos

Como funciona o update de produtos para ecommerce

1. Varremos todos os fornecedores
2. Pesquisamos quais dos produtos estão conectados ao Genesys (ecommerce_id != 0)
3. Analisamos a melhor oferta:
   - Produto com menor preço e com stock e comunicado
   - Ambos os fornecedores esgotados - comunicamos o melhor preço
4. Update e feito em 2 partes: 5. Descarregamos todos os fornecedores e atualizamos dados 6. Descrepancias sao carregadas para a nossa stream do redis 7. Consumidor de redis que atualiza 50 em 50 produtos de uma vez

#### Importar Produtos

Criar Wizzard de importação por passos:

1. Informação meta de produto (nome, imagem, categoria, marca) - dados pré-prenchidos 2. Colocamos a hipotse de gerar descrição com o n8n - ops.kontrolsat.com 3. Hipotse de alterar e editar dados
2. Mostramos categorias disponiveis do ecommerce e permitimos que sejam selecionadas, principal e subcategorias
3. Preço de venda com margem pré-selecionada
4. Importar

## Workers

1. Consumidor de feeds de fornecedores, responsavel por 2. Descarregar ficheiros 3. Aplicar o mapeamento 4. Comparar e escolher melhor ofertas 5. Adicionar a fila de redis

2. Consumidor de redis, responsavel por 3. Consumir a fila do redis 4. Comunicar para o ecommerce

3. Analisador de produtos que passaram para dropshipping - TBD
4. Alterador de margens de produtos - TBD
