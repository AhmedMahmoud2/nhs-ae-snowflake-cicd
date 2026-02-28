-- V001__use_target_context.sql
-- NHS-grade: database + schema are created once by an admin.
-- This migration only sets context.

USE DATABASE IDENTIFIER($SNOWFLAKE_DATABASE);
USE SCHEMA IDENTIFIER($SNOWFLAKE_SCHEMA);
