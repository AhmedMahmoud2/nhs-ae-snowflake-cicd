# Snowflake CI/CD – NHS A&E Dummy Data (DEV → UAT → PROD)

Enterprise-style CI/CD demo for Snowflake using:
- **Git branches**: `DEV` → `UAT` → `PROD`
- **GitHub Environments**: `DEV`, `UAT`, `PROD` (secrets + approvals)
- **schemachange** for ordered, versioned SQL migrations
- **PR validation**: SQL lint + destructive-change guardrails

## Branch strategy
- `feature/*` → PR into `DEV`
- PR `DEV` → `UAT` to promote
- PR `UAT` → `PROD` to promote (enable required reviewers on PROD environment)

## One-time Snowflake prerequisites (admin)
Run `admin/00_setup_snowflake_cicd.sql` once to create:
- Databases: `NHS_DEV`, `NHS_UAT`, `NHS_PROD`
- Schemas: `AE` in each database
- Warehouses: `WH_DEV`, `WH_UAT`, `WH_PROD`
- Deploy roles/users with least privilege per environment

Then set RSA public keys for users:
- `CICD_DEV`, `CICD_UAT`, `CICD_PROD`

Migrations assume the target **database + schema already exist**.

## GitHub Environments & secrets (per environment)
Create GitHub Environments: `DEV`, `UAT`, `PROD` and add:

- `SNOWFLAKE_ACCOUNT`
- `SNOWFLAKE_USER`
- `SNOWFLAKE_ROLE`
- `SNOWFLAKE_WAREHOUSE`
- `SNOWFLAKE_DATABASE`
- `SNOWFLAKE_SCHEMA`
- `SNOWFLAKE_PRIVATE_KEY` (required; passwordless)

## Workflows
- **PR Validation (SQL Lint + Guardrails)**: runs on PRs to `DEV/UAT/PROD`
- **Deploy Snowflake Migrations**: runs on push to `DEV/UAT/PROD`

## Migrations order
1. `V001__use_target_context.sql`
2. `V002__create_tables.sql`
3. `V003__generate_dummy_raw_data.sql`
4. `V004__dq_rules_and_clean.sql`
