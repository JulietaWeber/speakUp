
const supabase = require("../config/Supabase");
const supabaseAdmin = require("../config/SupabaseAdmin");
const crypto = require("crypto");

const CAMPOS =
  "id_pictogramas, id_categorias, nombre, imagen_url, audio_url, es_personalizado";

// =====================
// HELPERS GENERALES
// =====================

const ok = (res, data, status = 200) =>
  res.status(status).json({ data, error: null });

const fallo = (res, status, error) =>
  res.status(status).json({ data: null, error });

const texto = (x) =>
  typeof x === "string" ? x.trim() : "";

const idValido = (x) =>
  Number.isSafeInteger(Number(x)) && Number(x) > 0;

const nombreComparable = (x) =>
  texto(x).toLocaleLowerCase("es");

const validarNombre = (nombre) => {
  const n = texto(nombre);

  if (!n) {
    return "El nombre del pictograma no puede estar vacío";
  }

  if (n.length < 2) {
    return "El nombre del pictograma debe tener al menos 2 caracteres";
  }

  if (n.length > 50) {
    return "El nombre del pictograma no puede superar los 50 caracteres";
  }

  if (["poronga", "pete"].includes(nombreComparable(n))) {
    return "El nombre del pictograma no está permitido";
  }

  return null;
};

const registrarHistorial = async (
  id_usuario,
  accion,
  detalle
) => {
  const { error } = await supabase
    .from("historial_uso")
    .insert([{ id_usuario, accion, detalle }]);

  if (error) {
    console.error("Error en historial_uso:", error.message);
  }
};

// =====================
// CATEGORÍAS
// =====================

const buscarCategoria = async (id) => {
  const { data, error } = await supabase
    .from("categorias")
    .select(
      "id_categorias, nombre, id_usuario, es_personalizada"
    )
    .eq("id_categorias", id)
    .maybeSingle();

  if (error) throw error;

  return data;
};

const esCategoriaGeneral = (categoria) =>
  categoria.id_usuario === null &&
  categoria.es_personalizada === false;

const categoriaAccesible = (categoria, usuario) =>
  esCategoriaGeneral(categoria) ||
  Number(categoria.id_usuario) === Number(usuario);

const validarCategoria = async (
  res,
  id,
  usuario,
  general = false
) => {
  if (!idValido(id)) {
    return {
      respuesta: fallo(
        res,
        400,
        "ID de categoría inválido"
      )
    };
  }

  const categoria = await buscarCategoria(id);

  if (!categoria) {
    return {
      respuesta: fallo(
        res,
        404,
        "Categoría no encontrada"
      )
    };
  }

  if (general && !esCategoriaGeneral(categoria)) {
    return {
      respuesta: fallo(
        res,
        403,
        "Los pictogramas generales requieren una categoría general"
      )
    };
  }

  if (!general && !categoriaAccesible(categoria, usuario)) {
    return {
      respuesta: fallo(
        res,
        403,
        "No tenés permiso para usar esta categoría"
      )
    };
  }

  return { categoria };
};

// =====================
// PROPIEDAD Y CONSULTAS
// =====================

const verificarPropio = async (
  id_usuario,
  id_pictograma
) => {
  const { data, error } = await supabase
    .from("usuarios_pictogramas")
    .select(`
      id_usuario,
      id_pictogramas,
      pictogramas (${CAMPOS})
    `)
    .eq("id_usuario", id_usuario)
    .eq("id_pictogramas", id_pictograma)
    .maybeSingle();

  if (error) throw error;

  return (
    data &&
    data.pictogramas &&
    data.pictogramas.es_personalizado
  )
    ? data.pictogramas
    : null;
};

const buscarPictograma = async (id) => {
  const { data, error } = await supabase
    .from("pictogramas")
    .select(CAMPOS)
    .eq("id_pictogramas", id)
    .maybeSingle();

  if (error) throw error;

  return data;
};

// =====================
// DUPLICADOS
// =====================

const duplicadoGeneral = async (
  nombre,
  id_categorias,
  excluirId = null
) => {
  let query = supabase
    .from("pictogramas")
    .select("id_pictogramas, nombre")
    .eq("id_categorias", id_categorias)
    .eq("es_personalizado", false);

  if (excluirId) {
    query = query.neq("id_pictogramas", excluirId);
  }

  const { data, error } = await query;

  if (error) throw error;

  return data.some(
    (p) =>
      nombreComparable(p.nombre) ===
      nombreComparable(nombre)
  );
};

const duplicadoPropio = async (
  id_usuario,
  nombre,
  id_categorias,
  excluirId = null
) => {
  const { data, error } = await supabase
    .from("usuarios_pictogramas")
    .select(`
      id_pictogramas,
      pictogramas (
        id_pictogramas,
        id_categorias,
        nombre,
        es_personalizado
      )
    `)
    .eq("id_usuario", id_usuario);

  if (error) throw error;

  return data.some(({ pictogramas: p }) => {
    return (
      p &&
      p.es_personalizado &&
      Number(p.id_pictogramas) !== Number(excluirId) &&
      Number(p.id_categorias) === Number(id_categorias) &&
      nombreComparable(p.nombre) === nombreComparable(nombre)
    );
  });
};

// =====================
// COMPROBACIÓN DE USO
// =====================

const obtenerUso = async (id_pictograma) => {
  const tablas = [
    "tableros_pictogramas",
    "frase_pictogramas"
  ];

  for (const tabla of tablas) {
    const { data, error } = await supabase
      .from(tabla)
      .select("id_pictogramas")
      .eq("id_pictogramas", id_pictograma)
      .limit(1);

    if (error) throw error;

    if (data.length > 0) {
      return tabla;
    }
  }

  return null;
};

const asociacionCompartida = async (
  id_pictograma,
  id_usuario
) => {
  const { data, error } = await supabase
    .from("usuarios_pictogramas")
    .select("id_usuario")
    .eq("id_pictogramas", id_pictograma)
    .neq("id_usuario", id_usuario)
    .limit(1);

  if (error) throw error;

  return data.length > 0;
};

// =====================
// IMÁGENES
// =====================

const subirImagen = async (
  archivo,
  carpeta,
  nombreBase
) => {
  if (!archivo) {
    throw new Error("Falta imagen");
  }

  const extensiones = {
    "image/jpeg": "jpg",
    "image/pjpeg": "jpg",
    "image/png": "png",
    "image/webp": "webp"
  };

  const ext = extensiones[archivo.mimetype];

  if (!ext) {
    throw new Error("Formato de imagen no permitido");
  }

  const aleatorio = crypto
    .randomBytes(5)
    .toString("hex");

  const ruta =
    `${carpeta}/${nombreBase}-${Date.now()}-${aleatorio}.${ext}`;

  const { error } = await supabaseAdmin.storage
    .from("pictogramas-imagenes")
    .upload(ruta, archivo.buffer, {
      contentType: archivo.mimetype,
      upsert: false
    });

  if (error) throw error;

  const { data } = supabaseAdmin.storage
    .from("pictogramas-imagenes")
    .getPublicUrl(ruta);

  return {
    ruta,
    url: data.publicUrl
  };
};

const limpiarImagen = async (ruta) => {
  if (!ruta) return;

  const { error } = await supabaseAdmin.storage
    .from("pictogramas-imagenes")
    .remove([ruta]);

  if (error) {
    console.error(
      "No se pudo limpiar imagen:",
      error.message
    );
  }
};

// =====================
// GET /pictogramas
// GET /pictogramas/categoria/:id_categoria
// =====================

const listar = async (
  req,
  res,
  id_categoria = null
) => {
  try {
    const id_usuario = req.usuario?.id_usuario;
    const admin = req.usuario?.rol === "admin";

    let query = supabase
      .from("pictogramas")
      .select(CAMPOS);

    if (!admin) {
      query = query.eq("es_personalizado", false);
    }

    if (id_categoria !== null) {
      query = query.eq("id_categorias", id_categoria);
    }

    const { data: generales, error } = await query
      .order("id_pictogramas", { ascending: true });

    if (error) {
      return fallo(res, 500, error.message);
    }

    if (!id_usuario || admin) {
      return ok(res, generales);
    }

    const { data: relaciones, error: relError } =
      await supabase
        .from("usuarios_pictogramas")
        .select(`pictogramas (${CAMPOS})`)
        .eq("id_usuario", id_usuario);

    if (relError) {
      return fallo(res, 500, relError.message);
    }

    const propios = relaciones
      .map((r) => r.pictogramas)
      .filter(
        (p) =>
          p &&
          p.es_personalizado &&
          (
            id_categoria === null ||
            Number(p.id_categorias) ===
              Number(id_categoria)
          )
      );

    return ok(res, [
      ...generales,
      ...propios
    ]);

  } catch (error) {
    return fallo(res, 500, error.message);
  }
};

const obtenerPictogramas = (req, res) =>
  listar(req, res);

const obtenerPictogramasPorCategoria = (
  req,
  res
) => {
  if (!idValido(req.params.id_categoria)) {
    return fallo(
      res,
      400,
      "ID de categoría inválido"
    );
  }

  return listar(
    req,
    res,
    req.params.id_categoria
  );
};

// =====================
// CREACIÓN GENERAL / PERSONALIZADA
// =====================

const crear = async (
  req,
  res,
  personalizado,
  conImagen
) => {
  let archivoSubido = null;

  try {
    const id_usuario = req.usuario.id_usuario;

    const {
      id_categorias,
      nombre,
      imagen_url,
      audio_url
    } = req.body || {};

    if (!id_categorias || !nombre) {
      return fallo(
        res,
        400,
        "Faltan datos obligatorios: id_categorias o nombre"
      );
    }

    if (conImagen && !req.file) {
      return fallo(
        res,
        400,
        "Tenés que enviar una imagen en el campo imagen"
      );
    }

    const errorNombre = validarNombre(nombre);

    if (errorNombre) {
      return fallo(res, 400, errorNombre);
    }

    const check = await validarCategoria(
      res,
      id_categorias,
      id_usuario,
      !personalizado
    );

    if (check.respuesta) {
      return check.respuesta;
    }

    const repetido = personalizado
      ? await duplicadoPropio(
          id_usuario,
          nombre,
          id_categorias
        )
      : await duplicadoGeneral(
          nombre,
          id_categorias
        );

    if (repetido) {
      return fallo(
        res,
        400,
        personalizado
          ? "Ya tenés un pictograma con ese nombre en esta categoría"
          : "Ya existe un pictograma general con ese nombre en esta categoría"
      );
    }

    if (conImagen) {
      archivoSubido = await subirImagen(
        req.file,
        personalizado
          ? String(id_usuario)
          : "generales",
        personalizado
          ? `pictograma-${id_usuario}`
          : "general"
      );
    }

    const { data, error } = await supabase
      .from("pictogramas")
      .insert([
        {
          id_categorias,
          nombre: texto(nombre),
          imagen_url: conImagen
            ? archivoSubido.url
            : (imagen_url || null),
          audio_url: audio_url || null,
          es_personalizado: personalizado
        }
      ])
      .select(CAMPOS)
      .single();

    if (error) {
      await limpiarImagen(archivoSubido?.ruta);
      return fallo(res, 500, error.message);
    }

    if (personalizado) {
      const { error: relError } = await supabase
        .from("usuarios_pictogramas")
        .insert([
          {
            id_usuario,
            id_pictogramas: data.id_pictogramas
          }
        ]);

      if (relError) {
        const { error: rollbackError } =
          await supabase
            .from("pictogramas")
            .delete()
            .eq(
              "id_pictogramas",
              data.id_pictogramas
            );

        if (rollbackError) {
          console.error(
            "No se pudo revertir pictograma:",
            rollbackError.message
          );
        }

        await limpiarImagen(archivoSubido?.ruta);

        return fallo(
          res,
          500,
          relError.message
        );
      }

      await registrarHistorial(
        id_usuario,
        conImagen
          ? "crear_pictograma_con_imagen"
          : "crear_pictograma_personalizado",
        `Pictograma personalizado creado: ${data.nombre}`
      );

    } else if (conImagen) {
      await registrarHistorial(
        id_usuario,
        "crear_pictograma_general_con_imagen",
        `Pictograma general creado con imagen: ${data.nombre}`
      );
    }

    return ok(res, data, 201);

  } catch (error) {
    return fallo(res, 500, error.message);
  }
};

const crearPictograma = (req, res) =>
  crear(req, res, false, false);

const crearPictogramaPersonalizado = (req, res) =>
  crear(req, res, true, false);

const crearPictogramaPersonalizadoConImagen = (req, res) =>
  crear(req, res, true, true);

const crearPictogramaConImagen = (req, res) =>
  crear(req, res, false, true);

// =====================
// ACTUALIZAR METADATOS
// =====================

const actualizar = async (
  req,
  res,
  personalizado
) => {
  try {
    const id_usuario = req.usuario.id_usuario;
    const { id_pictograma } = req.params;

    if (!idValido(id_pictograma)) {
      return fallo(
        res,
        400,
        "ID de pictograma inválido"
      );
    }

    const actual = personalizado
      ? await verificarPropio(
          id_usuario,
          id_pictograma
        )
      : await buscarPictograma(id_pictograma);

    if (!actual) {
      return fallo(
        res,
        404,
        "Pictograma no encontrado"
      );
    }

    if (actual.es_personalizado !== personalizado) {
      return fallo(
        res,
        403,
        "Este endpoint no corresponde al tipo de pictograma"
      );
    }

    const {
      id_categorias,
      nombre,
      imagen_url,
      audio_url
    } = req.body || {};

    const cambios = {};

    if (id_categorias !== undefined) {
      const check = await validarCategoria(
        res,
        id_categorias,
        id_usuario,
        !personalizado
      );

      if (check.respuesta) {
        return check.respuesta;
      }

      cambios.id_categorias = id_categorias;
    }

    if (nombre !== undefined) {
      const errorNombre = validarNombre(nombre);

      if (errorNombre) {
        return fallo(
          res,
          400,
          errorNombre
        );
      }

      cambios.nombre = texto(nombre);
    }

    if (imagen_url !== undefined) {
      cambios.imagen_url = imagen_url;
    }

    if (audio_url !== undefined) {
      cambios.audio_url = audio_url;
    }

    if (!Object.keys(cambios).length) {
      return fallo(
        res,
        400,
        "No enviaste campos para actualizar"
      );
    }

    if (
      personalizado &&
      await asociacionCompartida(
        id_pictograma,
        id_usuario
      )
    ) {
      return fallo(
        res,
        409,
        "Este pictograma está compartido y no se puede editar desde esta cuenta"
      );
    }

    const categoriaFinal =
      cambios.id_categorias ??
      actual.id_categorias;

    const nombreFinal =
      cambios.nombre ??
      actual.nombre;

    const repetido = personalizado
      ? await duplicadoPropio(
          id_usuario,
          nombreFinal,
          categoriaFinal,
          id_pictograma
        )
      : await duplicadoGeneral(
          nombreFinal,
          categoriaFinal,
          id_pictograma
        );

    if (repetido) {
      return fallo(
        res,
        400,
        personalizado
          ? "Ya tenés un pictograma con ese nombre en esta categoría"
          : "Ya existe un pictograma general con ese nombre en esta categoría"
      );
    }

    const { data, error } = await supabase
      .from("pictogramas")
      .update(cambios)
      .eq(
        "id_pictogramas",
        id_pictograma
      )
      .eq(
        "es_personalizado",
        personalizado
      )
      .select(CAMPOS)
      .maybeSingle();

    if (error) {
      return fallo(res, 500, error.message);
    }

    if (!data) {
      return fallo(
        res,
        404,
        "Pictograma no encontrado"
      );
    }

    if (personalizado) {
      await registrarHistorial(
        id_usuario,
        "actualizar_pictograma_personalizado",
        `Pictograma personalizado actualizado: ${data.nombre}`
      );
    }

    return ok(res, data);

  } catch (error) {
    return fallo(res, 500, error.message);
  }
};

const actualizarPictograma = (req, res) =>
  actualizar(req, res, false);

const actualizarPictogramaPersonalizado = (req, res) =>
  actualizar(req, res, true);

// =====================
// ACTUALIZAR IMAGEN
// =====================

const actualizarImagen = async (
  req,
  res,
  personalizado
) => {
  try {
    const id_usuario = req.usuario.id_usuario;
    const { id_pictograma } = req.params;

    if (!idValido(id_pictograma)) {
      return fallo(
        res,
        400,
        "ID de pictograma inválido"
      );
    }

    if (!req.file) {
      return fallo(
        res,
        400,
        "Tenés que enviar una imagen en el campo imagen"
      );
    }

    const actual = personalizado
      ? await verificarPropio(
          id_usuario,
          id_pictograma
        )
      : await buscarPictograma(id_pictograma);

    if (!actual) {
      return fallo(
        res,
        404,
        "Pictograma no encontrado"
      );
    }

    if (actual.es_personalizado !== personalizado) {
      return fallo(
        res,
        403,
        "Este endpoint no corresponde al tipo de pictograma"
      );
    }

    if (
      personalizado &&
      await asociacionCompartida(
        id_pictograma,
        id_usuario
      )
    ) {
      return fallo(
        res,
        409,
        "Este pictograma está compartido y no se puede editar desde esta cuenta"
      );
    }

    const archivoSubido = await subirImagen(
      req.file,
      personalizado
        ? String(id_usuario)
        : "generales",
      personalizado
        ? `pictograma-${id_usuario}-${id_pictograma}`
        : `general-${id_pictograma}`
    );

    const { data, error } = await supabase
      .from("pictogramas")
      .update({
        imagen_url: archivoSubido.url
      })
      .eq(
        "id_pictogramas",
        id_pictograma
      )
      .eq(
        "es_personalizado",
        personalizado
      )
      .select(CAMPOS)
      .maybeSingle();

    if (error || !data) {
      await limpiarImagen(archivoSubido.ruta);

      return fallo(
        res,
        error ? 500 : 404,
        error?.message ||
          "Pictograma no encontrado"
      );
    }

    await registrarHistorial(
      id_usuario,
      personalizado
        ? "actualizar_imagen_pictograma"
        : "actualizar_imagen_pictograma_general",
      `Imagen actualizada para pictograma: ${data.nombre}`
    );

    return ok(res, data);

  } catch (error) {
    return fallo(res, 500, error.message);
  }
};

const actualizarImagenPictogramaPersonalizado = (
  req,
  res
) => actualizarImagen(req, res, true);

const actualizarImagenPictogramaGeneral = (
  req,
  res
) => actualizarImagen(req, res, false);

// =====================
// GET /pictogramas/mis-personalizados
// =====================

const obtenerMisPictogramasPersonalizados = async (
  req,
  res
) => {
  try {
    const { data, error } = await supabase
      .from("usuarios_pictogramas")
      .select(`
        id_usuario_pictograma,
        id_usuario,
        id_pictogramas,
        fecha_creacion,
        pictogramas (${CAMPOS})
      `)
      .eq(
        "id_usuario",
        req.usuario.id_usuario
      )
      .order(
        "fecha_creacion",
        { ascending: false }
      );

    if (error) {
      return fallo(
        res,
        500,
        error.message
      );
    }

    return ok(
      res,
      data
        .map((r) => r.pictogramas)
        .filter(
          (p) => p && p.es_personalizado
        )
    );

  } catch (error) {
    return fallo(
      res,
      500,
      error.message
    );
  }
};

// =====================
// ELIMINAR PICTOGRAMAS
// OPCIÓN A: BLOQUEAR SI ESTÁN EN USO
// =====================

const eliminar = async (
  req,
  res,
  personalizado
) => {
  try {
    const id_usuario = req.usuario.id_usuario;
    const { id_pictograma } = req.params;

    if (!idValido(id_pictograma)) {
      return fallo(
        res,
        400,
        "ID de pictograma inválido"
      );
    }

    const actual = personalizado
      ? await verificarPropio(
          id_usuario,
          id_pictograma
        )
      : await buscarPictograma(
          id_pictograma
        );

    if (!actual) {
      return fallo(
        res,
        404,
        "Pictograma no encontrado"
      );
    }

    if (actual.es_personalizado !== personalizado) {
      return fallo(
        res,
        403,
        "Este endpoint no corresponde al tipo de pictograma"
      );
    }

    // 1. Verificar si está en tableros o frases.
    const tablaUso = await obtenerUso(
      id_pictograma
    );

    if (tablaUso) {
      return fallo(
        res,
        409,
        "El pictograma está utilizado en tableros o frases. Quitalo de esos lugares antes de eliminarlo."
      );
    }

    if (personalizado) {
      // 2. No borrar datos compartidos.
      if (
        await asociacionCompartida(
          id_pictograma,
          id_usuario
        )
      ) {
        return fallo(
          res,
          409,
          "Este pictograma está asociado a otros usuarios y no puede eliminarse completamente"
        );
      }

      // 3. Eliminar asociación del propietario.
      const { error: relacionError } =
        await supabase
          .from("usuarios_pictogramas")
          .delete()
          .eq(
            "id_usuario",
            id_usuario
          )
          .eq(
            "id_pictogramas",
            id_pictograma
          );

      if (relacionError) {
        return fallo(
          res,
          500,
          relacionError.message
        );
      }

    } else {
      // Las FK tienen NO ACTION.
      // No puede haber asociaciones activas.
      const {
        data: relaciones,
        error: relacionesError
      } = await supabase
        .from("usuarios_pictogramas")
        .select("id_pictogramas")
        .eq(
          "id_pictogramas",
          id_pictograma
        )
        .limit(1);

      if (relacionesError) {
        return fallo(
          res,
          500,
          relacionesError.message
        );
      }

      if (relaciones.length > 0) {
        return fallo(
          res,
          409,
          "El pictograma tiene asociaciones de usuarios activas"
        );
      }
    }

    // 4. Borrar el pictograma.
    const { data, error } = await supabase
      .from("pictogramas")
      .delete()
      .eq(
        "id_pictogramas",
        id_pictograma
      )
      .eq(
        "es_personalizado",
        personalizado
      )
      .select("id_pictogramas")
      .maybeSingle();

    if (error) {
      return fallo(
        res,
        500,
        error.message
      );
    }

    if (!data) {
      return fallo(
        res,
        404,
        "Pictograma no encontrado"
      );
    }

    if (personalizado) {
      await registrarHistorial(
        id_usuario,
        "eliminar_pictograma_personalizado",
        `Pictograma personalizado eliminado: ${actual.nombre}`
      );
    }

    return ok(res, {
      mensaje: personalizado
        ? "Pictograma personalizado eliminado correctamente"
        : "Pictograma eliminado correctamente"
    });

  } catch (error) {
    return fallo(
      res,
      500,
      error.message
    );
  }
};

const eliminarPictograma = (req, res) =>
  eliminar(req, res, false);

const eliminarPictogramaPersonalizado = (
  req,
  res
) => eliminar(req, res, true);

// =====================
// EXPORTS
// =====================

module.exports = {
  obtenerPictogramas,
  obtenerPictogramasPorCategoria,
  crearPictograma,
  actualizarPictograma,
  eliminarPictograma,
  crearPictogramaPersonalizado,
  obtenerMisPictogramasPersonalizados,
  actualizarPictogramaPersonalizado,
  eliminarPictogramaPersonalizado,
  crearPictogramaPersonalizadoConImagen,
  actualizarImagenPictogramaPersonalizado,
  crearPictogramaConImagen,
  actualizarImagenPictogramaGeneral
};
