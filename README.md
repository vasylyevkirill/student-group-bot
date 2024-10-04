# UNIUS
Телеграмм бот для автоматизации менеджмента внутри студенческой группы.

Запуск всего проекта
```bash
docker volume create --name=university-manager-database
docker compose -f docker-compose.dev.yml up
```

Снять дамп БД
```bash
docker exec -i university-manager_dev_db pg_dump -c -U university-manager > "backup-$(date +%d-%m-%Y-%H-%M-%S).sql"
```

Накатить дамп БД
```bash
docker exec -i university-manager_dev_db psql -U university-manager db < <YOUR_BACKUP_FILE_NAME>
```
