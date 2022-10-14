migrate:
	docker exec -i ibit_test_db_1 mysql -uuser -ppassword points_db < resourse/initial_migration.sql

test:
	python -m unittest discover

run:
	docker-compose up

