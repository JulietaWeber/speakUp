
const supabase = require("../config/Supabase");

const CAMPOS_TABLERO =
  "id_tablero, id_usuario, nombre, color, icono, es_publico, fecha_creacion";

const CAMPOS_RELACIONES = `
  id_tablero_pictogramas,
  id_tablero,
  id_pictogramas,
  posicion_x,
  posicion_y,
  pictogramas (
    id_pictogramas,
    id_categorias,
    nombre,
    imagen_url,
    audio_url,
    es_personalizado
  )
`;

// =====================
// Helpers
// =====================

const ok = (res, data, status = 200) =>
  res.status(status).json({ data, error: null });

const fallo = (res, status, mensaje) =>
  res.status(status).json({ data: null, error: mensaje });

const errorInterno = (res, error) =>
  fallo(res, 500, error.message);

const idValido = (valor) => {
  const numero = Number(valor);
  return Number.isSafeInteger(numero) && numero > 0;
};

const registrarAccion = async (id_usuario, accion, detalle) => {
  const { error } = await supabase
    .from("historial_uso")
    .insert([{ id_usuario, accion, detalle }]);

  if (error) {
    console.error("No se pudo registrar historial_uso:", error.message);
  }
};

// Comprueba que el tablero exista y pertenezca al usuario.
const buscarTableroPropio = async (
  id_tablero,
  id_usuario,
  columnas = CAMPOS_TABLERO
) => {
  const { data, error } = await supabase
    .from("tableros")
    .select(columnas)
    .eq("id_tablero", id_tablero)
    .maybeSingle();

  if (error) {
    return { status: 500, mensaje: error.message };
  }

  if (!data) {
    return { status: 404, mensaje: "Tablero no encontrado" };
  }

  if (Number(data.id_usuario) !== Number(id_usuario)) {
    return {
      status: 403,
      mensaje: "No tenés permiso para acceder a este tablero"
    };
  }

  return { tablero: data };
};

const obtenerRelaciones = (id_tablero) =>
  supabase
    .from("tableros_pictogramas")
    .select(CAMPOS_RELACIONES)
    .eq("id_tablero", id_tablero)
    .order("posicion_y", { ascending: true })
    .order("posicion_x", { ascending: true });

// =====================
// GET /tableros/mis-tableros
// =====================

const obtenerMisTableros = async (req, res) => {
  try {
    const { data, error } = await supabase
      .from("tableros")
      .select(CAMPOS_TABLERO)
      .eq("id_usuario", req.usuario.id_usuario)
      .order("fecha_creacion", { ascending: false });

    if (error) return errorInterno(res, error);

    return ok(res, data);
  } catch (error) {
    return errorInterno(res, error);
  }
};

// =====================
// POST /tableros
// =====================

const crearTablero = async (req, res) => {
  try {
    const id_usuario = req.usuario.id_usuario;
    const { nombre, color, icono, es_publico } = req.body || {};

    if (typeof nombre !== "string" || !nombre.trim()) {
      return fallo(res, 400, "El nombre del tablero es obligatorio");
    }

    if (es_publico !== undefined && typeof es_publico !== "boolean") {
      return fallo(res, 400, "es_publico debe ser verdadero o falso");
    }

    const { data, error } = await supabase
      .from("tableros")
      .insert([
        {
          id_usuario,
          nombre: nombre.trim(),
          color: color || "#FFFFFF",
          icono: icono || null,
          es_publico: es_publico ?? false
        }
      ])
      .select(CAMPOS_TABLERO)
      .single();

    if (error) return errorInterno(res, error);

    await registrarAccion(
      id_usuario,
      "crear_tablero",
      `Tablero creado: ${data.nombre}`
    );

    return ok(res, data, 201);
  } catch (error) {
    return errorInterno(res, error);
  }
};

// =====================
// GET /tableros/:id_tablero/pictogramas
// =====================

const obtenerPictogramasDeTablero = async (req, res) => {
  try {
    const { id_tablero } = req.params;

    if (!idValido(id_tablero)) {
      return fallo(res, 400, "ID de tablero inválido");
    }

    const acceso = await buscarTableroPropio(
      id_tablero,
      req.usuario.id_usuario
    );

    if (acceso.mensaje) {
      return fallo(res, acceso.status, acceso.mensaje);
    }

    const { data, error } = await obtenerRelaciones(id_tablero);

    if (error) return errorInterno(res, error);

    return ok(res, data);
  } catch (error) {
    return errorInterno(res, error);
  }
};

// =====================
// POST /tableros/:id_tablero/pictogramas
// =====================

const agregarPictogramaATablero = async (req, res) => {
  try {
    const id_usuario = req.usuario.id_usuario;
    const { id_tablero } = req.params;
    const { id_pictogramas, posicion_x, posicion_y } = req.body || {};

    if (!idValido(id_tablero)) {
      return fallo(res, 400, "ID de tablero inválido");
    }

    if (!idValido(id_pictogramas)) {
      return fallo(res, 400, "Falta id_pictogramas válido");
    }

    for (const posicion of [posicion_x, posicion_y]) {
      if (
        posicion !== undefined &&
        (!Number.isInteger(posicion) || posicion < 0)
      ) {
        return fallo(
          res,
          400,
          "Las posiciones deben ser enteros no negativos"
        );
      }
    }

    const acceso = await buscarTableroPropio(id_tablero, id_usuario);

    if (acceso.mensaje) {
      return fallo(res, acceso.status, acceso.mensaje);
    }

    const { data: pictograma, error: pictogramaError } = await supabase
      .from("pictogramas")
      .select("id_pictogramas, nombre, es_personalizado")
      .eq("id_pictogramas", id_pictogramas)
      .maybeSingle();

    if (pictogramaError) {
      return errorInterno(res, pictogramaError);
    }

    if (!pictograma) {
      return fallo(res, 404, "Pictograma no encontrado");
    }

    // Los pictogramas personales deben pertenecer al usuario.
    if (pictograma.es_personalizado) {
      const { data: asociacion, error: asociacionError } = await supabase
        .from("usuarios_pictogramas")
        .select("id_pictogramas")
        .eq("id_usuario", id_usuario)
        .eq("id_pictogramas", id_pictogramas)
        .maybeSingle();

      if (asociacionError) {
        return errorInterno(res, asociacionError);
      }

      if (!asociacion) {
        return fallo(
          res,
          403,
          "No tenés permiso para usar este pictograma personalizado"
        );
      }
    }

    const { data, error } = await supabase
      .from("tableros_pictogramas")
      .insert([
        {
          id_tablero,
          id_pictogramas,
          posicion_x: posicion_x ?? 0,
          posicion_y: posicion_y ?? 0
        }
      ])
      .select()
      .single();

    if (error) return errorInterno(res, error);

    await registrarAccion(
      id_usuario,
      "agregar_pictograma_tablero",
      `Pictograma agregado al tablero: ${pictograma.nombre}`
    );

    return ok(res, data, 201);
  } catch (error) {
    return errorInterno(res, error);
  }
};

// =====================
// DELETE /tableros/:id_tablero/pictogramas/:id_pictogramas
// =====================

const eliminarPictogramaDeTablero = async (req, res) => {
  try {
    const id_usuario = req.usuario.id_usuario;
    const { id_tablero, id_pictogramas } = req.params;

    if (!idValido(id_tablero) || !idValido(id_pictogramas)) {
      return fallo(
        res,
        400,
        "ID de tablero o pictograma inválido"
      );
    }

    const acceso = await buscarTableroPropio(id_tablero, id_usuario);

    if (acceso.mensaje) {
      return fallo(res, acceso.status, acceso.mensaje);
    }

    const { error } = await supabase
      .from("tableros_pictogramas")
      .delete()
      .eq("id_tablero", id_tablero)
      .eq("id_pictogramas", id_pictogramas);

    if (error) return errorInterno(res, error);

    await registrarAccion(
      id_usuario,
      "eliminar_pictograma_tablero",
      `Pictograma eliminado del tablero ${id_tablero}`
    );

    return ok(res, {
      mensaje: "Pictograma eliminado del tablero"
    });
  } catch (error) {
    return errorInterno(res, error);
  }
};

// =====================
// GET /tableros/:id_tablero/completo
// =====================

const obtenerTableroCompleto = async (req, res) => {
  try {
    const { id_tablero } = req.params;

    if (!idValido(id_tablero)) {
      return fallo(res, 400, "ID de tablero inválido");
    }

    const acceso = await buscarTableroPropio(
      id_tablero,
      req.usuario.id_usuario
    );

    if (acceso.mensaje) {
      return fallo(res, acceso.status, acceso.mensaje);
    }

    const { data: relaciones, error } =
      await obtenerRelaciones(id_tablero);

    if (error) return errorInterno(res, error);

    const pictogramas = relaciones.map((relacion) => ({
      id_tablero_pictogramas: relacion.id_tablero_pictogramas,
      id_pictogramas: relacion.id_pictogramas,
      posicion_x: relacion.posicion_x,
      posicion_y: relacion.posicion_y,
      ...(relacion.pictogramas || {})
    }));

    return ok(res, {
      ...acceso.tablero,
      pictogramas
    });
  } catch (error) {
    return errorInterno(res, error);
  }
};

// =====================
// PUT /tableros/:id_tablero
// =====================

const actualizarTablero = async (req, res) => {
  try {
    const id_usuario = req.usuario.id_usuario;
    const { id_tablero } = req.params;

    if (!idValido(id_tablero)) {
      return fallo(res, 400, "ID de tablero inválido");
    }

    const acceso = await buscarTableroPropio(id_tablero, id_usuario);

    if (acceso.mensaje) {
      return fallo(res, acceso.status, acceso.mensaje);
    }

    const { nombre, color, icono, es_publico } = req.body || {};
    const cambios = {};

    if (nombre !== undefined) {
      if (typeof nombre !== "string" || !nombre.trim()) {
        return fallo(
          res,
          400,
          "El nombre del tablero es obligatorio"
        );
      }

      cambios.nombre = nombre.trim();
    }

    if (color !== undefined) cambios.color = color;
    if (icono !== undefined) cambios.icono = icono;

    if (es_publico !== undefined) {
      if (typeof es_publico !== "boolean") {
        return fallo(
          res,
          400,
          "es_publico debe ser verdadero o falso"
        );
      }

      cambios.es_publico = es_publico;
    }

    if (!Object.keys(cambios).length) {
      return fallo(res, 400, "No enviaste campos para actualizar");
    }

    const { data, error } = await supabase
      .from("tableros")
      .update(cambios)
      .eq("id_tablero", id_tablero)
      .eq("id_usuario", id_usuario)
      .select(CAMPOS_TABLERO)
      .maybeSingle();

    if (error) return errorInterno(res, error);

    if (!data) {
      return fallo(
        res,
        404,
        "Tablero no encontrado o sin permisos"
      );
    }

    await registrarAccion(
      id_usuario,
      "actualizar_tablero",
      `Tablero actualizado: ${data.nombre}`
    );

    return ok(res, data);
  } catch (error) {
    return errorInterno(res, error);
  }
};

// =====================
// DELETE /tableros/:id_tablero
// =====================

const eliminarTablero = async (req, res) => {
  try {
    const id_usuario = req.usuario.id_usuario;
    const { id_tablero } = req.params;

    if (!idValido(id_tablero)) {
      return fallo(res, 400, "ID de tablero inválido");
    }

    const acceso = await buscarTableroPropio(
      id_tablero,
      id_usuario,
      "id_tablero, id_usuario, nombre"
    );

    if (acceso.mensaje) {
      return fallo(res, acceso.status, acceso.mensaje);
    }

    // Primero eliminar las relaciones del tablero.
    const { error: relacionesError } = await supabase
      .from("tableros_pictogramas")
      .delete()
      .eq("id_tablero", id_tablero);

    if (relacionesError) {
      return errorInterno(res, relacionesError);
    }

    const { data: eliminado, error } = await supabase
      .from("tableros")
      .delete()
      .eq("id_tablero", id_tablero)
      .eq("id_usuario", id_usuario)
      .select("id_tablero")
      .maybeSingle();

    if (error) return errorInterno(res, error);

    if (!eliminado) {
      return fallo(
        res,
        404,
        "Tablero no encontrado o sin permisos"
      );
    }

    await registrarAccion(
      id_usuario,
      "eliminar_tablero",
      `Tablero eliminado: ${acceso.tablero.nombre}`
    );

    return ok(res, {
      mensaje: "Tablero eliminado correctamente"
    });
  } catch (error) {
    return errorInterno(res, error);
  }
};

// =====================
// Exports
// =====================

module.exports = {
  obtenerMisTableros,
  crearTablero,
  obtenerPictogramasDeTablero,
  agregarPictogramaATablero,
  eliminarPictogramaDeTablero,
  obtenerTableroCompleto,
  actualizarTablero,
  eliminarTablero
};
