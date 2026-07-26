# Solução de problemas

## `DATABASE_URL` inválida

Copie `.env.example` para `.env` ou exporte uma URL completa. Dentro do Compose,
o host é `db`; fora dele, normalmente é `localhost`.

## API sobe, mas a tabela não existe

Execute `docker-compose exec api alembic upgrade head` antes de chamar os
endpoints de users.

## `docker compose` não existe

Este ambiente foi configurado com o binário legado `docker-compose`. Use
`make compose-up`/`make compose-down` ou instale o plugin Compose v2.

## Falha de porta

Verifique se as portas 5432 ou 8000 já estão ocupadas. O Compose aceita
`DB_PORT=5433 API_PORT=8001 docker-compose up --build -d` sem alterar as portas
internas dos serviços.
