--
-- PostgreSQL database dump
--

\restrict vBSuciq18k7Pd7JJeavS1dmqgXTMumbvXznw8DaRPpbgN5efRq2FeUKEJtWPbyp

-- Dumped from database version 17.6
-- Dumped by pg_dump version 17.6

-- Started on 2025-09-25 15:40:00

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- TOC entry 6 (class 2615 OID 16723)
-- Name: inventario; Type: SCHEMA; Schema: -; Owner: inventario_user
--

CREATE SCHEMA inventario;


ALTER SCHEMA inventario OWNER TO inventario_user;

--
-- TOC entry 5 (class 2615 OID 2200)
-- Name: public; Type: SCHEMA; Schema: -; Owner: inventario_user
--

-- *not* creating schema, since initdb creates it


ALTER SCHEMA public OWNER TO inventario_user;

--
-- TOC entry 276 (class 1255 OID 17116)
-- Name: actualizar_fecha_modificacion(); Type: FUNCTION; Schema: inventario; Owner: inventario_user
--

CREATE FUNCTION inventario.actualizar_fecha_modificacion() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.fecha_modificacion = NOW();
    RETURN NEW;
END;
$$;


ALTER FUNCTION inventario.actualizar_fecha_modificacion() OWNER TO inventario_user;

--
-- TOC entry 278 (class 1255 OID 17316)
-- Name: fill_factura_id_empresa(); Type: FUNCTION; Schema: inventario; Owner: inventario_user
--

CREATE FUNCTION inventario.fill_factura_id_empresa() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
  IF NEW.id_empresa IS NULL THEN
    -- Si existe al menos un detalle con equipo, hereda.
    SELECT MIN(e.id_empresa)
    INTO NEW.id_empresa
    FROM inventario.detalle_factura df
    JOIN inventario.equipo e ON e.id_equipo = df.id_equipo
    WHERE df.id_factura = NEW.id_factura;

    -- si sigue NULL, puedes dejarlo nulo o forzar error (seg£n tu pol¡tica)
  END IF;
  RETURN NEW;
END $$;


ALTER FUNCTION inventario.fill_factura_id_empresa() OWNER TO inventario_user;

--
-- TOC entry 277 (class 1255 OID 17305)
-- Name: fill_hist_mant_id_empresa(); Type: FUNCTION; Schema: inventario; Owner: inventario_user
--

CREATE FUNCTION inventario.fill_hist_mant_id_empresa() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
  IF NEW.id_empresa IS NULL THEN
    -- 1) Por mantencion -> equipo
    SELECT eq.id_empresa
      INTO NEW.id_empresa
    FROM inventario.mantencion m
    JOIN inventario.equipo eq
      ON eq.id_equipo = m.id_equipo
    WHERE m.id_mantencion = NEW.id_mantencion
    LIMIT 1;

    -- 2) Si no, por responsable/solicitante
    IF NEW.id_empresa IS NULL THEN
      SELECT COALESCE(er.id_empresa, es.id_empresa)
        INTO NEW.id_empresa
      FROM inventario.mantencion m
      LEFT JOIN inventario.empleado er
        ON er.id_empleado = COALESCE(m.responsable_id, m.id_empleado_responsable)
      LEFT JOIN inventario.empleado es
        ON es.id_empleado = m.id_empleado_solicitante
      WHERE m.id_mantencion = NEW.id_mantencion
      LIMIT 1;
    END IF;
  END IF;

  RETURN NEW;
END
$$;


ALTER FUNCTION inventario.fill_hist_mant_id_empresa() OWNER TO inventario_user;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- TOC entry 275 (class 1259 OID 17255)
-- Name: agregacion_atributos_por_equipo; Type: TABLE; Schema: inventario; Owner: inventario_user
--

CREATE TABLE inventario.agregacion_atributos_por_equipo (
    id integer NOT NULL,
    id_equipo integer NOT NULL,
    id_atributo_equipo integer NOT NULL,
    valor character varying(250),
    id_empresa integer
);


ALTER TABLE inventario.agregacion_atributos_por_equipo OWNER TO inventario_user;

--
-- TOC entry 274 (class 1259 OID 17254)
-- Name: agregacion_atributos_por_equipo_id_seq; Type: SEQUENCE; Schema: inventario; Owner: inventario_user
--

CREATE SEQUENCE inventario.agregacion_atributos_por_equipo_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE inventario.agregacion_atributos_por_equipo_id_seq OWNER TO inventario_user;

--
-- TOC entry 5320 (class 0 OID 0)
-- Dependencies: 274
-- Name: agregacion_atributos_por_equipo_id_seq; Type: SEQUENCE OWNED BY; Schema: inventario; Owner: inventario_user
--

ALTER SEQUENCE inventario.agregacion_atributos_por_equipo_id_seq OWNED BY inventario.agregacion_atributos_por_equipo.id;


--
-- TOC entry 218 (class 1259 OID 16724)
-- Name: atributos_equipo; Type: TABLE; Schema: inventario; Owner: inventario_user
--

CREATE TABLE inventario.atributos_equipo (
    id_atributo_equipo integer NOT NULL,
    id_tipo_equipo integer NOT NULL,
    atributo character varying(100) NOT NULL,
    valor character varying(250),
    id_empresa integer,
    id_subtipo_equipo integer,
    subtipo_nombre character varying(100)
);


ALTER TABLE inventario.atributos_equipo OWNER TO inventario_user;

--
-- TOC entry 219 (class 1259 OID 16727)
-- Name: atributos_equipo_id_atributo_equipo_seq; Type: SEQUENCE; Schema: inventario; Owner: inventario_user
--

ALTER TABLE inventario.atributos_equipo ALTER COLUMN id_atributo_equipo ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME inventario.atributos_equipo_id_atributo_equipo_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- TOC entry 220 (class 1259 OID 16728)
-- Name: departamento; Type: TABLE; Schema: inventario; Owner: inventario_user
--

CREATE TABLE inventario.departamento (
    id_departamento integer NOT NULL,
    nombre_departamento character varying(150) NOT NULL,
    id_empresa integer NOT NULL
);


ALTER TABLE inventario.departamento OWNER TO inventario_user;

--
-- TOC entry 221 (class 1259 OID 16731)
-- Name: departamento_id_departamento_seq; Type: SEQUENCE; Schema: inventario; Owner: inventario_user
--

ALTER TABLE inventario.departamento ALTER COLUMN id_departamento ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME inventario.departamento_id_departamento_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- TOC entry 222 (class 1259 OID 16732)
-- Name: detalle_factura; Type: TABLE; Schema: inventario; Owner: inventario_user
--

CREATE TABLE inventario.detalle_factura (
    id_detalle_factura integer NOT NULL,
    id_factura integer NOT NULL,
    id_equipo integer,
    nombre_equipo character varying(150),
    cantidad integer DEFAULT 1 NOT NULL,
    valor_unitario integer DEFAULT 0 NOT NULL,
    valor_neto integer,
    iva integer,
    valor_total integer,
    id_empresa integer,
    CONSTRAINT detalle_factura_cantidad_check CHECK ((cantidad > 0)),
    CONSTRAINT detalle_factura_valor_unitario_check CHECK ((valor_unitario >= 0))
);


ALTER TABLE inventario.detalle_factura OWNER TO inventario_user;

--
-- TOC entry 223 (class 1259 OID 16739)
-- Name: detalle_factura_id_detalle_factura_seq; Type: SEQUENCE; Schema: inventario; Owner: inventario_user
--

ALTER TABLE inventario.detalle_factura ALTER COLUMN id_detalle_factura ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME inventario.detalle_factura_id_detalle_factura_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- TOC entry 224 (class 1259 OID 16740)
-- Name: empleado; Type: TABLE; Schema: inventario; Owner: inventario_user
--

CREATE TABLE inventario.empleado (
    id_empleado integer NOT NULL,
    rut character varying(20) NOT NULL,
    nombre character varying(100) NOT NULL,
    apellido_paterno character varying(100) NOT NULL,
    apellido_materno character varying(100),
    activo boolean DEFAULT true NOT NULL,
    cargo character varying(100),
    telefono character varying(20),
    id_empresa integer NOT NULL,
    id_departamento integer NOT NULL,
    rol character varying(50),
    user_id integer,
    correo character varying(255)
);


ALTER TABLE inventario.empleado OWNER TO inventario_user;

--
-- TOC entry 225 (class 1259 OID 16746)
-- Name: empleado_id_empleado_seq; Type: SEQUENCE; Schema: inventario; Owner: inventario_user
--

ALTER TABLE inventario.empleado ALTER COLUMN id_empleado ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME inventario.empleado_id_empleado_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- TOC entry 226 (class 1259 OID 16747)
-- Name: empresa; Type: TABLE; Schema: inventario; Owner: inventario_user
--

CREATE TABLE inventario.empresa (
    id_empresa integer NOT NULL,
    rut_empresa character varying(20) NOT NULL,
    nombre_empresa character varying(200) NOT NULL,
    direccion_empresa character varying(250),
    giro character varying(100)
);


ALTER TABLE inventario.empresa OWNER TO inventario_user;

--
-- TOC entry 227 (class 1259 OID 16752)
-- Name: empresa_id_empresa_seq; Type: SEQUENCE; Schema: inventario; Owner: inventario_user
--

ALTER TABLE inventario.empresa ALTER COLUMN id_empresa ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME inventario.empresa_id_empresa_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- TOC entry 228 (class 1259 OID 16753)
-- Name: equipo; Type: TABLE; Schema: inventario; Owner: inventario_user
--

CREATE TABLE inventario.equipo (
    id_equipo integer NOT NULL,
    nombre_equipo character varying(150) NOT NULL,
    id_marca integer NOT NULL,
    id_tipo_equipo integer NOT NULL,
    id_estado_equipo integer,
    id_empleado integer,
    id_proveedor integer,
    etiqueta character varying(150),
    qr_code character varying(1000),
    fecha_creacion timestamp without time zone DEFAULT now(),
    fecha_modificacion timestamp without time zone DEFAULT now(),
    id_empresa integer,
    departamento_id integer,
    observaciones text,
    activo_critico boolean DEFAULT false,
    confidencialidad numeric(5,2),
    integridad numeric(5,2),
    disponibilidad numeric(5,2),
    CONSTRAINT equipo_bodega_sin_responsable CHECK ((NOT ((id_estado_equipo = 1) AND (id_empleado IS NOT NULL))))
);


ALTER TABLE inventario.equipo OWNER TO inventario_user;

--
-- TOC entry 229 (class 1259 OID 16756)
-- Name: equipo_id_equipo_seq; Type: SEQUENCE; Schema: inventario; Owner: inventario_user
--

ALTER TABLE inventario.equipo ALTER COLUMN id_equipo ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME inventario.equipo_id_equipo_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- TOC entry 230 (class 1259 OID 16757)
-- Name: estado_equipo; Type: TABLE; Schema: inventario; Owner: inventario_user
--

CREATE TABLE inventario.estado_equipo (
    id_estado_equipo integer NOT NULL,
    descripcion character varying(100) NOT NULL,
    id_empresa integer
);


ALTER TABLE inventario.estado_equipo OWNER TO inventario_user;

--
-- TOC entry 231 (class 1259 OID 16760)
-- Name: estado_equipo_id_estado_equipo_seq; Type: SEQUENCE; Schema: inventario; Owner: inventario_user
--

ALTER TABLE inventario.estado_equipo ALTER COLUMN id_estado_equipo ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME inventario.estado_equipo_id_estado_equipo_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- TOC entry 232 (class 1259 OID 16761)
-- Name: estado_mantencion; Type: TABLE; Schema: inventario; Owner: inventario_user
--

CREATE TABLE inventario.estado_mantencion (
    id_estado_mantencion integer NOT NULL,
    tipo character varying(50) NOT NULL,
    id_empresa integer
);


ALTER TABLE inventario.estado_mantencion OWNER TO inventario_user;

--
-- TOC entry 233 (class 1259 OID 16764)
-- Name: estado_mantencion_id_estado_mantencion_seq; Type: SEQUENCE; Schema: inventario; Owner: inventario_user
--

ALTER TABLE inventario.estado_mantencion ALTER COLUMN id_estado_mantencion ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME inventario.estado_mantencion_id_estado_mantencion_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- TOC entry 234 (class 1259 OID 16765)
-- Name: factura; Type: TABLE; Schema: inventario; Owner: inventario_user
--

CREATE TABLE inventario.factura (
    id_factura integer NOT NULL,
    id_proveedor integer,
    fecha_emision date DEFAULT CURRENT_DATE,
    id_empresa integer
);


ALTER TABLE inventario.factura OWNER TO inventario_user;

--
-- TOC entry 235 (class 1259 OID 16769)
-- Name: factura_id_factura_seq; Type: SEQUENCE; Schema: inventario; Owner: inventario_user
--

ALTER TABLE inventario.factura ALTER COLUMN id_factura ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME inventario.factura_id_factura_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- TOC entry 264 (class 1259 OID 17062)
-- Name: historial_equipos; Type: TABLE; Schema: inventario; Owner: inventario_user
--

CREATE TABLE inventario.historial_equipos (
    id integer NOT NULL,
    equipo_id integer,
    etiqueta character varying(150),
    nombre_equipo character varying(150),
    modelo character varying(100),
    tipo_equipo_id integer,
    accion character varying(50),
    usuario_id integer,
    fecha timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    id_empresa integer,
    departamento_id integer,
    ubicacion character varying(200),
    estado_anterior_id integer,
    estado_nuevo_id integer,
    responsable_actual_id integer,
    comentario text,
    responsable_anterior_id integer
);


ALTER TABLE inventario.historial_equipos OWNER TO inventario_user;

--
-- TOC entry 263 (class 1259 OID 17061)
-- Name: historial_equipos_id_seq; Type: SEQUENCE; Schema: inventario; Owner: inventario_user
--

CREATE SEQUENCE inventario.historial_equipos_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE inventario.historial_equipos_id_seq OWNER TO inventario_user;

--
-- TOC entry 5321 (class 0 OID 0)
-- Dependencies: 263
-- Name: historial_equipos_id_seq; Type: SEQUENCE OWNED BY; Schema: inventario; Owner: inventario_user
--

ALTER SEQUENCE inventario.historial_equipos_id_seq OWNED BY inventario.historial_equipos.id;


--
-- TOC entry 270 (class 1259 OID 17190)
-- Name: historial_mantenciones; Type: TABLE; Schema: inventario; Owner: inventario_user
--

CREATE TABLE inventario.historial_mantenciones (
    id_historial integer NOT NULL,
    id_mantencion integer NOT NULL,
    fecha_evento timestamp without time zone DEFAULT now() NOT NULL,
    accion character varying(30) NOT NULL,
    usuario_app integer,
    detalle text,
    old_values jsonb,
    new_values jsonb,
    id_empresa integer
);


ALTER TABLE inventario.historial_mantenciones OWNER TO inventario_user;

--
-- TOC entry 269 (class 1259 OID 17189)
-- Name: historial_mantenciones_id_historial_seq; Type: SEQUENCE; Schema: inventario; Owner: inventario_user
--

CREATE SEQUENCE inventario.historial_mantenciones_id_historial_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE inventario.historial_mantenciones_id_historial_seq OWNER TO inventario_user;

--
-- TOC entry 5322 (class 0 OID 0)
-- Dependencies: 269
-- Name: historial_mantenciones_id_historial_seq; Type: SEQUENCE OWNED BY; Schema: inventario; Owner: inventario_user
--

ALTER SEQUENCE inventario.historial_mantenciones_id_historial_seq OWNED BY inventario.historial_mantenciones.id_historial;


--
-- TOC entry 273 (class 1259 OID 17224)
-- Name: historial_mantenciones_log; Type: TABLE; Schema: inventario; Owner: inventario_user
--

CREATE TABLE inventario.historial_mantenciones_log (
    id_evento bigint NOT NULL,
    id_mantencion integer NOT NULL,
    fecha_evento timestamp without time zone DEFAULT now() NOT NULL,
    accion character varying(30) NOT NULL,
    detalle text DEFAULT ''::text NOT NULL,
    usuario_app_username character varying(150),
    id_equipo integer,
    etiqueta character varying(150),
    equipo_nombre character varying(150),
    tipo_mantencion character varying(50),
    prioridad character varying(50),
    estado_actual character varying(50),
    responsable_nombre text,
    solicitante_nombre text,
    descripcion text,
    id_empresa integer
);


ALTER TABLE inventario.historial_mantenciones_log OWNER TO inventario_user;

--
-- TOC entry 272 (class 1259 OID 17223)
-- Name: historial_mantenciones_log_id_evento_seq; Type: SEQUENCE; Schema: inventario; Owner: inventario_user
--

CREATE SEQUENCE inventario.historial_mantenciones_log_id_evento_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE inventario.historial_mantenciones_log_id_evento_seq OWNER TO inventario_user;

--
-- TOC entry 5323 (class 0 OID 0)
-- Dependencies: 272
-- Name: historial_mantenciones_log_id_evento_seq; Type: SEQUENCE OWNED BY; Schema: inventario; Owner: inventario_user
--

ALTER SEQUENCE inventario.historial_mantenciones_log_id_evento_seq OWNED BY inventario.historial_mantenciones_log.id_evento;


--
-- TOC entry 236 (class 1259 OID 16770)
-- Name: mantencion; Type: TABLE; Schema: inventario; Owner: inventario_user
--

CREATE TABLE inventario.mantencion (
    id_mantencion integer NOT NULL,
    id_equipo integer NOT NULL,
    id_estado_mantencion integer NOT NULL,
    fecha date DEFAULT CURRENT_DATE,
    descripcion text,
    id_tipo_mantencion integer,
    id_prioridad integer,
    fecha_programada date,
    fecha_inicio timestamp without time zone,
    fecha_fin timestamp without time zone,
    id_empleado_responsable integer,
    id_empleado_solicitante integer,
    costo_total numeric(12,2) DEFAULT 0 NOT NULL,
    horas_hombre numeric(6,2) DEFAULT 0 NOT NULL,
    resultado character varying(50),
    observaciones text,
    tiempo_downtime interval,
    responsable_id integer,
    solicitante_user_id integer,
    id_empresa integer,
    CONSTRAINT mantencion_chk_fechas CHECK (((fecha_fin IS NULL) OR (fecha_inicio IS NULL) OR (fecha_fin >= fecha_inicio)))
);


ALTER TABLE inventario.mantencion OWNER TO inventario_user;

--
-- TOC entry 237 (class 1259 OID 16776)
-- Name: mantencion_id_mantencion_seq; Type: SEQUENCE; Schema: inventario; Owner: inventario_user
--

ALTER TABLE inventario.mantencion ALTER COLUMN id_mantencion ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME inventario.mantencion_id_mantencion_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- TOC entry 238 (class 1259 OID 16777)
-- Name: marca; Type: TABLE; Schema: inventario; Owner: inventario_user
--

CREATE TABLE inventario.marca (
    id_marca integer NOT NULL,
    nombre_marca character varying(100) NOT NULL,
    id_empresa integer
);


ALTER TABLE inventario.marca OWNER TO inventario_user;

--
-- TOC entry 239 (class 1259 OID 16780)
-- Name: marca_id_marca_seq; Type: SEQUENCE; Schema: inventario; Owner: inventario_user
--

ALTER TABLE inventario.marca ALTER COLUMN id_marca ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME inventario.marca_id_marca_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- TOC entry 268 (class 1259 OID 17153)
-- Name: prioridad_mantencion; Type: TABLE; Schema: inventario; Owner: inventario_user
--

CREATE TABLE inventario.prioridad_mantencion (
    id_prioridad integer NOT NULL,
    nombre character varying(30) NOT NULL,
    sla_horas integer DEFAULT 0 NOT NULL,
    id_empresa integer
);


ALTER TABLE inventario.prioridad_mantencion OWNER TO inventario_user;

--
-- TOC entry 267 (class 1259 OID 17152)
-- Name: prioridad_mantencion_id_prioridad_seq; Type: SEQUENCE; Schema: inventario; Owner: inventario_user
--

CREATE SEQUENCE inventario.prioridad_mantencion_id_prioridad_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE inventario.prioridad_mantencion_id_prioridad_seq OWNER TO inventario_user;

--
-- TOC entry 5324 (class 0 OID 0)
-- Dependencies: 267
-- Name: prioridad_mantencion_id_prioridad_seq; Type: SEQUENCE OWNED BY; Schema: inventario; Owner: inventario_user
--

ALTER SEQUENCE inventario.prioridad_mantencion_id_prioridad_seq OWNED BY inventario.prioridad_mantencion.id_prioridad;


--
-- TOC entry 240 (class 1259 OID 16781)
-- Name: proveedor; Type: TABLE; Schema: inventario; Owner: inventario_user
--

CREATE TABLE inventario.proveedor (
    id_proveedor integer NOT NULL,
    nombre_proveedor character varying(200) NOT NULL,
    rut_proveedor character varying(20),
    id_empresa integer
);


ALTER TABLE inventario.proveedor OWNER TO inventario_user;

--
-- TOC entry 241 (class 1259 OID 16784)
-- Name: proveedor_id_proveedor_seq; Type: SEQUENCE; Schema: inventario; Owner: inventario_user
--

ALTER TABLE inventario.proveedor ALTER COLUMN id_proveedor ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME inventario.proveedor_id_proveedor_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- TOC entry 242 (class 1259 OID 16785)
-- Name: tipo_equipo; Type: TABLE; Schema: inventario; Owner: inventario_user
--

CREATE TABLE inventario.tipo_equipo (
    id_tipo_equipo integer NOT NULL,
    tipo_equipo character varying(100) NOT NULL,
    id_empresa integer
);


ALTER TABLE inventario.tipo_equipo OWNER TO inventario_user;

--
-- TOC entry 243 (class 1259 OID 16788)
-- Name: tipo_equipo_id_tipo_equipo_seq; Type: SEQUENCE; Schema: inventario; Owner: inventario_user
--

ALTER TABLE inventario.tipo_equipo ALTER COLUMN id_tipo_equipo ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME inventario.tipo_equipo_id_tipo_equipo_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- TOC entry 266 (class 1259 OID 17144)
-- Name: tipo_mantencion; Type: TABLE; Schema: inventario; Owner: inventario_user
--

CREATE TABLE inventario.tipo_mantencion (
    id_tipo_mantencion integer NOT NULL,
    nombre character varying(50) NOT NULL,
    id_empresa integer
);


ALTER TABLE inventario.tipo_mantencion OWNER TO inventario_user;

--
-- TOC entry 265 (class 1259 OID 17143)
-- Name: tipo_mantencion_id_tipo_mantencion_seq; Type: SEQUENCE; Schema: inventario; Owner: inventario_user
--

CREATE SEQUENCE inventario.tipo_mantencion_id_tipo_mantencion_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE inventario.tipo_mantencion_id_tipo_mantencion_seq OWNER TO inventario_user;

--
-- TOC entry 5325 (class 0 OID 0)
-- Dependencies: 265
-- Name: tipo_mantencion_id_tipo_mantencion_seq; Type: SEQUENCE OWNED BY; Schema: inventario; Owner: inventario_user
--

ALTER SEQUENCE inventario.tipo_mantencion_id_tipo_mantencion_seq OWNED BY inventario.tipo_mantencion.id_tipo_mantencion;


--
-- TOC entry 250 (class 1259 OID 16801)
-- Name: auth_user; Type: TABLE; Schema: public; Owner: inventario_user
--

CREATE TABLE public.auth_user (
    id integer NOT NULL,
    password character varying(128) NOT NULL,
    last_login timestamp with time zone,
    is_superuser boolean NOT NULL,
    username character varying(150) NOT NULL,
    first_name character varying(150) NOT NULL,
    last_name character varying(150) NOT NULL,
    email character varying(254) NOT NULL,
    is_staff boolean NOT NULL,
    is_active boolean NOT NULL,
    date_joined timestamp with time zone NOT NULL
);


ALTER TABLE public.auth_user OWNER TO inventario_user;

--
-- TOC entry 271 (class 1259 OID 17217)
-- Name: vw_historial_mantenciones; Type: VIEW; Schema: inventario; Owner: inventario_user
--

CREATE VIEW inventario.vw_historial_mantenciones AS
 SELECT h.id_historial,
    h.id_mantencion,
    h.fecha_evento,
    h.accion,
    COALESCE(h.detalle, ''::text) AS detalle,
    u.username AS usuario_app_username,
    m.id_equipo,
    e.etiqueta,
    e.nombre_equipo AS equipo_nombre,
    m.descripcion,
    tm.nombre AS tipo_mantencion,
    pm.nombre AS prioridad,
    est.tipo AS estado_actual,
    TRIM(BOTH FROM (((((COALESCE(em_resp.nombre, ''::character varying))::text || ' '::text) || (COALESCE(em_resp.apellido_paterno, ''::character varying))::text) || ' '::text) || (COALESCE(em_resp.apellido_materno, ''::character varying))::text)) AS responsable_nombre,
    TRIM(BOTH FROM (((((COALESCE(em_sol.nombre, ''::character varying))::text || ' '::text) || (COALESCE(em_sol.apellido_paterno, ''::character varying))::text) || ' '::text) || (COALESCE(em_sol.apellido_materno, ''::character varying))::text)) AS solicitante_nombre,
    h.old_values,
    h.new_values
   FROM ((((((((inventario.historial_mantenciones h
     JOIN inventario.mantencion m ON ((m.id_mantencion = h.id_mantencion)))
     LEFT JOIN inventario.equipo e ON ((e.id_equipo = m.id_equipo)))
     LEFT JOIN inventario.estado_mantencion est ON ((est.id_estado_mantencion = m.id_estado_mantencion)))
     LEFT JOIN inventario.tipo_mantencion tm ON ((tm.id_tipo_mantencion = m.id_tipo_mantencion)))
     LEFT JOIN inventario.prioridad_mantencion pm ON ((pm.id_prioridad = m.id_prioridad)))
     LEFT JOIN inventario.empleado em_resp ON ((em_resp.id_empleado = m.id_empleado_responsable)))
     LEFT JOIN inventario.empleado em_sol ON ((em_sol.id_empleado = m.id_empleado_solicitante)))
     LEFT JOIN public.auth_user u ON ((u.id = h.usuario_app)));


ALTER VIEW inventario.vw_historial_mantenciones OWNER TO inventario_user;

--
-- TOC entry 244 (class 1259 OID 16789)
-- Name: auth_group; Type: TABLE; Schema: public; Owner: inventario_user
--

CREATE TABLE public.auth_group (
    id integer NOT NULL,
    name character varying(150) NOT NULL
);


ALTER TABLE public.auth_group OWNER TO inventario_user;

--
-- TOC entry 245 (class 1259 OID 16792)
-- Name: auth_group_id_seq; Type: SEQUENCE; Schema: public; Owner: inventario_user
--

ALTER TABLE public.auth_group ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.auth_group_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- TOC entry 246 (class 1259 OID 16793)
-- Name: auth_group_permissions; Type: TABLE; Schema: public; Owner: inventario_user
--

CREATE TABLE public.auth_group_permissions (
    id bigint NOT NULL,
    group_id integer NOT NULL,
    permission_id integer NOT NULL
);


ALTER TABLE public.auth_group_permissions OWNER TO inventario_user;

--
-- TOC entry 247 (class 1259 OID 16796)
-- Name: auth_group_permissions_id_seq; Type: SEQUENCE; Schema: public; Owner: inventario_user
--

ALTER TABLE public.auth_group_permissions ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.auth_group_permissions_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- TOC entry 248 (class 1259 OID 16797)
-- Name: auth_permission; Type: TABLE; Schema: public; Owner: inventario_user
--

CREATE TABLE public.auth_permission (
    id integer NOT NULL,
    name character varying(255) NOT NULL,
    content_type_id integer NOT NULL,
    codename character varying(100) NOT NULL
);


ALTER TABLE public.auth_permission OWNER TO inventario_user;

--
-- TOC entry 249 (class 1259 OID 16800)
-- Name: auth_permission_id_seq; Type: SEQUENCE; Schema: public; Owner: inventario_user
--

ALTER TABLE public.auth_permission ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.auth_permission_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- TOC entry 251 (class 1259 OID 16806)
-- Name: auth_user_groups; Type: TABLE; Schema: public; Owner: inventario_user
--

CREATE TABLE public.auth_user_groups (
    id bigint NOT NULL,
    user_id integer NOT NULL,
    group_id integer NOT NULL
);


ALTER TABLE public.auth_user_groups OWNER TO inventario_user;

--
-- TOC entry 252 (class 1259 OID 16809)
-- Name: auth_user_groups_id_seq; Type: SEQUENCE; Schema: public; Owner: inventario_user
--

ALTER TABLE public.auth_user_groups ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.auth_user_groups_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- TOC entry 253 (class 1259 OID 16810)
-- Name: auth_user_id_seq; Type: SEQUENCE; Schema: public; Owner: inventario_user
--

ALTER TABLE public.auth_user ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.auth_user_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- TOC entry 254 (class 1259 OID 16811)
-- Name: auth_user_user_permissions; Type: TABLE; Schema: public; Owner: inventario_user
--

CREATE TABLE public.auth_user_user_permissions (
    id bigint NOT NULL,
    user_id integer NOT NULL,
    permission_id integer NOT NULL
);


ALTER TABLE public.auth_user_user_permissions OWNER TO inventario_user;

--
-- TOC entry 255 (class 1259 OID 16814)
-- Name: auth_user_user_permissions_id_seq; Type: SEQUENCE; Schema: public; Owner: inventario_user
--

ALTER TABLE public.auth_user_user_permissions ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.auth_user_user_permissions_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- TOC entry 256 (class 1259 OID 16815)
-- Name: django_admin_log; Type: TABLE; Schema: public; Owner: inventario_user
--

CREATE TABLE public.django_admin_log (
    id integer NOT NULL,
    action_time timestamp with time zone NOT NULL,
    object_id text,
    object_repr character varying(200) NOT NULL,
    action_flag smallint NOT NULL,
    change_message text NOT NULL,
    content_type_id integer,
    user_id integer NOT NULL,
    CONSTRAINT django_admin_log_action_flag_check CHECK ((action_flag >= 0))
);


ALTER TABLE public.django_admin_log OWNER TO inventario_user;

--
-- TOC entry 257 (class 1259 OID 16821)
-- Name: django_admin_log_id_seq; Type: SEQUENCE; Schema: public; Owner: inventario_user
--

ALTER TABLE public.django_admin_log ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.django_admin_log_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- TOC entry 258 (class 1259 OID 16822)
-- Name: django_content_type; Type: TABLE; Schema: public; Owner: inventario_user
--

CREATE TABLE public.django_content_type (
    id integer NOT NULL,
    app_label character varying(100) NOT NULL,
    model character varying(100) NOT NULL
);


ALTER TABLE public.django_content_type OWNER TO inventario_user;

--
-- TOC entry 259 (class 1259 OID 16825)
-- Name: django_content_type_id_seq; Type: SEQUENCE; Schema: public; Owner: inventario_user
--

ALTER TABLE public.django_content_type ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.django_content_type_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- TOC entry 260 (class 1259 OID 16826)
-- Name: django_migrations; Type: TABLE; Schema: public; Owner: inventario_user
--

CREATE TABLE public.django_migrations (
    id bigint NOT NULL,
    app character varying(255) NOT NULL,
    name character varying(255) NOT NULL,
    applied timestamp with time zone NOT NULL
);


ALTER TABLE public.django_migrations OWNER TO inventario_user;

--
-- TOC entry 261 (class 1259 OID 16831)
-- Name: django_migrations_id_seq; Type: SEQUENCE; Schema: public; Owner: inventario_user
--

ALTER TABLE public.django_migrations ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.django_migrations_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- TOC entry 262 (class 1259 OID 16832)
-- Name: django_session; Type: TABLE; Schema: public; Owner: inventario_user
--

CREATE TABLE public.django_session (
    session_key character varying(40) NOT NULL,
    session_data text NOT NULL,
    expire_date timestamp with time zone NOT NULL
);


ALTER TABLE public.django_session OWNER TO inventario_user;

--
-- TOC entry 4911 (class 2604 OID 17258)
-- Name: agregacion_atributos_por_equipo id; Type: DEFAULT; Schema: inventario; Owner: inventario_user
--

ALTER TABLE ONLY inventario.agregacion_atributos_por_equipo ALTER COLUMN id SET DEFAULT nextval('inventario.agregacion_atributos_por_equipo_id_seq'::regclass);


--
-- TOC entry 4901 (class 2604 OID 17065)
-- Name: historial_equipos id; Type: DEFAULT; Schema: inventario; Owner: inventario_user
--

ALTER TABLE ONLY inventario.historial_equipos ALTER COLUMN id SET DEFAULT nextval('inventario.historial_equipos_id_seq'::regclass);


--
-- TOC entry 4906 (class 2604 OID 17193)
-- Name: historial_mantenciones id_historial; Type: DEFAULT; Schema: inventario; Owner: inventario_user
--

ALTER TABLE ONLY inventario.historial_mantenciones ALTER COLUMN id_historial SET DEFAULT nextval('inventario.historial_mantenciones_id_historial_seq'::regclass);


--
-- TOC entry 4908 (class 2604 OID 17227)
-- Name: historial_mantenciones_log id_evento; Type: DEFAULT; Schema: inventario; Owner: inventario_user
--

ALTER TABLE ONLY inventario.historial_mantenciones_log ALTER COLUMN id_evento SET DEFAULT nextval('inventario.historial_mantenciones_log_id_evento_seq'::regclass);


--
-- TOC entry 4904 (class 2604 OID 17156)
-- Name: prioridad_mantencion id_prioridad; Type: DEFAULT; Schema: inventario; Owner: inventario_user
--

ALTER TABLE ONLY inventario.prioridad_mantencion ALTER COLUMN id_prioridad SET DEFAULT nextval('inventario.prioridad_mantencion_id_prioridad_seq'::regclass);


--
-- TOC entry 4903 (class 2604 OID 17147)
-- Name: tipo_mantencion id_tipo_mantencion; Type: DEFAULT; Schema: inventario; Owner: inventario_user
--

ALTER TABLE ONLY inventario.tipo_mantencion ALTER COLUMN id_tipo_mantencion SET DEFAULT nextval('inventario.tipo_mantencion_id_tipo_mantencion_seq'::regclass);


--
-- TOC entry 5314 (class 0 OID 17255)
-- Dependencies: 275
-- Data for Name: agregacion_atributos_por_equipo; Type: TABLE DATA; Schema: inventario; Owner: inventario_user
--

COPY inventario.agregacion_atributos_por_equipo (id, id_equipo, id_atributo_equipo, valor, id_empresa) FROM stdin;
84	33	22	16 GB	\N
85	33	23	512 GB SSD	\N
86	33	24	Intel i5 12th Gen	\N
87	33	25	15 Pulgadas	\N
88	33	52	\N	\N
\.


--
-- TOC entry 5258 (class 0 OID 16724)
-- Dependencies: 218
-- Data for Name: atributos_equipo; Type: TABLE DATA; Schema: inventario; Owner: inventario_user
--

COPY inventario.atributos_equipo (id_atributo_equipo, id_tipo_equipo, atributo, valor, id_empresa, id_subtipo_equipo, subtipo_nombre) FROM stdin;
20	21	Numero de Folio	\N	2	\N	\N
21	21	Numero de hojas	\N	2	\N	\N
22	22	RAM	16 GB	2	\N	\N
23	22	Disco	512 GB SSD	2	\N	\N
24	22	CPU	Intel i5 12th Gen	2	\N	\N
25	22	Pantalla	15 Pulgadas	2	\N	\N
30	26	Alcance	50 mts	2	\N	\N
38	30	Tecnología	Inyección de tinta	2	\N	\N
41	36	Tamaño pantalla	6.5 pulgadas	2	\N	\N
42	36	Bateria	2500 mAh	2	\N	\N
43	36	Resolución Pantalla	500 ppi	2	\N	\N
52	22	Resolución	\N	2	\N	\N
55	48	Tinta	\N	1	\N	\N
53	49	RAM	\N	1	\N	\N
54	49	Almacenamiento	\N	1	\N	\N
56	49	Tamaño de Pantalla	\N	1	\N	\N
57	49	Procesador	\N	1	\N	\N
58	49	Bateria	\N	1	\N	\N
59	47	conector	\N	1	\N	\N
\.


--
-- TOC entry 5260 (class 0 OID 16728)
-- Dependencies: 220
-- Data for Name: departamento; Type: TABLE DATA; Schema: inventario; Owner: inventario_user
--

COPY inventario.departamento (id_departamento, nombre_departamento, id_empresa) FROM stdin;
1	TI	1
2	Operaciones	1
3	Finanzas	1
4	TI	2
5	Operaciones	2
7	Servicio de Limpieza	1
6	Asistencia Técnica	1
9	Informática	1
10	Mantenimiento	1
11	Comunicaciones	1
12	Reparaciones	2
13	Soporte	2
14	Comunicaciones	2
\.


--
-- TOC entry 5262 (class 0 OID 16732)
-- Dependencies: 222
-- Data for Name: detalle_factura; Type: TABLE DATA; Schema: inventario; Owner: inventario_user
--

COPY inventario.detalle_factura (id_detalle_factura, id_factura, id_equipo, nombre_equipo, cantidad, valor_unitario, valor_neto, iva, valor_total, id_empresa) FROM stdin;
2	2	1	HP ProBook 440 G9	3	700000	700000	133000	833000	1
3	1	29	MacBook Air	1	500000	500000	5000000	5000000	\N
1	1	28	HP ProBook 440 G9	1	550000	550000	104500	654500	1
4	3	29	Macbook Air10	4	600000	500000	100000	2400000	1
\.


--
-- TOC entry 5264 (class 0 OID 16740)
-- Dependencies: 224
-- Data for Name: empleado; Type: TABLE DATA; Schema: inventario; Owner: inventario_user
--

COPY inventario.empleado (id_empleado, rut, nombre, apellido_paterno, apellido_materno, activo, cargo, telefono, id_empresa, id_departamento, rol, user_id, correo) FROM stdin;
1	17.090.533-4	Hernán	Méndez	Sepúlveda	t	Jefe de TI	+56 911111111	1	1	admin	2	hernán.méndez@galilea.cl
2	16.111.222-5	Carla	Soto	Pérez	t	Encargada de Obras	+56 9 2222 2222	2	5	usuario	3	carla.soto@pehuenche.cl
11	12567234-6	Cristian	Rojas	Medina	t	Técnico Redes	+56 989898988	1	6	usuario	4	cristian.rojas@galilea.cl
12	33.333.333-4	Joselo	Puertas	Rojas	t	Asistente	+56 987654321	1	3	usuario	5	joselo.puertas@galilea.cl
5	11.111.111-1	Pedro	Perez	Poblete	t	Técnico Informático	+56 999999999	1	6	usuario	6	pedro.perez@galilea.cl
9	12.121.121-2	María	Contreras	Torres	t	Auxiliar de aseo	+569 12345678	1	7	usuario	7	maría.contreras@galilea.cl
3	18.444.555-6	Diego	Rojas	Castro	t	Soporte TI	+56 9 3333 3333	2	4	usuario	8	diego.rojas@pehuenche.cl
10	13.333.333-4	Camila	Castro	Carmona	t	Jefe de TI	987654321	2	4	admin	9	camila.castro@pehuenche.cl
13	17.708.025-k	Carolina	Cárdenas	Jofré	t	Departamento Salud	+569 53409306	2	5	usuario	10	carolina.cardenas@pehuenche.cl
14	22.222.222-2	Mario	Ortega	Castro	t	Asistente	+56987654321	2	14	usuario	11	mario.ortega@pehuenche.cl
15	23.333.333-4	Arturo	Vidal	Sanchez	t	Técnico Redes	+569 9999999	1	10	usuario	12	arturo.vidal@galilea.cl
\.


--
-- TOC entry 5266 (class 0 OID 16747)
-- Dependencies: 226
-- Data for Name: empresa; Type: TABLE DATA; Schema: inventario; Owner: inventario_user
--

COPY inventario.empresa (id_empresa, rut_empresa, nombre_empresa, direccion_empresa, giro) FROM stdin;
1	76.543.210-9	Galilea S.A.	Talca	Construcción
2	76.999.888-7	Pehuenche Ltda.	Curicó	Servicios
\.


--
-- TOC entry 5268 (class 0 OID 16753)
-- Dependencies: 228
-- Data for Name: equipo; Type: TABLE DATA; Schema: inventario; Owner: inventario_user
--

COPY inventario.equipo (id_equipo, nombre_equipo, id_marca, id_tipo_equipo, id_estado_equipo, id_empleado, id_proveedor, etiqueta, qr_code, fecha_creacion, fecha_modificacion, id_empresa, departamento_id, observaciones, activo_critico, confidencialidad, integridad, disponibilidad) FROM stdin;
36	Windows 11 Pro	74	41	\N	\N	13	SIS00001	qrcodes/qr_36.png	2025-09-25 00:27:32.423157	2025-09-25 02:07:23.425906	1	1		t	3.00	1.00	4.00
29	Macbook Air	61	49	11	9	5	NBK00005	qrcodes/qr_29.png	2025-09-15 14:41:45.442613	2025-09-25 02:32:00.809556	1	1	Equipo Nuevo completo con cargador	f	\N	\N	\N
18	Asus Zenbook duo	41	49	11	9	7	NBK00001	qrcodes/qr_equipo_18.png	2025-09-04 11:36:40.826248	2025-09-25 02:33:18.70661	1	7		f	\N	\N	\N
32	Mouse	62	47	11	11	5	PFC00003	qrcodes/qr_32.png	2025-09-16 12:10:04.688337	2025-09-25 11:38:09.81949	1	7		f	\N	\N	\N
23	TP-Link 1234Y	51	42	11	9	9	ROU00001	iVBORw0KGgoAAAANSUhEUgAAASIAAAEiAQAAAAB1xeIbAAABb0lEQVR4nO1YQW6EMAy0A9Ieg9QHhS/vD+Ap/QG5Z+XKOF6qHtpeCEnwHBDxjsRo4rUtI8HfWN0/SADGUhhLYSyFsRTGupqFGSPgzMc5amRuQH3jrECMjfsqjkALDHuA2lDfOCu+c1yx/w0u13UnFi0+SeGpS1ePrPHHGQHGVIEudyOWJ6Jlz3t44R4hotSK+qbzfhW/B8CwfSQEvYDLdLnbeE/vM0Fk2z01od41zQIZJcNRXzxPlvwImw6fS63qXQ/eH0WftoFt5wcl+dW8PznvSXutdN2Bkz9Z3pfIe5/EdnmTbD/ealXvumBFbroxrxP0+LCdwvl5f0CCUmms5hTstaBtdge/Ccz7QnvMSeZ7uQDbIRfdY3quNJ+I+RZO++LvuOMuDcKTQ554qzakytW7rryndWLH48SHF0JYalbvuvDec32PGl3nfAFUt3rX15xzrI95n2NzTtE95rdboNrVO2NlGEthLIWxFMaCjC98NOt+Jn7/CwAAAABJRU5ErkJggg==	2025-09-05 13:27:02.419077	2025-09-23 15:04:29.388229	1	7		f	\N	\N	\N
5	Mouse	42	19	12	2	10	PFC00001	iVBORw0KGgoAAAANSUhEUgAAASIAAAEiAQAAAAB1xeIbAAABh0lEQVR4nO2aS26EMAyG7YA0yyD1AD0KXK03CweqRJaVGLmyYzMz6qJdFMLD/2IUMp8UyxjbCSDB7xrDHyAAp0xOmZwyOWVyqjaFqhZg7O4IkG1mqGrXJaieWBOP+AegkQk6hvUHp7LF+IgtyKg8BrXtOjPV/piJny1Brm1XuCqFw9YrXjruI6f2DIAAN5IRHcD6cAZqlKam01qLA9xLm1PbrgvEPS3XkurpNer3a304AYUc6KXFwY5DXpr8+nZdg8o3wiHOnPlnoFQmlxuwd+uPSUHZQ9HUkKR6Sux73WXxHP+Z9mp9OIXvyUJe7sLTXtd9v7bvU1yCnzTnyBPgcb9+f9/LKY7ke9C4107/31cMTr34HvWqmWnkcT+9zci1lvZtfThBzgE9x7TiSo+q6zlndd9P2thYrZW2x/ucTSnkYzRKnG5S/PL+fkuKPsqWtiEcstfaTc8xoZ86wJ74iOF9XmPF4JTp+dUgcKqP2u4/Xhx6vl+HQv82SuWUySmTUyanTMemvgGjFt1ZLskxDAAAAABJRU5ErkJggg==	2025-09-04 11:36:40.826248	2025-09-23 10:23:56.110292	2	\N	\N	f	\N	\N	\N
1	HP ProBook 440 G9	56	22	12	2	6	NBK00003	iVBORw0KGgoAAAANSUhEUgAAASIAAAEiAQAAAAB1xeIbAAABgElEQVR4nO1ZQW7DMAyTnAA7Jj9yvrafJU/ZAwbExwEpOEi2ugI7bJfGbiwe3NQlUEKwVYpl0N/Ywj9IRM4yOMvgLIOzDM6qzeKCkXhJzHlRLFV1dcGKEOz6PACrLILaurpgJTvj23xj3dFrUF1XTyxgH1A6TUu6emDxMh3nfmO/rLG8TtLaExEozXkHL6A+XIG1qamZ5dzTIFW/ZZtTW1cH5x7399hm4nINauoKHbAoW8mIe5efxFnKEnczn2ur6sMVak/6CytL3AcpuzYer/0JtYeMVWWi2stsle+C1/75PoeGg2j6ZIrrFyNCOj8P4LbVhyuwNp1m00hY0xv0qQldXfQcw0OnAY7yqfecU3JMkiwt2/3l5/C3rf4yOeam3UeNJt2TncbVXyXHVMQPZrxbotm++tdkjb92kmxNx8jZ+1TSFTpkIfv73Opv/r/VKZkCHsYqm7LMBbnPeWqmkFGmWbWXmud47c/MMSlnyLqgdfXBWQXOMjjL4CyDs6jgG9x25qBUyaUPAAAAAElFTkSuQmCC	2025-09-04 11:36:40.826248	2025-09-23 10:23:56.110292	2	5	Color defectuoso\r\n\r\nSe arreglo el color	f	\N	\N	\N
27	Asus Zenbook duo	43	22	12	2	6	DSK00002	qrcodes/qr_27.png	2025-09-08 23:58:40.802768	2025-09-23 10:23:56.110292	2	\N	\N	f	\N	\N	\N
30	Lenovo Legion	63	49	11	11	9	NBK00006	qrcodes/qr_30.png	2025-09-15 14:51:56.978662	2025-09-25 02:31:52.755386	1	1	ok	t	1.00	1.00	1.00
3	Epson EcoTank L3250	57	48	9	\N	9	IMP00001	iVBORw0KGgoAAAANSUhEUgAAASIAAAEiAQAAAAB1xeIbAAABh0lEQVR4nO1YS47DIAw1BGmWyQ3mKPRqc7PkKL1BWI6UyKNnIKpm024SCPgt8qFP6pNx7IcN03ss9gMSkbIylJWhrAxlZSirNMskODJm2g1RyCuPorq6YHkGVjytA9rvIAt8D/U3Z4Wc44vkffwWXHldPbGYn45SpalJVw8s8xiPSlOTrhZZLt1HBDwQMYUprvAN1NsWWIuYmgl5T9Jr92hzSuvqIO/5eGcK6LXyGZTUZTtgUbSSnrdjBXmPou/FcuLnuVb1toXY04gQ48Lw98nka+wvyfsVh6mVKG7AjOSXb0Fjf37e02uliWfatAEa+7NnCutuyD+l82IXgjv7H9+gK5/DuEvDxS7MUm52w3Wrt23UHEEao8WXl+pTq3rb1hyTxl/x93EXdIZ85RzTo+j7pzH8kyea9au/J8v9X1i+N5fPtcNWuXrbVOyZwhd8znR03TK6bE8zBQAHLLj6eJGjlkB77UU+Z9ywBo+psb/I3yfg6TCaXLt6q6wEZWUoK0NZGcqihD+cQeltV0XqAwAAAABJRU5ErkJggg==	2025-09-04 11:36:40.826248	2025-09-25 02:33:05.384477	1	1	Toner defectuoso	t	1.00	1.00	1.00
2	Dell Latitude 5440	60	22	12	2	8	NBK00002	iVBORw0KGgoAAAANSUhEUgAAASIAAAEiAQAAAAB1xeIbAAABhElEQVR4nO2aX2rDMAzGJcfQR+dG8dV2M/soPUAheRw4aMh/FiisHRtJbEffS1P5R/thFEVWiwTv5dUvIAChioQqEqpIqCKhzqYwSwN4frVLidhTfV2Cmog186UJQA6GGKA23DdOLTnH0S46RdJtcLavS1ETEeVKU5WvDin9HPC48zcqoZ4oQ0SOL6Z5SFWeiMIz9VpC/Snvfcr24Tu+YgvuVQd7T1vAj4B8G5zsS12GwtzQayBnuLMsb0/2dZG8DxrAPBCmuw7c5GvydkWq273qYO8RzIOb/Bun/Irkx5k4pit3r5qmIB1fp3SMDanP2a7SgqvVveqAIsenWR8LvPlE8GNsNFdMfWfl7tvO+01xnrMtSN7vX3OyuNzESjPzQqo+svdHzTHRpprzj896I6F+mmOCxxtXmgBot8Nt7e47maWBiVN8ftYuQ6jcveqLmu6I9DHKPOfg/n4eKM4UYn+fn7ryrD2szwEu9eT4h0Ppc3amUP4blSVUkVBFQhUJVdQ29QUgh+FCbvy6hgAAAABJRU5ErkJggg==	2025-09-04 11:36:40.826248	2025-09-23 10:23:56.110292	2	4	\N	f	\N	\N	\N
37	Olidata	75	49	9	\N	5	NBK00007	qrcodes/qr_37.png	2025-09-25 04:04:16.076514	2025-09-25 11:41:01.178251	1	2	Desgastes por uso en carcasa.	t	4.00	4.00	4.00
35	Mouse	41	47	9	\N	5	PFC00004	qrcodes/qr_35.png	2025-09-24 21:14:59.63201	2025-09-25 12:52:20.423388	1	6		t	2.00	2.00	2.00
33	HP ProBook 440 G9	56	22	12	2	6	NBK000007	qrcodes/qr_33.png	2025-09-16 13:04:38.572958	2025-09-25 16:21:53.636006	2	5	Pantalla rota Arreglar	t	5.00	6.00	7.00
28	HP ProBook 440 G9	50	49	11	9	5	DSK00001	qrcodes/qr_28.png	2025-09-11 16:27:32.51967	2025-09-25 02:32:09.650114	1	7		t	3.00	3.00	3.00
26	Mouse Powershift	50	47	11	9	9	PER00001	qrcodes/qr_26.png	2025-09-08 13:32:00.645226	2025-09-25 02:32:18.036806	1	7		f	\N	\N	\N
25	Motorola 678	55	42	9	\N	5	TIP00001	qrcodes/qr_25.png	2025-09-05 14:37:53.26659	2025-09-23 15:05:20.794527	1	11		f	\N	\N	\N
38	Protocolo	76	40	11	1	\N	PRO00001	qrcodes/qr_38.png	2025-09-25 04:16:44.6731	2025-09-25 14:44:03.180643	1	6	Reparado	t	2.00	2.00	4.00
21	Macbook Pro	61	49	9	\N	5	NBK00004	iVBORw0KGgoAAAANSUhEUgAAASIAAAEiAQAAAAB1xeIbAAABh0lEQVR4nO1ZS26FMAwcB/Z5Ug/wjsK7WdWbhaP0AJVgH+TKTsL7bNrF4xc8G5IwEiPHmIkhxt/o3T9IgLEKjFVgrAJjFRhraxZltCC6TES3sazcNtV1ClbHggHggEY+v40u8DHUH5w1zjk+tmlFX4PNddXMal/m1PFEO9DlzsjqL2s/EWfPey+lfZTKH8Ca+HwA9a6G2PepzjSyAR8RwHPh2at6V0Hs+WHFR5nyIdS7ClgkFkddvdb77O1lZP5+ORaSjw9evLxXk1/8fbjf3at6VwVrJOJwN/k+At2wA101s5CPr16CzRF6uE2jIJXf8n6FmhNzO0GyPW9A2gWL/cKxn/HY3mF9Fyz2S9echKe8V7epsNgvGftOL4O6m2xxsu2x2K/hc0hN/uegrl56yN+t+fs1Wfx1lZZCOm/NjYXtdZ2hhwyMbQT8D6G/8t7VuypYXsq6DLphovuxymrOBj6nSb8QzWMuXnN4nucWphxzU0//7U90xsowVoGxCoxVYKyCd35rfwEXF+nglls38gAAAABJRU5ErkJggg==	2025-09-04 19:38:43.86377	2025-09-25 02:32:44.522319	1	9		f	\N	\N	\N
4	Teclado 1234h	62	47	9	\N	7	PFC00002	iVBORw0KGgoAAAANSUhEUgAAASIAAAEiAQAAAAB1xeIbAAABmElEQVR4nO1Zy23DMAx9lAXk6AAZoKPIG3SmjtQN7FG6gXU0IIMF9QkC59Be/BXfQZCUB/iBUp5Jmhh/YzD/IAHKKlBWgbIKlFWgrL1ZlGFBHWYCfNnpdtVVBcuxYJSpvzF1aOIGn0P9yVk+33Hu471P/wW7v66aWNS1Ydsn1suyizXDPxjwe+syFcW+FWuXiA+f+d7zCdSbU7Pw+kpFw3BjHMpOfAn3R1VvTs2iRU+BgObN8LWnsGZ+33kiDETEzBJ6b4HhPmt+v77fc7L3VqzGPwK5fiKWA+BjqzcX8nskg88zOQn1+9Vj7zjILDp9w5L2CILGfpN736QUJ0ac+1bOY8y/auxX9nvIEEDuW2orWQ73Z8ZzVPXmArGnvHoG29tAjueSgR5VvblCXet6Gf1Dkp1JTkLCHrsLO+kyNfYxv+7i8mPDRB+T5vdb9tLIjeDY1GFg1vx+W5an5DnxK8omT6yVZRd9TAaCJfdzS5d/N12mzj4mcnGb6y3N7zfI7187O2kmFe6h1RtlZSirQFkFyipQFjJ+AVEtzVNOP18hAAAAAElFTkSuQmCC	2025-09-04 11:36:40.826248	2025-09-25 02:32:58.036822	1	7	Desgastes asociados al uso	f	\N	\N	\N
31	Epson EcoTank L3250	57	48	11	12	5	IMP00002	qrcodes/qr_31.png	2025-09-15 21:02:49.663491	2025-09-25 11:40:40.536348	1	3	Articulo nuevo con todos sus componentes	f	\N	\N	\N
19	Iphone 13	48	36	12	2	8	SMP00001	iVBORw0KGgoAAAANSUhEUgAAASIAAAEiAQAAAAB1xeIbAAABcklEQVR4nO2aQW6EMAxF7RCpy3CDOQpcrTeDo/QAlSbLkYJc2YnV2XSmmxAg/hvAPImvyMQ2Agnea3X/gACMUhmlMkpllMqo1hQWeYAVPeAcNTI39dUFNRHrzmf3DWmBQQJ0Dvcnp2LJ8ZLo+V3w7X11Ra3jQEf01QUVHrrLH8vX9ShfjoGTPfJZ/CDkI53AvbsCtUpTM0qtlcCW25zWvjrIe3oObVheg5a+XDcUlobeA33euLPUy8a+eqCIG3qAkDQcEhBR0pbz2O7PSkEeoaY8VsmUlYCWILEyYNFyVPfuAmtPMtJCkDNZ8aSXtvbV+5wbL7EMt+GBecCavmy/3yXvVb+bviR/Dlre7/Idk3jP0Sa/4hPfqadaSyxe9qcbVmv3/Y4JXGGl2cFZpqxqT3ytHij/5x2COKSDu3cXW/uIQOv43diX64gKvK3LhJvHqhK2ubZ+rS0qtZYW+aZgtbYuhfZvVJFRKqNURqmMUp2b+gE8l9Hiy6rAfQAAAABJRU5ErkJggg==	2025-09-04 11:36:40.826248	2025-09-23 10:23:56.110292	2	\N	\N	f	\N	\N	\N
\.


--
-- TOC entry 5270 (class 0 OID 16757)
-- Dependencies: 230
-- Data for Name: estado_equipo; Type: TABLE DATA; Schema: inventario; Owner: inventario_user
--

COPY inventario.estado_equipo (id_estado_equipo, descripcion, id_empresa) FROM stdin;
9	bodega	1
10	bodega	2
11	asignado	1
12	asignado	2
13	mantenimiento	1
14	mantenimiento	2
15	baja	1
16	baja	2
\.


--
-- TOC entry 5272 (class 0 OID 16761)
-- Dependencies: 232
-- Data for Name: estado_mantencion; Type: TABLE DATA; Schema: inventario; Owner: inventario_user
--

COPY inventario.estado_mantencion (id_estado_mantencion, tipo, id_empresa) FROM stdin;
11	Programada	1
12	Programada	2
13	Terminada	1
14	Terminada	2
15	Completada	1
16	Completada	2
17	Cancelada	1
18	Cancelada	2
19	Incompleta	1
20	Incompleta	2
21	Pendiente	1
22	Pendiente	2
\.


--
-- TOC entry 5274 (class 0 OID 16765)
-- Dependencies: 234
-- Data for Name: factura; Type: TABLE DATA; Schema: inventario; Owner: inventario_user
--

COPY inventario.factura (id_factura, id_proveedor, fecha_emision, id_empresa) FROM stdin;
1	\N	2025-08-28	1
2	\N	2025-09-02	1
3	11	2025-09-19	\N
\.


--
-- TOC entry 5304 (class 0 OID 17062)
-- Dependencies: 264
-- Data for Name: historial_equipos; Type: TABLE DATA; Schema: inventario; Owner: inventario_user
--

COPY inventario.historial_equipos (id, equipo_id, etiqueta, nombre_equipo, modelo, tipo_equipo_id, accion, usuario_id, fecha, id_empresa, departamento_id, ubicacion, estado_anterior_id, estado_nuevo_id, responsable_actual_id, comentario, responsable_anterior_id) FROM stdin;
306	33	NBK000007	HP ProBook 440 G9	\N	22	OBSERVACIONES	\N	2025-09-19 22:46:11.049663	2	5	\N	10	10	\N	Pantalla rota Arreglar	\N
290	32	PFC00003	Mouse	\N	42		1	2025-09-16 21:34:25.380984	1	7	\N	9	11	1	\N	\N
54	25	TIP00001	Motorola 678	\N	42	DESASIGNACION MASIVA	1	2025-09-11 13:08:56.1719	1	\N	\N	11	9	\N	\N	1
55	26	PER00001	Mouse Powershift	\N	42	DESASIGNACION MASIVA	1	2025-09-11 13:08:56.1719	1	\N	\N	11	9	\N	\N	11
313	35	PFC00004	Mouse	\N	42		\N	2025-09-24 21:14:59.64956	1	6	\N	\N	9	\N	\N	\N
59	28	DSK00001	HP ProBook 440 G9	\N	42	DESASIGNACION MASIVA	1	2025-09-12 16:44:05.699971	1	\N	\N	11	9	\N	\N	1
20	23	ROU00001	TP-Link 1234Y	\N	42		\N	2025-09-05 13:27:02.421305	1	\N	\N	\N	9	\N	\N	\N
342	38	PRO00001	Protocolo	\N	40	OBSERVACIONES	1	2025-09-25 13:18:48.67507	1	6	\N	11	11	1	Fue revisado y necesita ajustes.\r\nefewfewf	1
12	5	PFC00001	Mouse	\N	\N	Cambio de responsable	\N	2025-09-04 14:20:32.790327	2	5	\N	12	12	2	\N	\N
1	5	\N	\N	\N	\N	Cambio de Estado	\N	2025-09-04 13:23:58.607282	2	\N	\N	12	10	\N	\N	\N
2	18	\N	\N	\N	\N	Cambio de Estado	\N	2025-09-04 13:33:39.438268	1	\N	\N	9	11	\N	\N	\N
3	18	\N	\N	\N	\N	Cambio de estado	\N	2025-09-04 13:52:41.807646	1	\N	\N	9	11	1	\N	\N
4	18	\N	\N	\N	\N	Cambio de responsable	\N	2025-09-04 13:52:41.81074	1	\N	\N	9	9	1	\N	\N
5	18	\N	\N	\N	\N	Estado cambiado de 'asignado' a 'bodega'	\N	2025-09-04 14:02:23.282364	1	\N	\N	11	9	\N	\N	\N
6	18	\N	\N	\N	\N	Cambio de estado	\N	2025-09-04 14:02:55.251334	1	\N	\N	11	9	\N	\N	\N
7	18	\N	\N	\N	\N	Cambio de responsable	\N	2025-09-04 14:02:55.253675	1	\N	\N	11	11	\N	\N	\N
8	5	\N	\N	\N	\N	Cambio de estado	\N	2025-09-04 14:13:53.86414	2	\N	\N	10	12	3	\N	\N
9	5	\N	\N	\N	\N	Cambio de responsable	\N	2025-09-04 14:13:53.869415	2	\N	\N	10	10	3	\N	\N
10	2	\N	\N	\N	\N	Cambio de estado	\N	2025-09-04 14:14:21.831604	2	\N	\N	10	12	9	\N	\N
11	2	\N	\N	\N	\N	Cambio de responsable	\N	2025-09-04 14:14:21.834553	2	\N	\N	10	10	9	\N	\N
53	27	DSK00002	Asus Zenbook duo	\N	22	DESASIGNACION MASIVA	1	2025-09-11 13:08:56.1719	2	\N	\N	12	10	\N	\N	1
307	5	PFC00001	Mouse	\N	19	ASIGNACION MASIVA	10	2025-09-22 14:59:16.481539	2	5	\N	10	12	2	\N	\N
308	1	NBK00003	HP ProBook 440 G9	\N	22	ASIGNACION MASIVA	10	2025-09-22 14:59:16.481539	2	5	\N	10	12	2	\N	\N
309	27	DSK00002	Asus Zenbook duo	\N	22	ASIGNACION MASIVA	10	2025-09-22 14:59:16.481539	2	5	\N	10	12	2	\N	\N
310	33	NBK000007	HP ProBook 440 G9	\N	22	ASIGNACION MASIVA	10	2025-09-22 14:59:16.481539	2	5	\N	10	12	2	\N	\N
311	2	NBK00002	Dell Latitude 5440	\N	22	ASIGNACION MASIVA	10	2025-09-22 14:59:16.481539	2	5	\N	10	12	2	\N	\N
312	19	SMP00001	Iphone 13	\N	36	ASIGNACION MASIVA	10	2025-09-22 14:59:16.481539	2	5	\N	10	12	2	\N	\N
291	31	IMP00002	Epson EcoTank L3250	\N	42		1	2025-09-16 21:34:36.664666	1	3	\N	9	11	12	\N	\N
69	4	PFC00002	Teclado 1234h	\N	42	DESASIGNACION MASIVA	1	2025-09-13 01:03:07.641713	1	\N	\N	11	9	\N	\N	11
71	3	IMP00001	Epson EcoTank L3250	\N	42	DESASIGNACION MASIVA	1	2025-09-13 01:03:07.641713	1	\N	\N	11	9	\N	\N	10
88	25	TIP00001	Motorola 678	\N	42	DESASIGNACION MASIVA	1	2025-09-13 01:05:27.330567	1	\N	\N	11	9	\N	\N	5
89	28	DSK00001	HP ProBook 440 G9	\N	42	DESASIGNACION MASIVA	1	2025-09-13 01:05:27.330567	1	\N	\N	11	9	\N	\N	5
90	18	NBK00001	Asus Zenbook duo	\N	42	DESASIGNACION MASIVA	1	2025-09-13 01:05:27.330567	1	\N	\N	11	9	\N	\N	5
91	23	ROU00001	TP-Link 1234Y	\N	42	DESASIGNACION MASIVA	1	2025-09-13 01:05:27.330567	1	\N	\N	11	9	\N	\N	5
314	35	PFC00004	Mouse	\N	42		\N	2025-09-25 00:24:46.577662	1	6	\N	9	11	15	\N	\N
95	21	NBK00004	Macbook Pro	\N	42	DESASIGNACION MASIVA	1	2025-09-13 01:05:27.330567	1	\N	\N	11	9	\N	\N	5
98	4	PFC00002	Teclado 1234h	\N	42	DESASIGNACION MASIVA	1	2025-09-13 01:05:27.330567	1	\N	\N	11	9	\N	\N	5
100	26	PER00001	Mouse Powershift	\N	42	DESASIGNACION MASIVA	1	2025-09-13 01:05:27.330567	1	\N	\N	11	9	\N	\N	5
101	3	IMP00001	Epson EcoTank L3250	\N	42	DESASIGNACION MASIVA	1	2025-09-13 01:05:27.330567	1	\N	\N	11	9	\N	\N	5
122	18	NBK00001	Asus Zenbook duo	\N	42	DESASIGNACION MASIVA	1	2025-09-13 02:24:45.449508	1	\N	\N	11	9	\N	\N	1
124	4	PFC00002	Teclado 1234h	\N	42	DESASIGNACION MASIVA	1	2025-09-13 02:24:45.449508	1	\N	\N	11	9	\N	\N	1
126	28	DSK00001	HP ProBook 440 G9	\N	42	DESASIGNACION MASIVA	1	2025-09-13 02:24:45.449508	1	\N	\N	11	9	\N	\N	10
127	25	TIP00001	Motorola 678	\N	42	DESASIGNACION MASIVA	1	2025-09-13 02:24:45.449508	1	\N	\N	11	9	\N	\N	1
128	21	NBK00004	Macbook Pro	\N	42	DESASIGNACION MASIVA	1	2025-09-13 02:24:45.449508	1	\N	\N	11	9	\N	\N	1
129	3	IMP00001	Epson EcoTank L3250	\N	42	DESASIGNACION MASIVA	1	2025-09-13 02:24:45.449508	1	\N	\N	11	9	\N	\N	1
343	38	PRO00001	Protocolo	\N	40	OBSERVACIONES	1	2025-09-25 13:22:06.582192	1	6	\N	11	11	1	Fue revisado y necesita ajustes.\r\nefewfewf\r\noooooo	1
68	5	PFC00001	Mouse	\N	19	DESASIGNACION MASIVA	1	2025-09-13 01:03:07.641713	2	\N	\N	12	10	\N	\N	3
70	1	NBK00003	HP ProBook 440 G9	\N	22	DESASIGNACION MASIVA	1	2025-09-13 01:03:07.641713	2	\N	\N	12	10	\N	\N	3
87	27	DSK00002	Asus Zenbook duo	\N	22	DESASIGNACION MASIVA	1	2025-09-13 01:05:27.330567	2	\N	\N	12	10	\N	\N	5
93	19	SMP00001	Iphone 13	\N	36	DESASIGNACION MASIVA	1	2025-09-13 01:05:27.330567	2	\N	\N	12	10	\N	\N	5
94	2	NBK00002	Dell Latitude 5440	\N	22	DESASIGNACION MASIVA	1	2025-09-13 01:05:27.330567	2	\N	\N	12	10	\N	\N	5
97	5	PFC00001	Mouse	\N	19	DESASIGNACION MASIVA	1	2025-09-13 01:05:27.330567	2	\N	\N	12	10	\N	\N	5
99	1	NBK00003	HP ProBook 440 G9	\N	22	DESASIGNACION MASIVA	1	2025-09-13 01:05:27.330567	2	\N	\N	12	10	\N	\N	5
121	1	NBK00003	HP ProBook 440 G9	\N	22	DESASIGNACION MASIVA	1	2025-09-13 02:24:45.449508	2	\N	\N	12	10	\N	\N	1
123	5	PFC00001	Mouse	\N	19	DESASIGNACION MASIVA	1	2025-09-13 02:24:45.449508	2	\N	\N	12	10	\N	\N	1
125	27	DSK00002	Asus Zenbook duo	\N	22	DESASIGNACION MASIVA	1	2025-09-13 02:24:45.449508	2	\N	\N	12	10	\N	\N	10
315	36	SIS00001	Windows 11 Pro	\N	41		\N	2025-09-25 00:27:32.428387	1	1	\N	\N	\N	\N	\N	\N
133	19	SMP00001	Iphone 13	\N	36	DESASIGNACION MASIVA	1	2025-09-13 02:24:45.449508	2	\N	\N	12	10	\N	\N	1
134	2	NBK00002	Dell Latitude 5440	\N	22	DESASIGNACION MASIVA	1	2025-09-13 02:24:45.449508	2	\N	\N	12	10	\N	\N	1
344	38	PRO00001	Protocolo	\N	40	OBSERVACIONES	\N	2025-09-25 14:44:03.1948	1	6	\N	11	11	1	Reparado	1
132	23	ROU00001	TP-Link 1234Y	\N	42	DESASIGNACION MASIVA	1	2025-09-13 02:24:45.449508	1	\N	\N	11	9	\N	\N	1
292	30	NBK00006	Lenovo Legion	\N	42	ASIGNACION MASIVA	1	2025-09-16 21:37:44.363595	1	6	\N	9	11	11	\N	\N
135	26	PER00001	Mouse Powershift	\N	42	DESASIGNACION MASIVA	1	2025-09-13 02:24:45.449508	1	\N	\N	11	9	\N	\N	10
74	28	DSK00001	HP ProBook 440 G9	\N	42	ASIGNACION MASIVA	1	2025-09-13 01:03:38.808294	1	6	\N	9	11	5	\N	\N
16	21	NBK00004	Macbook Pro	Notebook	42	Cambio de responsable	\N	2025-09-04 21:22:15.338326	1	1		9	11	1		\N
66	21	NBK00004	Macbook Pro	\N	42	DESASIGNACION MASIVA	1	2025-09-13 01:03:07.641713	1	\N	\N	11	9	\N	\N	1
75	19	SMP00001	Iphone 13	\N	42	ASIGNACION MASIVA	1	2025-09-13 01:03:38.808294	1	6	\N	9	11	5	\N	\N
76	18	NBK00001	Asus Zenbook duo	\N	42	ASIGNACION MASIVA	1	2025-09-13 01:03:38.808294	1	6	\N	9	11	5	\N	\N
77	2	NBK00002	Dell Latitude 5440	\N	42	ASIGNACION MASIVA	1	2025-09-13 01:03:38.808294	1	6	\N	9	11	5	\N	\N
78	23	ROU00001	TP-Link 1234Y	\N	42	ASIGNACION MASIVA	1	2025-09-13 01:03:38.808294	1	6	\N	9	11	5	\N	\N
80	21	NBK00004	Macbook Pro	\N	42	ASIGNACION MASIVA	1	2025-09-13 01:03:38.808294	1	6	\N	9	11	5	\N	\N
82	5	PFC00001	Mouse	\N	42	ASIGNACION MASIVA	1	2025-09-13 01:03:38.808294	1	6	\N	9	11	5	\N	\N
83	4	PFC00002	Teclado 1234h	\N	42	ASIGNACION MASIVA	1	2025-09-13 01:03:38.808294	1	6	\N	9	11	5	\N	\N
84	1	NBK00003	HP ProBook 440 G9	\N	42	ASIGNACION MASIVA	1	2025-09-13 01:03:38.808294	1	6	\N	9	11	5	\N	\N
85	26	PER00001	Mouse Powershift	\N	42	ASIGNACION MASIVA	1	2025-09-13 01:03:38.808294	1	6	\N	9	11	5	\N	\N
86	3	IMP00001	Epson EcoTank L3250	\N	42	ASIGNACION MASIVA	1	2025-09-13 01:03:38.808294	1	6	\N	9	11	5	\N	\N
102	1	NBK00003	HP ProBook 440 G9	\N	42		1	2025-09-13 02:12:43.347004	1	2	\N	9	11	3	\N	\N
103	1	NBK00003	HP ProBook 440 G9	\N	42		1	2025-09-13 02:13:00.437331	1	2	\N	11	9	\N	\N	3
107	25	TIP00001	Motorola 678	\N	42	ASIGNACION MASIVA	1	2025-09-13 02:14:04.362166	1	1	\N	9	11	1	\N	\N
108	21	NBK00004	Macbook Pro	\N	42	ASIGNACION MASIVA	1	2025-09-13 02:14:04.362166	1	1	\N	9	11	1	\N	\N
110	23	ROU00001	TP-Link 1234Y	\N	42	ASIGNACION MASIVA	1	2025-09-13 02:14:04.362166	1	1	\N	9	11	1	\N	\N
111	1	NBK00003	HP ProBook 440 G9	\N	42		1	2025-09-13 02:23:37.926681	1	2	\N	9	11	1	\N	\N
112	1	NBK00003	HP ProBook 440 G9	\N	42		1	2025-09-13 02:24:00.186019	1	2	\N	11	9	\N	\N	1
113	1	NBK00003	HP ProBook 440 G9	\N	42	ASIGNACION MASIVA	1	2025-09-13 02:24:17.188475	1	1	\N	9	11	1	\N	\N
114	18	NBK00001	Asus Zenbook duo	\N	42	ASIGNACION MASIVA	1	2025-09-13 02:24:17.188475	1	1	\N	9	11	1	\N	\N
115	5	PFC00001	Mouse	\N	42	ASIGNACION MASIVA	1	2025-09-13 02:24:17.188475	1	1	\N	9	11	1	\N	\N
116	4	PFC00002	Teclado 1234h	\N	42	ASIGNACION MASIVA	1	2025-09-13 02:24:17.188475	1	1	\N	9	11	1	\N	\N
117	3	IMP00001	Epson EcoTank L3250	\N	42	ASIGNACION MASIVA	1	2025-09-13 02:24:17.188475	1	1	\N	9	11	1	\N	\N
119	19	SMP00001	Iphone 13	\N	42	ASIGNACION MASIVA	1	2025-09-13 02:24:17.188475	1	1	\N	9	11	1	\N	\N
120	2	NBK00002	Dell Latitude 5440	\N	42	ASIGNACION MASIVA	1	2025-09-13 02:24:17.188475	1	1	\N	9	11	1	\N	\N
136	1	NBK00003	HP ProBook 440 G9	\N	42		1	2025-09-13 02:25:52.573215	1	2	\N	9	15	\N	\N	\N
137	1	NBK00003	HP ProBook 440 G9	\N	42		1	2025-09-13 02:26:09.910789	1	2	\N	15	9	\N	\N	\N
138	1	NBK00003	HP ProBook 440 G9	\N	42		1	2025-09-13 02:26:32.195217	1	2	\N	9	13	\N	\N	\N
155	3	IMP00001	Epson EcoTank L3250	\N	42		1	2025-09-13 04:40:15.000288	1	3	\N	11	9	\N	\N	10
156	4	PFC00002	Teclado 1234h	\N	42		1	2025-09-13 04:40:30.531927	1	1	\N	11	9	\N	\N	10
157	3	IMP00001	Epson EcoTank L3250	\N	42	ASIGNACION MASIVA	1	2025-09-13 05:00:10.117739	1	6	\N	11	11	11	\N	11
158	4	PFC00002	Teclado 1234h	\N	42	ASIGNACION MASIVA	1	2025-09-13 05:00:10.117739	1	6	\N	11	11	11	\N	11
159	18	NBK00001	Asus Zenbook duo	\N	42	DESASIGNACION MASIVA	1	2025-09-13 05:00:42.619029	1	\N	\N	9	9	\N	\N	\N
161	3	IMP00001	Epson EcoTank L3250	\N	42	DESASIGNACION MASIVA	1	2025-09-13 05:00:42.619029	1	\N	\N	9	9	\N	\N	\N
163	23	ROU00001	TP-Link 1234Y	\N	42	DESASIGNACION MASIVA	1	2025-09-13 05:00:42.619029	1	\N	\N	9	9	\N	\N	\N
164	28	DSK00001	HP ProBook 440 G9	\N	42	DESASIGNACION MASIVA	1	2025-09-13 05:00:42.619029	1	\N	\N	9	9	\N	\N	\N
165	25	TIP00001	Motorola 678	\N	42	DESASIGNACION MASIVA	1	2025-09-13 05:00:42.619029	1	\N	\N	9	9	\N	\N	\N
166	21	NBK00004	Macbook Pro	\N	42	DESASIGNACION MASIVA	1	2025-09-13 05:00:42.619029	1	\N	\N	9	9	\N	\N	\N
167	26	PER00001	Mouse Powershift	\N	42	DESASIGNACION MASIVA	1	2025-09-13 05:00:42.619029	1	\N	\N	9	9	\N	\N	\N
168	4	PFC00002	Teclado 1234h	\N	42	DESASIGNACION MASIVA	1	2025-09-13 05:00:42.619029	1	\N	\N	9	9	\N	\N	\N
196	28	DSK00001	HP ProBook 440 G9	\N	42	ASIGNACION MASIVA	1	2025-09-13 05:45:32.65394	1	1	\N	9	11	1	\N	\N
197	28	DSK00001	HP ProBook 440 G9	\N	42	ASIGNACION MASIVA	1	2025-09-13 05:45:32.65394	1	1	\N	11	11	1	\N	1
198	25	TIP00001	Motorola 678	\N	42	ASIGNACION MASIVA	1	2025-09-13 05:45:32.65394	1	1	\N	9	11	1	\N	\N
199	25	TIP00001	Motorola 678	\N	42	ASIGNACION MASIVA	1	2025-09-13 05:45:32.65394	1	1	\N	11	11	1	\N	1
200	26	PER00001	Mouse Powershift	\N	42	ASIGNACION MASIVA	1	2025-09-13 05:45:32.65394	1	1	\N	9	11	1	\N	\N
201	26	PER00001	Mouse Powershift	\N	42	ASIGNACION MASIVA	1	2025-09-13 05:45:32.65394	1	1	\N	11	11	1	\N	1
202	23	ROU00001	TP-Link 1234Y	\N	42	ASIGNACION MASIVA	1	2025-09-13 05:45:32.65394	1	1	\N	9	11	1	\N	\N
293	29	NBK00005	Macbook Air	\N	42	ASIGNACION MASIVA	1	2025-09-16 21:38:02.470186	1	7	\N	9	11	9	\N	\N
203	23	ROU00001	TP-Link 1234Y	\N	42	ASIGNACION MASIVA	1	2025-09-13 05:45:32.65394	1	1	\N	11	11	1	\N	1
204	28	DSK00001	HP ProBook 440 G9	\N	42	DESASIGNACION MASIVA	1	2025-09-13 05:46:24.513781	1	\N	\N	11	9	\N	\N	1
205	28	DSK00001	HP ProBook 440 G9	\N	42	DESASIGNACION MASIVA	1	2025-09-13 05:46:24.513781	1	\N	\N	9	9	\N	\N	\N
206	25	TIP00001	Motorola 678	\N	42	DESASIGNACION MASIVA	1	2025-09-13 05:46:24.513781	1	\N	\N	11	9	\N	\N	1
207	25	TIP00001	Motorola 678	\N	42	DESASIGNACION MASIVA	1	2025-09-13 05:46:24.513781	1	\N	\N	9	9	\N	\N	\N
208	26	PER00001	Mouse Powershift	\N	42	DESASIGNACION MASIVA	1	2025-09-13 05:46:24.513781	1	\N	\N	11	9	\N	\N	1
209	26	PER00001	Mouse Powershift	\N	42	DESASIGNACION MASIVA	1	2025-09-13 05:46:24.513781	1	\N	\N	9	9	\N	\N	\N
210	23	ROU00001	TP-Link 1234Y	\N	42	DESASIGNACION MASIVA	1	2025-09-13 05:46:24.513781	1	\N	\N	11	9	\N	\N	1
211	23	ROU00001	TP-Link 1234Y	\N	42	DESASIGNACION MASIVA	1	2025-09-13 05:46:24.513781	1	\N	\N	9	9	\N	\N	\N
212	3	IMP00001	Epson EcoTank L3250	\N	42		1	2025-09-13 05:47:34.873552	1	1	\N	9	11	1	\N	\N
213	28	DSK00001	HP ProBook 440 G9	\N	42	ASIGNACION MASIVA	1	2025-09-13 05:49:23.923892	1	3	\N	9	11	12	\N	\N
214	28	DSK00001	HP ProBook 440 G9	\N	42	ASIGNACION MASIVA	1	2025-09-13 05:49:23.923892	1	3	\N	11	11	12	\N	12
215	28	DSK00001	HP ProBook 440 G9	\N	42	DESASIGNACION MASIVA	1	2025-09-13 05:50:07.149192	1	\N	\N	11	9	\N	\N	12
216	28	DSK00001	HP ProBook 440 G9	\N	42	DESASIGNACION MASIVA	1	2025-09-13 05:50:07.149192	1	\N	\N	9	9	\N	\N	\N
217	28	DSK00001	HP ProBook 440 G9	\N	42	ASIGNACION MASIVA	1	2025-09-13 06:09:56.401077	1	6	\N	9	11	11	\N	\N
218	28	DSK00001	HP ProBook 440 G9	\N	42	DESASIGNACION MASIVA	1	2025-09-13 06:10:14.834473	1	\N	\N	11	9	\N	\N	11
219	28	DSK00001	HP ProBook 440 G9	\N	42	ASIGNACION MASIVA	1	2025-09-13 06:12:19.377497	1	6	\N	9	11	5	\N	\N
56	28	DSK00001	HP ProBook 440 G9	\N	42		1	2025-09-11 16:27:32.522997	1	1	\N	\N	9	\N	\N	\N
227	28	DSK00001	HP ProBook 440 G9	\N	42	ASIGNACION MASIVA	1	2025-09-13 06:22:15.701545	1	1	\N	9	11	1	\N	\N
229	21	NBK00004	Macbook Pro	\N	42	ASIGNACION MASIVA	1	2025-09-13 06:22:15.701545	1	1	\N	9	11	1	\N	\N
230	4	PFC00002	Teclado 1234h	\N	42	ASIGNACION MASIVA	1	2025-09-13 06:22:15.701545	1	1	\N	9	11	1	\N	\N
231	23	ROU00001	TP-Link 1234Y	\N	42	ASIGNACION MASIVA	1	2025-09-13 06:22:15.701545	1	1	\N	9	11	1	\N	\N
232	18	NBK00001	Asus Zenbook duo	\N	42	DESASIGNACION MASIVA	1	2025-09-13 06:22:37.836528	1	\N	\N	11	9	\N	\N	1
233	3	IMP00001	Epson EcoTank L3250	\N	42	DESASIGNACION MASIVA	1	2025-09-13 06:22:37.836528	1	\N	\N	11	9	\N	\N	1
235	25	TIP00001	Motorola 678	\N	42	DESASIGNACION MASIVA	1	2025-09-13 06:22:37.836528	1	\N	\N	11	9	\N	\N	1
236	26	PER00001	Mouse Powershift	\N	42	DESASIGNACION MASIVA	1	2025-09-13 06:22:37.836528	1	\N	\N	11	9	\N	\N	1
237	28	DSK00001	HP ProBook 440 G9	\N	42	DESASIGNACION MASIVA	1	2025-09-13 06:22:37.836528	1	\N	\N	11	9	\N	\N	1
239	21	NBK00004	Macbook Pro	\N	42	DESASIGNACION MASIVA	1	2025-09-13 06:22:37.836528	1	\N	\N	11	9	\N	\N	1
240	4	PFC00002	Teclado 1234h	\N	42	DESASIGNACION MASIVA	1	2025-09-13 06:22:37.836528	1	\N	\N	11	9	\N	\N	1
241	23	ROU00001	TP-Link 1234Y	\N	42	DESASIGNACION MASIVA	1	2025-09-13 06:22:37.836528	1	\N	\N	11	9	\N	\N	1
242	18	NBK00001	Asus Zenbook duo	\N	42	ASIGNACION MASIVA	1	2025-09-15 11:34:57.15837	1	7	\N	9	11	9	\N	\N
243	3	IMP00001	Epson EcoTank L3250	\N	42	ASIGNACION MASIVA	1	2025-09-15 11:34:57.15837	1	7	\N	9	11	9	\N	\N
245	25	TIP00001	Motorola 678	\N	42	ASIGNACION MASIVA	1	2025-09-15 11:34:57.15837	1	7	\N	9	11	9	\N	\N
246	26	PER00001	Mouse Powershift	\N	42	ASIGNACION MASIVA	1	2025-09-15 11:34:57.15837	1	7	\N	9	11	9	\N	\N
247	28	DSK00001	HP ProBook 440 G9	\N	42	ASIGNACION MASIVA	1	2025-09-15 11:34:57.15837	1	7	\N	9	11	9	\N	\N
249	21	NBK00004	Macbook Pro	\N	42	ASIGNACION MASIVA	1	2025-09-15 11:34:57.15837	1	7	\N	9	11	9	\N	\N
250	4	PFC00002	Teclado 1234h	\N	42	ASIGNACION MASIVA	1	2025-09-15 11:34:57.15837	1	7	\N	9	11	9	\N	\N
251	23	ROU00001	TP-Link 1234Y	\N	42	ASIGNACION MASIVA	1	2025-09-15 11:34:57.15837	1	7	\N	9	11	9	\N	\N
257	29	NBK00005	Macbook Air	\N	42	OBSERVACIONES	1	2025-09-15 14:41:45.453851	1	1	\N	9	9	\N	Observaciones iniciales:\nEquipo Nuevo, sin cargador (buscar cargador)	\N
258	18	NBK00001	Asus Zenbook duo	\N	42	DESASIGNACION MASIVA	1	2025-09-15 14:50:04.813104	1	\N	\N	11	9	\N	\N	9
259	3	IMP00001	Epson EcoTank L3250	\N	42	DESASIGNACION MASIVA	1	2025-09-15 14:50:04.813104	1	\N	\N	11	9	\N	\N	9
261	25	TIP00001	Motorola 678	\N	42	DESASIGNACION MASIVA	1	2025-09-15 14:50:04.813104	1	\N	\N	11	9	\N	\N	9
262	26	PER00001	Mouse Powershift	\N	42	DESASIGNACION MASIVA	1	2025-09-15 14:50:04.813104	1	\N	\N	11	9	\N	\N	9
263	28	DSK00001	HP ProBook 440 G9	\N	42	DESASIGNACION MASIVA	1	2025-09-15 14:50:04.813104	1	\N	\N	11	9	\N	\N	9
265	21	NBK00004	Macbook Pro	\N	42	DESASIGNACION MASIVA	1	2025-09-15 14:50:04.813104	1	\N	\N	11	9	\N	\N	9
266	4	PFC00002	Teclado 1234h	\N	42	DESASIGNACION MASIVA	1	2025-09-15 14:50:04.813104	1	\N	\N	11	9	\N	\N	9
267	23	ROU00001	TP-Link 1234Y	\N	42	DESASIGNACION MASIVA	1	2025-09-15 14:50:04.813104	1	\N	\N	11	9	\N	\N	9
269	3	IMP00001	Epson EcoTank L3250	\N	42	OBSERVACIONES	1	2025-09-15 15:02:49.272675	1	1	\N	9	9	\N	Toner defectuoso	\N
270	3	IMP00001	Epson EcoTank L3250	\N	42		1	2025-09-15 15:03:11.06906	1	1	\N	9	11	1	\N	\N
271	26	PER00001	Mouse Powershift	\N	42	ASIGNACION MASIVA	1	2025-09-15 15:04:16.410462	1	7	\N	9	11	9	\N	\N
272	28	DSK00001	HP ProBook 440 G9	\N	42	ASIGNACION MASIVA	1	2025-09-15 15:04:16.410462	1	7	\N	9	11	9	\N	\N
275	21	NBK00004	Macbook Pro	\N	42	ASIGNACION MASIVA	1	2025-09-15 15:04:30.139327	1	3	\N	9	11	12	\N	\N
276	18	NBK00001	Asus Zenbook duo	\N	42	ASIGNACION MASIVA	1	2025-09-15 15:04:48.464185	1	7	\N	9	11	9	\N	\N
277	25	TIP00001	Motorola 678	\N	42	ASIGNACION MASIVA	1	2025-09-15 15:04:48.464185	1	7	\N	9	11	9	\N	\N
278	4	PFC00002	Teclado 1234h	\N	42	ASIGNACION MASIVA	1	2025-09-15 15:04:48.464185	1	7	\N	9	11	9	\N	\N
316	37	NBK00007	Olidata	\N	49		\N	2025-09-25 04:04:16.09139	1	2	\N	\N	9	\N	\N	\N
331	38	PRO00001	Protocolo	\N	40		\N	2025-09-25 12:13:01.340814	1	6	\N	\N	\N	12	\N	11
317	38	PRO00001	Protocolo	\N	40		\N	2025-09-25 04:16:44.677946	1	6	\N	\N	\N	\N	\N	\N
26	18	NBK00001	Asus Zenbook duo	\N	42		1	2025-09-05 18:23:51.692732	1	1	\N	9	11	10	\N	\N
27	1	NBK00003	HP ProBook 440 G9	\N	42		1	2025-09-05 18:24:19.777364	1	2	\N	11	11	3	\N	5
28	2	NBK00002	Dell Latitude 5440	\N	42		1	2025-09-05 18:25:07.185944	1	1	\N	11	9	\N	\N	9
30	1	NBK00003	HP ProBook 440 G9	\N	42		1	2025-09-08 12:43:26.796154	1	2	\N	11	15	\N	\N	3
31	2	NBK00002	Dell Latitude 5440	\N	42		1	2025-09-08 12:43:54.203412	1	1	\N	9	13	2	\N	\N
35	26	PER00001	Mouse Powershift	\N	42		1	2025-09-09 20:10:35.7274	1	1	\N	9	9	3	\N	\N
36	26	PER00001	Mouse Powershift	\N	42		1	2025-09-09 20:10:52.81587	1	1	\N	9	9	9	\N	3
37	25	TIP00001	Motorola 678	\N	42		1	2025-09-10 19:53:51.369464	1	1	\N	9	9	\N	\N	9
39	26	PER00001	Mouse Powershift	\N	42		1	2025-09-10 19:54:13.654111	1	1	\N	9	9	\N	\N	9
40	4	PFC00002	Teclado 1234h	\N	42	ASIGNACION MASIVA	1	2025-09-10 21:28:57.696811	1	6	\N	9	11	11	\N	\N
41	27	DSK00002	Asus Zenbook duo	\N	42	ASIGNACION MASIVA	1	2025-09-10 21:28:57.696811	1	6	\N	9	11	11	\N	\N
42	26	PER00001	Mouse Powershift	\N	42	ASIGNACION MASIVA	1	2025-09-10 21:28:57.696811	1	6	\N	9	11	11	\N	\N
44	27	DSK00002	Asus Zenbook duo	\N	42	ASIGNACION MASIVA	1	2025-09-10 21:33:55.841327	1	1	\N	9	11	1	\N	\N
45	25	TIP00001	Motorola 678	\N	42	ASIGNACION MASIVA	1	2025-09-10 21:33:55.841327	1	1	\N	9	11	1	\N	\N
46	1	NBK00003	HP ProBook 440 G9	\N	42		1	2025-09-11 04:47:25.085765	1	2	\N	15	11	\N	\N	\N
47	1	NBK00003	HP ProBook 440 G9	\N	42		1	2025-09-11 04:47:51.667959	1	2	\N	11	9	\N	\N	\N
48	2	NBK00002	Dell Latitude 5440	\N	42		1	2025-09-11 04:48:09.76969	1	1	\N	13	9	\N	\N	2
49	3	IMP00001	Epson EcoTank L3250	\N	42		1	2025-09-11 04:48:22.344236	1	3	\N	11	9	\N	\N	2
52	2	NBK00002	Dell Latitude 5440	\N	42		1	2025-09-11 12:48:31.059349	1	1	\N	11	9	\N	\N	10
57	1	NBK00003	HP ProBook 440 G9	\N	42		1	2025-09-11 20:11:08.695172	1	2	\N	9	11	3	\N	\N
58	28	DSK00001	HP ProBook 440 G9	\N	42	ASIGNACION MASIVA	1	2025-09-12 16:43:48.015629	1	1	\N	9	11	1	\N	\N
60	28	DSK00001	HP ProBook 440 G9	\N	42	ASIGNACION MASIVA	1	2025-09-13 01:02:29.075068	1	6	\N	9	11	5	\N	\N
25	25	TIP00001	Motorola 678	\N	42		\N	2025-09-05 14:37:53.270265	1	1	\N	\N	9	9	\N	\N
279	23	ROU00001	TP-Link 1234Y	\N	42	ASIGNACION MASIVA	1	2025-09-15 15:04:48.464185	1	7	\N	9	11	9	\N	\N
283	4	PFC00002	Teclado 1234h	\N	42	OBSERVACIONES	1	2025-09-15 20:53:14.767467	1	7	\N	11	11	9	Desgastes asociados al uso	9
332	38	PRO00001	Protocolo	\N	40		\N	2025-09-25 12:13:15.890913	1	6	\N	\N	\N	11	\N	12
29	5	PFC00001	Mouse	\N	19		1	2025-09-08 12:27:12.074845	2	4	\N	12	10	\N	\N	2
32	5	PFC00001	Mouse	\N	19		1	2025-09-08 12:44:10.177412	2	4	\N	10	12	3	\N	\N
38	27	DSK00002	Asus Zenbook duo	\N	22		1	2025-09-10 19:54:03.090595	2	4	\N	10	10	\N	\N	3
43	27	DSK00002	Asus Zenbook duo	\N	22		1	2025-09-10 21:29:54.020175	2	4	\N	12	10	\N	\N	11
50	2	NBK00002	Dell Latitude 5440	\N	22	ASIGNACION MASIVA	1	2025-09-11 04:48:45.539786	2	4	\N	10	12	10	\N	\N
51	3	IMP00001	Epson EcoTank L3250	\N	30	ASIGNACION MASIVA	1	2025-09-11 04:48:45.539786	2	4	\N	10	12	10	\N	\N
295	32	PFC00003	Mouse	\N	42		1	2025-09-17 11:15:55.570473	1	7	\N	11	9	\N	\N	1
318	38	PRO00001	Protocolo	\N	40	OBSERVACIONES	\N	2025-09-25 04:19:36.319483	1	6	\N	\N	\N	\N	Requiere correcciones.	\N
333	38	PRO00001	Protocolo	\N	40		\N	2025-09-25 12:16:14.88557	1	6	\N	\N	\N	9	\N	11
319	32	PFC00003	Mouse	\N	47		\N	2025-09-25 11:34:15.558331	1	7	\N	9	11	15	\N	\N
296	32	PFC00003	Mouse	\N	42	ASIGNACION MASIVA	1	2025-09-17 11:16:13.001405	1	3	\N	9	11	12	\N	\N
334	38	PRO00001	Protocolo	\N	40		\N	2025-09-25 12:24:28.960407	1	6	\N	\N	\N	15	\N	9
320	32	PFC00003	Mouse	\N	47		\N	2025-09-25 11:38:09.825449	1	7	\N	11	11	11	\N	15
298	32	PFC00003	Mouse	\N	42	DESASIGNACION MASIVA	1	2025-09-17 11:29:16.619304	1	\N	\N	11	9	\N	\N	12
256	29	NBK00005	Macbook Air	\N	42		1	2025-09-15 14:41:45.451447	1	1	\N	\N	9	\N	\N	\N
268	30	NBK00006	Lenovo Legion	\N	42		1	2025-09-15 14:51:56.980797	1	1	\N	\N	9	\N	\N	\N
284	31	IMP00002	Epson EcoTank L3250	\N	42		1	2025-09-15 21:02:49.667364	1	3	\N	\N	9	\N	\N	\N
287	32	PFC00003	Mouse	\N	42		1	2025-09-16 12:10:04.693319	1	7	\N	\N	9	\N	\N	\N
220	28	DSK00001	HP ProBook 440 G9	\N	42	DESASIGNACION MASIVA	1	2025-09-13 06:12:30.684301	1	\N	\N	11	9	\N	\N	5
221	3	IMP00001	Epson EcoTank L3250	\N	42	DESASIGNACION MASIVA	1	2025-09-13 06:22:00.45395	1	\N	\N	11	9	\N	\N	1
222	18	NBK00001	Asus Zenbook duo	\N	42	ASIGNACION MASIVA	1	2025-09-13 06:22:15.701545	1	1	\N	9	11	1	\N	\N
335	35	PFC00004	Mouse	\N	47		\N	2025-09-25 12:24:50.471641	1	6	\N	9	11	1	\N	\N
288	33	NBK000007	HP ProBook 440 G9	\N	22		1	2025-09-16 13:04:38.575595	2	5	\N	\N	10	\N	\N	\N
300	3	IMP00001	Epson EcoTank L3250	\N	42	DESASIGNACION MASIVA	1	2025-09-17 11:29:42.274979	1	\N	\N	11	9	\N	\N	1
301	25	TIP00001	Motorola 678	\N	42	DESASIGNACION MASIVA	1	2025-09-17 11:29:42.274979	1	\N	\N	11	9	\N	\N	9
302	31	IMP00002	Epson EcoTank L3250	\N	42	DESASIGNACION MASIVA	1	2025-09-17 11:29:42.274979	1	\N	\N	11	9	\N	\N	12
303	21	NBK00004	Macbook Pro	\N	42	DESASIGNACION MASIVA	1	2025-09-17 11:29:42.274979	1	\N	\N	11	9	\N	\N	12
304	4	PFC00002	Teclado 1234h	\N	42	DESASIGNACION MASIVA	1	2025-09-17 11:29:42.274979	1	\N	\N	11	9	\N	\N	9
321	37	NBK00007	Olidata	\N	49	OBSERVACIONES	\N	2025-09-25 11:39:18.757135	1	2	\N	9	9	\N	Desgastes por uso en carcasa.	\N
336	38	PRO00001	Protocolo	\N	40		\N	2025-09-25 12:45:43.454655	1	6	\N	\N	\N	11	\N	15
62	19	SMP00001	Iphone 13	\N	36	DESASIGNACION MASIVA	1	2025-09-13 01:03:07.641713	2	\N	\N	12	10	\N	\N	1
322	37	NBK00007	Olidata	\N	49	ASIGNACION MASIVA	1	2025-09-25 11:40:40.543018	1	3	\N	9	11	12	\N	\N
323	31	IMP00002	Epson EcoTank L3250	\N	48	ASIGNACION MASIVA	1	2025-09-25 11:40:40.543018	1	3	\N	9	11	12	\N	\N
21	23	ROU00001	TP-Link 1234Y	\N	26		\N	2025-09-05 13:57:45.525508	2	5	\N	10	12	2	\N	\N
337	38	PRO00001	Protocolo	\N	40		1	2025-09-25 12:51:39.748447	1	6	\N	\N	\N	1	\N	11
104	27	DSK00002	Asus Zenbook duo	\N	22	ASIGNACION MASIVA	1	2025-09-13 02:13:18.105789	2	4	\N	10	12	10	\N	\N
105	28	DSK00001	HP ProBook 440 G9	\N	22	ASIGNACION MASIVA	1	2025-09-13 02:13:18.105789	2	4	\N	10	12	10	\N	\N
106	26	PER00001	Mouse Powershift	\N	19	ASIGNACION MASIVA	1	2025-09-13 02:13:18.105789	2	4	\N	10	12	10	\N	\N
139	18	NBK00001	Asus Zenbook duo	\N	22	ASIGNACION MASIVA	1	2025-09-13 02:26:51.02231	2	4	\N	10	12	10	\N	\N
140	5	PFC00001	Mouse	\N	19	ASIGNACION MASIVA	1	2025-09-13 02:26:51.02231	2	4	\N	10	12	10	\N	\N
141	27	DSK00002	Asus Zenbook duo	\N	22	ASIGNACION MASIVA	1	2025-09-13 02:26:51.02231	2	4	\N	10	12	10	\N	\N
142	3	IMP00001	Epson EcoTank L3250	\N	30	ASIGNACION MASIVA	1	2025-09-13 02:26:51.02231	2	4	\N	10	12	10	\N	\N
145	23	ROU00001	TP-Link 1234Y	\N	26	ASIGNACION MASIVA	1	2025-09-13 02:26:51.02231	2	4	\N	10	12	10	\N	\N
146	4	PFC00002	Teclado 1234h	\N	19	ASIGNACION MASIVA	1	2025-09-13 02:26:51.02231	2	4	\N	10	12	10	\N	\N
147	28	DSK00001	HP ProBook 440 G9	\N	22	ASIGNACION MASIVA	1	2025-09-13 02:26:51.02231	2	4	\N	10	12	10	\N	\N
148	25	TIP00001	Motorola 678	\N	35	ASIGNACION MASIVA	1	2025-09-13 02:26:51.02231	2	4	\N	10	12	10	\N	\N
149	21	NBK00004	Macbook Pro	\N	22	ASIGNACION MASIVA	1	2025-09-13 02:26:51.02231	2	4	\N	10	12	10	\N	\N
150	19	SMP00001	Iphone 13	\N	36	ASIGNACION MASIVA	1	2025-09-13 02:26:51.02231	2	4	\N	10	12	10	\N	\N
151	2	NBK00002	Dell Latitude 5440	\N	22	ASIGNACION MASIVA	1	2025-09-13 02:26:51.02231	2	4	\N	10	12	10	\N	\N
152	26	PER00001	Mouse Powershift	\N	19	ASIGNACION MASIVA	1	2025-09-13 02:26:51.02231	2	4	\N	10	12	10	\N	\N
153	5	PFC00001	Mouse	\N	19		1	2025-09-13 02:39:23.996664	2	4	\N	12	10	\N	\N	10
154	1	NBK00003	HP ProBook 440 G9	\N	22		1	2025-09-13 02:42:35.600079	2	4	\N	14	10	\N	\N	\N
61	28	DSK00001	HP ProBook 440 G9	\N	42	DESASIGNACION MASIVA	1	2025-09-13 01:02:36.380732	1	\N	\N	11	9	\N	\N	5
63	23	ROU00001	TP-Link 1234Y	\N	42	DESASIGNACION MASIVA	1	2025-09-13 01:03:07.641713	1	\N	\N	11	9	\N	\N	2
65	18	NBK00001	Asus Zenbook duo	\N	42	DESASIGNACION MASIVA	1	2025-09-13 01:03:07.641713	1	\N	\N	11	9	\N	\N	10
14	1	NBK00003	HP ProBook 440 G9	Notebook	42	Cambio de responsable	\N	2025-09-04 21:12:56.479174	1	6		9	11	5		\N
324	35	PFC00004	Mouse	\N	47	DESASIGNACION MASIVA	1	2025-09-25 11:41:01.180245	1	\N	\N	11	9	\N	\N	15
325	37	NBK00007	Olidata	\N	49	DESASIGNACION MASIVA	1	2025-09-25 11:41:01.180245	1	\N	\N	11	9	\N	\N	12
338	35	PFC00004	Mouse	\N	47		1	2025-09-25 12:52:20.428702	1	6	\N	11	9	\N	\N	1
169	5	PFC00001	Mouse	\N	19	ASIGNACION MASIVA	1	2025-09-13 05:01:34.637105	2	5	\N	12	12	2	\N	2
170	1	NBK00003	HP ProBook 440 G9	\N	22	ASIGNACION MASIVA	1	2025-09-13 05:01:34.637105	2	5	\N	12	12	2	\N	2
171	5	PFC00001	Mouse	\N	19	DESASIGNACION MASIVA	1	2025-09-13 05:01:48.182173	2	\N	\N	10	10	\N	\N	\N
172	1	NBK00003	HP ProBook 440 G9	\N	22	DESASIGNACION MASIVA	1	2025-09-13 05:01:48.182173	2	\N	\N	10	10	\N	\N	\N
173	27	DSK00002	Asus Zenbook duo	\N	22	DESASIGNACION MASIVA	1	2025-09-13 05:01:48.182173	2	\N	\N	10	10	\N	\N	\N
174	19	SMP00001	Iphone 13	\N	36	DESASIGNACION MASIVA	1	2025-09-13 05:01:48.182173	2	\N	\N	10	10	\N	\N	\N
175	2	NBK00002	Dell Latitude 5440	\N	22	DESASIGNACION MASIVA	1	2025-09-13 05:01:48.182173	2	\N	\N	10	10	\N	\N	\N
176	5	PFC00001	Mouse	\N	19	ASIGNACION MASIVA	1	2025-09-13 05:02:13.181224	2	4	\N	12	12	3	\N	3
177	1	NBK00003	HP ProBook 440 G9	\N	22	ASIGNACION MASIVA	1	2025-09-13 05:02:13.181224	2	4	\N	12	12	3	\N	3
178	27	DSK00002	Asus Zenbook duo	\N	22	ASIGNACION MASIVA	1	2025-09-13 05:02:13.181224	2	4	\N	12	12	3	\N	3
179	19	SMP00001	Iphone 13	\N	36	ASIGNACION MASIVA	1	2025-09-13 05:02:13.181224	2	4	\N	12	12	3	\N	3
180	2	NBK00002	Dell Latitude 5440	\N	22	ASIGNACION MASIVA	1	2025-09-13 05:02:13.181224	2	4	\N	12	12	3	\N	3
181	5	PFC00001	Mouse	\N	19	DESASIGNACION MASIVA	1	2025-09-13 05:02:47.379245	2	\N	\N	10	10	\N	\N	\N
182	1	NBK00003	HP ProBook 440 G9	\N	22	DESASIGNACION MASIVA	1	2025-09-13 05:02:47.379245	2	\N	\N	10	10	\N	\N	\N
183	27	DSK00002	Asus Zenbook duo	\N	22	DESASIGNACION MASIVA	1	2025-09-13 05:02:47.379245	2	\N	\N	10	10	\N	\N	\N
184	19	SMP00001	Iphone 13	\N	36	DESASIGNACION MASIVA	1	2025-09-13 05:02:47.379245	2	\N	\N	10	10	\N	\N	\N
185	2	NBK00002	Dell Latitude 5440	\N	22	DESASIGNACION MASIVA	1	2025-09-13 05:02:47.379245	2	\N	\N	10	10	\N	\N	\N
186	5	PFC00001	Mouse	\N	19	ASIGNACION MASIVA	1	2025-09-13 05:05:30.223888	2	4	\N	12	12	10	\N	10
187	1	NBK00003	HP ProBook 440 G9	\N	22	ASIGNACION MASIVA	1	2025-09-13 05:05:30.223888	2	4	\N	12	12	10	\N	10
188	27	DSK00002	Asus Zenbook duo	\N	22	ASIGNACION MASIVA	1	2025-09-13 05:05:30.223888	2	4	\N	12	12	10	\N	10
189	19	SMP00001	Iphone 13	\N	36	ASIGNACION MASIVA	1	2025-09-13 05:05:30.223888	2	4	\N	12	12	10	\N	10
190	2	NBK00002	Dell Latitude 5440	\N	22	ASIGNACION MASIVA	1	2025-09-13 05:05:30.223888	2	4	\N	12	12	10	\N	10
191	5	PFC00001	Mouse	\N	19	DESASIGNACION MASIVA	1	2025-09-13 05:06:15.57012	2	\N	\N	10	10	\N	\N	\N
192	1	NBK00003	HP ProBook 440 G9	\N	22	DESASIGNACION MASIVA	1	2025-09-13 05:06:15.57012	2	\N	\N	10	10	\N	\N	\N
193	27	DSK00002	Asus Zenbook duo	\N	22	DESASIGNACION MASIVA	1	2025-09-13 05:06:15.57012	2	\N	\N	10	10	\N	\N	\N
194	19	SMP00001	Iphone 13	\N	36	DESASIGNACION MASIVA	1	2025-09-13 05:06:15.57012	2	\N	\N	10	10	\N	\N	\N
195	2	NBK00002	Dell Latitude 5440	\N	22	DESASIGNACION MASIVA	1	2025-09-13 05:06:15.57012	2	\N	\N	10	10	\N	\N	\N
34	27	DSK00002	Asus Zenbook duo	\N	22		1	2025-09-08 23:58:40.812269	2	4	\N	\N	10	3	\N	\N
33	26	PER0001	Mouse	\N	42		1	2025-09-08 13:32:00.649941	1	1	\N	\N	9	\N	\N	\N
326	38	PRO00001	Protocolo	\N	40		\N	2025-09-25 11:42:47.659028	1	6	\N	\N	\N	1	\N	\N
339	38	PRO00001	Protocolo	\N	40	OBSERVACIONES	1	2025-09-25 12:52:56.157474	1	6	\N	\N	\N	1	Fue revisado y necesita ajustes.	1
252	1	NBK00003	HP ProBook 440 G9	\N	22		1	2025-09-15 12:04:46.033863	2	5	\N	10	12	2	\N	\N
253	2	NBK00002	Dell Latitude 5440	\N	22		1	2025-09-15 12:04:56.76191	2	4	\N	10	12	3	\N	\N
254	1	NBK00003	HP ProBook 440 G9	\N	22		1	2025-09-15 12:11:29.640521	2	5	\N	12	14	2	\N	2
255	1	NBK00003	HP ProBook 440 G9	\N	22	OBSERVACIONES	\N	2025-09-15 14:12:41.843362	2	5	\N	14	14	2	Cambio de observaciones.\nAntes: —\nAhora: Color defectuoso	2
280	1	NBK00003	HP ProBook 440 G9	\N	22	DESASIGNACION MASIVA	1	2025-09-15 19:34:22.837789	2	\N	\N	14	10	\N	\N	2
281	2	NBK00002	Dell Latitude 5440	\N	22	DESASIGNACION MASIVA	1	2025-09-15 19:34:22.837789	2	\N	\N	12	10	\N	\N	3
282	1	NBK00003	HP ProBook 440 G9	\N	22	OBSERVACIONES	1	2025-09-15 19:35:03.655217	2	5	\N	10	10	\N	Color defectuoso\r\n\r\nSe arreglo el color	\N
72	27	DSK00002	Asus Zenbook duo	\N	42	ASIGNACION MASIVA	1	2025-09-13 01:03:38.808294	1	6	\N	9	11	5	\N	\N
73	25	TIP00001	Motorola 678	\N	42	ASIGNACION MASIVA	1	2025-09-13 01:03:38.808294	1	6	\N	9	11	5	\N	\N
223	3	IMP00001	Epson EcoTank L3250	\N	42	ASIGNACION MASIVA	1	2025-09-13 06:22:15.701545	1	1	\N	9	11	1	\N	\N
225	25	TIP00001	Motorola 678	\N	42	ASIGNACION MASIVA	1	2025-09-13 06:22:15.701545	1	1	\N	9	11	1	\N	\N
226	26	PER00001	Mouse Powershift	\N	42	ASIGNACION MASIVA	1	2025-09-13 06:22:15.701545	1	1	\N	9	11	1	\N	\N
305	33	NBK000007	HP ProBook 440 G9	\N	22	OBSERVACIONES	\N	2025-09-19 22:17:50.021197	2	5	\N	10	10	\N	Pantalla tora Arreglar	\N
285	31	IMP00002	Epson EcoTank L3250	\N	42	OBSERVACIONES	1	2025-09-15 21:02:49.669524	1	3	\N	9	9	\N	Articulo nuevo con todos sus componentes	\N
327	38	PRO00001	Protocolo	\N	40		\N	2025-09-25 11:44:45.312462	1	6	\N	\N	\N	11	\N	1
340	38	PRO00001	Protocolo	\N	40		1	2025-09-25 13:01:50.006323	1	6	\N	\N	11	1	\N	1
341	38	PRO00001	Protocolo	\N	40	EDICION	1	2025-09-25 13:01:50.013758	1	6	\N	\N	11	1	Edición desde CRUD	1
\.


--
-- TOC entry 5310 (class 0 OID 17190)
-- Dependencies: 270
-- Data for Name: historial_mantenciones; Type: TABLE DATA; Schema: inventario; Owner: inventario_user
--

COPY inventario.historial_mantenciones (id_historial, id_mantencion, fecha_evento, accion, usuario_app, detalle, old_values, new_values, id_empresa) FROM stdin;
18	12	2025-09-09 21:04:56.853947	CREAR	\N	Creaci¢n de mantenci¢n	\N	{"fecha": "2025-10-10", "fecha_fin": null, "id_equipo": 19, "resultado": null, "costo_total": 0.00, "descripcion": "a", "fecha_inicio": null, "horas_hombre": 0.00, "id_prioridad": 2, "observaciones": null, "tiempo_downtime": null, "fecha_programada": null, "id_tipo_mantencion": 1, "id_estado_mantencion": 1, "id_empleado_responsable": null, "id_empleado_solicitante": null}	2
1	4	2025-09-09 14:39:45.339494	CREAR	\N	Creaci¢n de mantenci¢n	\N	{"fecha": "2025-09-25", "fecha_fin": null, "id_equipo": 19, "resultado": null, "costo_total": 0.00, "descripcion": "Actualización", "fecha_inicio": null, "horas_hombre": 0.00, "id_prioridad": null, "observaciones": null, "tiempo_downtime": null, "fecha_programada": null, "id_tipo_mantencion": null, "id_estado_mantencion": 1, "id_empleado_responsable": null, "id_empleado_solicitante": null}	2
16	10	2025-09-09 20:09:23.265363	ACTUALIZAR	\N	\N	{"descripcion": "s"}	{"descripcion": "Ajustes internos"}	1
7	8	2025-09-09 19:54:13.770514	CREAR	\N	Creaci¢n de mantenci¢n	\N	{"fecha": "2025-09-25", "fecha_fin": null, "id_equipo": 4, "resultado": null, "costo_total": 0.00, "descripcion": "prueba1", "fecha_inicio": null, "horas_hombre": 0.00, "id_prioridad": 1, "observaciones": null, "tiempo_downtime": null, "fecha_programada": null, "id_tipo_mantencion": 1, "id_estado_mantencion": 1, "id_empleado_responsable": null, "id_empleado_solicitante": null}	1
9	8	2025-09-09 19:56:01.010828	ACTUALIZAR	\N	Cambio de estado	{"id_estado_mantencion": 1}	{"id_estado_mantencion": 2}	1
10	8	2025-09-09 19:56:27.543406	ACTUALIZAR	\N	Cambio de estado	{"id_estado_mantencion": 2}	{"id_estado_mantencion": 3}	1
11	9	2025-09-09 19:57:57.809871	CREAR	\N	Creaci¢n de mantenci¢n	\N	{"fecha": "2025-09-04", "fecha_fin": null, "id_equipo": 19, "resultado": null, "costo_total": 0.00, "descripcion": "swss", "fecha_inicio": null, "horas_hombre": 0.00, "id_prioridad": 1, "observaciones": null, "tiempo_downtime": null, "fecha_programada": null, "id_tipo_mantencion": 1, "id_estado_mantencion": 1, "id_empleado_responsable": null, "id_empleado_solicitante": null}	1
12	9	2025-09-09 19:58:09.877103	ACTUALIZAR	\N	Cambio de estado	{"id_estado_mantencion": 1}	{"id_estado_mantencion": 2}	1
13	9	2025-09-09 20:00:18.554586	ELIMINAR	\N	Eliminaci¢n de mantenci¢n	{"fecha": "2025-09-04", "fecha_fin": null, "id_equipo": 19, "resultado": null, "costo_total": 0.00, "descripcion": "swss", "fecha_inicio": null, "horas_hombre": 0.00, "id_prioridad": 1, "observaciones": null, "tiempo_downtime": null, "fecha_programada": null, "id_tipo_mantencion": 1, "id_estado_mantencion": 2, "id_empleado_responsable": null, "id_empleado_solicitante": null}	\N	1
14	8	2025-09-09 20:00:47.019326	ELIMINAR	\N	Eliminaci¢n de mantenci¢n	{"fecha": "2025-09-25", "fecha_fin": null, "id_equipo": 4, "resultado": null, "costo_total": 0.00, "descripcion": "prueba1", "fecha_inicio": null, "horas_hombre": 0.00, "id_prioridad": 1, "observaciones": null, "tiempo_downtime": null, "fecha_programada": null, "id_tipo_mantencion": 1, "id_estado_mantencion": 3, "id_empleado_responsable": null, "id_empleado_solicitante": null}	\N	1
15	10	2025-09-09 20:03:03.131862	CREAR	\N	Creaci¢n de mantenci¢n	\N	{"fecha": "2025-09-04", "fecha_fin": null, "id_equipo": 18, "resultado": null, "costo_total": 0.00, "descripcion": "s", "fecha_inicio": null, "horas_hombre": 0.00, "id_prioridad": 2, "observaciones": null, "tiempo_downtime": null, "fecha_programada": null, "id_tipo_mantencion": 2, "id_estado_mantencion": 4, "id_empleado_responsable": null, "id_empleado_solicitante": null}	1
4	5	2025-09-09 18:40:09.712893	CREAR	\N	Creaci¢n de mantenci¢n	\N	{"fecha": "2025-10-10", "fecha_fin": null, "id_equipo": 22, "resultado": null, "costo_total": 0.00, "descripcion": "Cambio Pantalla", "fecha_inicio": null, "horas_hombre": 0.00, "id_prioridad": 1, "observaciones": null, "tiempo_downtime": null, "fecha_programada": null, "id_tipo_mantencion": 2, "id_estado_mantencion": 1, "id_empleado_responsable": null, "id_empleado_solicitante": null}	1
17	11	2025-09-09 20:59:03.159529	CREAR	\N	Creaci¢n de mantenci¢n	\N	{"fecha": "2025-09-04", "fecha_fin": null, "id_equipo": 4, "resultado": null, "costo_total": 0.00, "descripcion": "a", "fecha_inicio": null, "horas_hombre": 0.00, "id_prioridad": 1, "observaciones": null, "tiempo_downtime": null, "fecha_programada": null, "id_tipo_mantencion": 1, "id_estado_mantencion": 1, "id_empleado_responsable": null, "id_empleado_solicitante": null}	1
6	7	2025-09-09 19:30:16.101831	CREAR	\N	Creaci¢n de mantenci¢n	\N	{"fecha": "2025-09-10", "fecha_fin": null, "id_equipo": 4, "resultado": null, "costo_total": 0.00, "descripcion": "Cambio de teclas", "fecha_inicio": null, "horas_hombre": 0.00, "id_prioridad": 3, "observaciones": null, "tiempo_downtime": null, "fecha_programada": null, "id_tipo_mantencion": 4, "id_estado_mantencion": 9, "id_empleado_responsable": null, "id_empleado_solicitante": null}	1
5	6	2025-09-09 19:26:27.900278	CREAR	\N	Creaci¢n de mantenci¢n	\N	{"fecha": "2025-09-25", "fecha_fin": null, "id_equipo": 2, "resultado": null, "costo_total": 0.00, "descripcion": "Mantención y Limpieza", "fecha_inicio": null, "horas_hombre": 0.00, "id_prioridad": 2, "observaciones": null, "tiempo_downtime": null, "fecha_programada": null, "id_tipo_mantencion": 1, "id_estado_mantencion": 1, "id_empleado_responsable": null, "id_empleado_solicitante": null}	1
3	1	2025-09-09 16:30:03.757975	ACTUALIZAR	\N	Cambio de estado	{"id_estado_mantencion": 4}	{"id_estado_mantencion": 2}	1
2	1	2025-09-09 16:29:14.391234	ACTUALIZAR	\N	Cambio de estado	{"descripcion": "Revisión general y upgrade de RAM", "id_estado_mantencion": 1}	{"descripcion": "Mantención realizada con exito", "id_estado_mantencion": 4}	1
\.


--
-- TOC entry 5312 (class 0 OID 17224)
-- Dependencies: 273
-- Data for Name: historial_mantenciones_log; Type: TABLE DATA; Schema: inventario; Owner: inventario_user
--

COPY inventario.historial_mantenciones_log (id_evento, id_mantencion, fecha_evento, accion, detalle, usuario_app_username, id_equipo, etiqueta, equipo_nombre, tipo_mantencion, prioridad, estado_actual, responsable_nombre, solicitante_nombre, descripcion, id_empresa) FROM stdin;
4	13	2025-09-09 21:24:08.710467	CREAR	Alta de mantención	17.090.533-4	19	SMP00001	Iphone 13	Preventiva	Baja	Programada			wewe	2
5	13	2025-09-09 21:24:31.255695	ACTUALIZAR	Edición de mantención	17.090.533-4	19	SMP00001	Iphone 13	Correctiva	Baja	Programada			kgkgkg	2
6	1	2025-09-09 21:25:05.415375	ACTUALIZAR	Edición de mantención	17.090.533-4	2	NBK00002	Dell Latitude 5440	Instalación	Crítica	Cancelada			Mantención realizada con exito	1
7	13	2025-09-10 13:39:32.88047	ACTUALIZAR	Edición de mantención	17.090.533-4	19	SMP00001	Iphone 13	Correctiva	Baja	Programada			Cambio Altavoz	2
8	12	2025-09-10 13:40:10.566085	ACTUALIZAR	Edición de mantención	17.090.533-4	19	SMP00001	Iphone 13	Instalación	Media	Programada			Actualización	2
9	14	2025-09-10 14:42:01.051547	CREAR	Alta de mantención	17.090.533-4	19	SMP00001	Iphone 13	Preventiva	Alta	Programada			p	2
10	1	2025-09-10 15:28:51.925119	ACTUALIZAR	Edición de mantención	17.090.533-4	2	NBK00002	Dell Latitude 5440	Instalación	Crítica	Cancelada		hernanmendez	Mantención realizada con exito	1
11	1	2025-09-10 15:28:59.725673	ACTUALIZAR	Edición de mantención	17.090.533-4	2	NBK00002	Dell Latitude 5440	Instalación	Crítica	Cancelada		\N	Mantención realizada con exito	1
12	15	2025-09-10 15:42:02.651812	CREAR	Alta de mantención	17.090.533-4	19	SMP00001	Iphone 13	Instalación	Media	Completada	Pedro Perez Poblete	Hernán Méndez Sepúlveda	jk	2
13	1	2025-09-10 15:55:52.572384	ACTUALIZAR	Edición de mantención	17.090.533-4	2	NBK00002	Dell Latitude 5440	Instalación	Crítica	Programada	Hernán Méndez Sepúlveda	\N	Mantención	1
14	1	2025-09-10 16:08:56.434772	ACTUALIZAR	Edición de mantención	17.090.533-4	2	NBK00002	Dell Latitude 5440	Instalación	Crítica	Terminada	Hernán Méndez Sepúlveda	\N	Mantención	1
15	1	2025-09-15 18:37:42.961437	ACTUALIZAR	Edición de mantención	17.090.533-4	2	NBK00002	Dell Latitude 5440	Instalación	Crítica	Terminada	Camila Castro Carmona	\N	Mantención	\N
16	4	2025-09-15 18:56:16.64299	ACTUALIZAR	Edición de mantención	17.090.533-4	19	SMP00001	Iphone 13	Correctiva	Baja	Programada	Diego Rojas Castro	\N	Actualización	\N
17	1	2025-09-15 19:04:28.789561	ACTUALIZAR	Edición de mantención	17.090.533-4	2	NBK00002	Dell Latitude 5440	Instalación	Crítica	Completada	Camila Castro Carmona	\N	Mantención	\N
18	1	2025-09-15 19:33:38.027087	ACTUALIZAR	Edición de mantención	17.090.533-4	2	NBK00002	Dell Latitude 5440	Instalación	Crítica	Programada	Camila Castro Carmona	\N	Mantención	\N
19	15	2025-09-15 19:33:47.574841	ACTUALIZAR	Edición de mantención	17.090.533-4	19	SMP00001	Iphone 13	Instalación	Media	Programada		Hernán Méndez Sepúlveda	jk	\N
20	2	2025-09-15 21:01:17.482779	ACTUALIZAR	Edición de mantención	17.090.533-4	3	IMP00001	Epson EcoTank L3250	Correctiva	Alta	Programada	Cristian Rojas Medina	\N	Limpieza de cabezales	\N
22	17	2025-09-16 11:31:44.596606	CREAR	Alta de mantención	17.090.533-4	18	NBK00001	Asus Zenbook duo	Preventiva	Media	Programada	Hernán Méndez Sepúlveda	Hernán Méndez Sepúlveda	Total	\N
23	18	2025-09-16 11:42:53.135391	CREAR	Alta de mantención	17.090.533-4	18	NBK00001	Asus Zenbook duo	Preventiva	Baja	Programada	María Contreras Torres	Hernán Méndez Sepúlveda	Prueba	\N
24	19	2025-09-16 11:49:59.688199	CREAR	Alta de mantención	17.090.533-4	18	NBK00001	Asus Zenbook duo	Preventiva	Baja	Programada	Cristian Rojas Medina	Hernán Méndez Sepúlveda		\N
25	20	2025-09-16 11:58:22.017281	CREAR	Alta de mantención	17.090.533-4	18	NBK00001	Asus Zenbook duo	Preventiva	Baja	Programada	Pedro Perez Poblete	Hernán Méndez Sepúlveda		\N
26	21	2025-09-16 12:04:37.92359	CREAR	Alta de mantención	17.090.533-4	31	IMP00002	Epson EcoTank L3250	Preventiva	Baja	Terminada	María Contreras Torres	Hernán Méndez Sepúlveda		\N
27	22	2025-09-16 12:30:34.694614	CREAR	Alta de mantención	Hernán Méndez Sepúlveda	18	NBK00001	Asus Zenbook duo	Preventiva	Baja	Programada	Cristian Rojas Medina	Hernán Méndez Sepúlveda		\N
28	22	2025-09-23 12:38:42.558306	ACTUALIZAR	Edición de mantención	Hernán Méndez Sepúlveda	18	NBK00001	Asus Zenbook duo	Preventiva	Baja	Programada	Cristian Rojas Medina	Hernán Méndez Sepúlveda	XXXXXXX	\N
29	22	2025-09-25 11:53:07.411799	ACTUALIZAR	Edición de mantención	Hernán Méndez Sepúlveda	18	NBK00001	Asus Zenbook duo	Preventiva	Baja	Completada	Cristian Rojas Medina	Hernán Méndez Sepúlveda	XXXXXXX	\N
\.


--
-- TOC entry 5276 (class 0 OID 16770)
-- Dependencies: 236
-- Data for Name: mantencion; Type: TABLE DATA; Schema: inventario; Owner: inventario_user
--

COPY inventario.mantencion (id_mantencion, id_equipo, id_estado_mantencion, fecha, descripcion, id_tipo_mantencion, id_prioridad, fecha_programada, fecha_inicio, fecha_fin, id_empleado_responsable, id_empleado_solicitante, costo_total, horas_hombre, resultado, observaciones, tiempo_downtime, responsable_id, solicitante_user_id, id_empresa) FROM stdin;
14	19	12	2025-09-10	p	6	10	\N	\N	\N	\N	\N	0.00	0.00	\N	\N	\N	9	\N	2
12	19	12	2025-10-10	Actualización	10	8	\N	\N	\N	\N	\N	0.00	0.00	\N	\N	\N	\N	\N	2
13	19	12	2025-09-10	Cambio Altavoz	8	6	\N	\N	\N	\N	\N	0.00	0.00	\N	\N	\N	\N	\N	2
10	18	17	2025-09-04	Ajustes internos	7	7	\N	\N	\N	\N	\N	0.00	0.00	\N	\N	\N	\N	\N	1
11	4	11	2025-09-04	a	5	5	\N	\N	\N	\N	\N	0.00	0.00	\N	\N	\N	\N	\N	1
7	4	19	2025-09-10	Cambio de teclas	11	9	\N	\N	\N	\N	\N	0.00	0.00	\N	\N	\N	\N	\N	1
6	2	11	2025-09-25	Mantención y Limpieza	5	7	\N	\N	\N	\N	\N	0.00	0.00	\N	\N	\N	\N	\N	1
4	19	12	\N	Actualización	8	6	\N	\N	\N	\N	\N	0.00	0.00	\N	\N	\N	3	\N	2
1	2	11	\N	Mantención	9	11	\N	\N	\N	\N	\N	0.00	0.00	\N	\N	\N	10	\N	1
15	19	12	\N	jk	10	8	\N	\N	\N	\N	\N	0.00	0.00	\N	\N	\N	\N	2	2
2	3	11	2025-09-25	Limpieza de cabezales	7	9	\N	\N	\N	\N	\N	0.00	0.00	\N	\N	\N	11	\N	1
3	18	19	2025-09-25	Actualización de memoria RAM	\N	\N	\N	\N	\N	\N	\N	0.00	0.00	\N	\N	\N	\N	\N	1
17	18	11	2025-09-30	Total	5	7	\N	\N	\N	\N	\N	0.00	0.00	\N	\N	\N	1	2	1
22	18	15	\N	XXXXXXX	5	5	\N	\N	\N	\N	\N	0.00	0.00	\N	\N	\N	11	2	1
18	18	11	2025-09-27	Prueba	5	5	\N	\N	\N	\N	\N	0.00	0.00	\N	\N	\N	9	2	1
19	18	11	2025-09-18		5	5	\N	\N	\N	\N	\N	0.00	0.00	\N	\N	\N	11	2	1
20	18	11	2025-09-24		5	5	\N	\N	\N	\N	\N	0.00	0.00	\N	\N	\N	5	2	1
21	31	13	2025-09-26		5	5	\N	\N	\N	\N	\N	0.00	0.00	\N	\N	\N	9	2	1
\.


--
-- TOC entry 5278 (class 0 OID 16777)
-- Dependencies: 238
-- Data for Name: marca; Type: TABLE DATA; Schema: inventario; Owner: inventario_user
--

COPY inventario.marca (id_marca, nombre_marca, id_empresa) FROM stdin;
41	Asus	1
42	Logitech	2
43	Lenovo	2
44	Isuzu	1
45	ZTE	2
46	JBL	2
47	Dell	1
48	Apple	2
49	Epson	2
50	HP	1
51	TP-Link	1
52	Genérico	1
53	Motorola	2
54	Genérico	2
55	Motorola	1
56	HP	2
57	Epson	1
58	TP-Link	2
59	JBL	1
60	Dell	2
61	Apple	1
62	Logitech	1
63	Lenovo	1
64	Asus	2
65	ZTE	1
66	Isuzu	2
67	Panasonic	\N
69	Toyota	1
70	Nissan	2
68	Chevrolet	1
71	Intel	1
72	Sony	1
73	Pentium	2
74	Windows	1
75	Olidata	1
76	N/A	1
\.


--
-- TOC entry 5308 (class 0 OID 17153)
-- Dependencies: 268
-- Data for Name: prioridad_mantencion; Type: TABLE DATA; Schema: inventario; Owner: inventario_user
--

COPY inventario.prioridad_mantencion (id_prioridad, nombre, sla_horas, id_empresa) FROM stdin;
5	Baja	0	1
6	Baja	0	2
7	Media	0	1
8	Media	0	2
9	Alta	0	1
10	Alta	0	2
11	Crítica	0	1
12	Crítica	0	2
\.


--
-- TOC entry 5280 (class 0 OID 16781)
-- Dependencies: 240
-- Data for Name: proveedor; Type: TABLE DATA; Schema: inventario; Owner: inventario_user
--

COPY inventario.proveedor (id_proveedor, nombre_proveedor, rut_proveedor, id_empresa) FROM stdin;
5	Abastecimientos S.A.	76.111.111-1	1
6	Abastecimientos S.A.	76.111.111-1	2
7	Digitronic Ltda.	77.222.222-2	1
8	Digitronic Ltda.	77.222.222-2	2
9	TecnoPro SpA	78.333.333-3	1
10	TecnoPro SpA	78.333.333-3	2
11	UCM	77.777.777-7	1
12	UCM	77.777.777-7	2
13	PC Factory	79.888.999-6	1
14	Falabella	77.999.555-3	2
\.


--
-- TOC entry 5282 (class 0 OID 16785)
-- Dependencies: 242
-- Data for Name: tipo_equipo; Type: TABLE DATA; Schema: inventario; Owner: inventario_user
--

COPY inventario.tipo_equipo (id_tipo_equipo, tipo_equipo, id_empresa) FROM stdin;
19	Periférico	2
21	Cuentas Contables	2
22	Notebook	2
26	Router	2
30	Impresora	2
33	Mobiliario	2
34	Monitor	2
35	Teléfono IP	2
36	Smartphone	2
40	Información	1
41	Software	1
42	Hardware	1
44	Información	2
45	Software	2
46	Hardware	2
47	Periférico	1
48	Impresora/Scanner	1
49	Notebook	1
\.


--
-- TOC entry 5306 (class 0 OID 17144)
-- Dependencies: 266
-- Data for Name: tipo_mantencion; Type: TABLE DATA; Schema: inventario; Owner: inventario_user
--

COPY inventario.tipo_mantencion (id_tipo_mantencion, nombre, id_empresa) FROM stdin;
5	Preventiva	1
6	Preventiva	2
7	Correctiva	1
8	Correctiva	2
9	Instalación	1
10	Instalación	2
11	Garantía	1
12	Garantía	2
13	Obligatoria	1
\.


--
-- TOC entry 5284 (class 0 OID 16789)
-- Dependencies: 244
-- Data for Name: auth_group; Type: TABLE DATA; Schema: public; Owner: inventario_user
--

COPY public.auth_group (id, name) FROM stdin;
1	rol_admin
2	rol_usuario
3	rol_invitado
\.


--
-- TOC entry 5286 (class 0 OID 16793)
-- Dependencies: 246
-- Data for Name: auth_group_permissions; Type: TABLE DATA; Schema: public; Owner: inventario_user
--

COPY public.auth_group_permissions (id, group_id, permission_id) FROM stdin;
1	1	25
2	1	26
3	1	27
4	1	28
5	1	29
6	1	30
7	1	31
8	1	32
9	1	33
10	1	34
11	1	35
12	1	36
13	1	37
14	1	38
15	1	39
16	1	40
17	1	41
18	1	42
19	1	43
20	1	44
21	1	45
22	1	46
23	1	47
24	1	48
25	1	49
26	1	50
27	1	51
28	1	52
29	1	53
30	1	54
31	1	55
32	1	56
33	1	57
34	1	58
35	1	59
36	1	60
37	1	61
38	1	62
39	1	63
40	1	64
41	1	65
42	1	66
43	1	67
44	1	68
45	1	69
46	1	70
47	1	71
48	1	72
49	1	73
50	1	74
51	1	75
52	1	76
53	2	25
54	2	26
55	2	28
56	2	29
57	2	30
58	2	32
59	2	33
60	2	34
61	2	36
62	2	37
63	2	38
64	2	40
65	2	41
66	2	42
67	2	44
68	2	45
69	2	46
70	2	48
71	2	49
72	2	50
73	2	52
74	2	53
75	2	54
76	2	56
77	2	57
78	2	58
79	2	60
80	2	61
81	2	62
82	2	64
83	2	65
84	2	66
85	2	68
86	2	69
87	2	70
88	2	72
89	2	73
90	2	74
91	2	76
92	3	32
93	3	64
94	3	36
95	3	68
96	3	40
97	3	72
98	3	44
99	3	76
100	3	60
101	3	48
102	3	52
103	3	56
104	3	28
105	2	77
106	2	78
109	1	77
110	1	78
\.


--
-- TOC entry 5288 (class 0 OID 16797)
-- Dependencies: 248
-- Data for Name: auth_permission; Type: TABLE DATA; Schema: public; Owner: inventario_user
--

COPY public.auth_permission (id, name, content_type_id, codename) FROM stdin;
1	Can add log entry	1	add_logentry
2	Can change log entry	1	change_logentry
3	Can delete log entry	1	delete_logentry
4	Can view log entry	1	view_logentry
5	Can add permission	2	add_permission
6	Can change permission	2	change_permission
7	Can delete permission	2	delete_permission
8	Can view permission	2	view_permission
9	Can add group	3	add_group
10	Can change group	3	change_group
11	Can delete group	3	delete_group
12	Can view group	3	view_group
13	Can add user	4	add_user
14	Can change user	4	change_user
15	Can delete user	4	delete_user
16	Can view user	4	view_user
17	Can add content type	5	add_contenttype
18	Can change content type	5	change_contenttype
19	Can delete content type	5	delete_contenttype
20	Can view content type	5	view_contenttype
21	Can add session	6	add_session
22	Can change session	6	change_session
23	Can delete session	6	delete_session
24	Can view session	6	view_session
25	Can add atributos equipo	8	add_atributosequipo
26	Can change atributos equipo	8	change_atributosequipo
27	Can delete atributos equipo	8	delete_atributosequipo
28	Can view atributos equipo	8	view_atributosequipo
29	Can add departamento	15	add_departamento
30	Can change departamento	15	change_departamento
31	Can delete departamento	15	delete_departamento
32	Can view departamento	15	view_departamento
33	Can add detalle factura	13	add_detallefactura
34	Can change detalle factura	13	change_detallefactura
35	Can delete detalle factura	13	delete_detallefactura
36	Can view detalle factura	13	view_detallefactura
37	Can add empleado	9	add_empleado
38	Can change empleado	9	change_empleado
39	Can delete empleado	9	delete_empleado
40	Can view empleado	9	view_empleado
41	Can add empresa	16	add_empresa
42	Can change empresa	16	change_empresa
43	Can delete empresa	16	delete_empresa
44	Can view empresa	16	view_empresa
45	Can add equipo	10	add_equipo
46	Can change equipo	10	change_equipo
47	Can delete equipo	10	delete_equipo
48	Can view equipo	10	view_equipo
49	Can add estado equipo	12	add_estadoequipo
50	Can change estado equipo	12	change_estadoequipo
51	Can delete estado equipo	12	delete_estadoequipo
52	Can view estado equipo	12	view_estadoequipo
53	Can add estado mantencion	17	add_estadomantencion
54	Can change estado mantencion	17	change_estadomantencion
55	Can delete estado mantencion	17	delete_estadomantencion
56	Can view estado mantencion	17	view_estadomantencion
57	Can add factura	18	add_factura
58	Can change factura	18	change_factura
59	Can delete factura	18	delete_factura
60	Can view factura	18	view_factura
61	Can add mantencion	19	add_mantencion
62	Can change mantencion	19	change_mantencion
63	Can delete mantencion	19	delete_mantencion
64	Can view mantencion	19	view_mantencion
65	Can add marca	11	add_marca
66	Can change marca	11	change_marca
67	Can delete marca	11	delete_marca
68	Can view marca	11	view_marca
69	Can add proveedor	7	add_proveedor
70	Can change proveedor	7	change_proveedor
71	Can delete proveedor	7	delete_proveedor
72	Can view proveedor	7	view_proveedor
73	Can add tipo equipo	14	add_tipoequipo
74	Can change tipo equipo	14	change_tipoequipo
75	Can delete tipo equipo	14	delete_tipoequipo
76	Can view tipo equipo	14	view_tipoequipo
77	Can view HistorialEquipos	20	view_historialequipos
78	Can view HistorialMantencionesLog	21	view_historialmantencioneslog
\.


--
-- TOC entry 5290 (class 0 OID 16801)
-- Dependencies: 250
-- Data for Name: auth_user; Type: TABLE DATA; Schema: public; Owner: inventario_user
--

COPY public.auth_user (id, password, last_login, is_superuser, username, first_name, last_name, email, is_staff, is_active, date_joined) FROM stdin;
3		\N	f	16.111.222-5	Carla	Soto	carla.soto@pehuenche.cl	f	t	2025-09-18 13:46:36.327989-03
4		\N	f	12567234-6	Cristian	Rojas	cristian.rojas@galilea.cl	f	t	2025-09-18 13:46:36.340469-03
5		\N	f	33.333.333-4	Joselo	Puertas	joselo.puertas@galilea.cl	f	t	2025-09-18 13:46:36.342267-03
6		\N	f	11.111.111-1	Pedro	Perez	pedro.perez@galilea.cl	f	t	2025-09-18 13:46:36.343567-03
7		\N	f	12.121.121-2	María	Contreras	maría.contreras@galilea.cl	f	t	2025-09-18 13:46:36.344726-03
1	pbkdf2_sha256$1000000$Aid3VpJNu7e71vVoHEdUFm$zVKTwo7FWOxqYddnKXvgxwwloWzwbqaB9HMiTkSJePA=	2025-09-04 13:23:16.483587-04	t	hernanmendez	Hernán	Méndez Sepúlveda	hernan.mendez@galilea.cl	t	t	2025-08-28 09:45:54-04
11		\N	f	22.222.222-2	Mario	Ortega	mario.ortega@pehuenche.cl	f	t	2025-09-22 16:11:54.113975-03
10		\N	f	17.708.025-k	Carolina	Cárdenas	carolina.cardenas@pehuenche.cl	f	t	2025-09-19 19:26:22.120765-03
8	pbkdf2_sha256$1000000$E3Wzwr1k21eWb7dK0q7Zh2$6goasuOP8OtJTs+peMFlZcPeJjbYwO9Ux9QPnMOyC54=	2025-09-19 19:36:01.374866-03	f	18.444.555-6	Diego	Rojas	diego.rojas@pehuenche.cl	f	t	2025-09-18 13:46:36.345898-03
9	pbkdf2_sha256$1000000$DGQ6fl5JEsaAA14PostPJh$kerOzqtHQuujPZDPCGVPzcBdz21XNsHV9P5NHwpAWKs=	2025-09-24 23:23:49.638353-03	f	13.333.333-4	Camila	Castro	camila.castro@pehuenche.cl	t	t	2025-09-18 13:46:36.34702-03
12		\N	f	23.333.333-4	Arturo	Vidal	arturo.vidal@galilea.cl	f	t	2025-09-23 20:49:49.286759-03
2	pbkdf2_sha256$1000000$iZ4bIpvyHSOV2xVz0ILzTZ$rTBYbpn3iWRtZUGZKUP1HI97sDuYyE9UbSGnDJymh3E=	2025-09-25 13:21:28.721067-03	t	17.090.533-4				t	t	2025-09-05 13:16:34.987764-04
\.


--
-- TOC entry 5291 (class 0 OID 16806)
-- Dependencies: 251
-- Data for Name: auth_user_groups; Type: TABLE DATA; Schema: public; Owner: inventario_user
--

COPY public.auth_user_groups (id, user_id, group_id) FROM stdin;
1	2	1
2	3	2
3	4	2
4	5	2
5	6	2
6	7	2
7	8	2
8	9	1
11	10	2
15	11	2
21	12	2
\.


--
-- TOC entry 5294 (class 0 OID 16811)
-- Dependencies: 254
-- Data for Name: auth_user_user_permissions; Type: TABLE DATA; Schema: public; Owner: inventario_user
--

COPY public.auth_user_user_permissions (id, user_id, permission_id) FROM stdin;
1	2	1
2	2	2
3	2	3
4	2	4
5	2	5
6	2	6
7	2	7
8	2	8
9	2	9
10	2	10
11	2	11
12	2	12
13	2	13
14	2	14
15	2	15
16	2	16
17	2	17
18	2	18
19	2	19
20	2	20
21	2	21
22	2	22
23	2	23
24	2	24
25	2	25
26	2	26
27	2	27
28	2	28
29	2	29
30	2	30
31	2	31
32	2	32
33	2	33
34	2	34
35	2	35
36	2	36
37	2	37
38	2	38
39	2	39
40	2	40
41	2	41
42	2	42
43	2	43
44	2	44
45	2	45
46	2	46
47	2	47
48	2	48
49	2	49
50	2	50
51	2	51
52	2	52
53	2	53
54	2	54
55	2	55
56	2	56
57	2	57
58	2	58
59	2	59
60	2	60
61	2	61
62	2	62
63	2	63
64	2	64
65	2	65
66	2	66
67	2	67
68	2	68
69	2	69
70	2	70
71	2	71
72	2	72
73	2	73
74	2	74
75	2	75
76	2	76
\.


--
-- TOC entry 5296 (class 0 OID 16815)
-- Dependencies: 256
-- Data for Name: django_admin_log; Type: TABLE DATA; Schema: public; Owner: inventario_user
--

COPY public.django_admin_log (id, action_time, object_id, object_repr, action_flag, change_message, content_type_id, user_id) FROM stdin;
1	2025-08-28 17:28:28.70377-04	1	hernanmendez	2	[{"changed": {"fields": ["First name", "Last name", "Email address"]}}]	4	1
2	2025-08-28 17:45:16.089331-04	3	Diego Rojas Perez	2	[{"changed": {"fields": ["Apellido materno"]}}]	9	1
3	2025-08-28 17:47:40.365628-04	6	Teléfono IP	2	[]	14	1
4	2025-08-28 17:48:04.544374-04	6	Teléfono IP	2	[]	14	1
5	2025-08-28 17:48:11.226921-04	7	Camion	1	[{"added": {}}]	14	1
6	2025-08-28 17:48:14.010238-04	7	Camion	2	[]	14	1
7	2025-08-28 17:49:01.243456-04	5	Camion · Tonelaje = 20.000.000	2	[{"changed": {"fields": ["Id tipo equipo", "Atributo", "Valor"]}}]	8	1
8	2025-08-28 17:49:14.988651-04	5	Camion · Tonelaje = 20000000	2	[{"changed": {"fields": ["Valor"]}}]	8	1
9	2025-08-28 17:55:41.941905-04	6	Logitech	1	[{"added": {}}]	11	1
10	2025-08-28 17:55:54.659985-04	8	Periferico	1	[{"added": {}}]	14	1
11	2025-08-28 17:56:14.355782-04	4	Teclado - Logitech / Periferico	1	[{"added": {}}]	10	1
12	2025-08-28 17:58:01.992275-04	3	Diego Rojas Castro	2	[{"changed": {"fields": ["Apellido materno"]}}]	9	1
13	2025-08-29 11:36:59.622075-04	8	María Contreras Torres	2	[]	9	1
14	2025-08-29 11:37:41.869956-04	3	Nokia S.A	2	[{"changed": {"fields": ["Nombre empresa", "Giro"]}}]	16	1
\.


--
-- TOC entry 5298 (class 0 OID 16822)
-- Dependencies: 258
-- Data for Name: django_content_type; Type: TABLE DATA; Schema: public; Owner: inventario_user
--

COPY public.django_content_type (id, app_label, model) FROM stdin;
1	admin	logentry
2	auth	permission
3	auth	group
4	auth	user
5	contenttypes	contenttype
6	sessions	session
7	productos	proveedor
8	productos	atributosequipo
9	productos	empleado
10	productos	equipo
11	productos	marca
12	productos	estadoequipo
13	productos	detallefactura
14	productos	tipoequipo
15	productos	departamento
16	productos	empresa
17	productos	estadomantencion
18	productos	factura
19	productos	mantencion
20	productos	historialequipos
21	productos	historialmantencioneslog
\.


--
-- TOC entry 5300 (class 0 OID 16826)
-- Dependencies: 260
-- Data for Name: django_migrations; Type: TABLE DATA; Schema: public; Owner: inventario_user
--

COPY public.django_migrations (id, app, name, applied) FROM stdin;
1	contenttypes	0001_initial	2025-08-28 09:31:16.437172-04
2	auth	0001_initial	2025-08-28 09:31:16.561594-04
3	admin	0001_initial	2025-08-28 09:31:16.607693-04
4	admin	0002_logentry_remove_auto_add	2025-08-28 09:31:16.622674-04
5	admin	0003_logentry_add_action_flag_choices	2025-08-28 09:31:16.64015-04
6	contenttypes	0002_remove_content_type_name	2025-08-28 09:31:16.674844-04
7	auth	0002_alter_permission_name_max_length	2025-08-28 09:31:16.691527-04
8	auth	0003_alter_user_email_max_length	2025-08-28 09:31:16.711457-04
9	auth	0004_alter_user_username_opts	2025-08-28 09:31:16.726855-04
10	auth	0005_alter_user_last_login_null	2025-08-28 09:31:16.748952-04
11	auth	0006_require_contenttypes_0002	2025-08-28 09:31:16.752207-04
12	auth	0007_alter_validators_add_error_messages	2025-08-28 09:31:16.769305-04
13	auth	0008_alter_user_username_max_length	2025-08-28 09:31:16.805653-04
14	auth	0009_alter_user_last_name_max_length	2025-08-28 09:31:16.826079-04
15	auth	0010_alter_group_name_max_length	2025-08-28 09:31:16.850171-04
16	auth	0011_update_proxy_permissions	2025-08-28 09:31:16.866999-04
17	auth	0012_alter_user_first_name_max_length	2025-08-28 09:31:16.883965-04
18	sessions	0001_initial	2025-08-28 09:31:16.905175-04
19	productos	0001_initial	2025-09-01 10:28:03.241389-04
\.


--
-- TOC entry 5302 (class 0 OID 16832)
-- Dependencies: 262
-- Data for Name: django_session; Type: TABLE DATA; Schema: public; Owner: inventario_user
--

COPY public.django_session (session_key, session_data, expire_date) FROM stdin;
i8xffbs7a44wn99ew3kbzguns2669khz	e30:1uri5d:hqJX7HiaGlhhd6DEnwj8min6qdT2Sj0984nEmJtrbLQ	2025-09-11 16:15:17.535755-03
kwlhwt32g4marskdl73je2yk850lu3tg	e30:1uriHc:UZ0MP6whHKnb_5LIoXYJ0RNPKPOqShxx_tfQIsviQBk	2025-09-11 16:27:40.667068-03
h23zmjbwgng35r3upzgbsk81zc91vsdk	e30:1uricu:LMY4Ej7vKG5EUg8AeVzRWy9sG0JsgPngc7L1Pne7kW8	2025-09-11 16:49:40.566983-03
5ifc9n3v4wikpmon4vzjk49s9riysjd0	.eJxVjMsOwiAQRf-FtSHDS8Cl-34DGWCQqoGktCvjv2uTLnR7zzn3xQJuaw3boCXMmV2YYKffLWJ6UNtBvmO7dZ56W5c58l3hBx186pme18P9O6g46rcGXRCUBGucd8UTmJQwOe2QilZKZ-GjUECI-ewcCGNNUj7maKUsQIW9P9TvN80:1ut6X5:ReE-E4Sx0U-puSGD7k6LRGicC83S1xbiED66PO3ZXSM	2025-09-15 12:33:23.02393-03
\.


--
-- TOC entry 5326 (class 0 OID 0)
-- Dependencies: 274
-- Name: agregacion_atributos_por_equipo_id_seq; Type: SEQUENCE SET; Schema: inventario; Owner: inventario_user
--

SELECT pg_catalog.setval('inventario.agregacion_atributos_por_equipo_id_seq', 88, true);


--
-- TOC entry 5327 (class 0 OID 0)
-- Dependencies: 219
-- Name: atributos_equipo_id_atributo_equipo_seq; Type: SEQUENCE SET; Schema: inventario; Owner: inventario_user
--

SELECT pg_catalog.setval('inventario.atributos_equipo_id_atributo_equipo_seq', 59, true);


--
-- TOC entry 5328 (class 0 OID 0)
-- Dependencies: 221
-- Name: departamento_id_departamento_seq; Type: SEQUENCE SET; Schema: inventario; Owner: inventario_user
--

SELECT pg_catalog.setval('inventario.departamento_id_departamento_seq', 14, true);


--
-- TOC entry 5329 (class 0 OID 0)
-- Dependencies: 223
-- Name: detalle_factura_id_detalle_factura_seq; Type: SEQUENCE SET; Schema: inventario; Owner: inventario_user
--

SELECT pg_catalog.setval('inventario.detalle_factura_id_detalle_factura_seq', 5, true);


--
-- TOC entry 5330 (class 0 OID 0)
-- Dependencies: 225
-- Name: empleado_id_empleado_seq; Type: SEQUENCE SET; Schema: inventario; Owner: inventario_user
--

SELECT pg_catalog.setval('inventario.empleado_id_empleado_seq', 15, true);


--
-- TOC entry 5331 (class 0 OID 0)
-- Dependencies: 227
-- Name: empresa_id_empresa_seq; Type: SEQUENCE SET; Schema: inventario; Owner: inventario_user
--

SELECT pg_catalog.setval('inventario.empresa_id_empresa_seq', 3, true);


--
-- TOC entry 5332 (class 0 OID 0)
-- Dependencies: 229
-- Name: equipo_id_equipo_seq; Type: SEQUENCE SET; Schema: inventario; Owner: inventario_user
--

SELECT pg_catalog.setval('inventario.equipo_id_equipo_seq', 38, true);


--
-- TOC entry 5333 (class 0 OID 0)
-- Dependencies: 231
-- Name: estado_equipo_id_estado_equipo_seq; Type: SEQUENCE SET; Schema: inventario; Owner: inventario_user
--

SELECT pg_catalog.setval('inventario.estado_equipo_id_estado_equipo_seq', 17, true);


--
-- TOC entry 5334 (class 0 OID 0)
-- Dependencies: 233
-- Name: estado_mantencion_id_estado_mantencion_seq; Type: SEQUENCE SET; Schema: inventario; Owner: inventario_user
--

SELECT pg_catalog.setval('inventario.estado_mantencion_id_estado_mantencion_seq', 24, true);


--
-- TOC entry 5335 (class 0 OID 0)
-- Dependencies: 235
-- Name: factura_id_factura_seq; Type: SEQUENCE SET; Schema: inventario; Owner: inventario_user
--

SELECT pg_catalog.setval('inventario.factura_id_factura_seq', 3, true);


--
-- TOC entry 5336 (class 0 OID 0)
-- Dependencies: 263
-- Name: historial_equipos_id_seq; Type: SEQUENCE SET; Schema: inventario; Owner: inventario_user
--

SELECT pg_catalog.setval('inventario.historial_equipos_id_seq', 344, true);


--
-- TOC entry 5337 (class 0 OID 0)
-- Dependencies: 269
-- Name: historial_mantenciones_id_historial_seq; Type: SEQUENCE SET; Schema: inventario; Owner: inventario_user
--

SELECT pg_catalog.setval('inventario.historial_mantenciones_id_historial_seq', 18, true);


--
-- TOC entry 5338 (class 0 OID 0)
-- Dependencies: 272
-- Name: historial_mantenciones_log_id_evento_seq; Type: SEQUENCE SET; Schema: inventario; Owner: inventario_user
--

SELECT pg_catalog.setval('inventario.historial_mantenciones_log_id_evento_seq', 29, true);


--
-- TOC entry 5339 (class 0 OID 0)
-- Dependencies: 237
-- Name: mantencion_id_mantencion_seq; Type: SEQUENCE SET; Schema: inventario; Owner: inventario_user
--

SELECT pg_catalog.setval('inventario.mantencion_id_mantencion_seq', 22, true);


--
-- TOC entry 5340 (class 0 OID 0)
-- Dependencies: 239
-- Name: marca_id_marca_seq; Type: SEQUENCE SET; Schema: inventario; Owner: inventario_user
--

SELECT pg_catalog.setval('inventario.marca_id_marca_seq', 76, true);


--
-- TOC entry 5341 (class 0 OID 0)
-- Dependencies: 267
-- Name: prioridad_mantencion_id_prioridad_seq; Type: SEQUENCE SET; Schema: inventario; Owner: inventario_user
--

SELECT pg_catalog.setval('inventario.prioridad_mantencion_id_prioridad_seq', 12, true);


--
-- TOC entry 5342 (class 0 OID 0)
-- Dependencies: 241
-- Name: proveedor_id_proveedor_seq; Type: SEQUENCE SET; Schema: inventario; Owner: inventario_user
--

SELECT pg_catalog.setval('inventario.proveedor_id_proveedor_seq', 14, true);


--
-- TOC entry 5343 (class 0 OID 0)
-- Dependencies: 243
-- Name: tipo_equipo_id_tipo_equipo_seq; Type: SEQUENCE SET; Schema: inventario; Owner: inventario_user
--

SELECT pg_catalog.setval('inventario.tipo_equipo_id_tipo_equipo_seq', 49, true);


--
-- TOC entry 5344 (class 0 OID 0)
-- Dependencies: 265
-- Name: tipo_mantencion_id_tipo_mantencion_seq; Type: SEQUENCE SET; Schema: inventario; Owner: inventario_user
--

SELECT pg_catalog.setval('inventario.tipo_mantencion_id_tipo_mantencion_seq', 13, true);


--
-- TOC entry 5345 (class 0 OID 0)
-- Dependencies: 245
-- Name: auth_group_id_seq; Type: SEQUENCE SET; Schema: public; Owner: inventario_user
--

SELECT pg_catalog.setval('public.auth_group_id_seq', 3, true);


--
-- TOC entry 5346 (class 0 OID 0)
-- Dependencies: 247
-- Name: auth_group_permissions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: inventario_user
--

SELECT pg_catalog.setval('public.auth_group_permissions_id_seq', 110, true);


--
-- TOC entry 5347 (class 0 OID 0)
-- Dependencies: 249
-- Name: auth_permission_id_seq; Type: SEQUENCE SET; Schema: public; Owner: inventario_user
--

SELECT pg_catalog.setval('public.auth_permission_id_seq', 78, true);


--
-- TOC entry 5348 (class 0 OID 0)
-- Dependencies: 252
-- Name: auth_user_groups_id_seq; Type: SEQUENCE SET; Schema: public; Owner: inventario_user
--

SELECT pg_catalog.setval('public.auth_user_groups_id_seq', 21, true);


--
-- TOC entry 5349 (class 0 OID 0)
-- Dependencies: 253
-- Name: auth_user_id_seq; Type: SEQUENCE SET; Schema: public; Owner: inventario_user
--

SELECT pg_catalog.setval('public.auth_user_id_seq', 12, true);


--
-- TOC entry 5350 (class 0 OID 0)
-- Dependencies: 255
-- Name: auth_user_user_permissions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: inventario_user
--

SELECT pg_catalog.setval('public.auth_user_user_permissions_id_seq', 76, true);


--
-- TOC entry 5351 (class 0 OID 0)
-- Dependencies: 257
-- Name: django_admin_log_id_seq; Type: SEQUENCE SET; Schema: public; Owner: inventario_user
--

SELECT pg_catalog.setval('public.django_admin_log_id_seq', 14, true);


--
-- TOC entry 5352 (class 0 OID 0)
-- Dependencies: 259
-- Name: django_content_type_id_seq; Type: SEQUENCE SET; Schema: public; Owner: inventario_user
--

SELECT pg_catalog.setval('public.django_content_type_id_seq', 21, true);


--
-- TOC entry 5353 (class 0 OID 0)
-- Dependencies: 261
-- Name: django_migrations_id_seq; Type: SEQUENCE SET; Schema: public; Owner: inventario_user
--

SELECT pg_catalog.setval('public.django_migrations_id_seq', 19, true);


--
-- TOC entry 5043 (class 2606 OID 17262)
-- Name: agregacion_atributos_por_equipo agreg_attr_equipo_unq; Type: CONSTRAINT; Schema: inventario; Owner: inventario_user
--

ALTER TABLE ONLY inventario.agregacion_atributos_por_equipo
    ADD CONSTRAINT agreg_attr_equipo_unq UNIQUE (id_equipo, id_atributo_equipo);


--
-- TOC entry 5045 (class 2606 OID 17260)
-- Name: agregacion_atributos_por_equipo agregacion_atributos_por_equipo_pkey; Type: CONSTRAINT; Schema: inventario; Owner: inventario_user
--

ALTER TABLE ONLY inventario.agregacion_atributos_por_equipo
    ADD CONSTRAINT agregacion_atributos_por_equipo_pkey PRIMARY KEY (id);


--
-- TOC entry 4919 (class 2606 OID 16838)
-- Name: atributos_equipo atributos_equipo_id_tipo_equipo_atributo_key; Type: CONSTRAINT; Schema: inventario; Owner: inventario_user
--

ALTER TABLE ONLY inventario.atributos_equipo
    ADD CONSTRAINT atributos_equipo_id_tipo_equipo_atributo_key UNIQUE (id_tipo_equipo, atributo);


--
-- TOC entry 4921 (class 2606 OID 16840)
-- Name: atributos_equipo atributos_equipo_pkey; Type: CONSTRAINT; Schema: inventario; Owner: inventario_user
--

ALTER TABLE ONLY inventario.atributos_equipo
    ADD CONSTRAINT atributos_equipo_pkey PRIMARY KEY (id_atributo_equipo);


--
-- TOC entry 4923 (class 2606 OID 16842)
-- Name: departamento departamento_id_empresa_nombre_departamento_key; Type: CONSTRAINT; Schema: inventario; Owner: inventario_user
--

ALTER TABLE ONLY inventario.departamento
    ADD CONSTRAINT departamento_id_empresa_nombre_departamento_key UNIQUE (id_empresa, nombre_departamento);


--
-- TOC entry 4925 (class 2606 OID 16844)
-- Name: departamento departamento_pkey; Type: CONSTRAINT; Schema: inventario; Owner: inventario_user
--

ALTER TABLE ONLY inventario.departamento
    ADD CONSTRAINT departamento_pkey PRIMARY KEY (id_departamento);


--
-- TOC entry 4928 (class 2606 OID 16846)
-- Name: detalle_factura detalle_factura_pkey; Type: CONSTRAINT; Schema: inventario; Owner: inventario_user
--

ALTER TABLE ONLY inventario.detalle_factura
    ADD CONSTRAINT detalle_factura_pkey PRIMARY KEY (id_detalle_factura);


--
-- TOC entry 4931 (class 2606 OID 17419)
-- Name: empleado empleado_correo_unique; Type: CONSTRAINT; Schema: inventario; Owner: inventario_user
--

ALTER TABLE ONLY inventario.empleado
    ADD CONSTRAINT empleado_correo_unique UNIQUE (correo);


--
-- TOC entry 4933 (class 2606 OID 16848)
-- Name: empleado empleado_pkey; Type: CONSTRAINT; Schema: inventario; Owner: inventario_user
--

ALTER TABLE ONLY inventario.empleado
    ADD CONSTRAINT empleado_pkey PRIMARY KEY (id_empleado);


--
-- TOC entry 4935 (class 2606 OID 16850)
-- Name: empleado empleado_rut_key; Type: CONSTRAINT; Schema: inventario; Owner: inventario_user
--

ALTER TABLE ONLY inventario.empleado
    ADD CONSTRAINT empleado_rut_key UNIQUE (rut);


--
-- TOC entry 4937 (class 2606 OID 17137)
-- Name: empleado empleado_user_id_key; Type: CONSTRAINT; Schema: inventario; Owner: inventario_user
--

ALTER TABLE ONLY inventario.empleado
    ADD CONSTRAINT empleado_user_id_key UNIQUE (user_id);


--
-- TOC entry 4940 (class 2606 OID 16852)
-- Name: empresa empresa_pkey; Type: CONSTRAINT; Schema: inventario; Owner: inventario_user
--

ALTER TABLE ONLY inventario.empresa
    ADD CONSTRAINT empresa_pkey PRIMARY KEY (id_empresa);


--
-- TOC entry 4942 (class 2606 OID 16854)
-- Name: empresa empresa_rut_empresa_key; Type: CONSTRAINT; Schema: inventario; Owner: inventario_user
--

ALTER TABLE ONLY inventario.empresa
    ADD CONSTRAINT empresa_rut_empresa_key UNIQUE (rut_empresa);


--
-- TOC entry 4944 (class 2606 OID 16856)
-- Name: equipo equipo_pkey; Type: CONSTRAINT; Schema: inventario; Owner: inventario_user
--

ALTER TABLE ONLY inventario.equipo
    ADD CONSTRAINT equipo_pkey PRIMARY KEY (id_equipo);


--
-- TOC entry 4950 (class 2606 OID 16860)
-- Name: estado_equipo estado_equipo_pkey; Type: CONSTRAINT; Schema: inventario; Owner: inventario_user
--

ALTER TABLE ONLY inventario.estado_equipo
    ADD CONSTRAINT estado_equipo_pkey PRIMARY KEY (id_estado_equipo);


--
-- TOC entry 4953 (class 2606 OID 16862)
-- Name: estado_mantencion estado_mantencion_pkey; Type: CONSTRAINT; Schema: inventario; Owner: inventario_user
--

ALTER TABLE ONLY inventario.estado_mantencion
    ADD CONSTRAINT estado_mantencion_pkey PRIMARY KEY (id_estado_mantencion);


--
-- TOC entry 4955 (class 2606 OID 16866)
-- Name: factura factura_pkey; Type: CONSTRAINT; Schema: inventario; Owner: inventario_user
--

ALTER TABLE ONLY inventario.factura
    ADD CONSTRAINT factura_pkey PRIMARY KEY (id_factura);


--
-- TOC entry 5023 (class 2606 OID 17070)
-- Name: historial_equipos historial_equipos_pkey; Type: CONSTRAINT; Schema: inventario; Owner: inventario_user
--

ALTER TABLE ONLY inventario.historial_equipos
    ADD CONSTRAINT historial_equipos_pkey PRIMARY KEY (id);


--
-- TOC entry 5038 (class 2606 OID 17233)
-- Name: historial_mantenciones_log historial_mantenciones_log_pkey; Type: CONSTRAINT; Schema: inventario; Owner: inventario_user
--

ALTER TABLE ONLY inventario.historial_mantenciones_log
    ADD CONSTRAINT historial_mantenciones_log_pkey PRIMARY KEY (id_evento);


--
-- TOC entry 5033 (class 2606 OID 17198)
-- Name: historial_mantenciones historial_mantenciones_pkey; Type: CONSTRAINT; Schema: inventario; Owner: inventario_user
--

ALTER TABLE ONLY inventario.historial_mantenciones
    ADD CONSTRAINT historial_mantenciones_pkey PRIMARY KEY (id_historial);


--
-- TOC entry 4965 (class 2606 OID 16868)
-- Name: mantencion mantencion_pkey; Type: CONSTRAINT; Schema: inventario; Owner: inventario_user
--

ALTER TABLE ONLY inventario.mantencion
    ADD CONSTRAINT mantencion_pkey PRIMARY KEY (id_mantencion);


--
-- TOC entry 4968 (class 2606 OID 16872)
-- Name: marca marca_pkey; Type: CONSTRAINT; Schema: inventario; Owner: inventario_user
--

ALTER TABLE ONLY inventario.marca
    ADD CONSTRAINT marca_pkey PRIMARY KEY (id_marca);


--
-- TOC entry 5031 (class 2606 OID 17159)
-- Name: prioridad_mantencion prioridad_mantencion_pkey; Type: CONSTRAINT; Schema: inventario; Owner: inventario_user
--

ALTER TABLE ONLY inventario.prioridad_mantencion
    ADD CONSTRAINT prioridad_mantencion_pkey PRIMARY KEY (id_prioridad);


--
-- TOC entry 4971 (class 2606 OID 16874)
-- Name: proveedor proveedor_pkey; Type: CONSTRAINT; Schema: inventario; Owner: inventario_user
--

ALTER TABLE ONLY inventario.proveedor
    ADD CONSTRAINT proveedor_pkey PRIMARY KEY (id_proveedor);


--
-- TOC entry 4974 (class 2606 OID 16878)
-- Name: tipo_equipo tipo_equipo_pkey; Type: CONSTRAINT; Schema: inventario; Owner: inventario_user
--

ALTER TABLE ONLY inventario.tipo_equipo
    ADD CONSTRAINT tipo_equipo_pkey PRIMARY KEY (id_tipo_equipo);


--
-- TOC entry 5028 (class 2606 OID 17149)
-- Name: tipo_mantencion tipo_mantencion_pkey; Type: CONSTRAINT; Schema: inventario; Owner: inventario_user
--

ALTER TABLE ONLY inventario.tipo_mantencion
    ADD CONSTRAINT tipo_mantencion_pkey PRIMARY KEY (id_tipo_mantencion);


--
-- TOC entry 4977 (class 2606 OID 16882)
-- Name: auth_group auth_group_name_key; Type: CONSTRAINT; Schema: public; Owner: inventario_user
--

ALTER TABLE ONLY public.auth_group
    ADD CONSTRAINT auth_group_name_key UNIQUE (name);


--
-- TOC entry 4982 (class 2606 OID 16884)
-- Name: auth_group_permissions auth_group_permissions_group_id_permission_id_0cd325b0_uniq; Type: CONSTRAINT; Schema: public; Owner: inventario_user
--

ALTER TABLE ONLY public.auth_group_permissions
    ADD CONSTRAINT auth_group_permissions_group_id_permission_id_0cd325b0_uniq UNIQUE (group_id, permission_id);


--
-- TOC entry 4985 (class 2606 OID 16886)
-- Name: auth_group_permissions auth_group_permissions_pkey; Type: CONSTRAINT; Schema: public; Owner: inventario_user
--

ALTER TABLE ONLY public.auth_group_permissions
    ADD CONSTRAINT auth_group_permissions_pkey PRIMARY KEY (id);


--
-- TOC entry 4979 (class 2606 OID 16888)
-- Name: auth_group auth_group_pkey; Type: CONSTRAINT; Schema: public; Owner: inventario_user
--

ALTER TABLE ONLY public.auth_group
    ADD CONSTRAINT auth_group_pkey PRIMARY KEY (id);


--
-- TOC entry 4988 (class 2606 OID 16890)
-- Name: auth_permission auth_permission_content_type_id_codename_01ab375a_uniq; Type: CONSTRAINT; Schema: public; Owner: inventario_user
--

ALTER TABLE ONLY public.auth_permission
    ADD CONSTRAINT auth_permission_content_type_id_codename_01ab375a_uniq UNIQUE (content_type_id, codename);


--
-- TOC entry 4990 (class 2606 OID 16892)
-- Name: auth_permission auth_permission_pkey; Type: CONSTRAINT; Schema: public; Owner: inventario_user
--

ALTER TABLE ONLY public.auth_permission
    ADD CONSTRAINT auth_permission_pkey PRIMARY KEY (id);


--
-- TOC entry 4998 (class 2606 OID 16894)
-- Name: auth_user_groups auth_user_groups_pkey; Type: CONSTRAINT; Schema: public; Owner: inventario_user
--

ALTER TABLE ONLY public.auth_user_groups
    ADD CONSTRAINT auth_user_groups_pkey PRIMARY KEY (id);


--
-- TOC entry 5001 (class 2606 OID 16896)
-- Name: auth_user_groups auth_user_groups_user_id_group_id_94350c0c_uniq; Type: CONSTRAINT; Schema: public; Owner: inventario_user
--

ALTER TABLE ONLY public.auth_user_groups
    ADD CONSTRAINT auth_user_groups_user_id_group_id_94350c0c_uniq UNIQUE (user_id, group_id);


--
-- TOC entry 4992 (class 2606 OID 16898)
-- Name: auth_user auth_user_pkey; Type: CONSTRAINT; Schema: public; Owner: inventario_user
--

ALTER TABLE ONLY public.auth_user
    ADD CONSTRAINT auth_user_pkey PRIMARY KEY (id);


--
-- TOC entry 5004 (class 2606 OID 16900)
-- Name: auth_user_user_permissions auth_user_user_permissions_pkey; Type: CONSTRAINT; Schema: public; Owner: inventario_user
--

ALTER TABLE ONLY public.auth_user_user_permissions
    ADD CONSTRAINT auth_user_user_permissions_pkey PRIMARY KEY (id);


--
-- TOC entry 5007 (class 2606 OID 16902)
-- Name: auth_user_user_permissions auth_user_user_permissions_user_id_permission_id_14a6b632_uniq; Type: CONSTRAINT; Schema: public; Owner: inventario_user
--

ALTER TABLE ONLY public.auth_user_user_permissions
    ADD CONSTRAINT auth_user_user_permissions_user_id_permission_id_14a6b632_uniq UNIQUE (user_id, permission_id);


--
-- TOC entry 4995 (class 2606 OID 16904)
-- Name: auth_user auth_user_username_key; Type: CONSTRAINT; Schema: public; Owner: inventario_user
--

ALTER TABLE ONLY public.auth_user
    ADD CONSTRAINT auth_user_username_key UNIQUE (username);


--
-- TOC entry 5010 (class 2606 OID 16906)
-- Name: django_admin_log django_admin_log_pkey; Type: CONSTRAINT; Schema: public; Owner: inventario_user
--

ALTER TABLE ONLY public.django_admin_log
    ADD CONSTRAINT django_admin_log_pkey PRIMARY KEY (id);


--
-- TOC entry 5013 (class 2606 OID 16908)
-- Name: django_content_type django_content_type_app_label_model_76bd3d3b_uniq; Type: CONSTRAINT; Schema: public; Owner: inventario_user
--

ALTER TABLE ONLY public.django_content_type
    ADD CONSTRAINT django_content_type_app_label_model_76bd3d3b_uniq UNIQUE (app_label, model);


--
-- TOC entry 5015 (class 2606 OID 16910)
-- Name: django_content_type django_content_type_pkey; Type: CONSTRAINT; Schema: public; Owner: inventario_user
--

ALTER TABLE ONLY public.django_content_type
    ADD CONSTRAINT django_content_type_pkey PRIMARY KEY (id);


--
-- TOC entry 5017 (class 2606 OID 16912)
-- Name: django_migrations django_migrations_pkey; Type: CONSTRAINT; Schema: public; Owner: inventario_user
--

ALTER TABLE ONLY public.django_migrations
    ADD CONSTRAINT django_migrations_pkey PRIMARY KEY (id);


--
-- TOC entry 5020 (class 2606 OID 16914)
-- Name: django_session django_session_pkey; Type: CONSTRAINT; Schema: public; Owner: inventario_user
--

ALTER TABLE ONLY public.django_session
    ADD CONSTRAINT django_session_pkey PRIMARY KEY (session_key);


--
-- TOC entry 4917 (class 1259 OID 17411)
-- Name: atributos_emp_idx; Type: INDEX; Schema: inventario; Owner: inventario_user
--

CREATE INDEX atributos_emp_idx ON inventario.atributos_equipo USING btree (id_empresa);


--
-- TOC entry 4948 (class 1259 OID 17415)
-- Name: estado_equipo_emp_desc_uniq; Type: INDEX; Schema: inventario; Owner: inventario_user
--

CREATE UNIQUE INDEX estado_equipo_emp_desc_uniq ON inventario.estado_equipo USING btree (id_empresa, descripcion);


--
-- TOC entry 4951 (class 1259 OID 17414)
-- Name: estado_mantencion_emp_tipo_uniq; Type: INDEX; Schema: inventario; Owner: inventario_user
--

CREATE UNIQUE INDEX estado_mantencion_emp_tipo_uniq ON inventario.estado_mantencion USING btree (id_empresa, tipo);


--
-- TOC entry 5046 (class 1259 OID 17280)
-- Name: idx_agreg_attr_empresa; Type: INDEX; Schema: inventario; Owner: inventario_user
--

CREATE INDEX idx_agreg_attr_empresa ON inventario.agregacion_atributos_por_equipo USING btree (id_empresa);


--
-- TOC entry 5047 (class 1259 OID 17274)
-- Name: idx_agreg_attr_equipo_attr; Type: INDEX; Schema: inventario; Owner: inventario_user
--

CREATE INDEX idx_agreg_attr_equipo_attr ON inventario.agregacion_atributos_por_equipo USING btree (id_atributo_equipo);


--
-- TOC entry 5048 (class 1259 OID 17273)
-- Name: idx_agreg_attr_equipo_equipo; Type: INDEX; Schema: inventario; Owner: inventario_user
--

CREATE INDEX idx_agreg_attr_equipo_equipo ON inventario.agregacion_atributos_por_equipo USING btree (id_equipo);


--
-- TOC entry 4926 (class 1259 OID 16915)
-- Name: idx_departamento_empresa; Type: INDEX; Schema: inventario; Owner: inventario_user
--

CREATE INDEX idx_departamento_empresa ON inventario.departamento USING btree (id_empresa);


--
-- TOC entry 4929 (class 1259 OID 17286)
-- Name: idx_detalle_factura_empresa; Type: INDEX; Schema: inventario; Owner: inventario_user
--

CREATE INDEX idx_detalle_factura_empresa ON inventario.detalle_factura USING btree (id_empresa);


--
-- TOC entry 4938 (class 1259 OID 16916)
-- Name: idx_empleado_empresa_depto; Type: INDEX; Schema: inventario; Owner: inventario_user
--

CREATE INDEX idx_empleado_empresa_depto ON inventario.empleado USING btree (id_empresa, id_departamento);


--
-- TOC entry 4945 (class 1259 OID 17135)
-- Name: idx_equipo_depto; Type: INDEX; Schema: inventario; Owner: inventario_user
--

CREATE INDEX idx_equipo_depto ON inventario.equipo USING btree (departamento_id);


--
-- TOC entry 4946 (class 1259 OID 17134)
-- Name: idx_equipo_empresa; Type: INDEX; Schema: inventario; Owner: inventario_user
--

CREATE INDEX idx_equipo_empresa ON inventario.equipo USING btree (id_empresa);


--
-- TOC entry 4947 (class 1259 OID 16917)
-- Name: idx_equipo_marca_tipo_estado; Type: INDEX; Schema: inventario; Owner: inventario_user
--

CREATE INDEX idx_equipo_marca_tipo_estado ON inventario.equipo USING btree (id_marca, id_tipo_equipo, id_estado_equipo);


--
-- TOC entry 4956 (class 1259 OID 17310)
-- Name: idx_factura_empresa; Type: INDEX; Schema: inventario; Owner: inventario_user
--

CREATE INDEX idx_factura_empresa ON inventario.factura USING btree (id_empresa);


--
-- TOC entry 4957 (class 1259 OID 16918)
-- Name: idx_factura_proveedor; Type: INDEX; Schema: inventario; Owner: inventario_user
--

CREATE INDEX idx_factura_proveedor ON inventario.factura USING btree (id_proveedor);


--
-- TOC entry 5034 (class 1259 OID 17298)
-- Name: idx_hist_mant_empresa; Type: INDEX; Schema: inventario; Owner: inventario_user
--

CREATE INDEX idx_hist_mant_empresa ON inventario.historial_mantenciones USING btree (id_empresa);


--
-- TOC entry 5039 (class 1259 OID 17240)
-- Name: idx_hist_mant_fecha; Type: INDEX; Schema: inventario; Owner: inventario_user
--

CREATE INDEX idx_hist_mant_fecha ON inventario.historial_mantenciones_log USING btree (fecha_evento DESC);


--
-- TOC entry 5035 (class 1259 OID 17222)
-- Name: idx_hist_mant_id_mantencion; Type: INDEX; Schema: inventario; Owner: inventario_user
--

CREATE INDEX idx_hist_mant_id_mantencion ON inventario.historial_mantenciones USING btree (id_mantencion);


--
-- TOC entry 5040 (class 1259 OID 17304)
-- Name: idx_hist_mant_log_empresa; Type: INDEX; Schema: inventario; Owner: inventario_user
--

CREATE INDEX idx_hist_mant_log_empresa ON inventario.historial_mantenciones_log USING btree (id_empresa);


--
-- TOC entry 5041 (class 1259 OID 17239)
-- Name: idx_hist_mant_mant; Type: INDEX; Schema: inventario; Owner: inventario_user
--

CREATE INDEX idx_hist_mant_mant ON inventario.historial_mantenciones_log USING btree (id_mantencion);


--
-- TOC entry 5036 (class 1259 OID 17209)
-- Name: idx_hist_mant_mantencion_fecha; Type: INDEX; Schema: inventario; Owner: inventario_user
--

CREATE INDEX idx_hist_mant_mantencion_fecha ON inventario.historial_mantenciones USING btree (id_mantencion, fecha_evento DESC);


--
-- TOC entry 5024 (class 1259 OID 17123)
-- Name: idx_hist_responsable_anterior; Type: INDEX; Schema: inventario; Owner: inventario_user
--

CREATE INDEX idx_hist_responsable_anterior ON inventario.historial_equipos USING btree (responsable_anterior_id);


--
-- TOC entry 5025 (class 1259 OID 17111)
-- Name: idx_historial_fecha; Type: INDEX; Schema: inventario; Owner: inventario_user
--

CREATE INDEX idx_historial_fecha ON inventario.historial_equipos USING btree (fecha DESC);


--
-- TOC entry 4958 (class 1259 OID 17292)
-- Name: idx_mantencion_empresa; Type: INDEX; Schema: inventario; Owner: inventario_user
--

CREATE INDEX idx_mantencion_empresa ON inventario.mantencion USING btree (id_empresa);


--
-- TOC entry 4959 (class 1259 OID 16919)
-- Name: idx_mantencion_equipo_fecha; Type: INDEX; Schema: inventario; Owner: inventario_user
--

CREATE INDEX idx_mantencion_equipo_fecha ON inventario.mantencion USING btree (id_equipo, fecha);


--
-- TOC entry 4960 (class 1259 OID 17185)
-- Name: idx_mantencion_equipo_inicio; Type: INDEX; Schema: inventario; Owner: inventario_user
--

CREATE INDEX idx_mantencion_equipo_inicio ON inventario.mantencion USING btree (id_equipo, fecha_inicio DESC);


--
-- TOC entry 4961 (class 1259 OID 17186)
-- Name: idx_mantencion_estado; Type: INDEX; Schema: inventario; Owner: inventario_user
--

CREATE INDEX idx_mantencion_estado ON inventario.mantencion USING btree (id_estado_mantencion);


--
-- TOC entry 4962 (class 1259 OID 17188)
-- Name: idx_mantencion_prioridad; Type: INDEX; Schema: inventario; Owner: inventario_user
--

CREATE INDEX idx_mantencion_prioridad ON inventario.mantencion USING btree (id_prioridad);


--
-- TOC entry 4963 (class 1259 OID 17187)
-- Name: idx_mantencion_tipo; Type: INDEX; Schema: inventario; Owner: inventario_user
--

CREATE INDEX idx_mantencion_tipo ON inventario.mantencion USING btree (id_tipo_mantencion);


--
-- TOC entry 4966 (class 1259 OID 17408)
-- Name: marca_emp_nombre_uniq; Type: INDEX; Schema: inventario; Owner: inventario_user
--

CREATE UNIQUE INDEX marca_emp_nombre_uniq ON inventario.marca USING btree (id_empresa, nombre_marca);


--
-- TOC entry 5029 (class 1259 OID 17413)
-- Name: prioridad_emp_nombre_uniq; Type: INDEX; Schema: inventario; Owner: inventario_user
--

CREATE UNIQUE INDEX prioridad_emp_nombre_uniq ON inventario.prioridad_mantencion USING btree (id_empresa, nombre);


--
-- TOC entry 4969 (class 1259 OID 17409)
-- Name: proveedor_emp_rut_uniq; Type: INDEX; Schema: inventario; Owner: inventario_user
--

CREATE UNIQUE INDEX proveedor_emp_rut_uniq ON inventario.proveedor USING btree (id_empresa, rut_proveedor);


--
-- TOC entry 4972 (class 1259 OID 17410)
-- Name: tipo_equipo_emp_nombre_uniq; Type: INDEX; Schema: inventario; Owner: inventario_user
--

CREATE UNIQUE INDEX tipo_equipo_emp_nombre_uniq ON inventario.tipo_equipo USING btree (id_empresa, tipo_equipo);


--
-- TOC entry 5026 (class 1259 OID 17412)
-- Name: tipo_mantencion_emp_nombre_uniq; Type: INDEX; Schema: inventario; Owner: inventario_user
--

CREATE UNIQUE INDEX tipo_mantencion_emp_nombre_uniq ON inventario.tipo_mantencion USING btree (id_empresa, nombre);


--
-- TOC entry 4975 (class 1259 OID 16920)
-- Name: auth_group_name_a6ea08ec_like; Type: INDEX; Schema: public; Owner: inventario_user
--

CREATE INDEX auth_group_name_a6ea08ec_like ON public.auth_group USING btree (name varchar_pattern_ops);


--
-- TOC entry 4980 (class 1259 OID 16921)
-- Name: auth_group_permissions_group_id_b120cbf9; Type: INDEX; Schema: public; Owner: inventario_user
--

CREATE INDEX auth_group_permissions_group_id_b120cbf9 ON public.auth_group_permissions USING btree (group_id);


--
-- TOC entry 4983 (class 1259 OID 16922)
-- Name: auth_group_permissions_permission_id_84c5c92e; Type: INDEX; Schema: public; Owner: inventario_user
--

CREATE INDEX auth_group_permissions_permission_id_84c5c92e ON public.auth_group_permissions USING btree (permission_id);


--
-- TOC entry 4986 (class 1259 OID 16923)
-- Name: auth_permission_content_type_id_2f476e4b; Type: INDEX; Schema: public; Owner: inventario_user
--

CREATE INDEX auth_permission_content_type_id_2f476e4b ON public.auth_permission USING btree (content_type_id);


--
-- TOC entry 4996 (class 1259 OID 16924)
-- Name: auth_user_groups_group_id_97559544; Type: INDEX; Schema: public; Owner: inventario_user
--

CREATE INDEX auth_user_groups_group_id_97559544 ON public.auth_user_groups USING btree (group_id);


--
-- TOC entry 4999 (class 1259 OID 16925)
-- Name: auth_user_groups_user_id_6a12ed8b; Type: INDEX; Schema: public; Owner: inventario_user
--

CREATE INDEX auth_user_groups_user_id_6a12ed8b ON public.auth_user_groups USING btree (user_id);


--
-- TOC entry 5002 (class 1259 OID 16926)
-- Name: auth_user_user_permissions_permission_id_1fbb5f2c; Type: INDEX; Schema: public; Owner: inventario_user
--

CREATE INDEX auth_user_user_permissions_permission_id_1fbb5f2c ON public.auth_user_user_permissions USING btree (permission_id);


--
-- TOC entry 5005 (class 1259 OID 16927)
-- Name: auth_user_user_permissions_user_id_a95ead1b; Type: INDEX; Schema: public; Owner: inventario_user
--

CREATE INDEX auth_user_user_permissions_user_id_a95ead1b ON public.auth_user_user_permissions USING btree (user_id);


--
-- TOC entry 4993 (class 1259 OID 16928)
-- Name: auth_user_username_6821ab7c_like; Type: INDEX; Schema: public; Owner: inventario_user
--

CREATE INDEX auth_user_username_6821ab7c_like ON public.auth_user USING btree (username varchar_pattern_ops);


--
-- TOC entry 5008 (class 1259 OID 16929)
-- Name: django_admin_log_content_type_id_c4bce8eb; Type: INDEX; Schema: public; Owner: inventario_user
--

CREATE INDEX django_admin_log_content_type_id_c4bce8eb ON public.django_admin_log USING btree (content_type_id);


--
-- TOC entry 5011 (class 1259 OID 16930)
-- Name: django_admin_log_user_id_c564eba6; Type: INDEX; Schema: public; Owner: inventario_user
--

CREATE INDEX django_admin_log_user_id_c564eba6 ON public.django_admin_log USING btree (user_id);


--
-- TOC entry 5018 (class 1259 OID 16931)
-- Name: django_session_expire_date_a5c62663; Type: INDEX; Schema: public; Owner: inventario_user
--

CREATE INDEX django_session_expire_date_a5c62663 ON public.django_session USING btree (expire_date);


--
-- TOC entry 5021 (class 1259 OID 16932)
-- Name: django_session_session_key_c0390e0f_like; Type: INDEX; Schema: public; Owner: inventario_user
--

CREATE INDEX django_session_session_key_c0390e0f_like ON public.django_session USING btree (session_key varchar_pattern_ops);


--
-- TOC entry 5108 (class 2620 OID 17117)
-- Name: equipo trg_actualizar_fecha_modificacion; Type: TRIGGER; Schema: inventario; Owner: inventario_user
--

CREATE TRIGGER trg_actualizar_fecha_modificacion BEFORE UPDATE ON inventario.equipo FOR EACH ROW EXECUTE FUNCTION inventario.actualizar_fecha_modificacion();


--
-- TOC entry 5109 (class 2620 OID 17317)
-- Name: factura trg_factura_set_empresa; Type: TRIGGER; Schema: inventario; Owner: inventario_user
--

CREATE TRIGGER trg_factura_set_empresa BEFORE INSERT OR UPDATE ON inventario.factura FOR EACH ROW EXECUTE FUNCTION inventario.fill_factura_id_empresa();


--
-- TOC entry 5110 (class 2620 OID 17307)
-- Name: historial_mantenciones trg_hist_mant_set_empresa; Type: TRIGGER; Schema: inventario; Owner: inventario_user
--

CREATE TRIGGER trg_hist_mant_set_empresa BEFORE INSERT OR UPDATE OF id_mantencion ON inventario.historial_mantenciones FOR EACH ROW WHEN ((new.id_empresa IS NULL)) EXECUTE FUNCTION inventario.fill_hist_mant_id_empresa();


--
-- TOC entry 5111 (class 2620 OID 17309)
-- Name: historial_mantenciones trig_hist_mant_set_empresa; Type: TRIGGER; Schema: inventario; Owner: inventario_user
--

CREATE TRIGGER trig_hist_mant_set_empresa BEFORE INSERT OR UPDATE OF id_mantencion ON inventario.historial_mantenciones FOR EACH ROW EXECUTE FUNCTION inventario.fill_hist_mant_id_empresa();


--
-- TOC entry 5105 (class 2606 OID 17275)
-- Name: agregacion_atributos_por_equipo agreg_attr_equipo_id_empresa_fkey; Type: FK CONSTRAINT; Schema: inventario; Owner: inventario_user
--

ALTER TABLE ONLY inventario.agregacion_atributos_por_equipo
    ADD CONSTRAINT agreg_attr_equipo_id_empresa_fkey FOREIGN KEY (id_empresa) REFERENCES inventario.empresa(id_empresa);


--
-- TOC entry 5106 (class 2606 OID 17268)
-- Name: agregacion_atributos_por_equipo agregacion_atributos_por_equipo_id_atributo_equipo_fkey; Type: FK CONSTRAINT; Schema: inventario; Owner: inventario_user
--

ALTER TABLE ONLY inventario.agregacion_atributos_por_equipo
    ADD CONSTRAINT agregacion_atributos_por_equipo_id_atributo_equipo_fkey FOREIGN KEY (id_atributo_equipo) REFERENCES inventario.atributos_equipo(id_atributo_equipo) ON DELETE CASCADE;


--
-- TOC entry 5107 (class 2606 OID 17263)
-- Name: agregacion_atributos_por_equipo agregacion_atributos_por_equipo_id_equipo_fkey; Type: FK CONSTRAINT; Schema: inventario; Owner: inventario_user
--

ALTER TABLE ONLY inventario.agregacion_atributos_por_equipo
    ADD CONSTRAINT agregacion_atributos_por_equipo_id_equipo_fkey FOREIGN KEY (id_equipo) REFERENCES inventario.equipo(id_equipo) ON DELETE CASCADE;


--
-- TOC entry 5049 (class 2606 OID 17383)
-- Name: atributos_equipo atributos_equipo_id_empresa_fkey; Type: FK CONSTRAINT; Schema: inventario; Owner: inventario_user
--

ALTER TABLE ONLY inventario.atributos_equipo
    ADD CONSTRAINT atributos_equipo_id_empresa_fkey FOREIGN KEY (id_empresa) REFERENCES inventario.empresa(id_empresa);


--
-- TOC entry 5050 (class 2606 OID 16933)
-- Name: atributos_equipo atributos_equipo_id_tipo_equipo_fkey; Type: FK CONSTRAINT; Schema: inventario; Owner: inventario_user
--

ALTER TABLE ONLY inventario.atributos_equipo
    ADD CONSTRAINT atributos_equipo_id_tipo_equipo_fkey FOREIGN KEY (id_tipo_equipo) REFERENCES inventario.tipo_equipo(id_tipo_equipo) ON DELETE CASCADE;


--
-- TOC entry 5051 (class 2606 OID 16938)
-- Name: departamento departamento_id_empresa_fkey; Type: FK CONSTRAINT; Schema: inventario; Owner: inventario_user
--

ALTER TABLE ONLY inventario.departamento
    ADD CONSTRAINT departamento_id_empresa_fkey FOREIGN KEY (id_empresa) REFERENCES inventario.empresa(id_empresa) ON DELETE CASCADE;


--
-- TOC entry 5052 (class 2606 OID 17281)
-- Name: detalle_factura detalle_factura_id_empresa_fkey; Type: FK CONSTRAINT; Schema: inventario; Owner: inventario_user
--

ALTER TABLE ONLY inventario.detalle_factura
    ADD CONSTRAINT detalle_factura_id_empresa_fkey FOREIGN KEY (id_empresa) REFERENCES inventario.empresa(id_empresa);


--
-- TOC entry 5053 (class 2606 OID 16943)
-- Name: detalle_factura detalle_factura_id_equipo_fkey; Type: FK CONSTRAINT; Schema: inventario; Owner: inventario_user
--

ALTER TABLE ONLY inventario.detalle_factura
    ADD CONSTRAINT detalle_factura_id_equipo_fkey FOREIGN KEY (id_equipo) REFERENCES inventario.equipo(id_equipo) ON DELETE SET NULL;


--
-- TOC entry 5054 (class 2606 OID 16948)
-- Name: detalle_factura detalle_factura_id_factura_fkey; Type: FK CONSTRAINT; Schema: inventario; Owner: inventario_user
--

ALTER TABLE ONLY inventario.detalle_factura
    ADD CONSTRAINT detalle_factura_id_factura_fkey FOREIGN KEY (id_factura) REFERENCES inventario.factura(id_factura) ON DELETE CASCADE;


--
-- TOC entry 5055 (class 2606 OID 16953)
-- Name: empleado empleado_id_departamento_fkey; Type: FK CONSTRAINT; Schema: inventario; Owner: inventario_user
--

ALTER TABLE ONLY inventario.empleado
    ADD CONSTRAINT empleado_id_departamento_fkey FOREIGN KEY (id_departamento) REFERENCES inventario.departamento(id_departamento) ON DELETE RESTRICT;


--
-- TOC entry 5056 (class 2606 OID 16958)
-- Name: empleado empleado_id_empresa_fkey; Type: FK CONSTRAINT; Schema: inventario; Owner: inventario_user
--

ALTER TABLE ONLY inventario.empleado
    ADD CONSTRAINT empleado_id_empresa_fkey FOREIGN KEY (id_empresa) REFERENCES inventario.empresa(id_empresa) ON DELETE CASCADE;


--
-- TOC entry 5057 (class 2606 OID 17138)
-- Name: empleado empleado_user_id_fkey; Type: FK CONSTRAINT; Schema: inventario; Owner: inventario_user
--

ALTER TABLE ONLY inventario.empleado
    ADD CONSTRAINT empleado_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.auth_user(id) ON DELETE SET NULL;


--
-- TOC entry 5058 (class 2606 OID 17129)
-- Name: equipo equipo_departamento_id_fkey; Type: FK CONSTRAINT; Schema: inventario; Owner: inventario_user
--

ALTER TABLE ONLY inventario.equipo
    ADD CONSTRAINT equipo_departamento_id_fkey FOREIGN KEY (departamento_id) REFERENCES inventario.departamento(id_departamento);


--
-- TOC entry 5059 (class 2606 OID 17124)
-- Name: equipo equipo_empresa_id_fkey; Type: FK CONSTRAINT; Schema: inventario; Owner: inventario_user
--

ALTER TABLE ONLY inventario.equipo
    ADD CONSTRAINT equipo_empresa_id_fkey FOREIGN KEY (id_empresa) REFERENCES inventario.empresa(id_empresa);


--
-- TOC entry 5060 (class 2606 OID 16963)
-- Name: equipo equipo_id_empleado_fkey; Type: FK CONSTRAINT; Schema: inventario; Owner: inventario_user
--

ALTER TABLE ONLY inventario.equipo
    ADD CONSTRAINT equipo_id_empleado_fkey FOREIGN KEY (id_empleado) REFERENCES inventario.empleado(id_empleado) ON DELETE SET NULL;


--
-- TOC entry 5061 (class 2606 OID 16968)
-- Name: equipo equipo_id_estado_equipo_fkey; Type: FK CONSTRAINT; Schema: inventario; Owner: inventario_user
--

ALTER TABLE ONLY inventario.equipo
    ADD CONSTRAINT equipo_id_estado_equipo_fkey FOREIGN KEY (id_estado_equipo) REFERENCES inventario.estado_equipo(id_estado_equipo) ON DELETE SET NULL;


--
-- TOC entry 5062 (class 2606 OID 16973)
-- Name: equipo equipo_id_marca_fkey; Type: FK CONSTRAINT; Schema: inventario; Owner: inventario_user
--

ALTER TABLE ONLY inventario.equipo
    ADD CONSTRAINT equipo_id_marca_fkey FOREIGN KEY (id_marca) REFERENCES inventario.marca(id_marca) ON DELETE RESTRICT;


--
-- TOC entry 5063 (class 2606 OID 16978)
-- Name: equipo equipo_id_proveedor_fkey; Type: FK CONSTRAINT; Schema: inventario; Owner: inventario_user
--

ALTER TABLE ONLY inventario.equipo
    ADD CONSTRAINT equipo_id_proveedor_fkey FOREIGN KEY (id_proveedor) REFERENCES inventario.proveedor(id_proveedor) ON DELETE SET NULL;


--
-- TOC entry 5064 (class 2606 OID 16983)
-- Name: equipo equipo_id_tipo_equipo_fkey; Type: FK CONSTRAINT; Schema: inventario; Owner: inventario_user
--

ALTER TABLE ONLY inventario.equipo
    ADD CONSTRAINT equipo_id_tipo_equipo_fkey FOREIGN KEY (id_tipo_equipo) REFERENCES inventario.tipo_equipo(id_tipo_equipo) ON DELETE RESTRICT;


--
-- TOC entry 5065 (class 2606 OID 17403)
-- Name: estado_equipo estado_equipo_id_empresa_fkey; Type: FK CONSTRAINT; Schema: inventario; Owner: inventario_user
--

ALTER TABLE ONLY inventario.estado_equipo
    ADD CONSTRAINT estado_equipo_id_empresa_fkey FOREIGN KEY (id_empresa) REFERENCES inventario.empresa(id_empresa);


--
-- TOC entry 5066 (class 2606 OID 17398)
-- Name: estado_mantencion estado_mantencion_id_empresa_fkey; Type: FK CONSTRAINT; Schema: inventario; Owner: inventario_user
--

ALTER TABLE ONLY inventario.estado_mantencion
    ADD CONSTRAINT estado_mantencion_id_empresa_fkey FOREIGN KEY (id_empresa) REFERENCES inventario.empresa(id_empresa);


--
-- TOC entry 5067 (class 2606 OID 17311)
-- Name: factura factura_id_empresa_fkey; Type: FK CONSTRAINT; Schema: inventario; Owner: inventario_user
--

ALTER TABLE ONLY inventario.factura
    ADD CONSTRAINT factura_id_empresa_fkey FOREIGN KEY (id_empresa) REFERENCES inventario.empresa(id_empresa);


--
-- TOC entry 5068 (class 2606 OID 16988)
-- Name: factura factura_id_proveedor_fkey; Type: FK CONSTRAINT; Schema: inventario; Owner: inventario_user
--

ALTER TABLE ONLY inventario.factura
    ADD CONSTRAINT factura_id_proveedor_fkey FOREIGN KEY (id_proveedor) REFERENCES inventario.proveedor(id_proveedor) ON DELETE SET NULL;


--
-- TOC entry 5103 (class 2606 OID 17234)
-- Name: historial_mantenciones_log fk_hist_mant_mantencion; Type: FK CONSTRAINT; Schema: inventario; Owner: inventario_user
--

ALTER TABLE ONLY inventario.historial_mantenciones_log
    ADD CONSTRAINT fk_hist_mant_mantencion FOREIGN KEY (id_mantencion) REFERENCES inventario.mantencion(id_mantencion) ON DELETE CASCADE;


--
-- TOC entry 5069 (class 2606 OID 17241)
-- Name: mantencion fk_mantencion_responsable; Type: FK CONSTRAINT; Schema: inventario; Owner: inventario_user
--

ALTER TABLE ONLY inventario.mantencion
    ADD CONSTRAINT fk_mantencion_responsable FOREIGN KEY (responsable_id) REFERENCES inventario.empleado(id_empleado);


--
-- TOC entry 5070 (class 2606 OID 17246)
-- Name: mantencion fk_mantencion_solicitante_user; Type: FK CONSTRAINT; Schema: inventario; Owner: inventario_user
--

ALTER TABLE ONLY inventario.mantencion
    ADD CONSTRAINT fk_mantencion_solicitante_user FOREIGN KEY (solicitante_user_id) REFERENCES public.auth_user(id);


--
-- TOC entry 5101 (class 2606 OID 17293)
-- Name: historial_mantenciones hist_mant_id_empresa_fkey; Type: FK CONSTRAINT; Schema: inventario; Owner: inventario_user
--

ALTER TABLE ONLY inventario.historial_mantenciones
    ADD CONSTRAINT hist_mant_id_empresa_fkey FOREIGN KEY (id_empresa) REFERENCES inventario.empresa(id_empresa);


--
-- TOC entry 5104 (class 2606 OID 17299)
-- Name: historial_mantenciones_log hist_mant_log_id_empresa_fkey; Type: FK CONSTRAINT; Schema: inventario; Owner: inventario_user
--

ALTER TABLE ONLY inventario.historial_mantenciones_log
    ADD CONSTRAINT hist_mant_log_id_empresa_fkey FOREIGN KEY (id_empresa) REFERENCES inventario.empresa(id_empresa);


--
-- TOC entry 5090 (class 2606 OID 17091)
-- Name: historial_equipos historial_equipos_departamento_id_fkey; Type: FK CONSTRAINT; Schema: inventario; Owner: inventario_user
--

ALTER TABLE ONLY inventario.historial_equipos
    ADD CONSTRAINT historial_equipos_departamento_id_fkey FOREIGN KEY (departamento_id) REFERENCES inventario.departamento(id_departamento);


--
-- TOC entry 5091 (class 2606 OID 17086)
-- Name: historial_equipos historial_equipos_empresa_id_fkey; Type: FK CONSTRAINT; Schema: inventario; Owner: inventario_user
--

ALTER TABLE ONLY inventario.historial_equipos
    ADD CONSTRAINT historial_equipos_empresa_id_fkey FOREIGN KEY (id_empresa) REFERENCES inventario.empresa(id_empresa);


--
-- TOC entry 5092 (class 2606 OID 17071)
-- Name: historial_equipos historial_equipos_equipo_id_fkey; Type: FK CONSTRAINT; Schema: inventario; Owner: inventario_user
--

ALTER TABLE ONLY inventario.historial_equipos
    ADD CONSTRAINT historial_equipos_equipo_id_fkey FOREIGN KEY (equipo_id) REFERENCES inventario.equipo(id_equipo) ON DELETE CASCADE;


--
-- TOC entry 5093 (class 2606 OID 17096)
-- Name: historial_equipos historial_equipos_estado_anterior_id_fkey; Type: FK CONSTRAINT; Schema: inventario; Owner: inventario_user
--

ALTER TABLE ONLY inventario.historial_equipos
    ADD CONSTRAINT historial_equipos_estado_anterior_id_fkey FOREIGN KEY (estado_anterior_id) REFERENCES inventario.estado_equipo(id_estado_equipo);


--
-- TOC entry 5094 (class 2606 OID 17101)
-- Name: historial_equipos historial_equipos_estado_nuevo_id_fkey; Type: FK CONSTRAINT; Schema: inventario; Owner: inventario_user
--

ALTER TABLE ONLY inventario.historial_equipos
    ADD CONSTRAINT historial_equipos_estado_nuevo_id_fkey FOREIGN KEY (estado_nuevo_id) REFERENCES inventario.estado_equipo(id_estado_equipo);


--
-- TOC entry 5095 (class 2606 OID 17106)
-- Name: historial_equipos historial_equipos_responsable_actual_id_fkey; Type: FK CONSTRAINT; Schema: inventario; Owner: inventario_user
--

ALTER TABLE ONLY inventario.historial_equipos
    ADD CONSTRAINT historial_equipos_responsable_actual_id_fkey FOREIGN KEY (responsable_actual_id) REFERENCES inventario.empleado(id_empleado);


--
-- TOC entry 5096 (class 2606 OID 17118)
-- Name: historial_equipos historial_equipos_responsable_anterior_id_fkey; Type: FK CONSTRAINT; Schema: inventario; Owner: inventario_user
--

ALTER TABLE ONLY inventario.historial_equipos
    ADD CONSTRAINT historial_equipos_responsable_anterior_id_fkey FOREIGN KEY (responsable_anterior_id) REFERENCES inventario.empleado(id_empleado) ON DELETE SET NULL;


--
-- TOC entry 5097 (class 2606 OID 17076)
-- Name: historial_equipos historial_equipos_tipo_equipo_id_fkey; Type: FK CONSTRAINT; Schema: inventario; Owner: inventario_user
--

ALTER TABLE ONLY inventario.historial_equipos
    ADD CONSTRAINT historial_equipos_tipo_equipo_id_fkey FOREIGN KEY (tipo_equipo_id) REFERENCES inventario.tipo_equipo(id_tipo_equipo);


--
-- TOC entry 5098 (class 2606 OID 17081)
-- Name: historial_equipos historial_equipos_usuario_id_fkey; Type: FK CONSTRAINT; Schema: inventario; Owner: inventario_user
--

ALTER TABLE ONLY inventario.historial_equipos
    ADD CONSTRAINT historial_equipos_usuario_id_fkey FOREIGN KEY (usuario_id) REFERENCES inventario.empleado(id_empleado);


--
-- TOC entry 5102 (class 2606 OID 17204)
-- Name: historial_mantenciones historial_mant_usuario_fk; Type: FK CONSTRAINT; Schema: inventario; Owner: inventario_user
--

ALTER TABLE ONLY inventario.historial_mantenciones
    ADD CONSTRAINT historial_mant_usuario_fk FOREIGN KEY (usuario_app) REFERENCES public.auth_user(id) ON DELETE SET NULL;


--
-- TOC entry 5071 (class 2606 OID 17174)
-- Name: mantencion mantencion_empleado_resp_fk; Type: FK CONSTRAINT; Schema: inventario; Owner: inventario_user
--

ALTER TABLE ONLY inventario.mantencion
    ADD CONSTRAINT mantencion_empleado_resp_fk FOREIGN KEY (id_empleado_responsable) REFERENCES inventario.empleado(id_empleado) ON DELETE SET NULL;


--
-- TOC entry 5072 (class 2606 OID 17179)
-- Name: mantencion mantencion_empleado_solic_fk; Type: FK CONSTRAINT; Schema: inventario; Owner: inventario_user
--

ALTER TABLE ONLY inventario.mantencion
    ADD CONSTRAINT mantencion_empleado_solic_fk FOREIGN KEY (id_empleado_solicitante) REFERENCES inventario.empleado(id_empleado) ON DELETE SET NULL;


--
-- TOC entry 5073 (class 2606 OID 17287)
-- Name: mantencion mantencion_id_empresa_fkey; Type: FK CONSTRAINT; Schema: inventario; Owner: inventario_user
--

ALTER TABLE ONLY inventario.mantencion
    ADD CONSTRAINT mantencion_id_empresa_fkey FOREIGN KEY (id_empresa) REFERENCES inventario.empresa(id_empresa);


--
-- TOC entry 5074 (class 2606 OID 16993)
-- Name: mantencion mantencion_id_equipo_fkey; Type: FK CONSTRAINT; Schema: inventario; Owner: inventario_user
--

ALTER TABLE ONLY inventario.mantencion
    ADD CONSTRAINT mantencion_id_equipo_fkey FOREIGN KEY (id_equipo) REFERENCES inventario.equipo(id_equipo) ON DELETE CASCADE;


--
-- TOC entry 5075 (class 2606 OID 16998)
-- Name: mantencion mantencion_id_estado_mantencion_fkey; Type: FK CONSTRAINT; Schema: inventario; Owner: inventario_user
--

ALTER TABLE ONLY inventario.mantencion
    ADD CONSTRAINT mantencion_id_estado_mantencion_fkey FOREIGN KEY (id_estado_mantencion) REFERENCES inventario.estado_mantencion(id_estado_mantencion) ON DELETE RESTRICT;


--
-- TOC entry 5076 (class 2606 OID 17169)
-- Name: mantencion mantencion_prioridad_fk; Type: FK CONSTRAINT; Schema: inventario; Owner: inventario_user
--

ALTER TABLE ONLY inventario.mantencion
    ADD CONSTRAINT mantencion_prioridad_fk FOREIGN KEY (id_prioridad) REFERENCES inventario.prioridad_mantencion(id_prioridad) ON DELETE RESTRICT;


--
-- TOC entry 5077 (class 2606 OID 17164)
-- Name: mantencion mantencion_tipo_fk; Type: FK CONSTRAINT; Schema: inventario; Owner: inventario_user
--

ALTER TABLE ONLY inventario.mantencion
    ADD CONSTRAINT mantencion_tipo_fk FOREIGN KEY (id_tipo_mantencion) REFERENCES inventario.tipo_mantencion(id_tipo_mantencion) ON DELETE RESTRICT;


--
-- TOC entry 5078 (class 2606 OID 17368)
-- Name: marca marca_id_empresa_fkey; Type: FK CONSTRAINT; Schema: inventario; Owner: inventario_user
--

ALTER TABLE ONLY inventario.marca
    ADD CONSTRAINT marca_id_empresa_fkey FOREIGN KEY (id_empresa) REFERENCES inventario.empresa(id_empresa);


--
-- TOC entry 5100 (class 2606 OID 17393)
-- Name: prioridad_mantencion prioridad_mantencion_id_empresa_fkey; Type: FK CONSTRAINT; Schema: inventario; Owner: inventario_user
--

ALTER TABLE ONLY inventario.prioridad_mantencion
    ADD CONSTRAINT prioridad_mantencion_id_empresa_fkey FOREIGN KEY (id_empresa) REFERENCES inventario.empresa(id_empresa);


--
-- TOC entry 5079 (class 2606 OID 17373)
-- Name: proveedor proveedor_id_empresa_fkey; Type: FK CONSTRAINT; Schema: inventario; Owner: inventario_user
--

ALTER TABLE ONLY inventario.proveedor
    ADD CONSTRAINT proveedor_id_empresa_fkey FOREIGN KEY (id_empresa) REFERENCES inventario.empresa(id_empresa);


--
-- TOC entry 5080 (class 2606 OID 17378)
-- Name: tipo_equipo tipo_equipo_id_empresa_fkey; Type: FK CONSTRAINT; Schema: inventario; Owner: inventario_user
--

ALTER TABLE ONLY inventario.tipo_equipo
    ADD CONSTRAINT tipo_equipo_id_empresa_fkey FOREIGN KEY (id_empresa) REFERENCES inventario.empresa(id_empresa);


--
-- TOC entry 5099 (class 2606 OID 17388)
-- Name: tipo_mantencion tipo_mantencion_id_empresa_fkey; Type: FK CONSTRAINT; Schema: inventario; Owner: inventario_user
--

ALTER TABLE ONLY inventario.tipo_mantencion
    ADD CONSTRAINT tipo_mantencion_id_empresa_fkey FOREIGN KEY (id_empresa) REFERENCES inventario.empresa(id_empresa);


--
-- TOC entry 5081 (class 2606 OID 17003)
-- Name: auth_group_permissions auth_group_permissio_permission_id_84c5c92e_fk_auth_perm; Type: FK CONSTRAINT; Schema: public; Owner: inventario_user
--

ALTER TABLE ONLY public.auth_group_permissions
    ADD CONSTRAINT auth_group_permissio_permission_id_84c5c92e_fk_auth_perm FOREIGN KEY (permission_id) REFERENCES public.auth_permission(id) DEFERRABLE INITIALLY DEFERRED;


--
-- TOC entry 5082 (class 2606 OID 17008)
-- Name: auth_group_permissions auth_group_permissions_group_id_b120cbf9_fk_auth_group_id; Type: FK CONSTRAINT; Schema: public; Owner: inventario_user
--

ALTER TABLE ONLY public.auth_group_permissions
    ADD CONSTRAINT auth_group_permissions_group_id_b120cbf9_fk_auth_group_id FOREIGN KEY (group_id) REFERENCES public.auth_group(id) DEFERRABLE INITIALLY DEFERRED;


--
-- TOC entry 5083 (class 2606 OID 17013)
-- Name: auth_permission auth_permission_content_type_id_2f476e4b_fk_django_co; Type: FK CONSTRAINT; Schema: public; Owner: inventario_user
--

ALTER TABLE ONLY public.auth_permission
    ADD CONSTRAINT auth_permission_content_type_id_2f476e4b_fk_django_co FOREIGN KEY (content_type_id) REFERENCES public.django_content_type(id) DEFERRABLE INITIALLY DEFERRED;


--
-- TOC entry 5084 (class 2606 OID 17018)
-- Name: auth_user_groups auth_user_groups_group_id_97559544_fk_auth_group_id; Type: FK CONSTRAINT; Schema: public; Owner: inventario_user
--

ALTER TABLE ONLY public.auth_user_groups
    ADD CONSTRAINT auth_user_groups_group_id_97559544_fk_auth_group_id FOREIGN KEY (group_id) REFERENCES public.auth_group(id) DEFERRABLE INITIALLY DEFERRED;


--
-- TOC entry 5085 (class 2606 OID 17023)
-- Name: auth_user_groups auth_user_groups_user_id_6a12ed8b_fk_auth_user_id; Type: FK CONSTRAINT; Schema: public; Owner: inventario_user
--

ALTER TABLE ONLY public.auth_user_groups
    ADD CONSTRAINT auth_user_groups_user_id_6a12ed8b_fk_auth_user_id FOREIGN KEY (user_id) REFERENCES public.auth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- TOC entry 5086 (class 2606 OID 17028)
-- Name: auth_user_user_permissions auth_user_user_permi_permission_id_1fbb5f2c_fk_auth_perm; Type: FK CONSTRAINT; Schema: public; Owner: inventario_user
--

ALTER TABLE ONLY public.auth_user_user_permissions
    ADD CONSTRAINT auth_user_user_permi_permission_id_1fbb5f2c_fk_auth_perm FOREIGN KEY (permission_id) REFERENCES public.auth_permission(id) DEFERRABLE INITIALLY DEFERRED;


--
-- TOC entry 5087 (class 2606 OID 17033)
-- Name: auth_user_user_permissions auth_user_user_permissions_user_id_a95ead1b_fk_auth_user_id; Type: FK CONSTRAINT; Schema: public; Owner: inventario_user
--

ALTER TABLE ONLY public.auth_user_user_permissions
    ADD CONSTRAINT auth_user_user_permissions_user_id_a95ead1b_fk_auth_user_id FOREIGN KEY (user_id) REFERENCES public.auth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- TOC entry 5088 (class 2606 OID 17038)
-- Name: django_admin_log django_admin_log_content_type_id_c4bce8eb_fk_django_co; Type: FK CONSTRAINT; Schema: public; Owner: inventario_user
--

ALTER TABLE ONLY public.django_admin_log
    ADD CONSTRAINT django_admin_log_content_type_id_c4bce8eb_fk_django_co FOREIGN KEY (content_type_id) REFERENCES public.django_content_type(id) DEFERRABLE INITIALLY DEFERRED;


--
-- TOC entry 5089 (class 2606 OID 17043)
-- Name: django_admin_log django_admin_log_user_id_c564eba6_fk_auth_user_id; Type: FK CONSTRAINT; Schema: public; Owner: inventario_user
--

ALTER TABLE ONLY public.django_admin_log
    ADD CONSTRAINT django_admin_log_user_id_c564eba6_fk_auth_user_id FOREIGN KEY (user_id) REFERENCES public.auth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- TOC entry 2192 (class 826 OID 16391)
-- Name: DEFAULT PRIVILEGES FOR SEQUENCES; Type: DEFAULT ACL; Schema: public; Owner: postgres
--

ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public GRANT ALL ON SEQUENCES TO inventario_user;


--
-- TOC entry 2191 (class 826 OID 16390)
-- Name: DEFAULT PRIVILEGES FOR TABLES; Type: DEFAULT ACL; Schema: public; Owner: postgres
--

ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public GRANT ALL ON TABLES TO inventario_user;


-- Completed on 2025-09-25 15:40:02

--
-- PostgreSQL database dump complete
--

\unrestrict vBSuciq18k7Pd7JJeavS1dmqgXTMumbvXznw8DaRPpbgN5efRq2FeUKEJtWPbyp

