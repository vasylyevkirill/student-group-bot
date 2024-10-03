# Снять дамп БД
```bash
docker exec -i university-manager_dev_db pg_dump -c -U university-manager > "backup-$(date +%d-%m-%Y-%H-%M-%S).sql"
```

# Накатить дамп БД
```bash
docker exec -i university-manager_dev_db psql -U university-manager db < <YOUR_BACKUP_FILE_NAME>
```
