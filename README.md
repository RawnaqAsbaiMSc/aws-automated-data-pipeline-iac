# Serverless Data Pipeline (Lambda + S3 + Layers)

This repository contains a scaffold for a modular, serverless data pipeline implemented with AWS Lambda, S3, Lambda Layers, and Terraform for infrastructure as code. The design focuses on database ingestion via a dedicated ingestion Lambda that uses a Lambda Layer for DB drivers. The pipeline chains three stages via S3 events: raw -> processed -> analytics.

This scaffold is tuned for development inside GitHub Codespaces with Copilot assistance.

## Overview

- Source: Relational or NoSQL database (RDS, Aurora, DynamoDB, etc.)
- Pipeline stages:
	1. Ingestion Lambda: extracts data from the DB and writes to the `raw-data` bucket.
	2. Processing Lambda: transforms data from `raw-data` and writes to `processed-data`.
	3. Analytics Lambda: aggregates/analyzes `processed-data` and writes to `analytics-data`.
- Each Lambda should use a dedicated Lambda Layer for dependencies (DB drivers, pandas, numpy, etc.)
- Terraform is used to provision S3 buckets, IAM roles, Lambdas, and Layers. Code and layers are packaged from Codespaces and deployed via your preferred CI/CD.

## What I scaffolded

- `terraform/` - placeholder Terraform configuration and module skeletons.
- `src/ingestion_lambda/` - a production-ready Python Lambda handler template for ingestion and a `requirements.txt` for the layer.
- `scripts/` - convenience scripts to package a Lambda layer and the function deployment zip.
- `.gitignore` - common ignores for Python, Terraform, and zipped artifacts.

## Assumptions & Notes

- The ingestion Lambda expects DB connection info via environment variables (DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD). In production, use Secrets Manager or Parameter Store, not plain env vars.
- Some DB drivers (e.g., `psycopg2`) require platform-specific binary wheels; building a working Lambda layer typically requires using Amazon Linux (or a matching manylinux wheel) — the `scripts/package_layer.sh` provided installs into a `python/` folder suitable for zipping into a Lambda Layer from Codespaces but you may need to build layers in an Amazon Linux environment or use prebuilt layers.
- The Terraform scaffold is intentionally minimal and modular: it provides example bucket definitions and module placeholders so you can extend per environment.

## Quickstart (Codespaces + Copilot)

1. Open this repository in GitHub Codespaces (recommended image: with Python, AWS CLI, Terraform).
2. Edit `src/ingestion_lambda/handler.py` to implement your DB query and business logic (Copilot can help).
3. Build a layer and function package locally in Codespaces:

	 # From repo root
	 ./scripts/package_layer.sh src/ingestion_lambda/requirements.txt build/layer
	 ./scripts/package_lambda.sh src/ingestion_lambda build/function

4. Upload the layer and function deployment package to S3 or deploy via Terraform module (examples in `terraform/`).
5. Apply Terraform to provision buckets, roles, and Lambda resources. Use remote state for team environments.

## Next steps you can ask me to do

- Scaffold Terraform module implementations for Lambdas, roles, and S3 event wiring.
- Generate the Processing and Analytics Lambda handler templates.
- Add a GitHub Actions workflow to build and deploy packages and apply Terraform.

## Local testing with Chinook

You can run the ingestion handler locally against the Chinook sample SQLite database for quick functional tests.

1. Download the Chinook DB (saves to `data/chinook.db`):

```bash
./scripts/get_chinook.sh
```

2. Run the local ingestion runner (invokes the same handler code but reads the SQLite DB):

```bash
python src/ingestion_lambda/local_run.py
```

3. Run the basic pytest that downloads Chinook if needed and runs the local runner:

```bash
pip install pytest
pytest -q
```

Notes:
- The handler supports `DB_TYPE=sqlite` and `DB_PATH` for local testing. For production use, continue to use Postgres/RDS and secure credentials with Secrets Manager.
- Local run does not upload to S3 (set `RAW_BUCKET` to a real bucket and provide AWS credentials to test upload behavior).

---

If you'd like, I can now: (A) fully scaffold the Terraform modules and wire the S3 event triggers, (B) generate the Processing and Analytics Lambda handlers, or (C) add a CI workflow — tell me which and I'll continue.
