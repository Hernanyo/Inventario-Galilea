--
-- PostgreSQL database cluster dump
--

-- Started on 2025-09-26 09:02:28

\restrict 60zwrhBNOhnANrmXyB2Hh3TDcc1bJBL8lIq0oMeFBbnmhK5WY3G0PGdg66CbFRd

SET default_transaction_read_only = off;

SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;

--
-- Roles
--

CREATE ROLE inventario_user;
ALTER ROLE inventario_user WITH NOSUPERUSER INHERIT NOCREATEROLE NOCREATEDB LOGIN NOREPLICATION NOBYPASSRLS PASSWORD 'SCRAM-SHA-256$4096:av5sFfOWS8BypINiCMwdTg==$eklcBGU4qpPo8r+KHoPPIyTJ0NB6FajvknvD6VfkDLw=:SUCzCyzQa5Sq9M/scqhPBIdHtPAPbnNYB5nEWDQc4w0=';
CREATE ROLE postgres;
ALTER ROLE postgres WITH SUPERUSER INHERIT CREATEROLE CREATEDB LOGIN REPLICATION BYPASSRLS PASSWORD 'SCRAM-SHA-256$4096:bjSFgA4hKHyT8oJiLw6YDA==$57AYZGSUCIo6/Bx7sXp6r9R5gqt6SjTMCHTT5134SdQ=:5LhKCiyIIYw0Be25nkpcFjLzVqfE8TW2NcNsuoCMgoM=';

--
-- User Configurations
--








\unrestrict 60zwrhBNOhnANrmXyB2Hh3TDcc1bJBL8lIq0oMeFBbnmhK5WY3G0PGdg66CbFRd

-- Completed on 2025-09-26 09:02:28

--
-- PostgreSQL database cluster dump complete
--

