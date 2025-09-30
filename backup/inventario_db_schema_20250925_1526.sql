--
-- PostgreSQL database dump
--

\restrict UPt4sZXlUT77ogWQhsKXoikzgv1kcBl2AEjtgxhSp9a0DbLrhOThwqK4pzAzSAh

-- Dumped from database version 17.6
-- Dumped by pg_dump version 17.6

-- Started on 2025-09-25 15:26:41

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
-- TOC entry 5263 (class 0 OID 0)
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
-- TOC entry 5264 (class 0 OID 0)
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
-- TOC entry 5265 (class 0 OID 0)
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
-- TOC entry 5266 (class 0 OID 0)
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
-- TOC entry 5267 (class 0 OID 0)
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
-- TOC entry 5268 (class 0 OID 0)
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


-- Completed on 2025-09-25 15:26:46

--
-- PostgreSQL database dump complete
--

\unrestrict UPt4sZXlUT77ogWQhsKXoikzgv1kcBl2AEjtgxhSp9a0DbLrhOThwqK4pzAzSAh

