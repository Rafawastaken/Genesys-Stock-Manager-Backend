# Erros encontrados

- Produtos que nao tem stock = nao existe melhor oferta. Atualmente quando produto nao tem stock estamos a calcular melhor oferta.
  - Fornecedor A - 0 unidades - 2€
  - Fornecedor B - 0 unidades - 3€
  - Nao existe melhor oferta porque esta esgotado em ambos

- A melhor oferta deve ser baseada tambem com stock
  - Fornecedor A - 2 unidades - 5€
  - Fornecedor B - 0 unidades - 2€
  - Melhor Oferta: Fornecedor A
